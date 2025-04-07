import xml.etree.ElementTree as ET
import random
import httpx  # type: ignore
from xml.dom import minidom
import requests
from operator import itemgetter

import subprocess
import time

import os
import argparse
import shutil

from dotenv import load_dotenv

load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument("--config_path", type=str)
parser.add_argument(
    "--output_dir", type=str, default="/outputs", help="Writable output directory"
)
args = parser.parse_args()

writable_config_dir = "outputs/sumo_configs"
shutil.copytree(args.config_path, writable_config_dir, dirs_exist_ok=True)


dir = "outputs/models"
logg = "outputs/models/logg"

config_file = os.path.join(writable_config_dir, "osm4.sumocfg")
net_file = os.path.join(writable_config_dir, "osm4.net.xml")
route_file = os.path.join(writable_config_dir, "osm4.rou.xml")
trip_file1 = os.path.join(writable_config_dir, "custom_trips2.trips.xml")
route_file1 = os.path.join(writable_config_dir, "your_routes3.rou.xml")
output_file = writable_config_dir


# Replace with your Microsoft Azure Maps API Key
key = "2oQ2IayBB4tfBjtZkef5RMHXGCjfnxjkC3KLTPth7cS3lAxODnz1JQQJ99BDAC5RqLJcK7viAAAgAZMP2MLC"

# Define output path for .rou.xml file

# Edge to coordinates mapping
edge_to_coords = {
    "44487115#0": (-1.28336587627992, 36.82350916473359),
    "4741911#2": (-1.2849402419963587, 36.820726691875606),
    "4741910#1": (-1.2854374099168278, 36.81951898025666),
    "4741911#6": (-1.286242348236308, 36.81820470583933),
    "44487115#1": (-1.2834842496676846, 36.82326051822439),
}

# Allowed destinations
allowed_destinations = ["1151069805#0", "297314798#5", "297314798#3", "4741911#4"]

def run_duarouter(net_file, trip_file, route_file):
    time.sleep(0.1)
    """
    Run duarouter with the specified input files and save the generated route file.

    Parameters:
    - net_file: Path to the SUMO network file (.net.xml).
    - trip_file: Path to the SUMO trip file (.trips.xml).
    - route_file: Path to the output route file (.rou.xml).
    """
    # Delay to ensure any process is ready
    time.sleep(0.1)

    # Define the command and its arguments
    command = [
        "duarouter",  # This tells it to run the duarouter tool
        "--net-file",
        net_file,
        "--trip-files",
        trip_file,
        "--output-file",
        route_file,
        "--verbose",
    ]

    try:
        # Execute the command
        result = subprocess.run(command, check=True, text=True, capture_output=True)

        # Success message and output
        print("✅ duarouter ran successfully.")
        print(result.stdout)

        if result.stderr:
            print("⚠️ Errors:")
            print(result.stderr)

    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with error:\n{e.stderr}")

    except FileNotFoundError:
        print(
            "🚫 Error: 'duarouter' command not found. Make sure it's installed and in your PATH."
        )


def get_traffic_flow(lat, lon):
    """Fetch traffic data from Azure Maps API."""
    url = "https://atlas.microsoft.com/traffic/flow/segment/json"
    params = {
        "subscription-key": os.getenv("maps_key"),
        "api-version": "1.0",
        "style": "relative",
        "zoom": 10,
        "query": f"{lat},{lon}",
    }

    try:
        response = httpx.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        flow_data = data.get("flowSegmentData", {})
        current_speed = flow_data.get("currentSpeed", "N/A")
        free_flow_speed = flow_data.get("freeFlowSpeed", "N/A")
        current_travel_time = flow_data.get("currentTravelTime", "N/A")
        free_flow_travel_time = flow_data.get("freeFlowTravelTime", "N/A")
        congestion_info = (
            f"Speed: {current_speed} km/h | "
            f"Free Flow Speed: {free_flow_speed} km/h | "
            f"Travel Time: {current_travel_time} sec | "
            f"Free Flow Travel Time: {free_flow_travel_time} sec"
        )
        print(
            f"Traffic congestion at latitude {lat}, longitude {lon}: {congestion_info}"
        )
        print(
            "-------------------------------------------------------------------------"
        )

        if current_speed < free_flow_speed * 0.5:
            return "congested"
        elif current_speed < free_flow_speed * 0.8:
            return "moderate"
        return "freeFlow"
    except Exception as e:
        print(f"⚠️ Traffic API Error: {e}")
        return "unknown"

