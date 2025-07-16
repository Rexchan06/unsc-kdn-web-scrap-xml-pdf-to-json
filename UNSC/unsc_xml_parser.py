import requests
import json
import xmltodict
from typing import Union

def get_safe_string(value: Union[str, None]) -> str:
    """
    Safely converts a value to a string and strips whitespace.
    Returns an empty string if the value is None or not a string.
    """
    if isinstance(value, str):
        return value.strip()
    return ""

def get_safe_int(value: Union[str, dict, None]) -> Union[int, str]:
    """
    Safely converts a value to an integer.
    Handles cases where xmltodict might return a dict for elements with attributes and text.
    Returns an empty string if conversion to a valid integer is not possible.
    """
    if isinstance(value, dict):
        text_val = value.get("#text")
        if isinstance(text_val, str) and text_val.isdigit():
            return int(text_val)
    elif isinstance(value, str) and value.isdigit():
        return int(value)
    return "" # Return empty string for non-numeric or None values

def transform_individual_data(individual_data: dict) -> dict:
    """
    Transforms individual data from xmltodict's default format to the desired JSON format.
    Handles single-value elements, ensures arrays, and cleans up attributes.
    Fields are omitted if empty, except for specific ones that must always be present as empty strings.
    """
    transformed = {}

    # Fields to be included ONLY if they have a non-empty value
    fields_to_omit_if_empty = [
        "DATAID", "VERSIONNUM", "FIRST_NAME", "SECOND_NAME", "THIRD_NAME",
        "UN_LIST_TYPE", "REFERENCE_NUMBER", "LISTED_ON", "GENDER",
        "NAME_ORIGINAL_SCRIPT", "COMMENTS1"
    ]

    for field in fields_to_omit_if_empty:
        value = individual_data.get(field)
        if field == "DATAID":
            safe_value = get_safe_int(value)
            if safe_value != "":
                transformed[field] = safe_value
        else:
            safe_value = get_safe_string(value)
            if safe_value:
                transformed[field] = safe_value

    # Handle 'TITLE' - Omit if empty
    title = individual_data.get("TITLE")
    title_value = ""
    if isinstance(title, dict) and "VALUE" in title:
        title_value = get_safe_string(title["VALUE"])
    elif isinstance(title, str):
        title_value = get_safe_string(title)
    if title_value:
        transformed["TITLE"] = {"VALUE": title_value}

    # Handle 'DESIGNATION' - Omit if empty
    designation = individual_data.get("DESIGNATION")
    designation_values = []
    if isinstance(designation, dict) and "VALUE" in designation:
        if isinstance(designation["VALUE"], list):
            designation_values = [get_safe_string(val) for val in designation["VALUE"] if get_safe_string(val)]
        else:
            single_val = get_safe_string(designation["VALUE"])
            if single_val:
                designation_values = [single_val]
    elif isinstance(designation, str):
        single_val = get_safe_string(designation)
        if single_val:
            designation_values = [single_val]
    if designation_values:
        transformed["DESIGNATION"] = {"VALUE": designation_values}

    # Handle 'NATIONALITY' - Omit if empty
    nationality = individual_data.get("NATIONALITY")
    nationality_value = ""
    if isinstance(nationality, dict) and "VALUE" in nationality:
        nationality_value = get_safe_string(nationality["VALUE"])
    if nationality_value:
        transformed["NATIONALITY"] = {"VALUE": nationality_value}

    # Handle 'LIST_TYPE' - Omit if empty
    list_type = individual_data.get("LIST_TYPE")
    list_type_value = ""
    if isinstance(list_type, dict) and "VALUE" in list_type:
        list_type_value = get_safe_string(list_type["VALUE"])
    if list_type_value:
        transformed["LIST_TYPE"] = {"VALUE": list_type_value}

    # Handle 'LAST_DAY_UPDATED' - Omit if empty
    last_day_updated = individual_data.get("LAST_DAY_UPDATED")
    updated_dates = []
    if isinstance(last_day_updated, dict) and "VALUE" in last_day_updated:
        if isinstance(last_day_updated["VALUE"], list):
            updated_dates = [get_safe_string(val) for val in last_day_updated["VALUE"] if get_safe_string(val)]
        else:
            single_date = get_safe_string(last_day_updated["VALUE"])
            if single_date:
                updated_dates = [single_date]
    if updated_dates:
        if len(updated_dates) == 1:
            transformed["LAST_DAY_UPDATED"] = {"VALUE": updated_dates[0]}
        else:
            transformed["LAST_DAY_UPDATED"] = {"VALUE": updated_dates}

    # Handle 'INDIVIDUAL_ALIAS' - specific handling for empty case
    aliases = individual_data.get("INDIVIDUAL_ALIAS")
    processed_aliases = []
    if aliases:
        if isinstance(aliases, list):
            for a in aliases:
                if isinstance(a, dict):
                    alias_name = get_safe_string(a.get("ALIAS_NAME"))
                    if alias_name:
                        processed_aliases.append({
                            "QUALITY": get_safe_string(a.get("QUALITY")),
                            "ALIAS_NAME": alias_name
                        })
        elif isinstance(aliases, dict):
            alias_name = get_safe_string(aliases.get("ALIAS_NAME"))
            if alias_name:
                processed_aliases.append({
                    "QUALITY": get_safe_string(aliases.get("QUALITY")),
                    "ALIAS_NAME": alias_name
                })
    if processed_aliases:
        transformed["INDIVIDUAL_ALIAS"] = processed_aliases
    else:
        transformed["INDIVIDUAL_ALIAS"] = {"QUALITY": "", "ALIAS_NAME": ""}

    # Handle 'INDIVIDUAL_ADDRESS' - Omit if empty
    address = individual_data.get("INDIVIDUAL_ADDRESS")
    temp_address = {
        "COUNTRY": get_safe_string(address.get("COUNTRY")) if isinstance(address, dict) else "",
        "CITY": get_safe_string(address.get("CITY")) if isinstance(address, dict) else "",
        "STATE_PROVINCE": get_safe_string(address.get("STATE_PROVINCE")) if isinstance(address, dict) else "",
        "STREET": get_safe_string(address.get("STREET")) if isinstance(address, dict) else "",
        "ZIP_CODE": get_safe_string(address.get("ZIP_CODE")) if isinstance(address, dict) else "",
        "NOTE": get_safe_string(address.get("NOTE")) if isinstance(address, dict) else ""
    }
    cleaned_address = {k: v for k, v in temp_address.items() if v}
    if cleaned_address:
        transformed["INDIVIDUAL_ADDRESS"] = cleaned_address
    else:
        if "COUNTRY" in temp_address and not temp_address["COUNTRY"]:
            transformed["INDIVIDUAL_ADDRESS"] = {"COUNTRY": ""}

    # Handle 'INDIVIDUAL_DATE_OF_BIRTH' - Omit if empty
    dob = individual_data.get("INDIVIDUAL_DATE_OF_BIRTH")
    temp_dob = {
        "TYPE_OF_DATE": get_safe_string(dob.get("TYPE_OF_DATE")) if isinstance(dob, dict) else "",
        "DATE": get_safe_string(dob.get("DATE")) if isinstance(dob, dict) else "",
        "YEAR": get_safe_int(dob.get("YEAR")) if isinstance(dob, dict) else "",
        "FROM_YEAR": get_safe_int(dob.get("FROM_YEAR")) if isinstance(dob, dict) else "",
        "TO_YEAR": get_safe_int(dob.get("TO_YEAR")) if isinstance(dob, dict) else "",
        "NOTE": get_safe_string(dob.get("NOTE")) if isinstance(dob, dict) else ""
    }
    cleaned_dob = {k: v for k, v in temp_dob.items() if v != "" and v != 0}
    if cleaned_dob:
        transformed["INDIVIDUAL_DATE_OF_BIRTH"] = cleaned_dob

    # Handle 'INDIVIDUAL_PLACE_OF_BIRTH' - specific handling for empty case
    pob = individual_data.get("INDIVIDUAL_PLACE_OF_BIRTH")
    processed_pobs = []
    if pob:
        if isinstance(pob, list):
            for p in pob:
                if isinstance(p, dict):
                    temp_p = {
                        "CITY": get_safe_string(p.get("CITY")),
                        "STATE_PROVINCE": get_safe_string(p.get("STATE_PROVINCE")),
                        "COUNTRY": get_safe_string(p.get("COUNTRY")),
                        "NOTE": get_safe_string(p.get("NOTE"))
                    }
                    cleaned_p = {k: v for k, v in temp_p.items() if v}
                    if cleaned_p:
                        processed_pobs.append(cleaned_p)
        elif isinstance(pob, dict):
            temp_p = {
                "CITY": get_safe_string(pob.get("CITY")),
                "STATE_PROVINCE": get_safe_string(pob.get("STATE_PROVINCE")),
                "COUNTRY": get_safe_string(pob.get("COUNTRY")),
                "NOTE": get_safe_string(pob.get("NOTE"))
            }
            cleaned_p = {k: v for k, v in temp_p.items() if v}
            if cleaned_p:
                processed_pobs.append(cleaned_p)
    if processed_pobs:
        if len(processed_pobs) == 1:
            transformed["INDIVIDUAL_PLACE_OF_BIRTH"] = processed_pobs[0]
        else:
            transformed["INDIVIDUAL_PLACE_OF_BIRTH"] = processed_pobs
    else:
        transformed["INDIVIDUAL_PLACE_OF_BIRTH"] = {"COUNTRY": ""}

    # Handle 'INDIVIDUAL_DOCUMENT' - ALWAYS include as empty string if no content
    documents = individual_data.get("INDIVIDUAL_DOCUMENT")
    processed_documents = []
    if documents:
        if isinstance(documents, list):
            for d in documents:
                if isinstance(d, dict):
                    temp_d = {
                        "TYPE_OF_DOCUMENT": get_safe_string(d.get("TYPE_OF_DOCUMENT")),
                        "NUMBER": get_safe_string(d.get("NUMBER")),
                        "ISSUING_COUNTRY": get_safe_string(d.get("ISSUING_COUNTRY")),
                        "DATE_OF_ISSUE": get_safe_string(d.get("DATE_OF_ISSUE")),
                        "EXPIRY_DATE": get_safe_string(d.get("EXPIRY_DATE")),
                        "NOTE": get_safe_string(d.get("NOTE"))
                    }
                    cleaned_d = {k: v for k, v in temp_d.items() if v}
                    if cleaned_d:
                        processed_documents.append(cleaned_d)
        elif isinstance(documents, dict):
            temp_d = {
                "TYPE_OF_DOCUMENT": get_safe_string(documents.get("TYPE_OF_DOCUMENT")),
                "NUMBER": get_safe_string(documents.get("NUMBER")),
                "ISSUING_COUNTRY": get_safe_string(documents.get("ISSUING_COUNTRY")),
                "DATE_OF_ISSUE": get_safe_string(documents.get("DATE_OF_ISSUE")),
                "EXPIRY_DATE": get_safe_string(documents.get("EXPIRY_DATE")),
                "NOTE": get_safe_string(documents.get("NOTE"))
            }
            cleaned_d = {k: v for k, v in temp_d.items() if v}
            if cleaned_d:
                processed_documents.append(cleaned_d)
    if processed_documents:
        if len(processed_documents) == 1:
            transformed["INDIVIDUAL_DOCUMENT"] = processed_documents[0]
        else:
            transformed["INDIVIDUAL_DOCUMENT"] = processed_documents
    else:
        transformed["INDIVIDUAL_DOCUMENT"] = "" # Explicitly set to empty string

    # Handle SORT_KEY and SORT_KEY_LAST_MOD - ALWAYS include as empty string if no content
    transformed["SORT_KEY"] = get_safe_string(individual_data.get("SORT_KEY"))
    transformed["SORT_KEY_LAST_MOD"] = get_safe_string(individual_data.get("SORT_KEY_LAST_MOD"))

    return transformed

