import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from scripts.truck_loader.ingestion import create_customer_receipt
from scripts.truck_loader.services import find_new_items, save_state

def run_pipline_on_email(email_data):
    # Create the order receipt object
    customer_order_reciept = create_customer_receipt(email_data)

    # Compare against to DB/master sheet and identify new items
    missing_items = find_new_items(customer_order_reciept.order_details)

    # continue flow
    return finalize_pipeline_step(state=customer_order_reciept, 
                                missing_items=missing_items)

def run_pipeline_on_state(state):
    # check for missing items; should be none now
    missing_items = find_new_items(state.order_details)

    # continue flow
    return finalize_pipeline_step(state=state, 
                            missing_items=missing_items)

def finalize_pipeline_step(state, missing_items):
    # Only move on with flow if no new dimensions required
    if not missing_items:
        # Pass all requirements to the truck loader

        # Turn truck loader response into something for employees
        return {"response": "Sample truck load"}
    else:
        # in the case there are missing items we need to store current state
        save_state(state)

        return None