from azureml.core import Workspace, Experiment, Environment, Dataset
from azureml.core import ScriptRunConfig
from azureml.core.compute import AmlCompute, ComputeTarget
from azureml.core.compute_target import ComputeTargetException


import sys
import os
from dotenv import load_dotenv

load_dotenv()

path_to_src=os.getenv("path_to_src")

sys.path.append(path_to_src)


def submit_job():
    # Initialize workspace
    ws = Workspace.from_config()
    config_dataset = Dataset.get_by_name(ws, name="sumo_configs")

    # # Create environment
    # env = Environment.from_dockerfile(
    #     name="sumo-rl-env",
    #     dockerfile=="./azureml/Dockerfile",
    #     conda_specification=="./azureml/conda_dependencies.yml"
    # )

    # Create environment FROM YOUR DOCKERFILE
    env = Environment.from_dockerfile(
        name="sumo-rl-env5",
        dockerfile="./azureml/Dockerfile",  # Path to your Dockerfile
        conda_specification="./azureml/conda_dependencies.yml",  # Optional: Conda deps
    )

    compute_name = "cpu-cluster1"
    try:
        cluster = ComputeTarget(ws, compute_name)
        print(f"Using existing cluster: {compute_name}")
    except ComputeTargetException:
        print(f"Creating new cluster: {compute_name}")
        config = AmlCompute.provisioning_configuration(
            vm_size="Standard_DS2_v2",
            min_nodes=0,
            max_nodes=1,
            idle_seconds_before_scaledown=300,
        )
        cluster = ComputeTarget.create(ws, compute_name, config)
        cluster.wait_for_completion(show_output=True)

    # Configure job
    src = ScriptRunConfig(
        source_directory=".",
        script="src/training/loading.py",
        arguments=[
            "--config_path", config_dataset.as_mount(),
            "--output_dir", "./",
            ],  # Mount configs from blob
        compute_target="cpu-cluster1",
        environment=env,
    )
    
    # Submit experiment
    experiment = Experiment(ws, "cloud-loading")
    return experiment.submit(src)


submit_job()
print("here we are")
