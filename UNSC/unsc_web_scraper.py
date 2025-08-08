# unsc_web_scraper.py
import requests
import re
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from typing import Union
from urllib.parse import urljoin


def get_xml_link(url: str) -> Union[str, None]:
    """
    Fetches the webpage and finds the URL of the XML download link for the Consolidated List.

    Args:
        url (str): The URL of the UN Security Council Consolidated List webpage.

    Returns:
        Union[str, None]: The full (absolute) URL of the XML file, or None if not found or an error occurs.
    """
    try:
        response = requests.get(url, verify=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        doc_links = soup.find_all('a', {'class': 'documentlinks'})
        
        for link in doc_links:
            href = link.get('href', '')
            if 'xml' in href:
                if href.startswith('http'):
                    return href
                else:
                    return urljoin(url, href)
        
        logging.warning(f"XML download link not found on {url}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching XML link from {url}: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while finding XML link from {url}: {e}")
        return None
