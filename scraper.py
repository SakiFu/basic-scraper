import sys
import requests
import re
import geocoder
from bs4 import BeautifulSoup

INSPECTION_DOMAIN = 'http://info.kingcounty.gov'
INSPECTION_PATH = '/health/ehs/foodsafety/inspections/Results.aspx'
INSPECTION_PARAMS = {
    'Output': 'W',
    'Business_Name': '',
    'Business_Address': '',
    'Longitude': '',
    'Latitude': '',
    'City': '',
    'Zip_Code': '',
    'Inspection_Type': 'All',
    'Inspection_Start': '',
    'Inspection_End': '',
    'Inspection_Closed_Business': 'A',
    'Violation_Points': '',
    'Violation_Red_Points': '',
    'Violation_Descr': '',
    'Fuzzy_Search': 'N',
    'Sort': 'B'
}
LOCAL_COPY = 'inspection_page.html'


def get_inspection_page(**kwargs):
    params = INSPECTION_PARAMS.copy()
    for k, v in kwargs.items():
        if k in INSPECTION_PARAMS:
            params[k] = v
    resp = requests.get(INSPECTION_DOMAIN + INSPECTION_PATH, params)
    resp.raise_for_status()
    write_inspection_page(resp.content)
    return resp.content, resp.encoding


def write_inspection_page(content):
    with open(LOCAL_COPY, 'w') as fh:
        fh.write(content)


def load_inspection_page():
    with open(LOCAL_COPY, 'r') as fh:
        content = fh.read()
    return content, 'utf-8'


def parse_source(content, encoding='utf-8'):
    parsed = BeautifulSoup(content, 'html5lib', from_encoding=encoding)
    return parsed


def extract_data_listings(content):
    id_finder = re.compile(r'PR[\d]+~')
    return content.find_all('div', id=id_finder)


def has_two_tds(elem):
    is_tr = elem.name == 'tr'
    children = elem.find_all('td', recursive=False)
    has_two = len(children) == 2
    return is_tr and has_two


def clean_data(td):
    data = td.string
    try:
        return data.strip(" \n:-")
    except AttributeError:
        return u""


def extract_restaurant_metadata(elem):
    metadata_rows = elem.find('tbody').find_all(
        has_two_tds, recursive=False
    )
    rdata = {}
    current_label = ''
    for row in metadata_rows:
        key_cell, val_cell = row.find_all('td', recursive=False)
        new_label = clean_data(key_cell)
        current_label = new_label if new_label else current_label
        rdata.setdefault(current_label, []).append(clean_data(val_cell))
    return rdata


def is_inspection_row(elem):
    if not elem.name == 'tr':
        return False
    td_children = elem.find_all('td', recursive=False)
    has_four = len(td_children) == 4
    this_text = clean_data(td_children[0]).lower()
    contains_word = 'inspection' in this_text
    does_not_start = not this_text.startswith('inspection')
    return has_four and contains_word and does_not_start


def extract_score_data(listing):
    inspection_rows = listing.find_all(is_inspection_row)
    samples = len(inspection_rows)
    total = high_score = average = 0
    for row in inspection_rows:
        strval = clean_data(row.find_all('td')[2])
        try:
            intval = int(strval)
        except (ValueError, TypeError):
            samples -= 1
        else:
            total += intval
            high_score = intval if intval > high_score else high_score
    if samples:
        average = total / float(samples)
    data = {
        u'Average Score': average,
        u'High Score': high_score,
        u'Total Inspections': samples
    }
    return data


def generate_results(test=False):
    kwargs = {
        'Inspection_Start': '7/1/2014',
        'Inspection_End': '7/1/2015',
        'Zip_Code': '98004'
    }
    if test:
        content, encoding = load_inspection_page()
    else:
        content, encoding = get_inspection_page(**kwargs)
    doc = parse_source(content, encoding)
    listings = extract_data_listings(doc)
    for listing in listings:
        metadata = extract_restaurant_metadata(listing)
        score_data = extract_score_data(listing)
        metadata.update(score_data)
        yield metadata


def get_geojson(result):
    address = " ".join(result.get('Address', ''))
    if not address:
        return None
    geocoded = geocoder.google(address)
    return geocoded.geojson


if __name__ == '__main__':
    import pprint
    test = len(sys.argv) > 1 and sys.argv[1] == 'test'
    for result in generate_results(test):
        geo_result = get_geojson(result)
        pprint.pprint(geo_result)
