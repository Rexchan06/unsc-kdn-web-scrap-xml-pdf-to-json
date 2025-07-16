# main.py
import json
import os
from datetime import datetime

# --- Import functions for UN Security Council Sanction List ---
# Assuming these modules are in the 'UNSC' sub-directory
from UNSC.unsc_web_scraper import get_last_updated_date, get_xml_link
from UNSC.unsc_xml_parser import download_and_convert_xml_to_json # Your XML to JSON conversion function

# --- Import functions for KDN Sanction List ---
# Assuming these modules are in the 'KDN' sub-directory
from KDN.kdn_web_scraper import get_kdn_pdf_content, check_and_update_kdn_xml_url
from KDN.kdn_pdf_parser import convert_individuals_to_json, convert_groups_to_json

def run_unsc_sanction_list_process():
    """
    Handles the entire process for checking, downloading, and converting
    the UN Security Council Consolidated Sanction List.
    """
    un_security_council_url = "https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list"
    # Output file now in the 'UNSC' folder
    output_folder_unsc = 'UNSC'
    output_json_file_unsc = os.path.join(output_folder_unsc, 'UNSCR_SANCTION_LIST.json')

    print("\n--- Starting UN Sanction List update check ---")

    # Ensure the UNSC output directory exists
    os.makedirs(output_folder_unsc, exist_ok=True)

    # Get the last updated date from the website
    last_update_date = get_last_updated_date(un_security_council_url)
    today_date = datetime.now().date() # Get today's date for comparison

    if last_update_date:
        print(f"Last updated date on website: {last_update_date}")
        print(f"Today's date: {today_date}")

        # Compare the last updated date with today's date.
        # The condition `last_update_date == today_date` means it will only proceed
        # if the list was updated exactly today.
        if last_update_date == today_date:
            print("The UN list was updated today. Proceeding to download and convert.")
            xml_link = get_xml_link(un_security_council_url)
            if xml_link:
                # Call the function to download XML content and convert directly to JSON
                if download_and_convert_xml_to_json(xml_link, output_json_file_unsc):
                    print(f"UNSC JSON data saved to {output_json_file_unsc}")
                else:
                    print("Failed to convert UN XML to JSON.")
            else:
                print("Failed to get UN XML download link.")
        else:
            print("The UN list was not updated today. Skipping download and conversion.")
    else:
        print("Could not determine the UN list last updated date. Skipping download and conversion.")

def run_kdn_sanction_list_process():
    """
    Handles the entire process for checking, downloading, and converting
    the KDN Sanction List (PDF based).
    """
    # URL for the MOHA page containing the KDN sanction list links
    moha_kdn_page_url = "https://www.moha.gov.my/index.php/en/maklumat-perkhidmatan/membanteras-pembiayaan-keganasan2/senarai-kementerian-dalam-negeri"
    # File to store the last checked XML URL (this is the trigger for updates)
    # This file should also be in the KDN folder
    output_folder_kdn = 'KDN'
    xml_url_storage_file = os.path.join(output_folder_kdn, "latest_kdn_xml_url.txt")

    print("\n--- Starting KDN Sanction List update check ---")

    # Ensure the KDN output directory exists
    os.makedirs(output_folder_kdn, exist_ok=True)

    try:
        # Step 1: Check if the XML link on the MOHA page has changed.
        # This function also updates the 'latest_kdn_xml_url.txt' file if a new URL is found.
        xml_link_updated = check_and_update_kdn_xml_url(moha_kdn_page_url, xml_url_storage_file)

        pdf_content_bytes = None
        is_pdf_processed = False # Flag to indicate if PDF was processed

        if xml_link_updated:
            print("KDN XML link updated. Proceeding to download PDF content.")
            # If the XML link has changed, we assume there might be an updated PDF.
            # Call get_kdn_pdf_content to download the latest PDF.
            pdf_content_bytes = get_kdn_pdf_content(moha_kdn_page_url)

            if pdf_content_bytes:
                is_pdf_processed = True
            else:
                print("Failed to download KDN PDF content despite XML link update. No JSON files will be updated.")
        else:
            print("KDN XML link not updated. Skipping PDF content download and processing.")

        # Step 2: Convert the downloaded PDF content into structured JSON files
        # This step only runs if a PDF was successfully downloaded after an an XML link update.
        if is_pdf_processed and pdf_content_bytes:
            print("\nProcessing newly downloaded KDN PDF content...")

            # Extract data for individuals from the PDF
            print("--- Extracting Individual Data (Pages 1-11) ---")
            individual_data = convert_individuals_to_json(pdf_content_bytes)
            output_individuals_json_file = os.path.join(output_folder_kdn, "KDN_SANCTION_LIST_A.json")
            with open(output_individuals_json_file, 'w', encoding='utf-8') as f:
                json.dump(individual_data, f, indent=4, ensure_ascii=False)
            print(f"Successfully extracted individual data to {output_individuals_json_file}")
            print(f"Total individual records extracted: {len(individual_data)}")

            # Extract data for groups from the PDF (assuming pages 12-14)
            print("\n--- Extracting Group Data (Pages 12-14) ---")
            # Pages 12-14 correspond to 0-indexed page numbers 11, 12, and 13
            group_data = convert_groups_to_json(pdf_content_bytes, start_page_num=11, end_page_num=13)
            output_groups_json_file = os.path.join(output_folder_kdn, "KDN_SANCTION_LIST_B.json")
            with open(output_groups_json_file, 'w', encoding='utf-8') as f:
                json.dump(group_data, f, indent=4, ensure_ascii=False)
            print(f"Successfully extracted group data to {output_groups_json_file}")
            print(f"Total group records extracted: {len(group_data)}")

    except Exception as e:
        print(f"An overall error occurred during the KDN process: {e}")

if __name__ == "__main__":
    # Run the UN Security Council sanction list process
    run_unsc_sanction_list_process()

    # Run the KDN sanction list process
    run_kdn_sanction_list_process()

    print("\nAll sanction list updates checked and processed.")
