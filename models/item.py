from mongoengine import Document, StringField, FloatField

class Item(Document):
    item_number = StringField(required=True, unique=True)
    height = FloatField() # in inches
    width = FloatField() # in inches
    length = FloatField() # in inches
