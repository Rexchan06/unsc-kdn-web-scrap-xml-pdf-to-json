# KDN/kdn_web_scraper.py
import requests
from bs4 import BeautifulSoup
from typing import Union
from urllib.parse import urljoin, urlparse # Explicitly import urljoin and urlparse for clarity
# Removed: import certifi # Removed certifi import as it's no longer needed with verify=False

# --- Configuration for SSL Verification ---
# WARNING: Setting verify=False disables SSL certificate verification.
# This is INSECURE and makes your connection vulnerable to man-in-the-middle attacks.
# Use ONLY if absolutely necessary for development/testing and you understand the risks.
# For production, always strive to resolve the underlying SSL certificate issues.
# For this specific module, we are explicitly setting verify=False as requested.

def get_kdn_pdf_content(url: str) -> Union[bytes, None]:
    """
    Fetches the MOHA KDN webpage, finds the PDF download link,
    and downloads the PDF content.

    Args:
        url (str): The URL of the MOHA webpage to scrape for the PDF link.

    Returns:
        Union[bytes, None]: The PDF content as bytes if successfully downloaded, otherwise None.
    """
    pdf_content_bytes = None

    try:
        print("Fetching PDF URL from the Ministry of Home Affairs website...")
        # Explicitly setting verify=False as requested by the user.
        response = requests.get(url, verify=False)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        soup = BeautifulSoup(response.content, "html.parser")
        base_url = 'https://www.moha.gov.my'

        found_pdf_url = None
        for tag in soup.find_all("a"):
            href = tag.get("href", "")
            # Look for a link that contains 'SENARAI_KDN' and '.pdf' and is NOT an XML link
            if 'SENARAI_KDN' in href and '.pdf' in href and not href.endswith('.xml'):
                pdf_relative_url = href
                found_pdf_url = urljoin(base_url, pdf_relative_url) # Use urljoin for robustness
                break

        if not found_pdf_url:
            print("Warning: Could not find the PDF link on the webpage.")
            return None

        print(f"Found PDF link: {found_pdf_url}. Proceeding to download.")
        # Download the PDF content as bytes
        # Explicitly setting verify=False as requested by the user.
        pdf_response = requests.get(found_pdf_url, verify=False)
        pdf_response.raise_for_status()
        pdf_content_bytes = pdf_response.content
        print("PDF content downloaded successfully.")

    except requests.exceptions.RequestException as req_err:
        print(f"Network or HTTP error during web scraping or PDF download: {req_err}")
        print("NOTE: SSL verification is disabled for this URL. Re-enable for production.")
    except ValueError as val_err:
        print(f"Data error: {val_err}")
    except Exception as e:
        print(f"An unexpected error occurred during PDF URL retrieval or download: {e}")

    return pdf_content_bytes

def get_current_kdn_xml_url(url: str) -> Union[str, None]:
    """
    Fetches the MOHA KDN webpage and finds the XML download link.
    This function ONLY scrapes the URL and returns it.
    It does NOT handle any file storage or comparison logic.

    Args:
        url (str): The URL of the MOHA webpage to scrape for the XML link.

    Returns:
        Union[str, None]: The found XML URL (absolute path), or None if not found or an error occurs.
    """
    found_xml_url = None

    try:
        print(f"Checking for current XML link on: {url}")
        # Explicitly setting verify=False as requested by the user.
        response = requests.get(url, verify=False)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        soup = BeautifulSoup(response.content, "html.parser")
        base_url = "https://www.moha.gov.my" # Base URL to construct absolute link

        # Find all <a> tags on the page
        for tag in soup.find_all("a"):
            href = tag.get("href", "") # Get the 'href' attribute
            # Check if the link contains 'xml' to identify the XML download link
            if "xml" in href:
                # Construct the full URL
                if href.startswith('http'):
                    found_xml_url = href
                else:
                    found_xml_url = urljoin(base_url, href) # Use urljoin for robustness
                break # Exit loop once the XML link is found

        if not found_xml_url:
            print("Warning: XML download link not found on the webpage.")
            return None

        print(f"Found current XML link: {found_xml_url}")
        return found_xml_url

    except requests.exceptions.RequestException as req_err:
        print(f"Network or HTTP error during web scraping: {req_err}")
        print("NOTE: SSL verification is disabled for this URL. Re-enable for production.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return None # Return None if any error occurs
