# utils/local_file_utils.py
import os
import json
import logging
from typing import Union

# Configure logging for better visibility when running locally
# Note: In a real Lambda environment, the main.py logging config will apply.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def save_json_to_local_file(data: dict, file_path: str) -> bool:
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

def read_local_state_file(file_path: str) -> Union[str, None]:
    """
    Reads content from a local state file.
    Returns None if the file does not exist or an error occurs.
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            logging.info(f"Successfully read local state from: {file_path}")
            return content
        else:
            logging.info(f"Local state file does not exist: {file_path}")
            return None
    except Exception as e:
        logging.error(f"Error reading local state file {file_path}: {e}")
        return None

def write_local_state_file(content: str, file_path: str) -> bool:
    """
    Writes content to a local state file.
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        logging.info(f"Successfully wrote local state to: {file_path}")
        return True
    except Exception as e:
        logging.error(f"Error writing local state file {file_path}: {e}")
        return False
