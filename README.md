# Traffic Control with Reinforcement Learning (RL) and Real Time Data Integration

This project aims to develop an AI model for controlling traffic flow in a smart city using **Reinforcement Learning (RL)**, **SUMO (Simulation of Urban Mobility)**, and real-time data integration. The model is trained on **Azure Machine Learning (AML)**, using data from a **Microsoft Fabric Lakehouse** and APIs for real-time **weather** and **traffic flow** data.

---

## Key Components

### 1. SUMO Traffic Simulation
Simulates traffic flow in urban environments, where the RL agent controls traffic lights, vehicle movement, and routing.  
**Location**: Kenyatta Avenue (Latitude: -1.2832425480418013, Longitude: 36.82353601664417), a busy intersection in Nairobi’s central business district.

### 2. Reinforcement Learning (RL)
A single-agent RL model trained to control up to **five traffic light intersections**, learning optimal strategies through interaction with the SUMO simulation environment.

### 3. Weather Data
Real-time weather conditions influence vehicle speed limits, road behavior, and agent decision-making. This data is pulled from the Microsoft Fabric Lakehouse and served to the simulation environment.

### 4. Traffic-flow Data
Live traffic data from **four sections of the road** is fetched using the **Azure Maps API** and updated every training episode. This data dynamically adjusts vehicle generation to reflect real-world traffic flow.

### 5. Azure Machine Learning (AML)
Used for scalable training, experiment tracking, and deployment of the RL model.

### 6. Microsoft Fabric Lakehouse
Acts as the data hub for weather data, which is then pushed to a JSONBin or accessed via an Azure Function App.

### 7. Power BI
Post-training analysis of traffic simulation data (vehicle position and speed every 100 steps) is visualized in Power BI to evaluate agent performance and traffic efficiency.

---

## Resources and Tools

| Tool / Service                 | Function                                                                 |
|-------------------------------|--------------------------------------------------------------------------|
| Python 3.10+                  | Main programming language for RL model, simulation logic, and API access |
| SUMO                          | Traffic simulation environment                                           |
| Azure Machine Learning        | Training, model management, and scaling                                 |
| Microsoft Fabric Lakehouse    | Storage and management of weather data                                  |
| Azure Maps Account            | Access to live weather and traffic flow APIs                            |
| JSONBin / Azure Function App  | Middleware for serving weather data to the simulation                   |
| Azure Blob Storage            | Stores output files and vehicle logs                                    |
| Power BI                      | Visualizes traffic performance and simulation outcomes                  |

---

## Output

After training, the model generates detailed logs of every vehicle’s position and speed every 100 simulation steps. These logs are analyzed using Power BI to assess how effectively the RL agent managed traffic under various weather and traffic conditions.

```
└── 📁traffic
    └── 📁.azureml
        └── config.json
    └── 📁azureml
        └── compute.yaml
        └── conda_dependencies.yml
        └── Dockerfile
    └── 📁saved_models
        └── 165000.zip
        └── 📁images
            └── model15.png
            └── trained-loading.png
            └── untrained-loading.png
    └── 📁scripts
        └── run_training.bat
        └── setup_win.bat
    └── 📁src
        └── __init__.py
        └── 📁deployment
            └── deploy_model.py
            └── monitor.py
            └── see_train.py
            └── submit_loading.py
            └── submit_training.py
            └── upload_configs.py
        └── 📁environments
            └── __init__.py
            └── sumo_env.py
        └── 📁sumo_configs
            └── osm.poly.xml.gz
            └── osm4.net.xml
            └── osm4.rou.xml
            └── osm4.sumocfg
        └── 📁training
            └── __init__.py
            └── loading.py
            └── train2.py
        └── 📁utils
            └── __init__.py
            └── gen_rout.py
            └── make_csv.py
            └── utils.py
    └── .amlignore
    └── .env
    └── .gitignore
    └── README.md
    └── setup.md
```
