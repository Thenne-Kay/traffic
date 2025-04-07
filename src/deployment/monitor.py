from azureml.core import Workspace
from azureml.core.webservice import Webservice


def monitor_service():
    # Initialize workspace
    ws = Workspace.from_config()

    # Get deployed service
    service = Webservice(ws, name="traffic-service")

    # Print logs
    print(service.get_logs())

    # Return metrics
    return service.get_metrics()


monitor_service()