import re
import requests
import requests.exceptions
from urllib.parse import urlsplit
from collections import deque
from bs4 import BeautifulSoup

def extract_parent(starting_url):

    parent_url = starting_url.replace("http://", "").replace("https://", "").split('/')[0]
    unprocessed_urls = deque([starting_url])

    processed_urls = set()

    emails = set()
    cnt = 0
    cnt_child_urls = 0
    emails_all = []
    result = []
    while len(unprocessed_urls):
        if (cnt == (1 + cnt_child_urls)) or (cnt == 30):
            break
        cnt = cnt + 1
        url = unprocessed_urls.popleft()
        processed_urls.add(url)

        parts = urlsplit(url)
        base_url = "{0.scheme}://{0.netloc}".format(parts)
        path = url[:url.rfind('/')+1] if '/' in parts.path else url

        try:
            response = requests.get(url)

        except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
            continue

        new_emails = set(re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", response.text, re.I))
        emails.update(new_emails)

        for each in emails:
            if each in emails_all:
                continue
            else:
                emails_all.append(each)
                scraped = {
                    "url": url,
                    "email": each
                }
                #print(scraped)
                result.append(scraped)
        # create a beutiful soup for the html document
        soup = BeautifulSoup(response.text, 'lxml')

        # Once this document is parsed and processed, now find and process all the anchors i.e. linked urls in this document
        for anchor in soup.find_all("a"):
            # extract link url from the anchor
            link = anchor.attrs["href"] if "href" in anchor.attrs else ''
            # resolve relative links (starting with /)
            if link.startswith('/'):
                link = base_url + link
            elif not link.startswith('http'):
                link = path + link
            # add the new url to the queue if it was not in unprocessed list nor in processed list yet
            if not link in unprocessed_urls and not link in processed_urls:
                if cnt > 1:
                    continue
                if parent_url in link:
                    #print(link)
                    cnt_child_urls = cnt_child_urls + 1
                    unprocessed_urls.append(link)

    return result
#extract_parent(url)