from mongoengine import Document, ReferenceField, ListField, DateTimeField, EmbeddedDocument, IntField, EmbeddedDocumentField
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
    items = ListField(EmbeddedDocumentField(OrderItem), required=True)
    order_date = DateTimeField(required=True)

