import csv

from crawler import get_ports
from utils import save_csv

if __name__ == '__main__':
    csv_file = "ports.csv"

    ports = get_ports()
    save_csv(ports, csv_file)