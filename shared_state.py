from threading import Event

pipeline_trigger_event = Event()
order_id_holder = {"id": None}
email_data = None
