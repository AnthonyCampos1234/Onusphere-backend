from mongoengine import Document, ReferenceField, ListField, DateTimeField, EmbeddedDocument, IntField, EmbeddedDocumentField, StringField, DictField
from models.customer import Customer
from models.item import Item

class OrderItem(EmbeddedDocument):
    item = ReferenceField(Item, required=True)
    number_pallets = IntField(min_value=0, required=True)

    @staticmethod
    def calculate_pallets(order_quantity, units_per_pallet):
        # Returns the number of pallets for this item in this order
        if units_per_pallet <= 0:
            raise ValueError("Units per pallet must be greater than zero.")
        return max(1, -(-order_quantity // units_per_pallet))  # Ceiling division
    
    def set_pallets(self, order_quantity, units_per_pallet):
        self.number_pallets = self.calculate_pallets(order_quantity, units_per_pallet)

class Order(Document):
    customer = ReferenceField(Customer)
    items = ListField(EmbeddedDocumentField(OrderItem), required=True)
    order_date = DateTimeField(required=True)
    upcoming_shipment_times = ListField(StringField(), required=True)
    status = StringField(required=True, choices=['pending', 'loaded', 'delivered'], default='pending')
    loading_instructions = DictField()
