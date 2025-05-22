from abc import ABC, abstractmethod

class Item(ABC):
    """Abstract base class for all items that can be loaded into a truck."""
    
    def __init__(self, weight=1, name="unnamed"):
        self.weight = weight
        self.name = name
    
    @abstractmethod
    def get_dimensions(self):
        """Return the overall dimensions of the item as a dictionary with length, width, height."""
        pass
    
    @abstractmethod
    def get_volume(self):
        """Return the total volume of the item."""
        pass
    
    @property
    def length(self):
        return self.get_dimensions()['length']
    
    @property
    def width(self):
        return self.get_dimensions()['width']
    
    @property
    def height(self):
        return self.get_dimensions()['height']


class BoxItem(Item):
    """A simple box-shaped item with length, width, and height."""
    
    def __init__(self, dimensions, weight=1, name="unnamed"):
        super().__init__(weight, name)
        self._dimensions = {
            'length': dimensions['length'],
            'width': dimensions['width'],
            'height': dimensions['height']
        }
    
    def get_dimensions(self):
        return self._dimensions
    
    def get_volume(self):
        return self.length * self.width * self.height


class CompoundItem(Item):
    """An item composed of multiple sub-items arranged in a specific configuration."""
    
    def __init__(self, items, relative_positions, weight=None, name="compound"):
        """
        Create a compound item from multiple sub-items.
        
        Args:
            items: List of Item objects
            relative_positions: List of (x, y, z) positions for each item, relative to compound origin
            weight: Total weight (if None, will sum weights of all items)
            name: Name of the compound item
        """
        if weight is None:
            weight = sum(item.weight for item in items)
        
        super().__init__(weight, name)
        
        if len(items) != len(relative_positions):
            raise ValueError("Number of items must match number of positions")
            
        self.items = items
        self.relative_positions = relative_positions
    
    def get_dimensions(self):
        """Calculate the bounding box of all contained items."""
        if not self.items:
            return {'length': 0, 'width': 0, 'height': 0}
        
        # Find min/max coordinates of all items
        min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
        max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')
        
        for item, pos in zip(self.items, self.relative_positions):
            item_dims = item.get_dimensions()
            
            # Calculate item's bounding box in compound space
            item_min_x = pos[0]
            item_min_y = pos[1]
            item_min_z = pos[2]
            item_max_x = pos[0] + item_dims['length']
            item_max_y = pos[1] + item_dims['width']
            item_max_z = pos[2] + item_dims['height']
            
            # Update overall min/max
            min_x = min(min_x, item_min_x)
            min_y = min(min_y, item_min_y)
            min_z = min(min_z, item_min_z)
            max_x = max(max_x, item_max_x)
            max_y = max(max_y, item_max_y)
            max_z = max(max_z, item_max_z)
        
        return {
            'length': max_x - min_x,
            'width': max_y - min_y,
            'height': max_z - min_z
        }
    
    def get_volume(self):
        """Sum the volumes of all contained items."""
        return sum(item.get_volume() for item in self.items)


class CylindricalItem(Item):
    """A cylindrical item defined by diameter and height."""
    
    def __init__(self, diameter, height, weight=1, name="unnamed"):
        super().__init__(weight, name)
        self.diameter = diameter
        self._height = height
    
    def get_dimensions(self):
        """Return the bounding box dimensions of the cylinder."""
        return {
            'length': self.diameter,
            'width': self.diameter,
            'height': self._height
        }
    
    def get_volume(self):
        """Calculate the volume of the cylinder."""
        import math
        radius = self.diameter / 2
        return math.pi * radius * radius * self._height 