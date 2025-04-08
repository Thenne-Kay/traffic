from stable_baselines3 import PPO
from azureml.core.run import Run


import os
import sumolib
import traci
import numpy as np


from src.environments.sumo_env import SumoTrafficEnv
from src.utils.utils import RewardPrinter, CustomFeatureExtractor, EpisodeCallback
from src.utils.gen_rout import dir, logg, config_file, net_file, route_file

import matplotlib.pyplot as plt
from datetime import datetime


model_path = "saved_models/165000.zip"
waiting_time_storage={}
run=Run.get_context()


def store_waiting_times(env, label):
    """
    Stores waiting times from an environment with a given label

    Parameters:
    - env: Environment instance (with waiting_time_history)
    - label: Unique identifier for this dataset
    """
    
    for times in  np.array(env.waiting_time_history):
        run.log(label,times)
   


x = SumoTrafficEnv(config_file, net_file, route_file, False, 40001)
obs, info = x.reset()
# Run 10 steps


model = PPO.load(model_path, env=x)
for step in range(4000):
    # Action selection - random for demonstration
    # In practice, replace this with your model's action selection
    # Random action (0 or 1)
    action, _states = model.predict(obs, deterministic=True)
    # Take a step
    obs, reward, terminated, truncated, info = x.step(action)
    # obs, reward, terminated, truncated, info = y.step(action2)
    if (len(x.traffic_lights) > 0) and terminated == False:
        tl_status = x.get_traffic_light_status()

        for tl_id in x.traffic_lights:
            try:
                lanes = traci.trafficlight.getControlledLanes(tl_id)
            except:
                print("- Could not retrieve controlled lanes")
    else:
        print("\nNo traffic lights found in the simulation")
        # Check if episode ended
        if terminated or truncated:
            print("\nEpisode ended early!")
            # Close the environment
            x.close()
            # y.close()
            print("\nSimulation complete.")
            break

store_waiting_times(x, "trained")


# x = SumoTrafficEnv(config_file, net_file, route_file, False, 40001)
obs, info = x.reset()

action = np.array([0, 0, 0, 0, 0], dtype=np.int8)
for step in range(4000):
    # Action selection - random for demonstration
    # In practice, replace this with your model's action selection
    # Random action (0 or 1)

    # Take a step
    obs, reward, terminated, truncated, info = x.step(action)
    # obs, reward, terminated, truncated, info = y.step(action2)
    if (len(x.traffic_lights) > 0) and terminated == False:
        tl_status = x.get_traffic_light_status()

        for tl_id in x.traffic_lights:
            try:
                lanes = traci.trafficlight.getControlledLanes(tl_id)
            except:
                print("- Could not retrieve controlled lanes")
    else:
        print("\nNo traffic lights found in the simulation")
        # Check if episode ended
        if terminated or truncated:
            print("\nEpisode ended early!")
            # Close the environment
            x.close()
            # y.close()
            print("\nSimulation complete.")
            break
store_waiting_times(x, "untrained")


