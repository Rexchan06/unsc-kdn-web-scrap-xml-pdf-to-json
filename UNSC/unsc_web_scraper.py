# unsc_web_scraper.py
import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup
from typing import Union
from urllib.parse import urljoin # For robust URL construction

def get_last_updated_date(url: str) -> Union[datetime.date, None]:
    """
    Fetches the webpage and extracts the last updated date of the UN Consolidated List.

    Args:
        url (str): The URL of the UN Security Council Consolidated List webpage.

    Returns:
        Union[datetime.date, None]: The last updated date as a datetime.date object,
                                     or None if the date cannot be found or an error occurs.
    """
    try:
        # Fetch the webpage content, disabling SSL verification for this specific URL as per previous code.
        # (Note: For production, it's highly recommended to resolve SSL certificate issues
        # or ensure 'verify=True' works with proper certificate setup.)
        response = requests.get(url, verify=True)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        
        soup = BeautifulSoup(response.content, "html.parser")

        # Regex pattern to find dates in "DD Month YYYY" format (e.g., "15 July 2025")
        date_pattern = r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'
        
        # Search for the date pattern within the entire text content of the page
        page_text = soup.get_text()
        match = re.findall(date_pattern, page_text)

        if match:
            # Assuming the first found date is the relevant "last updated" date
            return datetime.strptime(match[0], "%d %B %Y").date()
        else:
            print(f"Warning: Last updated date not found on {url}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching last updated date from {url}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while parsing date from {url}: {e}")
        return None

def get_xml_link(url: str) -> Union[str, None]:
    """
    Fetches the webpage and finds the URL of the XML download link for the Consolidated List.

    Args:
        url (str): The URL of the UN Security Council Consolidated List webpage.

    Returns:
        Union[str, None]: The full (absolute) URL of the XML file, or None if not found or an error occurs.
    """
    try:
        # Fetch the webpage content
        response = requests.get(url, verify=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")

        # Find all <a> tags with the class 'documentlinks'
        doc_links = soup.find_all('a', {'class': 'documentlinks'})
        
        for link in doc_links:
            href = link.get('href', '')
            # Check if the href contains 'xml' to identify the XML download link
            if 'xml' in href:
                # Construct the full URL if the href is relative
                if href.startswith('http'):
                    return href  # Already an absolute URL
                else:
                    # Use urljoin to correctly combine base URL with relative path
                    # The base URL is the domain of the initial request
                    return urljoin(url, href)
        
        print(f"Warning: XML download link not found on {url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching XML link from {url}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while finding XML link from {url}: {e}")
        return None
