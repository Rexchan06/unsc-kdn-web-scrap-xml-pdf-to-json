import pdfplumber
import json
import re
import io
from typing import Union

# Import utility functions from kdn_utils module
from .kdn_utils import parse_date, MONTH_MAP 

def convert_individuals_to_json(pdf_content_bytes: bytes) -> list:
    """
    Extracts data from the 'A. INDIVIDUAL' table section of the PDF content
    and structures it into a list of dictionaries.

    Args:
        pdf_content_bytes (bytes): The byte content of the PDF file.
        
    Returns:
        list: A list of dictionaries, where each dictionary represents an individual's data.
    """
    structured_data = []
    
    # Open the PDF from bytes using an in-memory binary stream
    with pdfplumber.open(io.BytesIO(pdf_content_bytes)) as pdf:
        # Iterate through all pages of the PDF
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            
            # Define table extraction settings for pdfplumber
            # These settings are crucial for accurate table detection based on lines and text
            table_settings = {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 5, # How close text/lines need to be to snap together
                "text_tolerance": 5, # Tolerance for grouping text into cells
                "join_tolerance": 5, # Tolerance for joining nearby lines/text
                "min_words_horizontal": 1,
                "min_words_vertical": 1,
            }
            
            # Extract tables from the current page using the defined settings
            tables = page.extract_tables(table_settings=table_settings)
            
            # Extract all text from the page to check for section headers like "B. GROUP"
            page_text = page.extract_text()

            # If "B. GROUP" is found on the current page, it means we've passed the individual section.
            # Stop processing further pages for individuals.
            if "B. GROUP" in page_text:
                break

            # Process each table found on the page
            for table in tables:
                # Skip empty tables or tables with only a header row
                if not table or len(table) < 2:
                    continue
                
                # Create a string from the first row (header) to check for expected patterns
                first_row_str = " ".join([c if c else "" for c in table[0]]).lower()
                
                # Heuristic to identify the correct "Individual" table:
                # It should contain numeric column indicators like '(1)', '(3)', and '(13)'
                if not ('(1)' in first_row_str and '(3)' in first_row_str and '(13)' in first_row_str):
                    continue # Skip tables that don't match the expected individual header format

                # Iterate through data rows (skipping the first row which is the header)
                for row_index, row in enumerate(table[1:]):
                    # Clean each cell: replace newlines with spaces and strip leading/trailing whitespace
                    cleaned_row = [cell.replace('\n', ' ').strip() if cell else '' for cell in row]
                    
                    # Attempt to parse the ID from the first column to validate if it's a data row
                    id_val_raw = cleaned_row[0].replace('.', '') if cleaned_row and cleaned_row[0] else ''
                    current_id = None
                    if id_val_raw.isdigit():
                        current_id = int(id_val_raw)

                    # Only process the row if a valid integer ID is found
                    if current_id is not None:
                        # Pad the row to 13 elements with empty strings if pdfplumber collapsed empty cells.
                        # This ensures consistent indexing for all 13 expected columns.
                        padded_row = cleaned_row + [''] * (13 - len(cleaned_row))

                        # Map the padded row's cells to the desired JSON keys
                        person_data = {
                            "ID": current_id,
                            "REFERENCE_NUMBER": padded_row[1] if padded_row[1] else '-',
                            "NAME": padded_row[2] if padded_row[2] else '-',
                            "SALUTATION": padded_row[3] if padded_row[3] else '-',
                            "OCCUPATION": padded_row[4] if padded_row[4] else '-',
                            "DATE_OF_BIRTH": parse_date(padded_row[5]),
                            "BIRTH_PLACE": padded_row[6] if padded_row[6] else '-',
                            "OTHER_NAME": padded_row[7] if padded_row[7] else '-',
                            "NATIONALITY": padded_row[8] if padded_row[8] else '-',
                            "PASSPORT_NUMBER": padded_row[9] if padded_row[9] else '-',
                            "ID_NUMBER": padded_row[10] if padded_row[10] else '-',
                            "ADDRESS": padded_row[11] if padded_row[11] else '-',
                            "LISTED_DATE": parse_date(padded_row[12])
                        }
                        
                        structured_data.append(person_data)
                    else:
                        # If the first column is not an ID, and "B. GROUP" is detected,
                        # it indicates the end of the individual section for this page.
                        if "B. GROUP" in page_text:
                            break # Exit the inner loop for tables on this page

    return structured_data

