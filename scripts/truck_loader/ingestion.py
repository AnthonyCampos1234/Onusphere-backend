import warnings
import logging
warnings.filterwarnings("ignore", category=UserWarning, module="pdfminer")
logging.getLogger("pdfminer").setLevel(logging.CRITICAL)
import re
from typing import List
import json
import os
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
import pdfplumber
from models.customer import Customer
from models.order import Order, OrderItem
from models.item import Item


def parse_csv(file_path: str):
    """
    Parse a CSV file into a DataFrame.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        DataFrame: Parsed DataFrame.
    """

    df = pd.read_csv(file_path)

    df['Item'] = df['Item'].astype(str)

    return df

def extract_domain_from_pdf(pdf_path):
    """
    Extracts the first domain (e.g., 'shorr.com') found in the PDF.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: The domain found (e.g., 'shorr.com') or 'unknown'.
    """
    with pdfplumber.open(pdf_path) as pdf:
        first_page_text = pdf.pages[0].extract_text()
        match = re.search(r"\b(?:www\.)?([a-z0-9\-]+\.[a-z]{2,})\b", first_page_text, re.IGNORECASE)
        if match:
            return match.group(1).lower()
    return "unknown"

def extract_date_ordered_from_pdf(pdf_path):
    """
    Extracts the order acknowledgment date from the PDF.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: The date in MM/DD/YY format, or 'unknown' if not found.
    """
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            # Look for the line "Ack Date" and capture the date on the next line
            lines = text.splitlines()
            for i, line in enumerate(lines):
                if "Ack Date" in line and i + 2 < len(lines):
                    next_line = lines[i + 2]
                    match = re.search(r"(\d{2}/\d{2}/\d{2})", next_line)
                    if match:
                        return match.group(0)

    return "unknown"

def extract_units_per_pallet_from_pdf(pdf_path):
    """
    Extracts item_id and units_per_pallet from Shorr Packaging PDF.
    Returns:
        List[dict]: [{'item_id': '10202638', 'units_per_pallet': 2400}, ...]
    """
    results = []
    current_item_id = None

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            lines = page.extract_text().splitlines()

            for line in lines:
                # Step 1: Detect item line (starts with digit, then 8-digit ID)
                item_match = re.match(r"^\d+\s+(\d{8})\s+\d{2}/\d{2}/\d{2}", line)
                if item_match:
                    current_item_id = item_match.group(1)
                    continue

                # Step 2: Look for "###/pallet" pattern near current item
                if current_item_id:
                    pallet_match = re.search(r"(\d+)\s*(?:cs|EA|RL)?/pallet", line, re.IGNORECASE)
                    if pallet_match:
                        units = int(pallet_match.group(1))
                        results.append({
                            "item_id": current_item_id,
                            "units_per_pallet": units
                        })
                        current_item_id = None  # Reset after capture

    return results

