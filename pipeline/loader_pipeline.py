import sys
import os
import threading
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from models.types import Order
from scripts.truck_loader.ingestion import create_customer_receipt
from scripts.truck_loader.services import find_items_without_dimensions_from_order
import shared_state

pipeline_trigger_event = threading.Event()
shared_state.pipeline_trigger_event = pipeline_trigger_event  # inject shared event

def start_truck_loader_thread():
    def pipeline_loop():
        while True:
            pipeline_trigger_event.wait()
            pipeline_trigger_event.clear()

            try:
                order_id = shared_state.order_id_holder["id"]
                print("Triggered: Running pipeline...")
                if order_id:
                    run_pipeline_on_state(order_id)
                else:
                    order_id = run_pipline_on_email(shared_state.email_data)

                # send_email(order_id)
                print("Loader response done for ", order_id)
                print("Pipeline completed.")
            except Exception as e:
                print(f"Pipeline error: {e}")

    threading.Thread(target=pipeline_loop, daemon=True).start()

def run_pipline_on_email(email_data):
    # Initialize all of the objects 
    customer_order_reciept = create_customer_receipt(email_data)

    customer_domain = customer_order_reciept["customer_email_domain"]
    order_id = customer_order_reciept["order_id"]

    # Compare against to DB/master sheet and identify new items
    missing_items = find_items_without_dimensions_from_order(order_id)

    if not missing_items:
        # Pass all requirements to the truck loader
        response = ["img1", "img2", "img3", "img4"]

        Order.objects(id=order_id).update_one(
            set__loading_instructions=response,
            set__status="done"
        )

        return order_id

    Order.objects(id=order_id).update_one(set__status="incomplete")

    return order_id


def run_pipeline_on_state(order_id):
    # check for missing items; should be none now
    missing_items = find_items_without_dimensions_from_order(order_id)

    if not missing_items:
        # Pass all requirements to the truck loader
        response = ["img1", "img2", "img3", "img4"]

        Order.objects(id=order_id).update_one(
            set__loading_instructions=response,
            set__status="done"
        )

        return order_id

    Order.objects(id=order_id).update_one(set__status="incomplete")

    return order_id

