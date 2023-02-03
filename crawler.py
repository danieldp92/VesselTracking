import requests
from fake_useragent import UserAgent
import re
import time
from bs4 import BeautifulSoup
from retry_decorator import *

# Local imports
from exceptions import ScraperException


main_url = 'https://www.myshiptracking.com'
table_types = ["port_database", "inport", "arrivals", "port_calls", "event"]
DEFAULT_WAITING_TIME = 0.5


def __get_total_pages(soup):
    try:
        footer_text = soup.find('div', {'class': 'footer'}).find('div', {'class': None}).text
        footer_text = footer_text.split(' ')
    except Exception as e:
        print(e)
        raise ScraperException("Invalid scraping rules for the function 'get_total_pages'.")

    n_elements = int(footer_text[-2].strip())
    n_elements_per_page = int(footer_text[-4].strip())

    pages = n_elements/n_elements_per_page
    if pages.is_integer():
        pages = int(pages)
    else:
        pages = int(pages) + 1

    return pages


def __row_info_extraction(row, type="port_database"):
    """ Extract info in a table row, based on the table type
    :param type: type of the table to analyze. Valid values:
        port_database: table containing all ports
        inport: vessels in a specific port
        arrivals: vessel expected arrivals in a specific port
        port_calls: departure/arrival in a port"
        event: vessel event"
    :return: dict with the info extrated
    """

    if type not in table_types:
        raise ValueError(f"Invalid type value. Accepted values: {'|'.join(table_types)}")

    cells = row.find_all('td')
    if type == "port_database":
        attributes = ['id', 'name', 'country', 'type', 'size', 'url']
        port = dict.fromkeys(attributes, None)

        uri = cells[1].find('a')['href']
        uri_split = uri.split('-')

        port['id'] = uri_split[-1]
        port['name'] = cells[1].text
        port['country'] = uri_split[-3].capitalize()
        port['type'] = cells[2].text
        port['size'] = cells[3].text
        port['url'] = main_url + uri

        return port
    elif type == "inport":
        attributes = ['vessel_name', 'alpha2code', 'arrived', 'dwt', 'grt', 'built', 'size', 'url']
        vessel = dict.fromkeys(attributes, None)

        vessel['vessel_name'] = cells[0].find('span').text

        # Search the vessel's country inside its name
        vessel_split = vessel['vessel_name'].split(" ")
        if len(vessel_split) > 1:
            last_word = vessel_split[-1]
            if last_word[0] == "[" and last_word[-1] == "]":
                vessel['alpha2code'] = re.sub('[\[\]]', '', last_word).strip()
                vessel['vessel_name'] = " ".join(vessel_split[:-1])
            else:
                vessel['vessel_name'] = " ".join(vessel_split)

        vessel['arrived'] = cells[1].text

        if cells[2].text != "---":
            vessel['dwt'] = cells[2].text
        if cells[3].text != "---":
            vessel['grt'] = cells[3].text
        if cells[4].text != "---":
            vessel['built'] = cells[4].text

        vessel['size'] = cells[5].text
        vessel['url'] = main_url + cells[0].find('a')['href']

        return vessel
    elif type == "arrivals":
        attributes = ['mmsi', 'vessel_name', 'alpha2code', 'port', 'eta', 'url']
        arrival = dict.fromkeys(attributes, None)

        arrival['mmsi'] = cells[0].text
        arrival['vessel_name'] = cells[1].find('span').text

        # Search the vessel's country inside its name
        vessel_split = arrival['vessel_name'].split(" ")
        if len(vessel_split) > 1:
            last_word = vessel_split[-1]
            if last_word[0] == "[" and last_word[-1] == "]":
                arrival['alpha2code'] = re.sub('[\[\]]', '', last_word).strip()
                arrival['vessel_name'] = " ".join(vessel_split[:-1])
            else:
                arrival['vessel_name'] = " ".join(vessel_split)

        arrival['port'] = cells[2].text.strip().capitalize()
        arrival['eta'] = cells[3].text
        arrival['url'] = main_url + cells[2].find('a')['href']

        return arrival
    elif type == "port_calls":
        attributes = ['event', 'time', 'port', 'vessel_name', 'alpha2code', 'url']
        port_call = dict.fromkeys(attributes, None)

        port_call['event'] = cells[1].text
        port_call['time'] = cells[2].text
        port_call['port'] = cells[3].text.strip()
        port_call['vessel_name'] = cells[4].find('span').text

        # Search the vessel's country inside its name
        vessel_split = port_call['vessel_name'].split(" ")
        if len(vessel_split) > 1:
            last_word = vessel_split[-1]
            if last_word[0] == "[" and last_word[-1] == "]":
                port_call['alpha2code'] = re.sub('[\[\]]', '', last_word).strip()
                port_call['vessel_name'] = " ".join(vessel_split[:-1])
            else:
                port_call['vessel_name'] = " ".join(vessel_split)

        port_call['url'] = main_url + cells[4].find('a')['href']

        return port_call
    elif type == "event":
        attributes = ['time', 'event', 'detail', 'latitude', 'longitude', 'position', 'destination', 'destination_alpha2code']
        event = dict.fromkeys(attributes, None)

        event['time'] = cells[0].text
        event['event'] = cells[1].text.strip()

        detail_td = cells[2]
        if detail_td.text.strip() not in ["", " "]:
            # Span check
            if detail_td.find_all('span'):
                event['detail'] = ". ".join([span.text.strip() for span in detail_td.find_all('span')])
            else:
                event['detail'] = detail_td.text.strip()

        position_divs = cells[3].find_all('div', {'class': 'area_txt_1lines'})
        if position_divs:
            lat_lon = position_divs[0].text.strip()
            if lat_lon != "":
                lat_lon = lat_lon.split('/')
                event['latitude'] = lat_lon[0].strip()
                event['longitude'] = lat_lon[1].strip()

            if len(position_divs) > 1 and position_divs[1].text.strip() != "":
                event['position'] = position_divs[1].text.strip()

        destination = cells[3].find('div', {'class': 'small'}).text.strip()
        if destination != "":
            # Search the port's country inside the name
            pos_split = destination.split(" ")
            if len(pos_split) > 1:
                first_word = pos_split[0]
                if first_word[0] == "[" and first_word[-1] == "]":
                    event['destination_alpha2code'] = re.sub('[\[\]]', '', first_word).strip()
                    event['destination'] = " ".join(pos_split[1:])
                else:
                    event['destination'] = " ".join(pos_split)

        return event
    else:
        raise ValueError("Invalid value for parameter 'type'")