def extract_special_instructions(parsed_text: str):
    """
    Uses OpenAI API to extract special handling instructions per item from PDF text.
    
    Returns:
        list of dicts: Each dict has 'item_id' and 'instruction'.
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found. Set it in your .env file.")

    prompt = f"""You are given the raw extracted text from a PDF that contains shipping and handling details.

                Extract all **special handling instructions** related to specific items.

                Instructions:
                - Return a JSON array.
                - Each object in the array must contain:
                    - "item_id" (string): the 8-digit item number mentioned in the instruction.
                    - "instruction" (string): the full text of the instruction that applies to that item.
                - If one instruction applies to multiple items, return a separate object for each item with the same instruction.
                - Ignore general notes or shipping info not tied to a specific item.

                Output format:
                [
                {{
                    "item_id": "12345678",
                    "instruction": "Do not double stack this item."
                }},
                ...
                ]

                Only output the JSON array. Do not add any explanations or extra formatting.

                Text:
                {parsed_text}
                """

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    response_text = response.choices[0].message.content
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse OpenAI response: {response_text}") from e

def parse_pdf_for_special_instructions(pdf_path: str):
    """
    Extracts special handling instructions from the first page of a PDF.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        list of dicts: Each dict has 'item_id' and 'instruction'.
    """
    with pdfplumber.open(pdf_path) as pdf:
        first_page_text = pdf.pages[0].extract_text()
    return extract_special_instructions(first_page_text)

def parse_pdf(filePath):
  domain = extract_domain_from_pdf(filePath)
  date_ordered = extract_date_ordered_from_pdf(filePath)
  units_per_pallet = extract_units_per_pallet_from_pdf(filePath)
  special_instructions = parse_pdf_for_special_instructions(filePath)

  return domain, date_ordered, units_per_pallet, special_instructions

def finalize_df(df, special_instructions, units_per_pallet) -> pd.DataFrame:
    """
    Add relevant information to the DataFrame.

    Args:
        df (DataFrame): DataFrame containing order details.
        special_instructions (list): List of special instructions.
        units_per_pallet (list): List of units per pallet.
    Returns:
        DataFrame: Updated DataFrame.
    """
    for instr in special_instructions:
        item_id = instr["item_id"]
        instruction = instr["instruction"]

        # Now both sides are strings
        if item_id in df['Item'].values:
            print(f"Item {item_id} found in DataFrame.")
            df.loc[df['Item'] == item_id, 'Special_Instructions'] = instruction
        else:
            print(f"Item {item_id} NOT found in DataFrame.")

    # Add units per pallet
    for entry in units_per_pallet:
        item_id = entry["item_id"]
        units = entry["units_per_pallet"]

        if item_id in df['Item'].astype(str).values:
            print(f"Item {item_id} found in DataFrame for units per pallet.")
            df.loc[df['Item'].astype(str) == item_id, 'Units_Per_Pallet'] = units
        else:
            print(f"Item {item_id} NOT found in DataFrame for units per pallet.")


    return df

def get_upcoming_shipments(email_body: str) -> List[str]:
    """
    Extract upcoming shipment times from the email body.

    Args:
        email_body (str): Body of the email.

    Returns:
        list: List of upcoming shipment times.
    """
    # Split the email body into lines
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found. Make sure it's set in the .env file.")

    prompt = """
    You are given the text of an email body.

    Your task is to carefully read the text and extract all the delivery or loading times mentioned.

    Return the output as a clean JSON array of strings, where each string is one of the times found.

    Important rules:
    - Only include actual times (like "7am", "9am", "11am", "1pm").
    - Ignore any names, addresses, phone numbers, or other text.
    - Do not explain anything — only output the JSON array.

    Example expected output:

    [
    "7am",
    "9am",
    "11am",
    "11am",
    "1pm"
    ]

    Here is the email body text:
    """ + email_body

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    upcoming_shipments = json.loads(response.choices[0].message.content)

    return upcoming_shipments

def add_new_items_from_df(df) -> list:
    """
    Inserts new items into the database from a DataFrame.
    """
    added_item_ids = []

    for _, row in df.iterrows():
        item_number = row["Item"]

        # Skip if item already exists
        if Item.objects(item_number=item_number).first():
            continue

        # Create and save new item
        item = Item(
            item_number=item_number,
            height=row.get("Height", 0.0),
            width=row.get("Width", 0.0),
            length=row.get("Length", 0.0),
            special_instructions=row.get("SpecialInstructions", "")
        )
        item.save()

def create_customer_receipt(email_data: dict):
    """
        Create a customer order receipt from email data.

        Args:
            email_data (dict): Dictionary containing email data with keys:
                - csv_file_path: Path to the CSV file.
                - pdf_file_path: Path to the PDF file.
                - email_body: Body of the email.

        Returns:
            CustomerOrderReceipt: An object containing complete customer order details.
        """
    # Step 1: Parse CSV and PDF
    df = parse_csv(email_data["csv_file_path"])
    domain, date_ordered, units_per_pallet, special_instructions = parse_pdf(email_data["pdf_file_path"])

    # Step 2: Combine instructions into DataFrame
    final_df = finalize_df(df, special_instructions, units_per_pallet)

    # Step 3: Insert new Item objects into DB
    add_new_items_from_df(final_df)

    # Step 4: Extract upcoming shipment times
    upcoming_shipment_times = ", ".join(get_upcoming_shipments(email_data["email_body"]))

    # Step 5: Lookup or create Customer
    customer = Customer.objects(email_domain=domain).first()
    if not customer:
        customer = Customer(email_domain=domain)
        customer.save()

    # Step 6: Convert DataFrame rows to OrderItems
    order_items = []
    for _, row in final_df.iterrows():
        item = Item.objects(item_number=row["Item"]).first()
        if not item:
            continue  # Skip if item not found

        # Get quantity and units_per_pallet from the row
        order_quantity = int(row.get("Qty_Ord", 0))  # Adjust key name as needed
        units_per_pallet = int(row.get("Units_Per_Pallet", 1))  # Adjust key name as needed

        # Create OrderItem and calculate pallets
        order_item = OrderItem(item=item, number_pallets=0)
        order_item.set_pallets(order_quantity, units_per_pallet)

        order_items.append(order_item)


    # Step 7: Create and save the Order
    order = Order(
        customer=customer,
        items=order_items,
        order_date=pd.to_datetime(date_ordered),
        upcoming_shipment_times=upcoming_shipment_times
    )
    order.save()

    return {
        "customer_email_domain": customer.email_domain,
        "order_id": str(order.id),
    }
  

