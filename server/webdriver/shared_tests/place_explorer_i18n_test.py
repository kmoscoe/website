# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from server.webdriver import shared
from server.webdriver.base_utils import find_elem

# Regular expression for matching Japanese characters:
# Hiragana: \u3040-\u309F
# Katakana: \u30A0-\u30FF
# Common Kanji: \u4E00-\u9FAF (includes many Chinese characters used in Japanese)
JAPANESE_CHAR_PATTERN = re.compile(r'[\u3040-\u30FF\u4E00-\u9FAF]')


class PlaceI18nExplorerTestMixin():
  """Mixins to test the i18n place explorer page."""

  def test_japan_in_japanese(self):
    """Test translations from various sources are displayed correctly."""

    start_url = self.url_ + '/place/country/JPN?hl=ja&disable_dev_places=true'
    self.driver.get(start_url)

    place_name_present = EC.text_to_be_present_in_element((By.ID, 'place-name'),
                                                          '日本')
    WebDriverWait(self.driver, self.TIMEOUT_SEC).until(place_name_present)

    place_type_present = EC.text_to_be_present_in_element((By.ID, 'place-type'),
                                                          'アジア の 国')
    WebDriverWait(self.driver, self.TIMEOUT_SEC).until(place_type_present)

    economics_section_present = EC.text_to_be_present_in_element(
        (By.ID, 'Economics'), '経済')
    WebDriverWait(self.driver,
                  self.TIMEOUT_SEC).until(economics_section_present)

    # Test that charts are present
    charts = self.driver.find_elements(By.CSS_SELECTOR,
                                       '#main-pane [class*="chart-container"]')
    self.assertGreater(len(charts), 0,
                       "Expected at least one chart to be present")

    # Test that topics are translated
    health_topic = self.driver.find_element(By.XPATH,
                                            '//*[@id="nav-topics"]/li[3]/a')
    self.assertEqual(health_topic.text, '健康')

    # Test strings in descendent place component
    descendent_places = self.driver.find_element(By.XPATH,
                                                 '//*[@id="child-place-head"]')
    self.assertEqual(descendent_places.text, '日本 の地域')
    aa_children_label = self.driver.find_element(
        By.XPATH, '//*[@id="child-place"]/div/div')
    self.assertEqual(aa_children_label.text, '行政区域 1 の地域')
    aichi_prefecture = self.driver.find_element(
        By.XPATH, '//*[@id="child-place"]/div/a[1]')
    self.assertEqual(aichi_prefecture.text, '三重県,')

    # Test that timeline links are removed
    self.assertListEqual(
        self.driver.find_elements(By.CLASS_NAME, 'explore-more'), [])

  def test_japan_in_japanese_new_place_page(self):
    """Test translations from various sources are displayed correctly."""

    start_url = self.url_ + '/place/country/JPN?hl=ja&force_dev_places=true'
    self.driver.get(start_url)

    place_name_present = EC.text_to_be_present_in_element(
        (By.CSS_SELECTOR, '.place-info [data-testid="place-name"]'), '日本')
    WebDriverWait(self.driver, self.TIMEOUT_SEC).until(place_name_present)

    # TODO: Update this test once the place type is translated
    # Ensure that the place type in {parentPlace} is translated
    place_type_present = EC.text_to_be_present_in_element(
        (By.CSS_SELECTOR, '.place-info .subheader'), '国 in')
    WebDriverWait(self.driver, self.TIMEOUT_SEC).until(place_type_present)

    # Ensure that the topics tab links are translated
    economics_link = find_elem(self.driver,
                               by=By.CSS_SELECTOR,
                               value=".explore-topics-box .item-list-item a")
    self.assertEqual(economics_link.text, "経済")

    # Ensure that the economics section is translated
    # The first block-title-text is the economics section
    economics_section_present = EC.text_to_be_present_in_element(
        (By.CLASS_NAME, 'block-title-text'), '経済')
    WebDriverWait(self.driver,
                  self.TIMEOUT_SEC).until(economics_section_present)

    # Test that charts are present
    charts = self.driver.find_elements(By.CSS_SELECTOR, '.chart-container')
    self.assertGreater(len(charts), 0,
                       "Expected at least one chart to be present")

    # Wait for and scroll to ranking tile so it lazy loads
    ranking_tile_present = EC.presence_of_element_located(
        (By.CLASS_NAME, "ranking-tile"))
    ranking_tile = WebDriverWait(self.driver,
                                 self.TIMEOUT_SEC).until(ranking_tile_present)
    self.driver.execute_script("arguments[0].scrollIntoView();", ranking_tile)

    # Ensure the ranking tile footer text is translated
    self.assertEqual(
        find_elem(self.driver,
                  by=By.CSS_SELECTOR,
                  value=".chart-container .chart-footnote").text,
        "使用可能な最新のデータに基づくランキング。一部の地域は、対象の年の報告が不完全なため、欠落している可能性があります。")

    # Wait for and scroll to the first bar chart tile so it lazy loads
    bar_chart_tile_present = EC.presence_of_element_located(
        (By.CLASS_NAME, "bar-chart"))
    bar_chart_tile = WebDriverWait(
        self.driver, self.TIMEOUT_SEC).until(bar_chart_tile_present)
    self.driver.execute_script("arguments[0].scrollIntoView();", bar_chart_tile)

    # Ensure that the bar chart's axis labels (localized place names) have japanese text
    self.assertTrue(
        JAPANESE_CHAR_PATTERN.search(
            find_elem(self.driver,
                      by=By.CSS_SELECTOR,
                      value="svg text.place-tick").text))

    # TODO: Update this test once the see per capita link is translated
    self.assertEqual(
        find_elem(self.driver,
                  by=By.CSS_SELECTOR,
                  value=".block-controls [data-testid='see-per-capita']").text,
        "See per capita")

    # Test that related places callout is translated
    related_places = find_elem(self.driver,
                               by=By.CLASS_NAME,
                               value="related-places-callout")
    self.assertEqual(related_places.text, "日本 の地域")

    # Test that child place link is translated
    child_place_link = find_elem(self.driver,
                                 by=By.CSS_SELECTOR,
                                 value=".related-places .item-list-item a")
    self.assertEqual(child_place_link.text, "北海道")

    # Test that timeline links are removed
    self.assertListEqual(
        self.driver.find_elements(By.CLASS_NAME, 'explore-more'), [])

  def test_demographics_link_in_fr(self):
    """Test the demographics link in FR propagates."""

    # Load France page.
    self.driver.get(self.url_ +
                    '/place/country/FRA?hl=fr&disable_dev_places=true')

    # Wait until the Demographics link is present.
    element_present = EC.presence_of_element_located(
        (By.XPATH, '//*[@id="Demographics"]/a'))
    WebDriverWait(self.driver, self.TIMEOUT_SEC).until(element_present)

    # Find and click on the Demographics URL.
    demographics = self.driver.find_element(By.XPATH,
                                            '//*[@id="Demographics"]/a')
    self.assertEqual(demographics.text, 'DONNÉES DÉMOGRAPHIQUES')
    demographics.click()
    self.driver.get(self.driver.current_url + '&disable_dev_places=true')

    # Wait until the new page has loaded.
    element_present = EC.presence_of_element_located(
        (By.XPATH, '//*[@id="main-pane"]/section[4]/div/div[2]/div/h4'))
    WebDriverWait(self.driver, self.TIMEOUT_SEC).until(element_present)

    # Assert that Demographics and hl=fr is part of the new url.
    self.assertTrue("Demographics" in self.driver.current_url)
    self.assertTrue("&hl=fr" in self.driver.current_url)

    # Click through to ranking for population (Count_Person)
    pop_link = self.driver.find_element(
        By.CSS_SELECTOR, 'a.legend-link[title="Population totale"]')
    self.assertIsNotNone(pop_link, "Population totale link not found")
    pop_link.click()
    self.driver.get(self.driver.current_url + '&disable_dev_places=true')

    # Wait until ranking page has loaded
    element_present = EC.presence_of_element_located((By.TAG_NAME, 'h1'))
    WebDriverWait(self.driver, self.TIMEOUT_SEC).until(element_present)

    # Assert language is propagated
    url = self.driver.current_url
    self.assertTrue('Count_Person' in url)
    self.assertTrue('Country' in url)
    self.assertTrue('europe' in url)
    self.assertTrue('hl=fr' in url)
    self.assertEqual(
        self.driver.find_element(By.TAG_NAME, 'h1').text,
        'Classement par Population')

  def test_explorer_redirect_place_explorer(self):
    """Test the redirection from explore to place explore for single place queries keeps the locale and query string"""
    usa_explore_fr_locale = '/explore?hl=fr#q=United%20States%20Of%20America'

    start_url = self.url_ + usa_explore_fr_locale
    self.driver.get(start_url)

    # Assert 200 HTTP code: successful page load.
    self.assertEqual(shared.safe_url_open(self.driver.current_url), 200)

    # Wait for redirect and page load.
    redirect_finished = EC.url_changes(start_url)
    WebDriverWait(self.driver, self.TIMEOUT_SEC).until(redirect_finished)
    shared.wait_for_loading(self.driver)

    # Assert redirected URL is correct and contains the locale and query string.
    self.assertTrue('place/country/USA?q=United+States+Of+America&hl=fr' in
                    self.driver.current_url)

    # Assert localized page title is correct for the locale.
    WebDriverWait(self.driver,
                  self.TIMEOUT_SEC).until(EC.title_contains('États-Unis'))
