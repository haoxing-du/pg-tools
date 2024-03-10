# %%
from bs4 import BeautifulSoup
from collections import deque
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd
import matplotlib.pyplot as plt

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
import time
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
    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
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
# for previous xcontests
# url_template = "https://www.xcontest.org/{year}/world/en/flights/#flights[sort]=reg[start]@filter[date]={year}-{month}-{day}@filter[country]=US@flights[start]=0"
# for 2024 xcontest (starting oct 2023)
# url_template = "https://www.xcontest.org/world/en/flights/#flights[sort]=reg[start]@filter[date]={year}-{month}-{day}@filter[country]=US@flights[start]=0"

# overall
url_template = "https://www.xcontest.org/{prefix}world/en/flights/#flights[sort]=reg[start]@filter[date]={year}-{month}-{day}@filter[country]=US@flights[start]=0"

prefixes = {}

years = [2023, 2022, 2021, 2020, 2019]
months = [i for i in range(1, 13)]
days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
for year in years:
    for month in months:
        if year != 2023:
            if month < 10:
                prefixes[(year, month)] = f"{year}/"
            else:
                prefixes[(year, month)] = f"{year + 1}/"
        else:
            if month < 10:
                prefixes[(year, month)] = f"{year}/"
            else:
                prefixes[(year, month)] = f""

# %%
# sequential version

all_entries = []

start = time.time()
for year in years[:1]:
    for month in months[:1]:
        for day in range(1, days[month-1]+1)[:15]:
            url = url_template.format(year=year, month=month, day=day)
            entries = get_xcontest_entries(url)
            all_entries.extend(entries)
            print(f"Year: {year}, Month: {month}, Day: {day}, Entries: {len(entries)}")
end = time.time()
print(f"Time: {end - start}")

len(all_entries)
# %%
# concurrent version
def get_entries_from_date(date: tuple[int, int, int]) -> list[XContestEntry]:
    year, month, day = date
    url = url_template.format(year=year, month=month, day=day, prefix=prefixes[(year, month)])
    entries = get_xcontest_entries(url)
    print(f"Year: {year}, Month: {month}, Day: {day}, Entries: {len(entries)}")
    return entries

def scrape_xcontest(dates: list[tuple[int, int, int]]):
    to_retry = []
    entries = []
    future_to_date = {}
    with ThreadPoolExecutor(max_workers=16) as e:
        for date in dates:
            future = e.submit(get_entries_from_date, date)
            future_to_date[future] = date
            
        for future in as_completed(future_to_date):
            date = future_to_date[future]
            try:
                result = future.result()
                entries.extend(result)
                if len(result) == 100:
                    to_retry.append((date, "Too many entries"))
                if len(result) == 0:
                    to_retry.append((date, "No entries"))
            except Exception as e:
                print(f"An exception occurred for date {date}: {e}")
                to_retry.append((date, "Crashed"))  # Append the input date for retry
    return entries, to_retry

# %%
all_dates = [(year, month, day) 
             for year in years 
             for month in months 
             for day in range(1, days[month-1]+1)
]
start = time.time()
all_entries, to_retry = scrape_xcontest(all_dates)
end = time.time()
print(f"Time: {(end - start)/60} minutes")

# %%
# retry ones that crashed
old_to_retry = []
while to_retry:
    old_to_retry = old_to_retry.extend(to_retry)
    retry_dates = [date for date, reason in to_retry if reason == "Crashed"]
    new_entries, to_retry = scrape_xcontest(retry_dates)
    all_entries.extend(new_entries)
    print(f"{len(retry_dates)} remaining dates need to be retried")

# %%
all_entries = list(set(all_entries))
df = pd.DataFrame([entry.__dict__ for entry in all_entries])
# %%
# add a month and day column
df["month"] = df["date"].apply(lambda x: x.split(".")[1])
df["day"] = df["date"].apply(lambda x: x.split(".")[0])
df["year"] = df["date"].apply(lambda x: x.split(".")[2])
# %%
# plot distribution of flights by month
df["month"].value_counts().sort_index().plot(kind="bar")

# %%
df["year"].value_counts().sort_index().plot(kind="bar")
# %%
# save
df.to_csv('data/xcontest_data.csv', index=False)  # Set index=False if you don't want to save the index.

# %%
# load
df = pd.read_csv('data/xcontest_data.csv')
# %%
# get top 15 launches by count for each month
top_launches_by_month = df.groupby(["month", "launch"]).size().groupby(level=0, group_keys=False).nlargest(15)
for month, group in top_launches_by_month.groupby(level=0):
    print(month)
    print(group)
    print()
