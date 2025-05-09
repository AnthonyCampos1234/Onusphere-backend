from mongoengine import Document, StringField, FloatField, IntField

class Item(Document):
    item_number = StringField(required=True, unique=True)
    height = FloatField() # in inches, ex: 30.75 or 0 meaning not set
    width = FloatField() # in inches
    length = FloatField() # in inches
    special_instructions = StringField()

