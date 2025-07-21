import requests
import xmltodict
from typing import Union, Optional # Import Optional

# Import utility functions from common_utils module
from utils.common_utils import get_safe_string, get_safe_int

def transform_individual_data(individual_data: dict) -> dict:
    """
    Transforms individual data from xmltodict's default format to the desired JSON format.
    Handles single-value elements, ensures arrays, and cleans up attributes.
    Fields are omitted if empty, except for specific ones that must always be present as empty strings.
    """
    transformed = {}

    # Fields to be included even if empty, initialized to empty string or empty list
    always_present_fields = {
        "DATAID": "", "VERSIONNUM": "", "FIRST_NAME": "", "SECOND_NAME": "",
        "THIRD_NAME": "", "FOURTH_NAME": "", "UN_LIST_TYPE": "",
        "REFERENCE_NUMBER": "", "COMMENTS1": "", "NATIONALITY": [],
        "LISTED_ON": "", "NAME_ORIGINAL_SCRIPT": "", "SUBMITTED_BY": "",
        "INDIVIDUAL_ALIAS": [], "INDIVIDUAL_ADDRESS": [], "INDIVIDUAL_DATE_OF_BIRTH": [],
        "INDIVIDUAL_PLACE_OF_BIRTH": [], "INDIVIDUAL_DOCUMENT": [],
        "GENDER": "", "DESIGNATION": [], "NATIONAL_ID": [], "PASSPORT": [],
        "OTHER_INFORMATION": ""
    }
    transformed.update(always_present_fields)

    # Simple fields (string, int)
    transformed["DATAID"] = get_safe_int(individual_data.get("DATAID"))
    transformed["VERSIONNUM"] = get_safe_int(individual_data.get("VERSIONNUM"))
    transformed["FIRST_NAME"] = get_safe_string(individual_data.get("FIRST_NAME"))
    transformed["SECOND_NAME"] = get_safe_string(individual_data.get("SECOND_NAME"))
    transformed["THIRD_NAME"] = get_safe_string(individual_data.get("THIRD_NAME"))
    transformed["FOURTH_NAME"] = get_safe_string(individual_data.get("FOURTH_NAME"))
    transformed["UN_LIST_TYPE"] = get_safe_string(individual_data.get("UN_LIST_TYPE"))
    transformed["REFERENCE_NUMBER"] = get_safe_string(individual_data.get("REFERENCE_NUMBER"))
    transformed["COMMENTS1"] = get_safe_string(individual_data.get("COMMENTS1"))
    transformed["LISTED_ON"] = get_safe_string(individual_data.get("LISTED_ON"))
    transformed["NAME_ORIGINAL_SCRIPT"] = get_safe_string(individual_data.get("NAME_ORIGINAL_SCRIPT"))
    transformed["SUBMITTED_BY"] = get_safe_string(individual_data.get("SUBMITTED_BY"))
    transformed["GENDER"] = get_safe_string(individual_data.get("GENDER"))
    transformed["OTHER_INFORMATION"] = get_safe_string(individual_data.get("OTHER_INFORMATION"))

    # Handle lists of items (Nationality, Alias, Address, Date of Birth, Place of Birth, Document, Designation, National ID, Passport)
    # Ensure they are always lists, even if only one item or no items are present
    def ensure_list(item):
        if item is None:
            return []
        return [item] if not isinstance(item, list) else item

    # Nationality
    nationality_data = ensure_list(individual_data.get("NATIONALITY"))
    transformed["NATIONALITY"] = [get_safe_string(n.get("VALUE")) for n in nationality_data if n and n.get("VALUE")]

    # Alias
    alias_data = ensure_list(individual_data.get("INDIVIDUAL_ALIAS"))
    transformed["INDIVIDUAL_ALIAS"] = [
        {"QUALITY": get_safe_string(a.get("QUALITY")), "ALIAS_NAME": get_safe_string(a.get("ALIAS_NAME"))}
        for a in alias_data if a and a.get("ALIAS_NAME")
    ]

    # Address
    address_data = ensure_list(individual_data.get("INDIVIDUAL_ADDRESS"))
    transformed["INDIVIDUAL_ADDRESS"] = [
        {
            "CITY": get_safe_string(a.get("CITY")),
            "STREET": get_safe_string(a.get("STREET")),
            "STATE_PROVINCE": get_safe_string(a.get("STATE_PROVINCE")),
            "ZIP_CODE": get_safe_string(a.get("ZIP_CODE")),
            "COUNTRY": get_safe_string(a.get("COUNTRY")),
            "NOTE": get_safe_string(a.get("NOTE"))
        }
        for a in address_data if a and (a.get("CITY") or a.get("STREET") or a.get("COUNTRY")) # Only include if some address info exists
    ]

    # Date of Birth
    dob_data = ensure_list(individual_data.get("INDIVIDUAL_DATE_OF_BIRTH"))
    transformed["INDIVIDUAL_DATE_OF_BIRTH"] = [
        {
            "TYPE": get_safe_string(d.get("TYPE")),
            "DATE": get_safe_string(d.get("DATE")),
            "FROM_YEAR": get_safe_string(d.get("FROM_YEAR")),
            "TO_YEAR": get_safe_string(d.get("TO_YEAR")),
            "NOTE": get_safe_string(d.get("NOTE"))
        }
        for d in dob_data if d and (d.get("DATE") or d.get("FROM_YEAR") or d.get("TO_YEAR"))
    ]

    # Place of Birth
    pob_data = ensure_list(individual_data.get("INDIVIDUAL_PLACE_OF_BIRTH"))
    transformed["INDIVIDUAL_PLACE_OF_BIRTH"] = [
        {
            "CITY": get_safe_string(p.get("CITY")),
            "STATE_PROVINCE": get_safe_string(p.get("STATE_PROVINCE")),
            "COUNTRY": get_safe_string(p.get("COUNTRY")),
            "NOTE": get_safe_string(p.get("NOTE"))
        }
        for p in pob_data if p and (p.get("CITY") or p.get("COUNTRY"))
    ]

    # Document (Passport, National ID, etc.)
    doc_data = ensure_list(individual_data.get("INDIVIDUAL_DOCUMENT"))
    transformed["INDIVIDUAL_DOCUMENT"] = [
        {
            "TYPE": get_safe_string(d.get("TYPE")),
            "NUMBER": get_safe_string(d.get("NUMBER")),
            "ISSUE_DATE": get_safe_string(d.get("ISSUE_DATE")),
            "EXPIRY_DATE": get_safe_string(d.get("EXPIRY_DATE")),
            "COUNTRY_OF_ISSUE": get_safe_string(d.get("COUNTRY_OF_ISSUE")),
            "NOTE": get_safe_string(d.get("NOTE"))
        }
        for d in doc_data if d and d.get("NUMBER")
    ]

    # Designation
    designation_data = ensure_list(individual_data.get("DESIGNATION"))
    transformed["DESIGNATION"] = [get_safe_string(d.get("VALUE")) for d in designation_data if d and d.get("VALUE")]

    # National ID
    national_id_data = ensure_list(individual_data.get("NATIONAL_ID"))
    transformed["NATIONAL_ID"] = [
        {
            "TYPE": get_safe_string(n.get("TYPE")),
            "NUMBER": get_safe_string(n.get("NUMBER")),
            "ISSUE_DATE": get_safe_string(n.get("ISSUE_DATE")),
            "COUNTRY_OF_ISSUE": get_safe_string(n.get("COUNTRY_OF_ISSUE")),
            "NOTE": get_safe_string(n.get("NOTE"))
        }
        for n in national_id_data if n and n.get("NUMBER")
    ]

    # Passport
    passport_data = ensure_list(individual_data.get("PASSPORT"))
    transformed["PASSPORT"] = [
        {
            "NUMBER": get_safe_string(p.get("NUMBER")),
            "ISSUE_DATE": get_safe_string(p.get("ISSUE_DATE")),
            "COUNTRY_OF_ISSUE": get_safe_string(p.get("COUNTRY_OF_ISSUE")),
            "NOTE": get_safe_string(p.get("NOTE"))
        }
        for p in passport_data if p and p.get("NUMBER")
    ]

    return transformed