def convert_groups_to_json(pdf_content_bytes: bytes, start_page_num: int, end_page_num: int) -> list:
    """
    Extracts data from the 'B. GROUP' table section of the PDF content
    (specifically targeting a page range) and structures it into a list of dictionaries.

    Args:
        pdf_content_bytes (bytes): The byte content of the PDF file.
        start_page_num (int): The 0-indexed starting page number to process.
        end_page_num (int): The 0-indexed ending page number to process (inclusive).
        
    Returns:
        list: A list of dictionaries, where each dictionary represents a group/entity's data.
    """
    structured_data = []
    
    # Open the PDF from bytes using an in-memory binary stream
    with pdfplumber.open(io.BytesIO(pdf_content_bytes)) as pdf:
        # Iterate through the specified page range (0-indexed)
        # min() ensures we don't go beyond the actual number of pages in the PDF
        for page_index in range(start_page_num, min(end_page_num + 1, len(pdf.pages))):
            page = pdf.pages[page_index]
            
            # Define table extraction settings for pdfplumber (similar to individuals, but for group table layout)
            table_settings = {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 5,
                "text_tolerance": 5,
                "join_tolerance": 5,
                "min_words_horizontal": 1,
                "min_words_vertical": 1,
            }
            
            # Extract tables from the current page
            tables = page.extract_tables(table_settings=table_settings)
            
            # Process each table found on the page
            for table in tables:
                # Skip empty tables or tables with only a header row
                if not table or len(table) < 2:
                    continue
                
                # Create a string from the first row (header) to check for expected patterns
                first_row_str = " ".join([c if c else "" for c in table[0]]).lower()
                
                # Heuristic to identify the correct "Group" table:
                # It should contain numeric column indicators like '(1)', '(4)', and '(7)'
                if not ('(1)' in first_row_str and '(4)' in first_row_str and '(7)' in first_row_str):
                    continue # Skip tables that don't match the expected group header format

                # Iterate through data rows (skipping the first row which is the header)
                for row_index, row in enumerate(table[1:]):
                    # Clean each cell: replace newlines with spaces and strip leading/trailing whitespace
                    cleaned_row = [cell.replace('\n', ' ').strip() if cell else '' for cell in row]
                    
                    # Attempt to parse the ID from the first column to validate if it's a data row
                    id_val_raw = cleaned_row[0].replace('.', '') if cleaned_row and cleaned_row[0] else ''
                    current_id = None
                    if id_val_raw.isdigit():
                        current_id = int(id_val_raw)

                    # Only process the row if a valid integer ID is found
                    if current_id is not None:
                        # Pad the row to 7 elements with empty strings if pdfplumber collapsed empty cells.
                        # This ensures consistent indexing for all 7 expected columns for group data.
                        padded_row = cleaned_row + [''] * (7 - len(cleaned_row))

                        # Map the padded row's cells to the desired JSON keys for group data
                        group_data = {
                            "ID": current_id,
                            "REFERENCE_NUMBER": padded_row[1] if padded_row[1] else '-',
                            "NAME": padded_row[2] if padded_row[2] else '-',
                            "ALIAS": padded_row[3] if padded_row[3] else '-',
                            "OTHER_NAME": padded_row[4] if padded_row[4] else '-',
                            "ADDRESS": padded_row[5] if padded_row[5] else '-',
                            "LISTED_DATE": parse_date(padded_row[6])
                        }
                        
                        structured_data.append(group_data)
                    # No "B. GROUP" check needed here as we are already targeting the group section pages.

    return structured_data
