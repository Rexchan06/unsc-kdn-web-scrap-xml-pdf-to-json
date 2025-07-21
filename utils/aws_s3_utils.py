import boto3
import json
import io
import logging
from typing import Union
from config.settings import APP_AWS_REGION

# --- S3 Utility Functions ---
def upload_json_to_s3(
    json_data: dict,
    bucket_name: str,
    object_key: str,
    region_name: str = APP_AWS_REGION,
    content_type: str = 'application/json'
) -> bool:
    """
    Uploads a Python dictionary as a JSON file to an AWS S3 bucket.
    """
    try:
        s3_client = boto3.client('s3', region_name=region_name)
        logging.info(f"Attempting to upload data to s3://{bucket_name}/{object_key}")

        json_string = json.dumps(json_data, indent=2, ensure_ascii=False)
        json_bytes = json_string.encode('utf-8')
        file_obj = io.BytesIO(json_bytes)

        s3_client.upload_fileobj(
            file_obj,
            bucket_name,
            object_key,
            ExtraArgs={
                'ContentType': content_type,
            }
        )
        logging.info(f"Successfully uploaded {object_key} to {bucket_name}")
        return True

    except boto3.exceptions.S3UploadFailedError as e:
        logging.error(f"S3 upload failed for {object_key}: {e}")
        return False
    except json.JSONEncodeError as e:
        logging.error(f"Error encoding JSON data for {object_key}: {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during S3 upload for {object_key}: {e}")
        return False

def read_s3_state_file(bucket_name: str, object_key: str, region_name: str = APP_AWS_REGION) -> Union[str, None]:
    """
    Reads the content of a state file (e.g., last known URL) from S3.
    Returns None if the file does not exist or an error occurs.
    """
    s3_client = boto3.client('s3', region_name=region_name)
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        content = response['Body'].read().decode('utf-8').strip()
        logging.info(f"Successfully read state file from s3://{bucket_name}/{object_key}")
        return content
    except s3_client.exceptions.NoSuchKey:
        logging.info(f"State file s3://{bucket_name}/{object_key} does not exist.")
        return None
    except Exception as e:
        logging.error(f"Error reading state file from s3://{bucket_name}/{object_key}: {e}")
        return None

def write_s3_state_file(content: str, bucket_name: str, object_key: str, region_name: str = APP_AWS_REGION) -> bool:
    """
    Writes content to a state file in S3.
    """
    s3_client = boto3.client('s3', region_name=region_name)
    try:
        s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=content.encode('utf-8'))
        logging.info(f"Successfully wrote state file to s3://{bucket_name}/{object_key}")
        return True
    except Exception as e:
        logging.error(f"Error writing state file to s3://{bucket_name}/{object_key}: {e}")
        return False