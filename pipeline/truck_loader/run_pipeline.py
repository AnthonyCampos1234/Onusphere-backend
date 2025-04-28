import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from scripts.truck_loader.ingestion import create_customer_receipt

def main():
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
    order_reciept = create_customer_receipt(email_data)
    print(f"Order Receipt Created: {order_reciept}")

    # Step 3: Compare against master excel sheet and identify new items

    # Step 4: Pass all items to the truck loader

    # Step 5: Process truck loader response into something for employees

    print("Pipeline completed successfully.")

if __name__ == "__main__":
    main()