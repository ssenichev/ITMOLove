import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

import re


def setup_browser(login_url: str, login: str, password:str):
    opts = Options()
    opts.add_argument("--headless")
    driver = webdriver.Firefox(options=opts)
    driver.maximize_window()
    driver.get(login_url)
    driver.find_element(By.NAME, 'username').send_keys(login)

    driver.find_element(By.NAME, 'password').send_keys(password)

    driver.find_element(By.NAME, 'login').click()

    return driver


def get_student_info(isu: str, driver: webdriver, timeout: int):
    try:
        element_present = EC.presence_of_element_located((By.ID, 'f50'))
        WebDriverWait(driver, timeout).until(element_present)
    except TimeoutException:
        print("Timed out waiting for page to load")
    finally:
        print("Page loaded")
    driver.find_element(By.ID, 'f50').send_keys(isu)
    driver.find_element(By.ID, "f50").send_keys(Keys.RETURN)
    try:
        element_present = EC.presence_of_element_located((By.ID, 'PERSON_MAIN_INFO'))
        WebDriverWait(driver, timeout).until(element_present)
    except TimeoutException:
        print("Timed out waiting for page to load")
    finally:
        print("Page loaded")

    # extract the data using BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    info = soup.find(id="PERSON_MAIN_INFO")
    li = info.find_all("li") # добавить try catch, чтобы проверить, получилось ли
    expression = li[-1].get_text().strip() + ","
    expression = re.sub(r'\s+', ' ', expression).strip()

    #retrieve data using regulars
    match = re.search(r'\d+-й курс', expression)
    if match:
        course = match.group()
    else:
        course = None

    # Extract the faculty value
    match = re.search(r'\[(\d+)\] (.*?)\s*,', expression)
    if match:
        faculty = match.group(2)
    else:
        faculty = None

    # Extract the program value
    match = re.search(r'образовательная программа (\S.*\S) \d{4}', expression)
    if match:
        program = match.group(1)
    else:
        program = None
    return course, faculty, program


driver = setup_browser('https://isu.ifmo.ru/', "367167", "praisetheGod")
print(get_student_info("371471", driver,4))