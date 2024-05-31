
import string
import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
import json
from datetime import date
from tqdm import tqdm


def search(char="", skip=0, cdcr_num=""):
    """Generates urls based on parameters, sends a GET request and then
    returns response's text. If a cdcr_num is passed, then the url is for an
    individual's record page, and skip is not required. If a char is passed,
    then the url is for a general keyword search and cdcr_num is not
    required. Skip indicates which page of results is being queried."""

    if cdcr_num == "":
        base_url = "https://apps.cdcr.ca.gov/api/ciris/v1/incarceratedpersons?"
        url1 = f"{base_url}lastName={char}&%24limit=20&%24sort%5BfullName%5D=1&%24skip={skip}"
    else:
        base_url = "https://apps.cdcr.ca.gov/api/ciris/v1/parole/"
        url1 = f"{base_url}{cdcr_num}"
    r1 = requests.get(url1)
    return r1.text


def get_params(response):
    """Uses BeautifulSoup to parse the response of a general keyword search.
    Returns pages—the number of pages of results—and a binary indicator of
    whether the search returned results (found)"""
    soup = bs(response, 'lxml')
    table = soup.find('p')
    j = json.loads(table.text)

    pages = j['total'] // 20  # divides by 20 to see number of pages

    if len(j['data']) > 0:
        found = 1
    else:
        found = 0

    return pages, found


def go_time(char, pages):
    for x in tqdm(range(pages + 1), colour="green", desc=f"{char}", leave=False):
        # loops over each
        # page
        # of main search
        # results
        r1 = search(char=char, skip=x)
        j = json.loads(r1)
        data = j['data']
        cdcr_nums = [x['cdcrNumber'] for x in data]
        for c in tqdm(cdcr_nums, colour="blue", desc="Page",
                      leave=False):
            r2 = search(cdcr_num=c)
            j = json.loads(r2)
            record = j['incarceratedPerson']
            b = {
                'cdcrNumber': record['cdcrNumber'],
                'typeCode': record['typeCode'],
                'lastName': record['lastName'],
                'firstName': record['firstName'],
                'middleName': record['middleName'],
                'nameSuffix': record['nameSuffix'],
                'fullName': record['fullName'],
                'age': record['age'],
                'admissionDate': record['admissionDate'],
                'location': record['location'],
                'locationHref': record['locationHref'],
                'commitmentCounty': record['commitmentCounties'],
                'locationAddress': record['locationAddress'],
                }
            try:
                b['paroleEligibleDate'] = j['paroleInformation'][
                    'paroleEligibleDate']
                b['bphActions'] = j['paroleInformation']['bphActions']
            except KeyError:
                ...

            DETAILS.append(b)
    return


def main():
    for char in tqdm(SEARCHES, colour="red", desc="Total"):
        r = search(char=char)
        pages, success = get_params(r)
        if not success:
            continue
        go_time(char, pages)

    df = pd.DataFrame(DETAILS)
    df.to_csv(f'{OUT_NAME}.csv')


OUT_NAME = f'./cdcr_roster_{str(date.today())}'
DETAILS = []
SEARCHES = list(string.ascii_uppercase)

if __name__ == "__main__":
    main()
