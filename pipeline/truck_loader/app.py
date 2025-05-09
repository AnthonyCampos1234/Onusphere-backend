from fastapi import FastAPI
from contextlib import asynccontextmanager
import threading
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from models.order_reciept import OrderReceipt
from pipeline.truck_loader.run_pipeline import run_pipeline_on_state, run_pipline_on_email
from config.db import connect_db
from routes import routes

pipeline_trigger_event = threading.Event()
routes.pipeline_trigger_event = pipeline_trigger_event  # inject shared event
routes.order_id_holder = {"id": None}
routes.truck_loader_response_holder = {"data": None}
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_db()

    def pipeline_loop():
        while True:
            pipeline_trigger_event.wait()
            pipeline_trigger_event.clear()

            try:
                order_id = routes.order_id_holder["id"]
                print("Triggered: Running pipeline...")
                if order_id:
                  # get order reciept from db
                  state = OrderReceipt.objects(id=order_id).first()
                  routes.truck_loader_response_holder["data"] = run_pipeline_on_state(state)
                else:
                  routes.truck_loader_response_holder["data"] = run_pipline_on_email(email_data)

                # send_email(truck_loader_response)
                print("Pipeline completed.")
            except Exception as e:
                print(f"Pipeline error: {e}")

    threading.Thread(target=pipeline_loop, daemon=True).start()
    yield
    print("Shutting down pipeline...")

app = FastAPI(lifespan=lifespan)
app.include_router(routes.router)
