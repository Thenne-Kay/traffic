from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

from gymnasium import spaces
import gymnasium as gym

import torch as th
import torch.nn as nn

from src.utils.gen_rout import run_duarouter, create_sumo_trips_file
from src.utils.gen_rout import output_file, edge_to_coords
from src.utils.gen_rout import net_file, trip_file1, route_file1






class EpisodeCallback(BaseCallback):
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_rewards = []
        self.episode_reward = 0.0
        # self.count=0

    def _on_step(self) -> bool:
        # Add current reward
        self.episode_reward += self.locals["rewards"][0]
        # self.count+=1

        # Check if the episode is done
        if self.locals["dones"][0]:
            self.episode_rewards.append(self.episode_reward)
            print(f"Episode done! Total reward: {self.episode_reward}")
            create_sumo_trips_file(edge_to_coords, trip_file1)
            run_duarouter(net_file, trip_file1, route_file1)
            print("-------new trips generated-----------")
            self.episode_reward = 0.0
            
            
        # if self.count%20==0:
        #     self.episode_rewards.append(self.episode_reward)
        #     print(f"count done! Total reward: {self.episode_reward}")
        #     create_sumo_trips_file(edge_to_coords, trip_file1)
        #     run_duarouter(net_file, trip_file1, route_file1)
        #     print("-------new trips generated-----------")
        #     self.episode_reward = 0.0
            

        return True


class RewardPrinter(BaseCallback):
    def __init__(self):
        super().__init__()
        self.episode_count = 0

    def _on_step(self) -> bool:
        # Print reward for each completed episode
        if "infos" in self.locals:
            for info in self.locals["infos"]:
                if "episode" in info:
                    self.episode_count += 1
                    reward = info["episode"]["r"]
                    print(
                        f"Episode {self.episode_count}, Step {self.num_timesteps}: Reward = {reward:.2f}"
                    )
        return True


class CustomFeatureExtractor(BaseFeaturesExtractor):
    """
    Feature extractor for 10-dimensional observation space
    Handles both vehicle and traffic light features
    """

    def __init__(self, observation_space: gym.spaces.Box, features_dim: int = 128):
        super().__init__(observation_space, features_dim)

        # Calculate number of traffic lights from observation shape
        # Assuming first 4 values are vehicle/time features, then 2 per traffic light
        self.num_tls = (observation_space.shape[0] - 4) // 2

        # Network architecture
        self.net = nn.Sequential(
            nn.Linear(
                observation_space.shape[0], 256
            ),  # Input layer for all 10 features
            nn.ReLU(),
            nn.Linear(256, features_dim),
            nn.ReLU(),
        )

        # Optional: Separate processing paths
        self.vehicle_net = nn.Sequential(
            nn.Linear(4, 64), nn.ReLU()  # First 4 features (time + vehicle metrics)
        )

        self.tl_net = nn.Sequential(
            nn.Linear(self.num_tls * 2, 64), nn.ReLU()  # Traffic light features
        )

        self.combined_net = nn.Sequential(
            nn.Linear(64 + 64, features_dim), nn.ReLU()  # Combined features
        )

    def forward(self, observations: th.Tensor) -> th.Tensor:
        # print(f"Observations: {observations.shape}")  # Debugging print statement
        vehicle_features = self.vehicle_net(observations[:, :4])
        tl_features = self.tl_net(observations[:, 4:])
        combined = th.cat([vehicle_features, tl_features], dim=1)
        # print(f"Combined Features: {combined.shape}")  # Debugging print statement
        return self.combined_net(combined)
