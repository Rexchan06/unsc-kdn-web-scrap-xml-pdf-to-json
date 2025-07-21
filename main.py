# main.py
import json
import os
from datetime import datetime
import logging
import requests # Added for downloading raw XML content
from config.settings import APP_AWS_REGION, UN_SECURITY_COUNCIL_URL, KDN_MOHA_URL, KDN_LAST_XML_URL_KEY, UNSC_S3_OBJECT_KEY, S3_BUCKET_NAME, KDN_GROUPS_S3_KEY, KDN_INDIVIDUALS_S3_KEY, LOCAL_OUTPUT_DIRECTORY, UNSC_LAST_XML_HASH_KEY
from utils.aws_s3_utils import upload_json_to_s3, read_s3_state_file, write_s3_state_file
from utils.common_utils import calculate_sha256 # Import the new hashing utility

# Configure logging for better visibility in CloudWatch Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Import functions for UN Security Council Sanction List ---
# Assuming these modules are in the 'UNSC' sub-directory
from UNSC.unsc_web_scraper import get_xml_link # get_last_updated_date is no longer used for primary check
from UNSC.unsc_xml_parser import download_and_convert_xml_to_json

# --- Import functions for KDN Sanction List ---
# Assuming these modules are in the 'KDN' sub-directory
from KDN.kdn_web_scraper import get_kdn_pdf_content, get_current_kdn_xml_url
from KDN.kdn_pdf_parser import convert_individuals_to_json, convert_groups_to_json

# --- Core Processing Functions ---

def run_unsc_sanction_list_process(local_mode: bool = False):
    """
    Handles the entire process for checking, downloading, and converting
    the UN Security Council Consolidated Sanction List, then uploading to S3 or saving locally.
    Uses content hashing to determine if an update is needed.
    """

    logging.info("\n--- Starting UN Sanction List update check ---")

    xml_link = get_xml_link(UN_SECURITY_COUNCIL_URL)
    if not xml_link:
        logging.error("Failed to get UN XML download link. Skipping process.")
        return

    logging.info(f"Found UN XML link: {xml_link}")

    try:
        # Step 1: Download the raw XML content to calculate its hash
        logging.info("Downloading raw UN XML content to check for changes...")
        response = requests.get(xml_link, verify=True) # Ensure verify=True as per unsc_web_scraper
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        current_xml_content_bytes = response.content
        current_xml_hash = calculate_sha256(current_xml_content_bytes)
        logging.info(f"Current UN XML content hash: {current_xml_hash}")

        # Step 2: Read the last known hash from S3 or local file
        last_known_xml_hash = None
        unsc_hash_local_file_path = os.path.join(LOCAL_OUTPUT_DIRECTORY, os.path.basename(UNSC_LAST_XML_HASH_KEY))

        if not local_mode:
            last_known_xml_hash = read_s3_state_file(S3_BUCKET_NAME, UNSC_LAST_XML_HASH_KEY)
            logging.info(f"Last known UN XML hash from S3: {last_known_xml_hash}")
        else:
            # Use local_file_utils for local mode operations
            from utils.local_file_utils import read_local_state_file
            last_known_xml_hash = read_local_state_file(unsc_hash_local_file_path)
            logging.info(f"Last known UN XML hash from local file: {last_known_xml_hash}")


        # Step 3: Compare hashes to decide if processing is needed
        if current_xml_hash != last_known_xml_hash:
            logging.info("UNSC XML content has changed! Proceeding to parse and upload.")
            
            # Step 4: Convert the (already downloaded) XML content to JSON
            # We can pass the content directly to avoid a second HTTP request
            unsc_json_data = download_and_convert_xml_to_json(xml_link, xml_content_bytes=current_xml_content_bytes)
            
            if unsc_json_data:
                if local_mode:
                    # Use local_file_utils for local mode operations
                    from utils.local_file_utils import save_json_to_local_file, write_local_state_file
                    output_file_path = os.path.join(LOCAL_OUTPUT_DIRECTORY, os.path.basename(UNSC_S3_OBJECT_KEY))
                    if save_json_to_local_file(unsc_json_data, output_file_path):
                        # Update the local state file with the new hash
                        write_local_state_file(current_xml_hash, unsc_hash_local_file_path)
                else:
                    if upload_json_to_s3(unsc_json_data, S3_BUCKET_NAME, UNSC_S3_OBJECT_KEY):
                        logging.info(f"UNSC JSON data successfully uploaded to s3://{S3_BUCKET_NAME}/{UNSC_S3_OBJECT_KEY}")
                        # Step 5: Update the last known hash in S3
                        if not write_s3_state_file(current_xml_hash, S3_BUCKET_NAME, UNSC_LAST_XML_HASH_KEY):
                            logging.error("Failed to update UNSC XML hash state in S3. Data might be re-processed next run.")
                    else:
                        logging.error("Failed to upload UNSC JSON data to S3.")
            else:
                logging.error("Failed to convert UN XML to JSON (returned None).")
        else:
            logging.info("UNSC XML content has not changed since last check. Skipping processing.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading UN XML from {xml_link}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during UN Sanction List process: {e}")


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

        # Read the last known XML URL from S3 or local file
        last_known_xml_url = None
        kdn_xml_url_local_file_path = os.path.join(LOCAL_OUTPUT_DIRECTORY, os.path.basename(KDN_LAST_XML_URL_KEY))

        if not local_mode:
            last_known_xml_url = read_s3_state_file(S3_BUCKET_NAME, KDN_LAST_XML_URL_KEY)
            logging.info(f"Last known KDN XML URL from S3: {last_known_xml_url}")
        else:
            # Use local_file_utils for local mode operations
            from utils.local_file_utils import read_local_state_file
            last_known_xml_url = read_local_state_file(kdn_xml_url_local_file_path)
            logging.info(f"Last known KDN XML URL from local file: {last_known_xml_url}")

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
                    # Use local_file_utils for local mode operations
                    from utils.local_file_utils import write_local_state_file # <-- Added this import
                    write_local_state_file(current_xml_url, kdn_xml_url_local_file_path)
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
                    # Use local_file_utils for local mode operations
                    from utils.local_file_utils import save_json_to_local_file
                    output_file_path = os.path.join(LOCAL_OUTPUT_DIRECTORY, os.path.basename(KDN_INDIVIDUALS_S3_KEY))
                    save_json_to_local_file(individual_data, output_file_path)
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
                    # Use local_file_utils for local mode operations
                    from utils.local_file_utils import save_json_to_local_file
                    output_file_path = os.path.join(LOCAL_OUTPUT_DIRECTORY, os.path.basename(KDN_GROUPS_S3_KEY))
                    save_json_to_local_file(group_data, output_file_path)
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
    logging.info(f"S3 Bucket: {S3_BUCKET_NAME}, App Region: {APP_AWS_REGION}")

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
    # os.environ['APP_AWS_REGION'] = 'us-east-1' # Use the new variable name here

    logging.info("Running script locally (not in Lambda context).")
    logging.info(f"JSON files and state files will be saved to the '{LOCAL_OUTPUT_DIRECTORY}' directory.")
    
    # Import local file utilities only when in local mode
    # This ensures these functions are not part of the Lambda deployment package
    # when building the Docker image for production.
    # The .dockerignore file will explicitly exclude utils/local_file_utils.py
    # and the local_output directory.
    
    run_unsc_sanction_list_process(local_mode=True)
    run_kdn_sanction_list_process(local_mode=True)
    logging.info("\nAll sanction list updates checked and processed locally.")
