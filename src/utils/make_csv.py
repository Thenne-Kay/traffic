import os
import pytz
import datetime
import pandas as pd
import traci


from src.utils.gen_rout import output_file



class csvCallback():
    def __init__(self):
        self.count=0
        self.packVehicleData=[]
        self.packTLSData = []
        self.packBigData = []


    def get_current_time_str(self):
        # Use Nairobi timezone
        utc_now = pytz.utc.localize(datetime.datetime.utcnow())
        nairobi_now = utc_now.astimezone(pytz.timezone("Africa/Nairobi"))
        return nairobi_now.strftime("%Y-%m-%d %H:%M:%S")

    def flatten_list(self,_2d_list):
        flat_list = []
        for element in _2d_list:
            if type(element) is list:
                for item in element:
                    flat_list.append(item)
            else:
                flat_list.append(element)
        return flat_list

    def output_data(self):
        vehicles = traci.vehicle.getIDList()
        trafficlights = traci.trafficlight.getIDList()

        for i in range(0, len(vehicles)):

            # Function descriptions
            # https://sumo.dlr.de/docs/TraCI/Vehicle_Value_Retrieval.html
            # https://sumo.dlr.de/pydoc/traci._vehicle.html#VehicleDomain-getSpeed
            vehid = vehicles[i]
            x, y = traci.vehicle.getPosition(vehicles[i])
            coord = [x, y]
            lon, lat = traci.simulation.convertGeo(x, y)
            gpscoord = [lon, lat]
            spd = round(traci.vehicle.getSpeed(vehicles[i]) * 3.6, 2)
            edge = traci.vehicle.getRoadID(vehicles[i])
            lane = traci.vehicle.getLaneID(vehicles[i])
            displacement = round(traci.vehicle.getDistance(vehicles[i]), 2)
            turnAngle = round(traci.vehicle.getAngle(vehicles[i]), 2)
            nextTLS = traci.vehicle.getNextTLS(vehicles[i])

            # Packing of all the data for export to CSV/XLSX
            vehList = [
                self.get_current_time_str(),
                vehid,
                coord,
                gpscoord,
                spd,
                edge,
                lane,
                displacement,
                turnAngle,
                nextTLS,
            ]
            idd = traci.vehicle.getLaneID(vehicles[i])

            tlsList = []

            for k in range(0, len(trafficlights)):

                # Function descriptions
                # https://sumo.dlr.de/docs/TraCI/Traffic_Lights_Value_Retrieval.html#structure_of_compound_object_controlled_links
                # https://sumo.dlr.de/pydoc/traci._trafficlight.html#TrafficLightDomain-setRedYellowGreenState

                if idd in traci.trafficlight.getControlledLanes(trafficlights[k]):

                    tflight = trafficlights[k]
                    tl_state = traci.trafficlight.getRedYellowGreenState(trafficlights[k])
                    tl_phase_duration = traci.trafficlight.getPhaseDuration(
                        trafficlights[k]
                    )
                    tl_lanes_controlled = traci.trafficlight.getControlledLanes(
                        trafficlights[k]
                    )
                    tl_program = traci.trafficlight.getCompleteRedYellowGreenDefinition(
                        trafficlights[k]
                    )
                    tl_next_switch = traci.trafficlight.getNextSwitch(trafficlights[k])

                    # Packing of all the data for export to CSV/XLSX
                    tlsList = [
                        tflight,
                        tl_state,
                        tl_phase_duration,
                        tl_lanes_controlled,
                        tl_program,
                        tl_next_switch,
                    ]

            # Pack Simulated Data
            self.packBigDataLine = self.flatten_list([vehList, tlsList])
            self.packBigData.append(self.packBigDataLine)

    def save_traffic_data_to_excel(self,output_path):

        columnnames = [
            "dateandtime",
            "vehid",
            "coord",
            "gpscoord",
            "spd",
            "edge",
            "lane",
            "displacement",
            "turnAngle",
            "nextTLS",
            "tflight",
            "tl_state",
            "tl_phase_duration",
            "tl_lanes_controlled",
            "tl_program",
            "tl_next_switch",
        ]

        df = pd.DataFrame(self.packBigData, columns=columnnames)

        # with pd.ExcelWriter(output_path) as writer:
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            # Sheet 1: Vehicle Data
            df[
                [
                    "dateandtime",
                    "vehid",
                    "coord",
                    "gpscoord",
                    "spd",
                    "edge",
                    "lane",
                    "displacement",
                    "turnAngle",
                    "nextTLS",
                ]
            ].to_excel(writer, sheet_name="Vehicle Data", index=False)

            # Sheet 2: Traffic Light Data
            df[
                [
                    "dateandtime",
                    "tflight",
                    "tl_state",
                    "tl_phase_duration",
                    "tl_lanes_controlled",
                    "tl_program",
                    "tl_next_switch",
                ]
            ].to_excel(writer, sheet_name="Traffic Light Data", index=False)

        print(f"Excel file saved at: {output_path}")
        self.packVehicleData = []
        self.packTLSData = []
        self.packBigData = []
