Traffic Control with Reinforcement Learning (RL) and Weather Data Integration
This project aims to develop an AI model for controlling traffic flow in a smart city using Reinforcement Learning (RL), SUMO (Simulation of Urban Mobility), and real time data integration. The model is trained on Azure Machine Learning (AML), using data from a Microsoft Fabric Lakehouse and APIs for real-time weather and traffic flow data.
Key Components:
•	SUMO Traffic Simulation: Simulation of traffic flow in urban environments, where the RL agent controls traffic lights, vehicle movement, and routing. Kenyatta Avenue (-1.2832425480418013, 36.82353601664417), a busy intersection at the heart of Nairobi was chosen as the training environment.
•	Reinforcement Learning (RL): The model learns optimal traffic control strategies by interacting with the SUMO environment. It is a single agent model optimized to control up to five traffic light intersections
•	Weather Data: Integrated weather data influences vehicle speeds, traffic conditions, and agent behavior in the simulation.
•	Traffic-flow Data: Traffic-flow data at four sections of the road are monitored and updated every training episode. The data is obtained from an Azure Maps API.
•	Azure Machine Learning (AML): Training and model management are done on AML to scale the RL training process efficiently.
•	Microsoft Fabric Lakehouse: Weather data is retrieved from Fabric Lakehouse, processed, and stored in a JSON bin via an API for integration with the RL model.
•	Power BI: Post-training analysis of vehicle data (position, speed) every 100 steps, visualized using Power BI for insights into the traffic flow and agent performance.
Resources:
•	Python 3.1+
•	Fabric Lakehouse
•	Azure Machine Learning Workspace
•	Jsonbin/Azure Function App
•	SUMO configuration files
•	Azure Maps Account for traffic flow and weather APIs
•	Azure Blob Storage
•	Power Bi for post training analysis


```
└── 📁traffic
    └── 📁.azureml
        └── config.json
    └── 📁azureml
        └── compute.yaml
        └── conda_dependencies.yml
        └── Dockerfile
    └── 📁outputs
    └── 📁scripts
        └── run_training.bat
        └── setup_win.bat
    └── 📁src
        └── __init__.py
        └── 📁deployment
            └── .amlignore
            └── deploy_model.py
            └── monitor.py
            └── see_train.py
            └── submit_training.py
            └── upload_configs.py
        └── 📁environments
            └── __init__.py
            └── sumo_env.py
        └── 📁sumo_configs
            └── osm.poly.xml.gz
        └── 📁training
            └── __init__.py
            └── train2.py
        └── 📁utils
            └── __init__.py
            └── gen_rout.py
            └── make_csv.py
            └── utils.py
    └── .env
    └── .gitignore
```