def get_weather(lat, lon):
    """Fetch traffic data from Azure Maps API."""

    url = "https://atlas.microsoft.com/weather/currentConditions/json"
    params = {
        "subscription-key": key,
        "api-version": "1.0",
        "unit": "metric",  # or "imperial"
        "details": "true",  # Optional: Include air quality, pollution, etc.
        "style": "relative",
        "zoom": 10,
        "query": f"{lat},{lon}",
    }

    print("✅⚠️✅⚠️✅⚠️✅⚠️✅⚠️✅⚠️✅⚠️✅⚠️✅⚠️✅⚠️✅⚠️✅⚠️✅⚠️✅⚠️✅⚠️✅⚠️✅⚠️✅⚠️✅⚠️ ")

    try:
        response = httpx.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        current_weather = data["results"][0]  # Extract the first result

        Condition= {current_weather['phrase']}
        temp= {current_weather['temperature']['value']}
        daytime = {current_weather["isDayTime"]}

        weather_info = (
            f"condition: {Condition} "
            f"temp: {temp}"
            f"day?: {daytime} "
        )
        print(
            f"weather at latitude {lat}, longitude {lon}: {weather_info}"
        )
        print(
            "-------------------------------------------------------------------------"
        )

        if Condition=={"Rain"} or daytime== {False}:
            return 1
        return 0
    except Exception as e:
        print(f"⚠️ weather API Error: {e}")
        return 0


def create_sumo_trips_file(edge_to_coords, trips_file):
    """Generate sorted SUMO trips file."""
    # Collect all trips first
    trips = []
    trip_id = 5000   

    for edge, (lat, lon) in edge_to_coords.items():
        traffic_level = get_traffic_flow(lat, lon)
        num_vehicles = (
            50
            if traffic_level == "congested"
            else 10 if traffic_level == "moderate" else 1
        )
        print(num_vehicles)
        for i in range(num_vehicles):
            trips.append(
                {
                    "id": f"veh{trip_id}",
                    "depart": i * 5,
                    "from": edge,
                    "to": random.choice(allowed_destinations),
                }
            )
            trip_id += 1

    # Sort trips by departure time
    trips.sort(key=itemgetter("depart"))

    # Create XML structure
    root = ET.Element(
        "routes",
        {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "http://sumo.dlr.de/xsd/routes_file.xsd",
        },
    )

    ET.SubElement(root, "vType", id="veh_passenger2", vClass="passenger")

    # Writing trips to XML
    for trip in trips:
        trip_element = ET.SubElement(
            root,
            "trip",
            {
                "id": trip["id"],
                "type": "veh_passenger2",
                "depart": f"{trip['depart']:.2f}",
                "departLane": "best",
                "departSpeed": "max",
                "from": trip["from"],
                "to": trip["to"],
            },
        )

    # Convert the ElementTree to a string and pretty-print it
    xml_str = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")

    # Use minidom to pretty-print the XML
    xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ")

    # Write to file with proper formatting
    with open(trips_file, "w", encoding="utf-8") as f:
        f.write(xml_str)

    print(f"✅ Sorted SUMO trips file created: {trips_file}")


def get_safe_speed():
    url = 'https://api.jsonbin.io/v3/b/67f2fc7f8561e97a50f9ee30/latest'
    headers = {
        "X-Master-Key": os.getenv("X-Master-Key"),
        "X-Access-Key": os.getenv("X-Access-Key"),
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    try:
        weather = data['record']['results'][0]
    except (KeyError, IndexError) as e:
        print("Error: Unexpected data structure or empty results")
        return 999  # default safe speed fallback

    precip_mm = weather['precipitationSummary']['pastHour']['value']
    wind_kph = weather['wind']['speed']['value']
    visibility_km = weather['visibility']['value']
    cloud_cover = weather['cloudCover']
    humidity = weather['relativeHumidity']

    def calculate_safe_speed(precip_mm, wind_kph, visibility_km, cloud_cover, humidity):
        base_speed = 80
        if precip_mm > 0.5:
            base_speed -= 20
        elif precip_mm > 0.1:
            base_speed -= 10

        if wind_kph > 30:
            base_speed -= 10
        elif wind_kph > 20:
            base_speed -= 5

        if visibility_km < 1:
            base_speed -= 30
        elif visibility_km < 3:
            base_speed -= 15

        if cloud_cover > 80:
            base_speed -= 5

        if humidity > 90:
            base_speed -= 5

        return max(30, int(base_speed))

    return calculate_safe_speed(precip_mm, wind_kph, visibility_km, cloud_cover, humidity)
