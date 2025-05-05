class OrderReceipt:
    def __init__(self, customer_id: str, order_id: str, date_ordered, upcoming_shipment_times, order_details):
        self.customer_id = customer_id
        self.order_id = order_id
        self.date_ordered = date_ordered
        self.upcoming_shipment_times = upcoming_shipment_times
        self.order_details = order_details