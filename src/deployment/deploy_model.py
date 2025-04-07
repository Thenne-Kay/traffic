from azureml.core import Workspace, Model
from azureml.core.webservice import AciWebservice


def deploy():
    # Initialize workspace
    ws = Workspace.from_config()

    # Get registered model
    model = Model(ws, name="traffic_light_ppo")

    # Configure deployment
    aci_config = AciWebservice.deploy_configuration(
        cpu_cores=2, memory_gb=4, tags={"framework": "SB3"}
    )

    # Deploy
    service = Model.deploy(
        workspace=ws,
        name="traffic-service",
        models=[model],
        deployment_config=aci_config,
    )
    service.wait_for_deployment(show_output=True)
    return service


deploy()