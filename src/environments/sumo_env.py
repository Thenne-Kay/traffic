import traci
import os
import gymnasium as gym
from gymnasium import spaces
from azureml.core.run import Run


import numpy as np

import time

from src.utils.gen_rout import get_weather, dir, edge_to_coords, get_safe_speed
from src.utils.make_csv import csvCallback 


class SumoTrafficEnv(gym.Env):
    """Advanced SUMO Environment with per-light control"""

    def __init__(
        self,
        sumo_config: str,
        net_file: str,
        route_file: str,
        use_gui: bool = False,
        max_steps: int = 1000,
    ):
        super().__init__()

        # Configuration
        self.sumo_config = sumo_config
        self.net_file = net_file
        self.route_file = route_file
        self.use_gui = use_gui
        self.max_steps = max_steps
        self.waiting_time_history = []  # Track waiting times per step
        self.current_step_waiting = 0  # Track current step waiting
        # State tracking
        self.current_step = 0
        self.sumo_started = False
        self.arrived_count = 0
        self.run=Run.get_context()
        self.csvclass=csvCallback()
        self.episode=0
        self.lat, self.lon = next(iter(edge_to_coords.values()))
        
        self.max_speed=get_safe_speed()

        # Initialize spaces
        self.traffic_lights = []  # Will be populated in _ensure_traci_started
        self.action_space = spaces.MultiBinary(1)  # Start with size 1, will resize

        # Observation space: [time_progress, vehicle_count, stopped_vehicles, avg_speed] + light_states
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(10,), dtype=np.float32
        )

        # Start TraCI connection
        self._ensure_traci_started()

    def _ensure_traci_started(self):
        """Initialize or restart TraCI connection"""
        if not self.sumo_started:
            sumo_binary = "sumo-gui" if self.use_gui else "sumo"
            traci.start(
                [
                    sumo_binary,
                    "-c",
                    self.sumo_config,
                    "--net-file",
                    self.net_file,
                    "--route-files",
                    self.route_file,
                    "--quit-on-end",
                ]
            )

            self.traffic_lights = sorted(traci.trafficlight.getIDList())
            self.action_space = spaces.MultiBinary(len(self.traffic_lights))
            self.sumo_started = True
            time.sleep(0.1)  # Connection stabilization

            self.set_max_speed2(self.max_speed)

    def reset(self, seed=None, **kwargs):
        """Reset the environment"""
        try:
            if self.sumo_started:
                traci.close()
                self.sumo_started = False

            self._ensure_traci_started()
            self.current_step = 0
            self.arrived_count = 0
            return self._get_observation(), {}

        except Exception as e:
            print(f"Reset error: {e}")
            self.sumo_started = False
            raise

    def step(self, action: np.ndarray):
        """
        Execute one time step
        Args:
            action: Array where each element corresponds to a traffic light:
                   0 = keep current phase
                   1 = switch to next phase
        """

        try:
            # Validate action
            if len(action) != len(self.traffic_lights):
                raise ValueError(
                    f"Action size {len(action)} doesn't match number of lights {len(self.traffic_lights)}"
                )

            # Apply actions to traffic lights
            for tl_idx, tl_action in enumerate(action):
                if tl_action == 1:  # Switch phase
                    tl_id = self.traffic_lights[tl_idx]
                    current_phase = traci.trafficlight.getPhase(tl_id)
                    traci.trafficlight.setPhase(tl_id, (current_phase + 1) % 4)

            # Advance simulation
            vehicle_ids = traci.vehicle.getIDList()
            self.current_step_waiting = sum(
                traci.vehicle.getWaitingTime(v) for v in vehicle_ids
            )
            self.waiting_time_history.append(self.current_step_waiting)
            traci.simulationStep()
            self.current_step += 1
            self.arrived_count += traci.simulation.getArrivedNumber()
            num_vehicles = traci.vehicle.getIDCount()

            # Get new state
            obs = self._get_observation()
            reward = self._calculate_reward()
            self.run.log("rewards",reward)
            # Check if any vehicles have ever been in the simulation
            if num_vehicles > 0:
                self.vehicles_started = True

            # Termination condition: Either max steps reached OR all vehicles have arrived (after vehicles were introduced)
            terminated = (self.current_step >= self.max_steps) or (
                self.vehicles_started and (num_vehicles == 0)  ) 

            # Optional: Add early termination conditions
            truncated = False

            # Debug output
            if self.current_step % 50 == 0:
                print(
                    f"Step {self.current_step}: Reward={reward:.2f} | Active lights changed: {sum(action)}"
                )
                print(
                    f"\nStep {self.current_step}, Vehicles: {num_vehicles}, Arrived: {self.arrived_count}"
                )

            if self.current_step % 100 == 0 and self.max_steps==40001 :
                self.csvclass.output_data()

            if(terminated) :
                output_path=os.path.join(dir, "docs")
                os.makedirs(output_path, exist_ok=True)
                output_path=os.path.join(output_path, "sheet" + f"{self.episode}.xlsx")
                self.episode+=1
                self.csvclass.save_traffic_data_to_excel(output_path)
                self.run.log("episode_length",self.current_step)
                print("✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅ " )  

            return obs, reward, terminated, truncated, {}

        except traci.exceptions.FatalTraCIError as e:
            print(f"SUMO connection lost: {e}")
            self.sumo_started = False
            return (
                np.zeros(self.observation_space.shape),
                -10,
                True,
                False,
                {"error": "SUMO crashed"},
            )

    def _get_observation(self) -> np.ndarray:
        """Enhanced observation with per-light information"""
        try:
            # Basic traffic metrics
            vehicle_ids = traci.vehicle.getIDList()
            speeds = [traci.vehicle.getSpeed(v) * 3.6 for v in vehicle_ids]

            obs = [
                self.current_step / self.max_steps,  # Time progress
                len(vehicle_ids) / 100,  # Vehicle count
                sum(1 for v in vehicle_ids if traci.vehicle.getSpeed(v) < 0.1)
                / 10,  # Stopped vehicles
                np.mean(speeds) / 50 if speeds else 0,  # Avg speed
            ]

            # Per-light information (first 3 lights max)
            for tl_id in self.traffic_lights[:3]:
                # Phase info
                phase = traci.trafficlight.getPhase(tl_id)
                obs.append(phase / 7.0)  # Normalized

                # Queue lengths (simplified)
                incoming_lanes = traci.trafficlight.getControlledLanes(tl_id)
                queue_length = sum(
                    traci.lane.getLastStepHaltingNumber(lane) for lane in incoming_lanes
                )
                obs.append(min(queue_length / 20, 1.0))  # Cap at 20 vehicles

            # Pad if needed
            while len(obs) < 10:
                obs.append(0.0)

            return np.array(obs[:10], dtype=np.float32)

        except traci.exceptions.FatalTraCIError:
            return np.zeros(self.observation_space.shape)

    def set_max_speed(self,reduction_factor=0.9):
        # return

        for veh_id in traci.vehicle.getIDList():
            current_max_speed = traci.vehicle.getMaxSpeed(veh_id)
            new_max_speed = current_max_speed * reduction_factor
            traci.vehicle.setMaxSpeed(veh_id, new_max_speed)

        # # Process vehicle types (for future vehicles)
        # for type_id in traci.vehicletype.getIDList():
        #     current_type_speed = traci.vehicletype.getMaxSpeed(type_id)
        #     new_type_speed = current_type_speed * reduction_factor
        #     traci.vehicletype.setMaxSpeed(type_id, new_type_speed)
        
        
    def set_max_speed2(self,max_speed=80):
        # return

        for veh_id in traci.vehicle.getIDList():
            current_max_speed = traci.vehicle.getMaxSpeed(veh_id)
            if(current_max_speed>max_speed) :
                traci.vehicle.setMaxSpeed(veh_id, max_speed)

        # # Process vehicle types (for future vehicles)
        # for type_id in traci.vehicletype.getIDList():
        #     current_type_speed = traci.vehicletype.getMaxSpeed(type_id)
        #     new_type_speed = current_type_speed * reduction_factor
        #     traci.vehicletype.setMaxSpeed(type_id, new_type_speed)

    def get_traffic_light_status(self):
        """Returns detailed phase information including duration and state"""
        status = {}
        for tl_id in traci.trafficlight.getIDList():
            program = traci.trafficlight.getAllProgramLogics(tl_id)[0]
            current_phase = traci.trafficlight.getPhase(tl_id)
            status[tl_id] = {
                "phase_index": current_phase,
                "phase_duration": program.phases[current_phase].duration,
                "phase_state": program.phases[current_phase].state,
                "min_duration": program.phases[current_phase].minDur,
                "max_duration": program.phases[current_phase].maxDur,
            }
        return status

    def get_all_phase_states(self):
        """Returns dictionary of {tl_id: current_phase_state} for all traffic lights"""
        return {
            tl_id: traci.trafficlight.getRedYellowGreenState(tl_id)
            for tl_id in traci.trafficlight.getIDList()
        }

    def _calculate_reward(self) -> float:
        """Improved reward function with debugging"""
        try:
            vehicle_ids = traci.vehicle.getIDList()
            if not vehicle_ids:
                print("No vehicles in simulation - neutral reward")
                return 100

            # Calculate components
            waiting_times = [traci.vehicle.getWaitingTime(v) for v in vehicle_ids]
            speeds = [traci.vehicle.getSpeed(v) * 3.6 for v in vehicle_ids]  # km/h

            # Calculate metrics
            total_waiting = sum(waiting_times)
            avg_speed = np.mean(speeds) if speeds else 0

            # Weighted reward components
            reward = (avg_speed * 0.1) - (total_waiting * 0.01)
            return float(reward)

        except Exception as e:
            print(f"Reward calculation error: {e}")
            return 0.0

    def close(self):
        """Cleanup method"""
        try:
            if self.sumo_started and traci.isConnected():
                traci.close()
            self.sumo_started = False
        except:
            traci.close()
            pass
