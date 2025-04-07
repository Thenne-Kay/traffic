from azureml.core import Workspace, Dataset
from azureml.data.datapath import DataPath
import os

# Initialize workspace
ws = Workspace.from_config()

# Get default datastore
datastore = ws.get_default_datastore()

# Create dataset from directory
dataset = Dataset.File.upload_directory(
    src_dir=os.path.abspath("src/sumo_configs"),  # Local directory with SUMO configs
    target=DataPath(datastore, "sumo_configs"),  # Target in blob storage
    overwrite=True,
    show_progress=True,
)

# Register dataset for reuse
dataset.register(
    workspace=ws,
    name="sumo_configs",
    description="SUMO simulation configuration files",
    create_new_version=True,
)

print(f"Uploaded {len(dataset.to_path())} config files to Azure Blob Storage")
