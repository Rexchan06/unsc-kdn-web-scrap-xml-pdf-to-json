# unsc_xml_parser.py
import requests
import json
import xmltodict
from typing import Union

def download_and_convert_xml_to_json(xml_url: str, output_json_path: str) -> bool:
    """
    Downloads an XML file's content directly into memory, converts it to JSON,
    and then saves the JSON data to a specified file. The raw XML file is NOT saved to disk.

    Args:
        xml_url (str): The URL of the XML file to download.
        output_json_path (str): The local file path where the converted JSON data will be saved.

    Returns:
        bool: True if the XML was successfully downloaded, converted, and saved as JSON, False otherwise.
    """
    try:
        print(f"Downloading XML content from: {xml_url}")
        # Download the XML content as bytes
        xml_response_content = requests.get(xml_url, verify=True).content
        
        # Parse the XML content (bytes) directly into a Python dictionary
        xml_dict = xmltodict.parse(xml_response_content)
        
        # Save the parsed dictionary as a JSON file
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(xml_dict, f, indent=2, ensure_ascii=False)
        
        print(f"JSON converted and saved to: {output_json_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading XML from {xml_url}: {e}")
        return False
    except xmltodict.expat.ExpatError as e:
        print(f"Error parsing XML from {xml_url}: {e}. The XML might be malformed or empty.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during XML download or conversion: {e}")
        return False
