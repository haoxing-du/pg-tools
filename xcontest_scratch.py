# %%
from bs4 import BeautifulSoup
from collections import deque
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# %%
url = "https://www.xcontest.org/2022/world/en/flights/#flights[sort]=reg@filter[country]=US@flights[start]=100"

# %%
class XContestEntry():
    def __init__(self, entry):
        self.entry = entry
        self.pilot = self.get_pilot()
        self.date = self.get_date()
        self.time = self.get_time()
        self.utc_offset = self.get_utc_offset()
        self.country = self.get_country()
        self.distance = self.get_distance()
        self.duration = self.get_duration()
        self.launch = self.get_launch()
        # self.landing = self.get_landing()
        self.points = self.get_points()
        self.url = self.get_url()

    def get_pilot(self):
        return self.entry.find("a", class_="plt").text

    def get_date(self):
        return self.entry.find_all("td")[1].text.split(" ")[0]

    def get_time(self):
        return self.entry.find_all("td")[1].text.split(" ")[1].split("=")[0]

    def get_utc_offset(self):
        return self.entry.find("span", class_="XCutcOffset").text[1:]

    def get_country(self):
        return self.entry.find("span", class_="cic flag_us").text

    def get_distance(self):
        return self.entry.find("td", class_="km").text

    def get_duration(self):
        return self.entry.find("td", class_="dur").text
    
    def get_launch(self):
        return self.entry.find("a", class_="lau").text

    def get_landing(self):
        return self.entry.find("td", class_="lad").text

    def get_points(self):
        return self.entry.find("td", class_="pts").text

    def get_url(self):
        return self.entry.find("a", class_="lau")["href"].replace(" ", "%20")

    def __str__(self):
        return f"Pilot: {self.pilot}\nDate: {self.date}\nTime: {self.time}\nUTC Offset: {self.utc_offset}\nCountry: {self.country}\nDistance: {self.distance}\nDuration: {self.duration}\nLaunch: {self.launch}\nPoints: {self.points}\nURL: {self.url}"
    
def get_xcontest_soup(url: str) -> BeautifulSoup:
    driver = webdriver.Chrome()
    driver.get(url)

    # Wait for the actual list to load
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'XClist'))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    finally:
        driver.quit()
    return soup

def get_xcontest_entries(url: str) -> list[XContestEntry]:
    soup = get_xcontest_soup(url)
    entries = soup.find_all("tr", id=lambda x: x and x.startswith("flight"))
    xcontest_entries = [XContestEntry(entry) for entry in entries]
    return xcontest_entries

# %%
entries = get_xcontest_entries(url)
# %%
