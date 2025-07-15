import requests
from bs4 import BeautifulSoup
import os
from typing import Union
from urllib.parse import urljoin # Explicitly import urljoin for clarity

def get_kdn_pdf_content(url: str) -> Union[bytes, None]:
    """
    Fetches the MOHA KDN webpage, finds the PDF download link,
    and downloads the PDF content. This function does NOT use file-based URL storage
    for the PDF link itself.

    Args:
        url (str): The URL of the MOHA webpage to scrape for the PDF link.

    Returns:
        Union[bytes, None]: The PDF content as bytes if successfully downloaded, otherwise None.
    """
    pdf_content_bytes = None

    try:
        print("Fetching PDF URL from the Ministry of Home Affairs website...")
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
        pdf_response = requests.get(found_pdf_url, verify=False)
        pdf_response.raise_for_status()
        pdf_content_bytes = pdf_response.content
        print("PDF content downloaded successfully.")
            
    except requests.exceptions.RequestException as req_err:
        print(f"Network or HTTP error during web scraping or PDF download: {req_err}")
    except ValueError as val_err:
        print(f"Data error: {val_err}")
    except Exception as e:
        print(f"An unexpected error occurred during PDF URL retrieval or download: {e}")

    return pdf_content_bytes

def check_and_update_kdn_xml_url(url: str, url_storage_path: str) -> bool:
    """
    Fetches the MOHA KDN webpage, finds the XML download link,
    and compares it with a previously stored URL.
    Updates the stored URL and returns True if a new URL is found,
    otherwise returns False. Creates the storage file if it doesn't exist.

    Args:
        url (str): The URL of the MOHA webpage to scrape for the XML link.
        url_storage_path (str): The file path where the last updated XML URL is stored.

    Returns:
        bool: True if a new XML URL was found and updated, False otherwise.
    """
    found_xml_url = None
    
    try:
        print(f"Checking for new XML link on: {url}")
        # Fetch the webpage content, disabling SSL verification as per previous code
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
            return False

        # --- Handle URL storage file ---
        # If the storage file doesn't exist, create it as an empty file
        if not os.path.exists(url_storage_path):
            with open(url_storage_path, "w") as f:
                f.write("") # Create an empty file
            print(f"Created empty URL storage file: {url_storage_path}")

        # Read the last updated URL from the storage file
        last_updated_url = ""
        with open(url_storage_path, "r") as f:
            last_updated_url = f.read().strip() # Read and strip whitespace

        # Compare the found URL with the last stored URL
        if found_xml_url == last_updated_url:
            print(f"XML URL has not changed: {found_xml_url}. No update needed.")
            return False
        else:
            print(f"New XML URL found: {found_xml_url}. Updating storage.")
            # Write the new URL to the storage file
            with open(url_storage_path, "w") as f:
                f.write(found_xml_url)
            return True

    except requests.exceptions.RequestException as req_err:
        print(f"Network or HTTP error during web scraping: {req_err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    return False # Return False if any error occurs

if __name__ == "__main__":
    # This block is for testing this module independently
    moha_kdn_url = "https://www.moha.gov.my/index.php/en/maklumat-perkhidmatan/membanteras-pembiayaan-keganasan2/senarai-kementerian-dalam-negeri"
    xml_url_storage_file = "latest_kdn_xml_url.txt" 

    print("--- Testing check_and_update_kdn_xml_url ---")
    if check_and_update_kdn_xml_url(moha_kdn_url, xml_url_storage_file):
        print("XML URL was updated in storage.")
    else:
        print("XML URL was not updated in storage.")

    print("\n--- Testing get_kdn_pdf_content ---")
    pdf_content = get_kdn_pdf_content(moha_kdn_url)
    if pdf_content:
        print(f"PDF content downloaded successfully. Size: {len(pdf_content)} bytes")
    else:
        print("Failed to download PDF content.")
