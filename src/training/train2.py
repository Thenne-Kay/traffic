import subprocess
# subprocess.run(["pip", "install", "dotenv"], check=True)

import os
import sumolib
import traci
import numpy as np

from typing import Dict, List

from stable_baselines3 import PPO


import matplotlib.pyplot as plt
from datetime import datetime
import warnings

from src.environments.sumo_env import SumoTrafficEnv
from src.utils.utils import RewardPrinter, CustomFeatureExtractor, EpisodeCallback
from src.utils.gen_rout import dir, logg ,config_file, net_file, route_file

from azureml.core.run import Run




# callback functions for the training
callbacks = [EpisodeCallback(), RewardPrinter()]


# sumo enviroment configs setup
x2 = SumoTrafficEnv(
    config_file,
    net_file,
    route_file,
    False,
    40001,
)
env = x2

policy_kwargs = dict(
    features_extractor_class=CustomFeatureExtractor,
    features_extractor_kwargs=dict(features_dim=128),
    net_arch=dict(pi=[64, 64], vf=[64, 64]),  # Shared network architecture
)


run = Run.get_context()


# Log hyperparameters
run.log("Algorithm", "PPO")
run.log("Policy", "MlpPolicy")
run.log("Network Architecture", "64x64")


# Create PPO model with proper settings
model = PPO(
    "MlpPolicy",  # For Box observation space
    env,
    policy_kwargs=policy_kwargs,
    verbose=1,
    learning_rate=3e-4,
    n_steps=1024,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    ent_coef=0.01,
    tensorboard_log=logg,
)

# Disable all warnings
warnings.filterwarnings("ignore")
subprocess.Popen(["tensorboard", "--logdir", logg, "--port", "6006"])


TIMESTEPS = 11000


# Training with just reward printing
print("Starting training...")
try:
    for i in range(1,31):
        model.learn(
            total_timesteps=TIMESTEPS,
            reset_num_timesteps=False,
            callback=callbacks,
            progress_bar=False,
            tb_log_name="PPO",
        )
        model.save(f"{dir}/{TIMESTEPS*i}")  # Save the trained model
    print("Training completed successfully!")

except Exception as e:
    print(f"Training failed: {str(e)}")

finally:
    env.close()

