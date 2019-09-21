"""

.. module:: data18
   :synopsis: This module provides an abstraction layer for the Data18 website.
"""

import re
import lxml
import sys
from datetime import datetime, timedelta

class DetailsPage:
    """
    This class represents the details page for a video.
    """
    url_pattern = re.compile('url\(([^\)]+)\)')
    hours_pattern = re.compile('(\d+) hrs.')
    minutes_pattern = re.compile('(\d+) mins.')
    def __init__(self, data):
        """
        :param lxml.etree._ElementTree data: The root node of the details page.
        """
        self.data = data

    @staticmethod
    def capitalize(line):
        """
        Capitalize the words in a line.
        :param str line:
        :rtype: str
        """
        return ' '.join([word[0].upper() + word[1:].lower() for word in line.split(' ')])
    @staticmethod
    def extract_img_url(tag):
        """
        Extract the background image url from a tag's style attribute.
        :param lxml.etree._ElementTree tag:
        """
        background_image = [style for style in tag.get('style').split(';') if style.startswith('background-image')][0]
        return DetailsPage.url_pattern.search(background_image).group(1)
    @staticmethod
    def disambiguate_release_date_elements(tag, target_name):
        """
        Due to a bug in data18 both the release date and the runtime may have
        the same xpath. This function accepts a tree element and the target
        name either "Released" or "Length" for the release date or runtime
        respectively and returns the correct element or None if it cannot be
        found.
        :param lxml.etree._ElementTree tag: the parent tag to search within
        :param str target_name: Either "Released" or "Length"
        :rtype: lxml.etree._ElementTree|None
        """
        target_tags = [target for target in tag.xpath('.//div[@class="release-date"]/span') if target_name in target.text]
        if len(target_tags) != 0:
            return target_tags[0]
        return None
    def get_title(self):
        """
        :rtype: str
        """
        # We have to use xpath here to use the contains function
        return self.data.xpath('.//div[contains(@class, "video-title")]/h1')[0].text.strip()
    def get_tagline(self):
        """
        :rtype: str|None
        """
        tag_tag = self.data.find('.//*[@class="tag-line"]')
        if tag_tag == None:
            return None
        return tag_tag.text.strip()

    def get_synopsis(self):
        """
        :rtype: str|None
        """
        tag = self.data.find('.//div[@class="synopsis"]/p')
        if tag == None:
            return None
        synopsis = ""
        # The synopsis paragraph may contain children to style individual words
        # so we must iterate through all the text to assemble the synopsis
        for text in tag.itertext():
            synopsis += text
        return synopsis.strip()
    def get_categories(self):
        """
        :rtype: [str]
        """
        return [DetailsPage.capitalize(a.text.strip()) for a in self.data.xpath('//div[@class="categories"]/a')]
    def get_studio(self):
        """
        :rtype: str
        """
        return self.data.find('.//a[@data-label="Studio"]').text.strip()
    def get_director(self):
        """
        :rtype: str
        """
        return self.data.find('.//a[@data-label="Director"]').text.strip()
    def get_release_date(self):
        """
        :rtype: datetime.datetime|None
        """
        tag = DetailsPage.disambiguate_release_date_elements(self.data, 'Released')
        if tag == None:
            return None
        date = tag.tail.strip()
        return datetime.strptime(date, '%b %d, %Y')
    def get_release_year(self):
        """
        :rtype: int
        """
        date = self.get_release_date()
        if date == None:
            return None
        return date.year
    def get_runtime(self):
        """
        Get the runtime or None if it cannot be found on the page.
        :rtype: datetime.timedelta|None
        """
        runtime_tag = DetailsPage.disambiguate_release_date_elements(self.data, 'Length')
        if runtime_tag == None:
            return None
        runtime = runtime_tag.tail.strip()
        hrs_match = DetailsPage.hours_pattern.search(runtime)
        mins_match = DetailsPage.minutes_pattern.search(runtime)
        hours = 0
        minutes = 0
        if hrs_match:
            hours = int(hrs_match.group(1))
        if mins_match:
            minutes = int(mins_match.group(1))
        return timedelta(hours=hours, minutes=minutes)
    def get_background_url(self):
        """
        Get the full URL for the background image or None if it cannot be found.
        :rtype: str|None
        """
        style_tag = self.data.find('.//style')
        url_match = DetailsPage.url_pattern.search(style_tag.text)
        if url_match:
            return  url_match.group(1)
        return None
    def get_cover_url(self):
        """
        Get the full URL for the cover image.
        :rtype: str
        """
        return self.data.find('.//a[@class="boxcover"]//source').get('srcset')
    def get_actors(self):
        """
        Get an array of tuples with the actor name and the full url to the
        actor's image.
        :rtype: [(str, str)]
        """
        actors = self.data.xpath('.//div[@class="video-performer"]//img')
        return [(actor.get('title'), DetailsPage.extract_img_url(actor)) for actor in actors]


class SearchResult:
    """
    This class represents an individual search result.
    """
    def __init__(self, data):
        """
        :param lxml.etree._ElementTree data: The root node of a search result.
        """
        self.data = data
    def get_title(self):
        """
        :rtype: str
        """
        return self.data.xpath('.//*[@title]')[0].get('title')
    def get_details_path(self):
        """
        Get the relative path to the details page for a video.
        :rtype: str
        """
        return self.data.xpath('.//*[@href]')[0].get('href')

class SearchPage:
    """
    This class represents the search results page.
    """
    def __init__(self, data):
        """
        :param lxml.etree._ElementTree data: The root node of the search results
            page.
        """
        self.data = data
    def get_search_results(self):
        """
        Get an array of search results.
        :rtype: [SearchResult]
        """
        return [SearchResult(item) for item in self.data.xpath('//div[@class="grid-item"]')]
