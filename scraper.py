import pandas as pd
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow,Flow
from google.auth.transport.requests import Request
import os
import pickle
from lxml import html
import requests
import re
from urllib.parse import urlsplit
from collections import deque
from bs4 import BeautifulSoup
import xlsxwriter
from crawler import extract_parent

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SAMPLE_SPREADSHEET_ID_input = '1zVvsjSCJflvSJDkMx0gqaqHmBCpRhnx1baRQof_Ivo8'
SAMPLE_RANGE_NAME = 'A1:AA1000'

def readGoogleSheet():
    global values_input, service
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES) # here enter the name of your downloaded JSON file
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result_input = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID_input,
                                range=SAMPLE_RANGE_NAME).execute()
    values_input = result_input.get('values', [])

    if not values_input:
        print('No data found.')


def get_Emails(url):
    unscraped = deque([url])

    scraped = set()

    emails = set()

    while len(unscraped):
        url = unscraped.popleft()
        scraped.add(url)

        parts = urlsplit(url)

        base_url = "{0.scheme}://{0.netloc}".format(parts)
        if '/' in parts.path:
            path = url[:url.rfind('/') + 1]
        else:
            path = url

        try:
            response = requests.get(url)
        except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
            continue

        new_emails = set(re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.com", response.text, re.I))
        emails.update(new_emails)

        soup = BeautifulSoup(response.text, 'lxml')

        for anchor in soup.find_all("a"):
            if "href" in anchor.attrs:
                link = anchor.attrs["href"]
            else:
                link = ''

                if link.startswith('/'):
                    link = base_url + link

                elif not link.startswith('http'):
                    link = path + link

                if not link.endswith(".gz"):
                    if not link in unscraped and not link in scraped:
                        unscraped.append(link)
    return emails


def listToString(s):
    str1 = ""
    for ele in s:
        str1 += ele
        str1 += ', '
    return str1


def mainFunction():
    cnt = 1
    workbook = xlsxwriter.Workbook('result.xlsx')
    worksheet = workbook.add_worksheet()

    for src_link in values_input:
        emails = extract_parent(src_link[0])
        print(emails)
        if cnt == 1:
            worksheet.write('A' + str(cnt), "Website Link(origin)")
            worksheet.write('B' + str(cnt), "Website Link(founded)")
            worksheet.write('C' + str(cnt), "Emails")
            cnt = cnt + 1
            continue

        if len(emails) == 0:
            worksheet.write('A' + str(cnt), src_link[0])
            worksheet.write('B' + str(cnt), "error")
            worksheet.write('C' + str(cnt), "error")
            cnt = cnt + 1
        else:
            for each in emails:
                worksheet.write('A' + str(cnt), src_link[0])
                worksheet.write('B' + str(cnt), each['url'])
                worksheet.write('C' + str(cnt), each['email'])
                cnt = cnt + 1

    workbook.close()


readGoogleSheet()
mainFunction()