def transform_entity_data(entity_data: dict) -> dict:
    """
    Transforms entity data from xmltodict's default format to the desired JSON format.
    Handles single-value elements, ensures arrays, and cleans up attributes.
    Fields are omitted if empty, except for specific ones that must always be present as empty strings.
    """
    transformed = {}

    # Fields to be included even if empty, initialized to empty string or empty list
    always_present_fields = {
        "DATAID": "", "VERSIONNUM": "", "FIRST_NAME": "", "UN_LIST_TYPE": "",
        "REFERENCE_NUMBER": "", "COMMENTS1": "", "LISTED_ON": "",
        "NAME_ORIGINAL_SCRIPT": "", "SUBMITTED_BY": "", "ENTITY_ALIAS": [],
        "ENTITY_ADDRESS": [], "OTHER_INFORMATION": ""
    }
    transformed.update(always_present_fields)

    # Simple fields (string, int)
    transformed["DATAID"] = get_safe_int(entity_data.get("DATAID"))
    transformed["VERSIONNUM"] = get_safe_int(entity_data.get("VERSIONNUM"))
    transformed["FIRST_NAME"] = get_safe_string(entity_data.get("FIRST_NAME")) # For entities, this is the entity name
    transformed["UN_LIST_TYPE"] = get_safe_string(entity_data.get("UN_LIST_TYPE"))
    transformed["REFERENCE_NUMBER"] = get_safe_string(entity_data.get("REFERENCE_NUMBER"))
    transformed["COMMENTS1"] = get_safe_string(entity_data.get("COMMENTS1"))
    transformed["LISTED_ON"] = get_safe_string(entity_data.get("LISTED_ON"))
    transformed["NAME_ORIGINAL_SCRIPT"] = get_safe_string(entity_data.get("NAME_ORIGINAL_SCRIPT"))
    transformed["SUBMITTED_BY"] = get_safe_string(entity_data.get("SUBMITTED_BY"))
    transformed["OTHER_INFORMATION"] = get_safe_string(entity_data.get("OTHER_INFORMATION"))

    # Handle lists of items (Alias, Address)
    def ensure_list(item):
        if item is None:
            return []
        return [item] if not isinstance(item, list) else item

    # Alias
    alias_data = ensure_list(entity_data.get("ENTITY_ALIAS"))
    transformed["ENTITY_ALIAS"] = [
        {"QUALITY": get_safe_string(a.get("QUALITY")), "ALIAS_NAME": get_safe_string(a.get("ALIAS_NAME"))}
        for a in alias_data if a and a.get("ALIAS_NAME")
    ]

    # Address
    address_data = ensure_list(entity_data.get("ENTITY_ADDRESS"))
    transformed["ENTITY_ADDRESS"] = [
        {
            "CITY": get_safe_string(a.get("CITY")),
            "STREET": get_safe_string(a.get("STREET")),
            "STATE_PROVINCE": get_safe_string(a.get("STATE_PROVINCE")),
            "ZIP_CODE": get_safe_string(a.get("ZIP_CODE")),
            "COUNTRY": get_safe_string(a.get("COUNTRY")),
            "NOTE": get_safe_string(a.get("NOTE"))
        }
        for a in address_data if a and (a.get("CITY") or a.get("STREET") or a.get("COUNTRY")) # Only include if some address info exists
    ]

    return transformed


