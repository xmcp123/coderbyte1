import requests
import re
import phonenumbers
from bs4 import BeautifulSoup, SoupStrainer
from phonenumbers import carrier, timezone, geocoder
import json


def is_valid_phone(phone):
    return re.match(r"(\+[0-9]+\s*)?(\([0-9]+\))?[\s0-9\-]+[0-9]+", phone) and len(phone)==12


class ScraperJob(object):
    def __init__(self, max_pages=10):

        self.used = set()
        self.phone_numbers = set()
        self.results = []
        self.index = 0
        self.max_pages = max_pages
        self.visited_pages = 0
    def process_phone(self, phone):
        ph = None
        if not phone.startswith("+"):
            ph = phonenumbers.parse(phone, "US")
        else:
            ph = phonenumbers.parse(phone)

        phone = phonenumbers.format_number(ph, phonenumbers.PhoneNumberFormat.E164)

        if phonenumbers.is_valid_number(ph) and phone not in self.phone_numbers:
            self.phone_numbers.add(phone)
            result_obj = {
                "carrier": carrier.name_for_number(ph, "en"),
                "timezone": timezone.time_zones_for_number(ph),
                "phone_number": phone,
            }
            self.results.append(result_obj)
        elif phone not in self.phone_numbers and is_valid_phone(
            phone
        ):  # edgecase because the sample url does not actually use a valid phone number.
            self.phone_numbers.add(phone)
            result_obj = {
                "carrier": "Fake Carrier",
                "timezone": "Fake Timezone",
                "phone_number": phone,
            }
            self.results.append(result_obj)
        else:
            print("Invalid: {}\t{}".format(phone, len(phone)))

    def process_url(self, url):
        self.visited_pages += 1
        page = ScrapedPage(url)
        for phone in page.get_phone_numbers():
            self.process_phone(phone)
        for link in page.get_links():
            link = link.split("#")[0]
            if not link in self.used:
                print("Found Link: {}".format(link))
                self.used.add(link)
                yield link
    def get_results(self):
        return self.results
    def scrape(self, url):
        self.queue = [url]
        index = 0
        while index < len(self.queue) and index < self.max_pages:
            print("Processing page {}".format(self.queue[index]))
            for link in self.process_url(self.queue[index]):
                if  link not in self.queue:
                    self.queue.append(link)
            index+=1


class ScrapedPage(object):
    def __init__(self, url):
        self.url, self.status_code, self.content = self.get_url(url)

    def get_url(self, url):
        sess = requests.Session()
        useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36"
        headers = {"User-agent": useragent}
        result = sess.get(url, headers=headers)
        return result.url, result.status_code, result.text

    def fix_url(self, link):
        init_url = self.url
        if link.lower().startswith("http://") or link.startswith("https://"):
            return link
        else:
            return requests.compat.urljoin(init_url, link)

    def get_links(self):
        soup = BeautifulSoup(self.content, "lxml")
        for link in soup.find_all("a"):
            if link.has_attr("href"):
                yield self.fix_url(link["href"])

    def get_phone_numbers(self):
        pattern = r"(\d{3}[-\.\s]\d{3}[-\.\s]\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]\d{4}|\d{3}[-\.\s]\d{4})"
        compiled = re.compile(pattern)
        for match in re.findall(pattern, self.content):
            yield match



