class SpecialInstructions:
    def __init__(self, item_number: str, instructions: str):
        self.item_number = item_number
        self.instructions = instructions

class CustomerOrderReceipt:
    def __init__(self, customer_id: str, order_id: str, date_ordered, upcoming_shipments, order_details, order_pdf_link: str):
        self.customer_id = customer_id
        self.order_id = order_id
        self.date_ordered = date_ordered
        self.upcoming_shipments = upcoming_shipments
        self.order_details = order_details
        self.order_pdf_link = order_pdf_link
