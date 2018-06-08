'''
author: Michelle Ho, Yiqi Xie
note:   mainly borrowed from Michelle's notebook version
        some minor modifications are made by Yiqi
'''
import os
import sys
import time
import requests
import shutil
from random import randint
# import locale
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


# XIE: a global tuner of sleep time (0.2 works best for me)
BASE_INTERVAL = 1
COEFF_NAIVEREQUEST = 1
COEFF_KEYBOARDINPUT = 1
COEFF_BUTTONCLICK = 3

# locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
class Redfin():
    def __init__(self):
        self.base_url = "https://www.redfin.com/"
        self.browser = None
        self.properties = {} # a dictionary of properties, key = house mls number

    def __rand_sleep(self):
        time.sleep(randint(3,20))


    def init_browser(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--incognito")
        self.browser = webdriver.Chrome(chrome_options=options)
        self.browser.wait = WebDriverWait(self.browser, 5)
        self.browser.get(self.base_url)

    def search_mls(self, mls):
        # search a single mls
        # if no browser open, initialize browser
        if self.browser is None:
            self.init_browser()
        else:
            # XIE: in case last search failed, return to the redfin homepage
            self.browser.get(self.base_url)

        # search for mls
        searchContainer = self.browser.find_element_by_class_name("search-container")
        searchField = searchContainer.find_element_by_id("search-box-input")
        searchBtn = searchContainer.find_element_by_class_name("SearchButton")

        searchField.send_keys(mls)
        time.sleep(COEFF_KEYBOARDINPUT*BASE_INTERVAL)

        searchBtn.click()
        time.sleep(COEFF_BUTTONCLICK*BASE_INTERVAL)

        # XIE: in case of search failure, check dialogue
        try:
            dialogsContainer = self.browser.find_element_by_class_name("dialogsContainer")
            dialogsHeader = dialogsContainer.find_element_by_class_name("header")
        except NoSuchElementException:
            print('search clicked')
        else:
            print('search failed')
            raise KeyError('Dialog Message: ' + dialogsHeader.text) # 'sorry we coudn`t find xxxxxx'

    def get_property_info(self, mls):
        # check if mls is already scraped
        if mls in list(self.properties.keys()):
            return self.properties[mls]
        else:
            # if not already scraped, scrape the page and add to self.properties
            property_info = self.scrape_property(mls)
            return property_info

    def scrape_property(self, mls):
        self.search_mls(mls)
        house_info = {}

        # address
        house_info['address_street'] = self.browser.find_element_by_class_name("street-address").text
        house_info['address_city'] = self.browser.find_element_by_class_name("citystatezip").text
        house_info['address_full'] = house_info['address_street'] + " " + house_info['address_city']

        # overview
        # XIE: try-except added
        overview = self.browser.find_element_by_id("overview-scroll")
        try:
            house_info['mls'] = overview.find_element_by_xpath("//span[contains(text(),'MLS#')]/following-sibling::span").text
        except NoSuchElementException:
            house_info['mls'] = str(mls)
        try:
            house_info['remarks'] = overview.find_element_by_class_name("remarks").text
        except NoSuchElementException:
            house_info['remarks'] = 'n/a'
        try:
            house_info['property_style'] = overview.find_element_by_xpath("//span[contains(text(),'Style')]/following-sibling::span").text
        except NoSuchElementException:
            house_info['property_style'] = 'n/a'
        try:
            house_info['community'] = overview.find_element_by_xpath("//span[contains(text(),'Community')]/following-sibling::span").text
        except NoSuchElementException:
            house_info['community'] = 'n/a'
        try:
            house_info['county'] = overview.find_element_by_xpath("//span[contains(text(),'County')]/following-sibling::span").text
        except NoSuchElementException:
            house_info['county'] = 'n/a'

        # basic house facts
        main_stat = self.browser.find_element_by_class_name("HomeMainStats")
        try:
            house_info['beds'] = main_stat.find_element_by_xpath("//span[contains(text(),'Beds')]/preceding-sibling::div").text
        except NoSuchElementException:
            try:
                house_info['beds'] = main_stat.find_element_by_xpath("//span[contains(text(),'Bed')]/preceding-sibling::div").text
            except NoSuchElementException:
                house_info['beds'] = "n/a"
        try:
            house_info['baths'] = main_stat.find_element_by_xpath("//span[contains(text(),'Baths')]/preceding-sibling::div").text
        except NoSuchElementException:
            try:
                house_info['baths'] = main_stat.find_element_by_xpath("//span[contains(text(),'Bath')]/preceding-sibling::div").text
            except NoSuchElementException:
                house_info['baths'] = "n/a"
        house_info['sqft_living'] = main_stat.find_element_by_xpath("//span[contains(text(),'Sq. Ft.')]/preceding-sibling::span").text

        public_records = self.browser.find_element_by_id("public-records-scroll")
        house_info['sqft_finished'] = public_records.find_element_by_xpath("//span[contains(text(),'Finished Sq. Ft.')]/following-sibling::div").text
        house_info['sqft_unfinished'] = public_records.find_element_by_xpath("//span[contains(text(),'Unfinished Sq. Ft.')]/following-sibling::div").text
        house_info['sqft_total'] = public_records.find_element_by_xpath("//span[contains(text(),'Total Sq. Ft.')]/following-sibling::div").text
        house_info['stories'] = public_records.find_element_by_xpath("//span[contains(text(),'Stories')]/following-sibling::div").text
        house_info['lot_size'] = public_records.find_element_by_xpath("//span[contains(text(),'Lot Size')]/following-sibling::div").text
        house_info['property_type'] = public_records.find_element_by_xpath("//span[contains(text(),'Style')]/following-sibling::div").text
        house_info['year_built'] = public_records.find_element_by_xpath("//span[contains(text(),'Year Built')]/following-sibling::div").text
        house_info['year_renovated'] = public_records.find_element_by_xpath("//span[contains(text(),'Year Renovated')]/following-sibling::div").text

        # details
        details = self.browser.find_element_by_id("property-details-scroll")
        try:
            house_info['parking_feat'] = details.find_element_by_xpath("//span[contains(text(),'Parking Features: ')]/span").text
        except NoSuchElementException:
            house_info['parking_feat'] = "n/a"
        try:
            house_info['parking_space'] = details.find_element_by_xpath("//span[contains(text(),'# of Parking Spaces: ')]/span").text
        except NoSuchElementException:
            house_info['parking_space'] = "n/a"
        try:
            house_info['garage_space'] = details.find_element_by_xpath("//span[contains(text(),'# of Garage Spaces: ')]/span").text
        except NoSuchElementException:
            house_info['garage_space'] = "n/a"
        try:
            house_info['hoa_fee'] = details.find_element_by_xpath("//span[contains(text(),'Fee: ')]/span").text.split("$")[1]
        except NoSuchElementException:
            house_info['hoa_fee'] = "0"
        try:
            house_info['hoa_freq'] = details.find_element_by_xpath("//span[contains(text(),'Payment Frequency: ')]/span").text
        except NoSuchElementException:
            house_info['hoa_freq'] = "n/a"
        try:
            house_info['lot_size_sqft'] = details.find_element_by_xpath("//span[contains(text(),'Lot Size (Sq. Ft.): ')]/span").text
        except NoSuchElementException:
            house_info['lot_size_sqft'] = "n/a"

        # school information
        school_info = self.browser.find_element_by_id("schools-scroll")
        try:
            tabs = school_info.find_element_by_class_name("tabs")
            elementaryTab = tabs.find_element_by_xpath("//div[contains(text(),'Elementary Schools')]")
            middleTab = tabs.find_element_by_xpath("//div[contains(text(),'Middle Schools')]")
            highTab = tabs.find_element_by_xpath("//div[contains(text(),'High Schools')]")

            # elementary school
            elementaryTab.click()
            elementary_ratings = []
            elementary_distances = []
            for school in school_info.find_elements_by_tag_name("tr")[1:]:
                elementary_ratings.append(school.find_element_by_class_name("rating").text)
                elementary_distances.append(school.find_element_by_class_name("distance-col").text.split(" ")[0])

            house_info['school_ratings_elementary'] = elementary_ratings
            house_info['school_distances_elementary'] = elementary_distances

            # middle school
            middleTab.click()
            middle_ratings = []
            middle_distances = []
            for school in school_info.find_elements_by_tag_name("tr")[1:]:
                middle_ratings.append(school.find_element_by_class_name("rating").text)
                middle_distances.append(school.find_element_by_class_name("distance-col").text.split(" ")[0])
            house_info['school_ratings_middle'] = middle_ratings
            house_info['school_distances_middle'] = middle_distances

            # high school
            highTab.click()
            high_ratings = []
            high_distances = []
            for school in school_info.find_elements_by_tag_name("tr")[1:]:
                high_ratings.append(school.find_element_by_class_name("rating").text)
                high_distances.append(school.find_element_by_class_name("distance-col").text.split(" ")[0])
            house_info['school_ratings_high'] = high_ratings
            house_info['school_distances_high'] = high_distances
        except NoSuchElementException:
            house_info['school_ratings_elementary'] = -1
            house_info['school_distances_elementary'] = -1
            house_info['school_ratings_middle'] = -1
            house_info['school_distances_middle'] = -1
            house_info['school_ratings_high'] = -1
            house_info['school_distances_high'] = -1

        # neighborhood info
        neighborhood = self.browser.find_element_by_id("neighborhood-info-scroll")
        scores = neighborhood.find_elements_by_class_name("percentage")
        score_labels = neighborhood.find_elements_by_class_name("label")
        if scores:
            for i, score in enumerate(scores):
                label = score_labels[i].text[:-1].lower().replace(" ", "_")
                house_info[label] = score.text
        # check if walk, transit and bike scores are present
        if 'walk_score' not in list(house_info.keys()):
            house_info['walk_score'] = "n/a"
        if 'transit_score' not in list(house_info.keys()):
            house_info['transit_score'] = "n/a"
        if 'bike_score' not in list(house_info.keys()):
            house_info['bike_score'] = "n/a"

        # get all photo urls
        house_info['num_photo'], house_info['photo_urls'] = self.__scrape_image_urls()
        self.properties[mls] = house_info

        return house_info

    def __scrape_image_urls(self):
        photo_urls = []
        mediaBrowser = self.browser.find_element_by_class_name("MediaBrowser")
        photoArea = mediaBrowser.find_element_by_class_name("PhotoArea")

        # find the first photo
        first_photo = photoArea.find_element_by_class_name("img-card")
        num_photo = int(first_photo.get_attribute("title").split('of ')[1])

        # scrape all photo urls
        # XIE: prevent clicking 'next' when num_photo <= 1
        if num_photo > 1:
            nextBtn = photoArea.find_element_by_class_name("next")
            for i in range(num_photo):
                nextBtn.click()
                time.sleep(COEFF_BUTTONCLICK*BASE_INTERVAL)
                photo = photoArea.find_element_by_class_name("visible").find_element_by_class_name("img-card")
                photo_urls.append(photo.get_attribute("src"))
        else:
            photo_urls.append(first_photo.get_attribute("src"))

        return num_photo, photo_urls


    def download_images(self, dirname, mls):
        self.__make_dir(dirname)
        urls = self.get_property_info(mls)['photo_urls']
        length = len(urls)
        for index, url in enumerate(urls):
            print('Downloading {0} of {1} images'.format(index + 1, length), end='\r')
            sys.stdout.flush()
            response = requests.get(url, stream=True)
            self.__save_image_to_file(response, dirname, mls, index)
            time.sleep(COEFF_NAIVEREQUEST*BASE_INTERVAL)
            del response
        print()

    def quit_browser(self):
        # XIE: in case the browser is already closed
        if self.browser is not None:
            self.browser.quit()
            self.browser = None

    def __save_image_to_file(self, image, dirname, mls, suffix):
        with open('{dirname}/{mls}_img_{suffix}.jpg'.format(dirname=dirname, mls=mls, suffix=suffix), 'wb') as out_file:
            shutil.copyfileobj(image.raw, out_file)

    def __make_dir(self, dirname):
        current_path = os.getcwd()
        path = os.path.join(current_path, dirname)
        if not os.path.exists(path):
            os.makedirs(path)
