from scripts.truck_loader.order_reciept_interface import CustomerOrderReceipt, SpecialInstructions
from typing import List
import json
import os
import uuid
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

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

def extract_special_instructions(parsed_text: str) -> list:
    """
    Parses full text and returns a list of special instruction objects.
    One object per item_id, even if multiple ids appear in the same instruction.
    """
    
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found. Make sure it's set in the .env file.")

    prompt = """You are given the raw extracted text from a PDF that contains information about product shipping, handling requirements, and customer order details.

                Your task is to carefully read through the text and extract the following information:

                1. Special Handling Instructions:
                - Extract all special handling instructions related to specific items.
                - Return them as a JSON array where each object contains:
                    - "item_id" (string): the item number mentioned in the instruction.
                    - "instruction" (string): the full text of the instruction that applies to that item.
                - If an instruction applies to multiple items, include a separate object for each item with the same instruction.

                2. Order Metadata:
                - Extract the "date_ordered" from the document. It should be the date the order was created or acknowledged (usually near "Ack Date" or at the top of the document).
                - Extract the "customer_id", which is the name of the customer receiving the shipment (found in the "Ship To" section). Use the full customer name string as it appears.

                Important rules:
                - Only include items that are explicitly mentioned inside special handling instructions (like stacking restrictions, oversized warnings, etc).
                - Ignore general order information, addresses, or contacts not tied to specific item handling.
                - Extract exactly the item IDs as they appear (usually 8-digit numbers).
                - Format your final output strictly as a clean JSON object.

                Final JSON output format:

                {
                "date_ordered": "MM/DD/YY",
                "customer_id": "Customer Name",
                "special_instructions": [
                    {
                    "item_id": "ItemNumber1",
                    "instruction": "Full special handling instruction text."
                    },
                    {
                    "item_id": "ItemNumber2",
                    "instruction": "Another instruction text."
                    }
                ]
                }

                Only output the JSON object. Do not add any explanations, comments, or extra text.

                Here is the extracted PDF text:
                """ + parsed_text

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    full_response = json.loads(response.choices[0].message.content)
    date_ordered = full_response["date_ordered"]
    customer_id = full_response["customer_id"]
    special_instructions = full_response["special_instructions"]

    return special_instructions, date_ordered, customer_id

def parse_pdf(file_path: str) -> List[SpecialInstructions]:
    """
    Parse a PDF file into special instructions.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        list: List of special instructions.
    """
    from PyPDF2 import PdfReader

    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    
    special_instructions = extract_special_instructions(text)

    return special_instructions

def add_instructions_to_dataframe(df, special_instructions) -> pd.DataFrame:
    """
    Add special instructions to the DataFrame.

    Args:
        df (DataFrame): DataFrame containing order details.
        special_instructions (list): List of special instructions.

    Returns:
        DataFrame: Updated DataFrame with special instructions.
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

def create_customer_receipt(email_data: dict) -> CustomerOrderReceipt:
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
  # Parse CSV into a DataFrame
  df = parse_csv(email_data["csv_file_path"])
    
  # Parse PDF into important information
  special_instructions, date_ordered, customer_id = parse_pdf(email_data["pdf_file_path"])

  # Collect upcoming shipments from the email body
  upcoming_shipment_times = get_upcoming_shipments(email_data["email_body"])

  # Combine special instructions into the DataFrame
  final_df = add_instructions_to_dataframe(df, special_instructions)

  # Return the customer order receipt object
  return {
      "customer_id": customer_id,
      "order_id": uuid.uuid4(),
      "date_ordered": date_ordered,
      "upcoming_shipment_times": upcoming_shipment_times,
      "order_details": final_df,
  }
  

