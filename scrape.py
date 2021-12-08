import requests
import re
import phonenumbers
from bs4 import BeautifulSoup, SoupStrainer
from phonenumbers import carrier, timezone, geocoder


def is_valid_phone(phone):
    """
    The real phone number validation is too good for the example url. This will validate phone numbers that aren't really valid
    :param phone: str international phone number format
    :return: boolean
    """
    return (
        re.match(r"(\+[0-9]+\s*)?(\([0-9]+\))?[\s0-9\-]+[0-9]+", phone)
        and len(phone) == 12
    )


class ScraperJob(object):
    def __init__(self, max_pages=10):

        self.phone_numbers = set()
        self.results = []
        self.index = 0
        self.max_pages = max_pages
        self.visited_pages = 0

    def process_phone(self, phone):
        """
        Validate and extract phone numbers
        :param phone: the phone number
        :return: None
        """
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

    def process_url(self, url):
        """
        Scrape a url, add links, process phone numbers
        :param url:  string
        :return: None
        """
        self.visited_pages += 1
        page = ScrapedPage(url)
        for phone in page.get_phone_numbers():
            self.process_phone(phone)
        for link in page.get_links():
            link = link.split("#")[0]
            yield link

    def get_results(self):
        """
        Retrieve the results object
        :return:  dict
        """
        return self.results

    def scrape(self, url):
        """
        Begin the scraping of a URL
        :param url: the url to scrape
        :return:
        """
        self.queue = [url]
        index = 0
        while index < len(self.queue) and index < self.max_pages:
            print("Processing page {}".format(self.queue[index]))
            for link in self.process_url(self.queue[index]):
                if link not in self.queue:
                    self.queue.append(link)
            index += 1
        return self.get_results()


class ScrapedPage(object):
    def __init__(self, url):
        self.url, self.status_code, self.content = self.get_url(url)

    def get_url(self, url):
        """
        Retrieve a URL
        :param url: string
        :return: touple (url, status_code, text)
        """
        sess = requests.Session()
        useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36"
        headers = {"User-agent": useragent}
        result = sess.get(url, headers=headers)
        return result.url, result.status_code, result.text

    def fix_url(self, link):
        """
        Make relative links absolute, or return an alredy absolute url
        :param link: url
        :return: string
        """
        init_url = self.url
        if link.lower().startswith("http://") or link.startswith("https://"):
            return link
        else:
            return requests.compat.urljoin(init_url, link)

    def get_links(self):
        """
        Extract links from the processed page
        :return: absolute url
        """
        soup = BeautifulSoup(self.content, "lxml")
        for link in soup.find_all("a"):
            if link.has_attr("href"):
                yield self.fix_url(link["href"])

    def get_phone_numbers(self):
        """
        Extract phone numbers from the page. Validation occurs later
        :return: string (phone number)
        """
        pattern = r"(\d{3}[-\.\s]\d{3}[-\.\s]\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]\d{4}|\d{3}[-\.\s]\d{4})"
        for match in re.findall(pattern, self.content):
            yield match