def download_and_convert_xml_to_json(xml_url: str, xml_content_bytes: Optional[bytes] = None) -> Union[dict, None]:
    """
    Downloads an XML file from the given URL and converts it to a structured JSON dictionary.
    Optionally accepts pre-downloaded XML content to avoid redundant HTTP requests.

    Args:
        xml_url (str): The URL of the XML file.
        xml_content_bytes (Optional[bytes]): Pre-downloaded XML content as bytes. If None,
                                             the function will download it from xml_url.

    Returns:
        Union[dict, None]: A dictionary representing the XML content in the desired JSON format,
                           or None if an error occurs.
    """
    try:
        if xml_content_bytes is None:
            print(f"Downloading XML content from {xml_url}...")
            # Fetch the XML content, ensuring SSL verification is enabled
            response = requests.get(xml_url, verify=True)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            xml_content_bytes = response.content
        else:
            print("Using pre-downloaded XML content for conversion.")

        # Convert XML to Python dictionary using xmltodict
        # The process_namespaces=True helps in handling XML namespaces correctly,
        # but we then strip them for cleaner JSON keys.
        xml_dict = xmltodict.parse(xml_content_bytes, process_namespaces=False)

        final_json_data = {"CONSOLIDATED_LIST": {}}

        # Extract CONSOLIDATED_LIST and its attributes
        consolidated_list = xml_dict.get("CONSOLIDATED_LIST", {})
        if consolidated_list:
            # Handle INDIVIDUALS
            individuals_data = consolidated_list.get("INDIVIDUALS", {}).get("INDIVIDUAL")
            if individuals_data:
                # Ensure individuals_data is always a list for consistent processing
                if not isinstance(individuals_data, list):
                    individuals_data = [individuals_data]
                final_json_data["CONSOLIDATED_LIST"]["INDIVIDUALS"] = {
                    "INDIVIDUAL": [transform_individual_data(individual) for individual in individuals_data]
                }
            else:
                final_json_data["CONSOLIDATED_LIST"]["INDIVIDUALS"] = {"INDIVIDUAL": []}

            # Handle ENTITIES
            entities_data = consolidated_list.get("ENTITIES", {}).get("ENTITY")
            if entities_data:
                # Ensure entities_data is always a list for consistent processing
                if not isinstance(entities_data, list):
                    entities_data = [entities_data]
                final_json_data["CONSOLIDATED_LIST"]["ENTITIES"] = {
                    "ENTITY": [transform_entity_data(entity) for entity in entities_data]
                }
            else:
                final_json_data["CONSOLIDATED_LIST"]["ENTITIES"] = {"ENTITY": []}


            # Extract and rename specific attributes from the top-level CONSOLIDATED_LIST
            attribute_map = {
                "@xmlns:xsi": "_xmlns:xsi",
                "@xsi:noNamespaceSchemaLocation": "_xsi:noNamespaceSchemaLocation",
                "@dateGenerated": "_dateGenerated"
            }

            attributes_to_move = {}
            for original_key, new_key in attribute_map.items():
                if original_key in consolidated_list:
                    attributes_to_move[new_key] = consolidated_list.pop(original_key)

            # Add the moved attributes to the final_json_data["CONSOLIDATED_LIST"]
            final_json_data["CONSOLIDATED_LIST"].update(attributes_to_move)

        print(f"XML content from {xml_url} converted to JSON dictionary.")
        return final_json_data # Return the dictionary instead of saving to file

    except requests.exceptions.RequestException as e:
        print(f"Error downloading XML from {xml_url}: {e}")
        return None
    except xmltodict.expat.ExpatError as e:
        print(f"Error parsing XML from {xml_url}: {e}. The XML might be malformed or empty.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during XML conversion: {e}")
        return None
