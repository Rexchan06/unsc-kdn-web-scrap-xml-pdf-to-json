import json
import os # For file operations

# Import functions from our custom modules
from kdn_web_scraper import get_kdn_pdf_content, check_and_update_kdn_xml_url
from kdn_pdf_parser import convert_individuals_to_json, convert_groups_to_json

if __name__ == "__main__":
    # URL for the MOHA page containing the KDN sanction list links
    moha_kdn_page_url = "https://www.moha.gov.my/index.php/en/maklumat-perkhidmatan/membanteras-pembiayaan-keganasan2/senarai-kementerian-dalam-negeri"
    # File to store the last checked XML URL (this is the trigger for updates)
    xml_url_storage_file = "latest_kdn_xml_url.txt" 

    try:
        # Step 1: Check if the XML link on the MOHA page has changed.
        # This function also updates the 'latest_kdn_xml_url.txt' file if a new URL is found.
        xml_link_updated = check_and_update_kdn_xml_url(moha_kdn_page_url, xml_url_storage_file)

        pdf_content_bytes = None
        is_pdf_processed = False # Flag to indicate if PDF was processed

        if xml_link_updated:
            print("\nXML link updated. Proceeding to download PDF content.")
            # If the XML link has changed, we assume there might be an updated PDF.
            # Call get_kdn_pdf_content to download the latest PDF.
            pdf_content_bytes = get_kdn_pdf_content(moha_kdn_page_url)
            
            if pdf_content_bytes:
                is_pdf_processed = True
            else:
                print("Failed to download PDF content despite XML link update. No JSON files will be updated.")
        else:
            print("\nXML link not updated. Skipping PDF content download and processing.")

        # Step 2: Convert the downloaded PDF content into structured JSON files
        # This step only runs if a PDF was successfully downloaded after an XML link update.
        if is_pdf_processed and pdf_content_bytes:
            print("\nProcessing newly downloaded PDF content...")
            
            # Extract data for individuals from the PDF
            print("--- Extracting Individual Data (Pages 1-11) ---")
            individual_data = convert_individuals_to_json(pdf_content_bytes)
            output_individuals_json_file = "KDN_SANCTION_LIST_A.json" 
            with open(output_individuals_json_file, 'w', encoding='utf-8') as f:
                json.dump(individual_data, f, indent=4, ensure_ascii=False)
            print(f"Successfully extracted individual data to {output_individuals_json_file}")
            print(f"Total individual records extracted: {len(individual_data)}")

            # Extract data for groups from the PDF (assuming pages 12-14)
            print("\n--- Extracting Group Data (Pages 12-14) ---")
            # Pages 12-14 correspond to 0-indexed page numbers 11, 12, and 13
            group_data = convert_groups_to_json(pdf_content_bytes, start_page_num=11, end_page_num=13)
            output_groups_json_file = "KDN_SANCTION_LIST_B.json" 
            with open(output_groups_json_file, 'w', encoding='utf-8') as f:
                json.dump(group_data, f, indent=4, ensure_ascii=False)
            print(f"Successfully extracted group data to {output_groups_json_file}")
            print(f"Total group records extracted: {len(group_data)}")

    except Exception as e:
        print(f"An overall error occurred during the process: {e}")
