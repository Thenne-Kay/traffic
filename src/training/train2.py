import os
import sumolib
import traci
import numpy as np

from typing import Dict, List

from stable_baselines3 import PPO


import matplotlib.pyplot as plt
from datetime import datetime
import warnings
import subprocess

from src.environments.sumo_env import SumoTrafficEnv
from src.utils.utils import RewardPrinter, CustomFeatureExtractor, EpisodeCallback
from src.utils.gen_rout import dir, logg ,config_file, net_file, route_file

from azureml.core.run import Run


REFERENCE_STATES = {
    # Position: (state_pattern1, state_pattern2, ...)
    1: ("GGGggrrrrGGGggrrrr", "GGGggrrrrrGGGggrrrrr", "GGggrrrGGGg"),  # Position 1
    2: ("yyyggrrrryyyggrrrr", "yyyggrrrrryyyggrrrrr", "yyggrrryyyg"),  # Position 2
    3: ("rrrGGrrrrrrrGGrrrr", "rrrGGrrrrrrrrGGrrrrr", "rrGGrrrrrrG"),  # Position 3
    4: ("rrryyrrrrrrryyrrrr", "rrryyrrrrrrrryyrrrrr", "rryyrrrrrry"),  # Position 4
    5: ("rrrrrGGggrrrrrGGgg", "rrrrrGGGggrrrrrGGGgg", "rrrrGGgGrrr"),  # Position 5
    6: (
        "rrrrryyggrrrrryygg",
        "rrrrryyyggrrrrryyygg",
    ),  # Position 6
    7: ("rrrrrrrGGrrrrrrrGG", "rrrrrrrrGGrrrrrrrrGG", "rrrryyyyrrr"),  # Position 7
}

callbacks = [EpisodeCallback(), RewardPrinter()]


def get_normalized_phase_states():
    """Matches states allowing multiple patterns per position"""
    results = {}
    for tl_id in traci.trafficlight.getIDList():
        state = traci.trafficlight.getRedYellowGreenState(tl_id)
        results[tl_id] = -1  # Default if no match

        for position, patterns in REFERENCE_STATES.items():
            if any(state.startswith(p) for p in patterns):
                results[tl_id] = position
                break

    return results


# Global storage for waiting time histories
waiting_time_storage = {}


def store_waiting_times(env, label):
    """
    Stores waiting times from an environment with a given label

    Parameters:
    - env: Environment instance (with waiting_time_history)
    - label: Unique identifier for this dataset
    """
    waiting_time_storage[label] = {
        "data": np.array(env.waiting_time_history),
        "time_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def plot_stored_waiting_times(labels_to_compare, figsize=(12, 6)):
    """
    Plots previously stored waiting times for comparison

    Parameters:
    - labels_to_compare: List of labels to plot (must match store labels)
    - figsize: Figure dimensions
    """
    if not waiting_time_storage:
        raise ValueError(
            "No waiting time data stored. Call store_waiting_times() first."
        )

    plt.figure(figsize=figsize)
    colors = plt.cm.tab10.colors  # Use matplotlib's color cycle

    max_length = max(
        len(waiting_time_storage[label]["data"]) for label in labels_to_compare
    )

    for i, label in enumerate(labels_to_compare):
        if label not in waiting_time_storage:
            raise KeyError(f"Label '{label}' not found in stored data")

        data = waiting_time_storage[label]["data"]
        time_axis = np.arange(len(data))

        plt.plot(
            time_axis,
            data,
            color=colors[i % len(colors)],
            linestyle=["-", "--", ":", "-."][i % 4],
            linewidth=1.5,
            label=f"{label} ({len(data)} steps)",
        )

    plt.title("Waiting Time Comparison Across Runs")
    plt.xlabel("Time Step")
    plt.ylabel("Waiting Time")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


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
    for i in range(1,20):
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