@retry(Exception, tries=5, timeout_secs=5)
def __table_info_extraction(url, type="port_database"):
    base_url = url
    ua = UserAgent()

    header = {'User-Agent': ua.random}
    page = requests.get(base_url, headers=header)

    soup = BeautifulSoup(page.content, 'html.parser')
    try:
        pages = __get_total_pages(soup)
    except:
        pages = 0

    ports = []
    for i in range(1, pages+1):
        print(f"Analyzing page {i} of {pages}")
        if i > 1:
            base_url = url + '&page=' + str(i)

            header = {'User-Agent': ua.random}
            page = requests.get(base_url, headers=header)
            soup = BeautifulSoup(page.content, 'html.parser')

        rows = soup.find('tbody', {'class': 'table-body'}).find_all('tr')
        for row in rows:
            port = __row_info_extraction(row, type)
            ports.append(port)

        time.sleep(DEFAULT_WAITING_TIME)

    return ports


def get_ports():
    url = main_url + '/ports?sort=ID'
    return __table_info_extraction(url, "port_database")


def search_port(port):
    if not isinstance(port, str):
        raise TypeError(f"port parameter: expected str instance, {type(port)} found. ")

    url = main_url + "/ports?sort=ID&search=" + port.lower()
    return __table_info_extraction(url, "port_database")


def get_inport_vessels(port_id):
    url = main_url + '/inport?sort=TIME&pid=' + str(port_id)
    return __table_info_extraction(url, "inport")


def get_arrivals(port_id):
    url = main_url + '/estimate?sort=TIME&pid=' + str(port_id)
    return __table_info_extraction(url, "arrivals")


def get_inport_calls(port_id):
    url = main_url + "/ports-arrivals-departures/?sort=TIME&pid=" + str(port_id)
    return __table_info_extraction(url, "port_calls")


def get_vessel_last_ports(mmsi):
    """
    Get the list of 'Last Port Calls' for a specific vessel
    :param mmsi: the vessel mmsi code
    :return: a list with all ports visited by the vessel
    """
    url = main_url + "/ports-arrivals-departures/?sort=TIME&mmsi=" + str(mmsi)
    return __table_info_extraction(url, "port_calls")


def get_vessel_events(mmsi):
    url = main_url + "/vessel-events?sort=TIME&mmsi=" + str(mmsi)
    return __table_info_extraction(url, "event")