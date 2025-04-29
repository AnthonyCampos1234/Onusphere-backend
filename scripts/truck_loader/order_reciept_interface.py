class CustomerOrderReceipt:
    def __init__(self, customer_id: str, order_id: str, date_ordered, upcoming_shipment_times, order_details, order_pdf_link: str):
        self.customer_id = customer_id
        self.order_id = order_id
        self.date_ordered = date_ordered
        self.upcoming_shipment_times = upcoming_shipment_times
        self.order_details = order_details

class SpecialInstructions:
    def __init__(self, item_id: str, instructions: str):
        self.item_id = item_id
        self.instructions = instructions