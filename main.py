# main.py
import json
import os
from datetime import datetime
import logging
from config.settings import AWS_REGION, UN_SECURITY_COUNCIL_URL, KDN_MOHA_URL, KDN_LAST_XML_URL_KEY, UNSC_S3_OBJECT_KEY, S3_BUCKET_NAME, KDN_GROUPS_S3_KEY, KDN_INDIVIDUALS_S3_KEY, LOCAL_OUTPUT_DIRECTORY
from utils.aws_s3_utils import upload_json_to_s3, read_s3_state_file, write_s3_state_file

# Configure logging for better visibility in CloudWatch Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Import functions for UN Security Council Sanction List ---
# Assuming these modules are in the 'UNSC' sub-directory
from UNSC.unsc_web_scraper import get_last_updated_date, get_xml_link
from UNSC.unsc_xml_parser import download_and_convert_xml_to_json

# --- Import functions for KDN Sanction List ---
# Assuming these modules are in the 'KDN' sub-directory
from KDN.kdn_web_scraper import get_kdn_pdf_content, get_current_kdn_xml_url # get_current_kdn_xml_url is the new name
from KDN.kdn_pdf_parser import convert_individuals_to_json, convert_groups_to_json

# --- Helper function for local file saving ---
def _save_json_to_local_file(data: dict, file_path: str) -> bool:
    """
    Saves JSON data to a local file.
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"JSON data successfully saved to local file: {file_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to save JSON data to local file {file_path}: {e}")
        return False

# --- Core Processing Functions ---

def run_unsc_sanction_list_process(local_mode: bool = False):
    """
    Handles the entire process for checking, downloading, and converting
    the UN Security Council Consolidated Sanction List, then uploading to S3 or saving locally.
    """

    logging.info("\n--- Starting UN Sanction List update check ---")

    # unsc_web_scraper.py and unsc_xml_parser.py are now set to verify=True
    last_update_date = get_last_updated_date(UN_SECURITY_COUNCIL_URL)
    today_date = datetime.now().date()

    if last_update_date:
        logging.info(f"Last updated date on UN website: {last_update_date}")
        logging.info(f"Today's date: {today_date}")

        if last_update_date <= today_date:
            logging.info("The UN list was updated today. Proceeding to download and convert.")
            xml_link = get_xml_link(UN_SECURITY_COUNCIL_URL)
            if xml_link:
                # download_and_convert_xml_to_json now returns the dict
                unsc_json_data = download_and_convert_xml_to_json(xml_link)
                if unsc_json_data:
                    if local_mode:
                        output_file_path = os.path.join(LOCAL_OUTPUT_DIRECTORY, os.path.basename(UNSC_S3_OBJECT_KEY))
                        _save_json_to_local_file(unsc_json_data, output_file_path)
                    else:
                        if upload_json_to_s3(unsc_json_data, S3_BUCKET_NAME, UNSC_S3_OBJECT_KEY):
                            logging.info(f"UNSC JSON data successfully uploaded to s3://{S3_BUCKET_NAME}/{UNSC_S3_OBJECT_KEY}")
                        else:
                            logging.error("Failed to upload UNSC JSON data to S3.")
                else:
                    logging.error("Failed to convert UN XML to JSON (returned None).")
            else:
                logging.error("Failed to get UN XML download link.")
        else:
            logging.info("The UN list was not updated today. Skipping download and conversion.")
    else:
        logging.error("Could not determine the UN list last updated date. Skipping download and conversion.")

def run_kdn_sanction_list_process(local_mode: bool = False):
    """
    Handles the entire process for checking, downloading, and converting
    the KDN Sanction List (PDF based), then uploading to S3 or saving locally.
    """

    logging.info("\n--- Starting KDN Sanction List update check ---")

    try:
        # Get the current XML URL from the MOHA page
        # get_current_kdn_xml_url is assumed to use verify=False internally
        current_xml_url = get_current_kdn_xml_url(KDN_MOHA_URL)

        if not current_xml_url:
            logging.error("Could not retrieve current KDN XML URL. Skipping PDF processing.")
            return # Exit if we can't even get the URL

        # Read the last known XML URL from S3 (only if not in local mode)
        last_known_xml_url = None
        if not local_mode:
            last_known_xml_url = read_s3_state_file(S3_BUCKET_NAME, KDN_LAST_XML_URL_KEY)
        else:
            # In local mode, we don't track state via S3, always process if XML link changes
            # For simplicity in local testing, we'll just assume it's always "new" or
            # you can implement a local state file if needed.
            # For this request, we'll always process in local_mode if the XML link is found.
            logging.info("Running in local mode, skipping S3 state file check for KDN.")
            last_known_xml_url = "" # Force processing in local mode if current_xml_url is not empty

        pdf_content_bytes = None
        is_pdf_processed = False

        if current_xml_url != last_known_xml_url:
            logging.info("KDN XML link updated. Proceeding to download PDF content.")
            # get_kdn_pdf_content is assumed to use verify=False internally
            pdf_content_bytes = get_kdn_pdf_content(KDN_MOHA_URL)

            if pdf_content_bytes:
                is_pdf_processed = True
                if not local_mode:
                    # Update the state file in S3 with the new XML URL
                    if not write_s3_state_file(current_xml_url, S3_BUCKET_NAME, KDN_LAST_XML_URL_KEY):
                        logging.error("Failed to update KDN XML URL state in S3. Data might be re-processed next run.")
                else:
                    logging.info("Skipping S3 state file write in local mode.")
            else:
                logging.error("Failed to download KDN PDF content despite XML link update. No JSON files will be updated.")
        else:
            logging.info("KDN XML link not updated. Skipping PDF content download and processing.")

        if is_pdf_processed and pdf_content_bytes:
            logging.info("\nProcessing newly downloaded KDN PDF content...")

            # Extract data for individuals from the PDF
            logging.info("--- Extracting Individual Data (Pages 1-11) ---")
            individual_data = convert_individuals_to_json(pdf_content_bytes)
            if individual_data:
                if local_mode:
                    output_file_path = os.path.join(LOCAL_OUTPUT_DIRECTORY, os.path.basename(KDN_INDIVIDUALS_S3_KEY))
                    _save_json_to_local_file(individual_data, output_file_path)
                else:
                    if upload_json_to_s3(individual_data, S3_BUCKET_NAME, KDN_INDIVIDUALS_S3_KEY):
                        logging.info(f"KDN Individual JSON data successfully uploaded to s3://{S3_BUCKET_NAME}/{KDN_INDIVIDUALS_S3_KEY}")
                    else:
                        logging.error("Failed to upload KDN Individual JSON data to S3.")
            else:
                logging.warning("No individual data extracted from KDN PDF.")

            # Extract data for groups from the PDF (assuming pages 12-14)
            logging.info("\n--- Extracting Group Data (Pages 12-14) ---")
            group_data = convert_groups_to_json(pdf_content_bytes, start_page_num=11, end_page_num=13)
            if group_data:
                if local_mode:
                    output_file_path = os.path.join(LOCAL_OUTPUT_DIRECTORY, os.path.basename(KDN_GROUPS_S3_KEY))
                    _save_json_to_local_file(group_data, output_file_path)
                else:
                    if upload_json_to_s3(group_data, S3_BUCKET_NAME, KDN_GROUPS_S3_KEY):
                        logging.info(f"KDN Group JSON data successfully uploaded to s3://{S3_BUCKET_NAME}/{KDN_GROUPS_S3_KEY}")
                    else:
                        logging.error("Failed to upload KDN Group JSON data to S3.")
            else:
                logging.warning("No group data extracted from KDN PDF.")

    except Exception as e:
        logging.error(f"An overall error occurred during the KDN process: {e}")

# --- AWS Lambda Handler ---
def lambda_handler(event, context):
    """
    Main entry point for AWS Lambda.
    This function orchestrates the scraping, parsing, and S3 uploading of
    UNSC and KDN sanction lists.
    """
    logging.info("Lambda function started.")
    logging.info(f"S3 Bucket: {S3_BUCKET_NAME}, AWS Region: {AWS_REGION}")

    run_unsc_sanction_list_process(local_mode=False) # Always upload to S3 in Lambda
    run_kdn_sanction_list_process(local_mode=False) # Always upload to S3 in Lambda

    logging.info("Lambda function finished.")
    return {
        'statusCode': 200,
        'body': json.dumps('Sanction list processing complete!')
    }

# This __name__ == "__main__" block is for local testing.
# In Lambda, the `lambda_handler` function is the entry point.
if __name__ == "__main__":
    # For local testing, you might want to set dummy environment variables
    # os.environ['S3_BUCKET_NAME'] = 'your-local-test-bucket'
    # os.environ['AWS_REGION'] = 'us-east-1'

    logging.info("Running script locally (not in Lambda context).")
    logging.info(f"JSON files will be saved to the '{LOCAL_OUTPUT_DIRECTORY}' directory.")
    
    # Run in local mode
    run_unsc_sanction_list_process(local_mode=True)
    run_kdn_sanction_list_process(local_mode=True)
    logging.info("\nAll sanction list updates checked and processed locally.")
