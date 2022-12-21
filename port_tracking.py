import sys
import json
import os
from datetime import datetime

import crawler
# from crawler import search_port, get_inport_vessels
from utils import pretty_table, save_csv

data_folder = "data"


def find_id(port_id, ports):
    port_id = str(port_id)
    for port in ports:
        if port['id'] == port_id:
            return True

    return False


if __name__ == '__main__':
    port = "Rotterdam"

    # Create data folder
    if not os.path.exists(data_folder):
        os.mkdir(data_folder)

    today_folder = os.path.join(data_folder, datetime.today().strftime('%Y-%m-%d %Hh%mm'))
    today_tms = int(datetime.today().timestamp())

    ports = crawler.search_port(port)
    print(f"Ports found under {port.upper()}: {len(ports)}\n")
    if not ports:
        sys.exit(0)

    pretty_table(ports)

    port_id = input("\nInsert the port id: ")
    if not find_id(port_id, ports):
        print("Port id not found.")
        sys.exit(0)

    # Create data today folder
    if not os.path.exists(today_folder):
        os.mkdir(today_folder)

    # Create port folder
    i = 0
    while i < len(ports) and ports[i]['id'] != str(port_id):
        i += 1

    if i == len(ports):
        print(f"No port found under id {port_id}")
        sys.exit(0)

    port_folder = os.path.join(today_folder, ports[i]['name'])
    os.mkdir(port_folder)

    print("\nINPORT extraction")
    inport_vessels = crawler.get_inport_vessels(port_id)
    inport_filename = f"port_{port_id}_{today_tms}_inport.csv"
    save_csv(inport_vessels, os.path.join(port_folder, inport_filename))

    print("\nArrivals extraction")
    arrival_vessels = crawler.get_arrivals(port_id)
    arrival_filename = f"port_{port_id}_{today_tms}_arrivals.csv"
    save_csv(arrival_vessels, os.path.join(port_folder, arrival_filename))

    print("\nINPORT calls extraction")
    inport_calls = crawler.get_inport_calls(port_id)
    calls_filename = f"port_{port_id}_{today_tms}_calls.csv"
    save_csv(inport_calls, os.path.join(port_folder, calls_filename))

    print(f"\nVESSEL analysis. Total vessels: {len(arrival_vessels)}")
    i = 1
    for vessel in arrival_vessels:
        print(f"\nAnalysis vessel with mmsi {vessel['mmsi']} ({i} of {len(arrival_vessels)})")
        i += 1

        ports = crawler.get_vessel_last_ports(vessel['mmsi'])
        port_filename = f"vessel_{vessel['mmsi']}_{today_tms}_ports.csv"
        save_csv(ports, os.path.join(port_folder, port_filename))

        events = crawler.get_vessel_events(vessel['mmsi'])
        event_filename = f"vessel_{vessel['mmsi']}_{today_tms}_events.csv"
        save_csv(events, os.path.join(port_folder, event_filename))