def transform_entity_data(entity_data: dict) -> dict:
    """
    Transforms entity data from xmltodict's default format to the desired JSON format.
    Handles single-value elements, ensures arrays, and cleans up attributes.
    Fields are omitted if empty, except for specific ones that must always be present as empty strings.
    """
    transformed = {}

    # Fields to be included ONLY if they have a non-empty value
    fields_to_omit_if_empty = [
        "DATAID", "VERSIONNUM", "FIRST_NAME", "UN_LIST_TYPE", "REFERENCE_NUMBER",
        "LISTED_ON", "COMMENTS1"
    ]

    for field in fields_to_omit_if_empty:
        value = entity_data.get(field)
        if field == "DATAID":
            safe_value = get_safe_int(value)
            if safe_value != "":
                transformed[field] = safe_value
        else:
            safe_value = get_safe_string(value)
            if safe_value:
                transformed[field] = safe_value

    # Handle 'LIST_TYPE' - Omit if empty
    list_type = entity_data.get("LIST_TYPE")
    list_type_value = ""
    if isinstance(list_type, dict) and "VALUE" in list_type:
        list_type_value = get_safe_string(list_type["VALUE"])
    if list_type_value:
        transformed["LIST_TYPE"] = {"VALUE": list_type_value}

    # Handle 'LAST_DAY_UPDATED' - Omit if empty
    last_day_updated = entity_data.get("LAST_DAY_UPDATED")
    updated_dates = []
    if isinstance(last_day_updated, dict) and "VALUE" in last_day_updated:
        if isinstance(last_day_updated["VALUE"], list):
            updated_dates = [get_safe_string(val) for val in last_day_updated["VALUE"] if get_safe_string(val)]
        else:
            single_date = get_safe_string(last_day_updated["VALUE"])
            if single_date:
                updated_dates = [single_date]
    if updated_dates:
        if len(updated_dates) == 1:
            transformed["LAST_DAY_UPDATED"] = {"VALUE": updated_dates[0]}
        else:
            transformed["LAST_DAY_UPDATED"] = {"VALUE": updated_dates}

    # Handle 'ENTITY_ALIAS' - specific handling for empty case
    aliases = entity_data.get("ENTITY_ALIAS")
    processed_aliases = []
    if aliases:
        if isinstance(aliases, list):
            for a in aliases:
                if isinstance(a, dict):
                    alias_name = get_safe_string(a.get("ALIAS_NAME"))
                    if alias_name:
                        processed_aliases.append({
                            "QUALITY": get_safe_string(a.get("QUALITY")),
                            "ALIAS_NAME": alias_name
                        })
        elif isinstance(aliases, dict):
            alias_name = get_safe_string(aliases.get("ALIAS_NAME"))
            if alias_name:
                processed_aliases.append({
                    "QUALITY": get_safe_string(aliases.get("QUALITY")),
                    "ALIAS_NAME": alias_name
                })
    if processed_aliases:
        transformed["ENTITY_ALIAS"] = processed_aliases
    else:
        transformed["ENTITY_ALIAS"] = {"QUALITY": "", "ALIAS_NAME": ""}

    # Handle 'ENTITY_ADDRESS'
    address = entity_data.get("ENTITY_ADDRESS")
    processed_addresses = []
    if address:
        if isinstance(address, list):
            for a in address:
                if isinstance(a, dict):
                    temp_a = {
                        "STREET": get_safe_string(a.get("STREET")),
                        "CITY": get_safe_string(a.get("CITY")),
                        "STATE_PROVINCE": get_safe_string(a.get("STATE_PROVINCE")),
                        "ZIP_CODE": get_safe_string(a.get("ZIP_CODE")),
                        "COUNTRY": get_safe_string(a.get("COUNTRY")),
                        "NOTE": get_safe_string(a.get("NOTE"))
                    }
                    cleaned_a = {k: v for k, v in temp_a.items() if v}
                    if cleaned_a:
                        processed_addresses.append(cleaned_a)
        elif isinstance(address, dict):
            temp_a = {
                "STREET": get_safe_string(address.get("STREET")),
                "CITY": get_safe_string(address.get("CITY")),
                "STATE_PROVINCE": get_safe_string(address.get("STATE_PROVINCE")),
                "ZIP_CODE": get_safe_string(address.get("ZIP_CODE")),
                "COUNTRY": get_safe_string(address.get("COUNTRY")),
                "NOTE": get_safe_string(address.get("NOTE"))
            }
            cleaned_a = {k: v for k, v in temp_a.items() if v}
            if cleaned_a:
                processed_addresses.append(cleaned_a)
    if processed_addresses:
        if len(processed_addresses) == 1:
            transformed["ENTITY_ADDRESS"] = processed_addresses[0]
        else:
            transformed["ENTITY_ADDRESS"] = processed_addresses
    else:
        transformed["ENTITY_ADDRESS"] = {"COUNTRY": ""} # Always include country even if empty

    # Handle SORT_KEY and SORT_KEY_LAST_MOD - ALWAYS include as empty string if no content
    transformed["SORT_KEY"] = get_safe_string(entity_data.get("SORT_KEY"))
    transformed["SORT_KEY_LAST_MOD"] = get_safe_string(entity_data.get("SORT_KEY_LAST_MOD"))

    return transformed


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
        xml_response_content = requests.get(xml_url, verify=True).content

        # Parse the XML content (bytes) directly into a Python dictionary
        xml_dict = xmltodict.parse(
            xml_response_content,
            dict_constructor=dict
        )

        final_json_data = {}
        if "CONSOLIDATED_LIST" in xml_dict:
            consolidated_list = xml_dict["CONSOLIDATED_LIST"]
            final_json_data["CONSOLIDATED_LIST"] = {}

            # Handle INDIVIDUALS
            if "INDIVIDUALS" in consolidated_list and "INDIVIDUAL" in consolidated_list["INDIVIDUALS"]:
                individuals_data = consolidated_list["INDIVIDUALS"]["INDIVIDUAL"]
                if not isinstance(individuals_data, list):
                    individuals_data = [individuals_data]

                final_json_data["CONSOLIDATED_LIST"]["INDIVIDUALS"] = {
                    "INDIVIDUAL": [transform_individual_data(ind) for ind in individuals_data]
                }
            else:
                final_json_data["CONSOLIDATED_LIST"]["INDIVIDUALS"] = {"INDIVIDUAL": []}

            # Handle ENTITIES
            if "ENTITIES" in consolidated_list and "ENTITY" in consolidated_list["ENTITIES"]:
                entities_data = consolidated_list["ENTITIES"]["ENTITY"]
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

        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(final_json_data, f, indent=2, ensure_ascii=False)

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