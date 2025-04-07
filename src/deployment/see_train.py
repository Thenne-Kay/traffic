from azureml.core import Workspace, Experiment

ws = Workspace.from_config()
experiment = Experiment(ws, "cloud-training")
run = list(experiment.get_runs())[0]  # Get latest run

print(f"Run status: {run.status}")
print(f"View at: {run.get_portal_url()}")
