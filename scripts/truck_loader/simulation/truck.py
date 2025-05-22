class Truck:
    def __init__(self, dimensions):
        self.length = dimensions['length']
        self.width = dimensions['width']
        self.height = dimensions['height']
        self.door_width = dimensions.get('door_width', self.width)  # Default to full width if not specified
        self.door_height = dimensions.get('door_height', self.height)  # Default to full height if not specified
        self.loaded_items = []
        
    def add_item(self, item, position, rotation):
        self.loaded_items.append({
            'item': item,
            'position': position,
            'rotation': rotation
        }) 