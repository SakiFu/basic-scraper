import sys
import requests
import re
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


if __name__ == '__main__':
    kwargs = {
        'Inspection_Start': '7/1/2014',
        'Inspection_End': '7/1/2015',
        'Zip_Code': '98004'
    }
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        content, encoding = load_inspection_page()
    else:
        content, encoding = get_inspection_page(**kwargs)
    doc = parse_source(content, encoding)
    listings = extract_data_listings(doc)
    for listing in listings[:5]:
        metadata_rows = listing.find('tbody').find_all(
            has_two_tds, recursive=False
        )
        for row in metadata_rows:
            for td in row.find_all('td', recursive=False):
                print repr(clean_data(td)),
            print
        print
