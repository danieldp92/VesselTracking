import os
import sys
from datetime import datetime

import crawler
from utils import save_csv, load_csv
from crawler import get_ports


port_file = "ports.csv"
data_folder = "data"

filters = {
    'country': 'Netherlands',
    'type': 'Port',
    'size': 'Medium'
}


def generate_numeric_size_value(size):
    if size == "XLarge":
        return 4
    elif size == "Large":
        return 3
    elif size == "Medium":
        return 2
    elif size == "Small":
        return 1
    else:
        return 0


def port_filtering(ports):
    ports_filtered = []

    for port in ports:
        if port['country'] == filters['country'] and port['type'] == filters['type']:
            size = generate_numeric_size_value(port['size'])
            filter_size = generate_numeric_size_value(filters['size'])
            if size >= filter_size:
                ports_filtered.append(port)

    return ports_filtered


if __name__ == '__main__':
    if not os.path.exists(port_file):
        all_ports = get_ports()
        save_csv(all_ports, port_file)
    else:
        all_ports = load_csv(port_file)

    ports = port_filtering(all_ports)

    print(f"Ports found under country {filters['country']}: {len(ports)}\n")
    if not ports:
        sys.exit(0)

    # Create data folder
    if not os.path.exists(data_folder):
        os.mkdir(data_folder)

    today_folder = os.path.join(data_folder, datetime.today().strftime('%Y-%m-%d %Hh%mm'))
    today_tms = int(datetime.today().timestamp())

    # Create data today folder
    if not os.path.exists(today_folder):
        os.mkdir(today_folder)

    # Extract info for each port
    j = 1
    for port in ports:
        print(f"Analysis of port '{port['name']}' ({j} of {len(ports)})")
        j += 1

        port_folder = os.path.join(today_folder, port['name'])
        os.mkdir(port_folder)

        port_id = port['id']

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

            vessel_ports = crawler.get_vessel_last_ports(vessel['mmsi'])
            port_filename = f"vessel_{vessel['mmsi']}_{today_tms}_ports.csv"
            save_csv(vessel_ports, os.path.join(port_folder, port_filename))

            events = crawler.get_vessel_events(vessel['mmsi'])
            event_filename = f"vessel_{vessel['mmsi']}_{today_tms}_events.csv"
            save_csv(events, os.path.join(port_folder, event_filename))