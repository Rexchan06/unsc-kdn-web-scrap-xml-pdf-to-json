# main_unsc.py
import json
from datetime import datetime
import os # For file operations like checking if storage file exists

# Import functions from our custom modules
from unsc_web_scraper import get_last_updated_date, get_xml_link
from unsc_xml_parser import download_and_convert_xml_to_json

if __name__ == "__main__":
    un_security_council_url = "https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list"
    output_json_file = 'UNSCR_SANCTION_LIST.json'

    print("Starting UN Sanction List update check...")
    
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
            print("The list was updated today. Proceeding to download and convert.")
            xml_link = get_xml_link(un_security_council_url)
            if xml_link:
                # Call the function to download XML content and convert directly to JSON
                download_and_convert_xml_to_json(xml_link, output_json_file)
            else:
                print("Failed to get XML download link.")
        else:
            print("The list was not updated today. Skipping download and conversion.")
    else:
        print("Could not determine the last updated date. Skipping download and conversion.")

