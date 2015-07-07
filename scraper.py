import requests

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
    with open('inspection_page.html', 'w') as fh:
        fh.write(content)


def load_inspection_page():
    with open('inspection_page.html', 'r') as fh:
        content = fh.read()
    return content, 'utf-8'
