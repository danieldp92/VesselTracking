import os
import sys
import time
from datetime import datetime
from enum import Enum
from apscheduler.schedulers.blocking import BlockingScheduler

# Local imports
import crawler
from utils import save_csv, load_csv
from crawler import get_ports

port_file = "ports.csv"
data_folder = "data"


class PortSize(Enum):
    XSMALL = 0
    SMALL = 1
    MEDIUM = 2
    LARGE = 3
    XLARGE = 4


def get_enum_value(enum_class, string):
    try:
        return getattr(enum_class, string.upper()).value
    except AttributeError:
        return 0


def tracking_ports(ports):
    """
    Tracks all ports of a specific country
    :param country: the country to analyze
    :param size: the port size (PortSize class type)
    :return:
    """
    # Create data today folder
    today_folder = os.path.join(data_folder, datetime.today().strftime('%Y-%m-%d %Hh%Mm'))
    today_tms = int(datetime.today().timestamp())
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

            print("Last ports")
            vessel_ports = crawler.get_vessel_last_ports(vessel['mmsi'])
            port_filename = f"vessel_{vessel['mmsi']}_{today_tms}_ports.csv"
            save_csv(vessel_ports, os.path.join(port_folder, port_filename))

            print("Events")
            events = crawler.get_vessel_events(vessel['mmsi'])
            event_filename = f"vessel_{vessel['mmsi']}_{today_tms}_events.csv"
            save_csv(events, os.path.join(port_folder, event_filename))


if __name__ == '__main__':
    country = 'Netherlands'
    size = PortSize.MEDIUM

    # Download or read locally the port list
    if not os.path.exists(port_file):
        all_ports = get_ports()
        save_csv(all_ports, port_file)
    else:
        all_ports = load_csv(port_file)

    # # Takes only ports of a specific country and greater or equal than a specific size
    ports = [port for port in all_ports if port['country'] == country and
             port['type'] == 'Port' and get_enum_value(PortSize, port['size']) >= size.value]

    print(f"Ports found under country {country}: {len(ports)}\n")
    if not ports:
        sys.exit(0)

    # Create data folder
    if not os.path.exists(data_folder):
        os.mkdir(data_folder)

    scheduler = BlockingScheduler()
    scheduler.add_job(tracking_ports, 'interval', hours=1, args=[ports])
    scheduler.start()



    # while True:
    #     today_folder = os.path.join(data_folder, datetime.today().strftime('%Y-%m-%d %Hh%mm'))
    #     today_tms = int(datetime.today().timestamp())
    #
    #     # Create data today folder
    #     if not os.path.exists(today_folder):
    #         os.mkdir(today_folder)
    #
    #     # Extract info for each port
    #     j = 1
    #     for port in ports:
    #         print(f"Analysis of port '{port['name']}' ({j} of {len(ports)})")
    #         j += 1
    #
    #         port_folder = os.path.join(today_folder, port['name'])
    #         os.mkdir(port_folder)
    #
    #         port_id = port['id']
    #
    #         print("\nINPORT extraction")
    #         inport_vessels = crawler.get_inport_vessels(port_id)
    #         inport_filename = f"port_{port_id}_{today_tms}_inport.csv"
    #         save_csv(inport_vessels, os.path.join(port_folder, inport_filename))
    #
    #         print("\nArrivals extraction")
    #         arrival_vessels = crawler.get_arrivals(port_id)
    #         arrival_filename = f"port_{port_id}_{today_tms}_arrivals.csv"
    #         save_csv(arrival_vessels, os.path.join(port_folder, arrival_filename))
    #
    #         print("\nINPORT calls extraction")
    #         inport_calls = crawler.get_inport_calls(port_id)
    #         calls_filename = f"port_{port_id}_{today_tms}_calls.csv"
    #         save_csv(inport_calls, os.path.join(port_folder, calls_filename))
    #
    #         print(f"\nVESSEL analysis. Total vessels: {len(arrival_vessels)}")
    #         i = 1
    #         for vessel in arrival_vessels:
    #             print(f"\nAnalysis vessel with mmsi {vessel['mmsi']} ({i} of {len(arrival_vessels)})")
    #             i += 1
    #
    #             print("Last ports")
    #             vessel_ports = crawler.get_vessel_last_ports(vessel['mmsi'])
    #             port_filename = f"vessel_{vessel['mmsi']}_{today_tms}_ports.csv"
    #             save_csv(vessel_ports, os.path.join(port_folder, port_filename))
    #
    #             print("Events")
    #             events = crawler.get_vessel_events(vessel['mmsi'])
    #             event_filename = f"vessel_{vessel['mmsi']}_{today_tms}_events.csv"
    #             save_csv(events, os.path.join(port_folder, event_filename))
    #     time.sleep(7200)


