import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from config.db import connect_db
from scripts.truck_loader.ingestion import create_customer_receipt
from scripts.truck_loader.services import find_new_items, store_customer_order_in_db

def main():
    connect_db()

    # Step 1: Recieve order confirmation to trigger the pipeline
    # Listen to an email inbox for new order confirmations to be forwarded
    email_data = {
        "csv_file_path": "data/example_order.csv",
        "pdf_file_path": "data/example_order.pdf",
        "email_body": """Warehouse team- please have loaded for below times

                        7am
                        9am
                        11am
                        11am
                        1pm


                        Shaina Reed - Fleet Operations Manager
                        825 Locust Point Road | York, PA 17406
                        P: 717-790-6260  | C: 717-462-8550""",
    }

    # Step 2: Create the order receipt object
    customer_order_reciept = create_customer_receipt(email_data)
    # print(f"Customer Order Created: {customer_order_reciept}")

    # Step 3.1: Compare against to DB/master sheet and identify new items
    missing_items = find_new_items(customer_order_reciept.order_details)

    # Only move on with flow if no new dimensions required
    while missing_items:
        print(f"Waiting for {len(missing_items)} missing item(s) to be added: {missing_items}")
        time.sleep(10)  # check again in 10 seconds
        # prompt user to enter new dimensions
        missing_items = find_new_items(customer_order_reciept.order_details)

    # Step 3.2: Store all data into DB
    # Going to be updating item table with new items(done when user enters new dimension in)
    # Also update the customer order table with the complete order
    store_customer_order_in_db(customer_order_reciept)

    # Step 4: Pass all items to the truck loader

    # Step 5: Process truck loader response into something for employees

    print("Pipeline completed successfully.")

if __name__ == "__main__":
    main()