import pybullet as p
import numpy as np
import json
import os

# Change these relative imports to be explicit
from .item import BoxItem, CompoundItem, CylindricalItem, Item
from .truck import Truck

class PackingEngine:
    def __init__(self):
        # Initialize PyBullet in DIRECT mode (no GUI needed as we'll use Three.js)
        self.physics_client = p.connect(p.DIRECT)
        self.unplaced_items = []  # Items waiting to be placed
        self.trucks = []          # List of trucks available for packing
        
    def add_truck(self, truck):
        """Add a truck to the packing engine."""
        self.trucks.append(truck)
        return len(self.trucks) - 1  # Return the truck ID
        
    def add_item(self, item):
        """Add an item to the list of unplaced items."""
        self.unplaced_items.append(item)
    
    def add_items(self, items: list[Item]):
        """Add multiple items to the list of unplaced items."""
        self.unplaced_items.extend(items)
        
    def place_item(self, item_id, truck_id, position, rotation):
        """Move an item from unplaced to placed in the specified truck."""
        # First validate the placement
        print("attmpeting to place item with id: ", item_id, "in truck with id: ", truck_id, "at position: ", position, "with rotation: ", rotation)
        if self.validate_placement(item_id, truck_id, position, rotation):
            # If valid, move the item from unplaced to the truck
            item = self.unplaced_items.pop(item_id)
            self.trucks[truck_id].add_item(item, position, rotation)
            return True
        print("placement is not valid: ")
        return False
        
    def validate_placement(self, item_id, truck_id, position, rotation):
        """Check if placement is valid in the specified truck."""
        if 0 <= item_id < len(self.unplaced_items) and 0 <= truck_id < len(self.trucks):
            item = self.unplaced_items[item_id]
            truck = self.trucks[truck_id]
            
            # Get item dimensions
            item_dims = item.get_dimensions()
            
            # Check if item is within truck boundaries
            if (position[0] < 0 or 
                position[1] < 0 or 
                position[2] < 0 or
                position[0] + item_dims['length'] > truck.length or
                position[1] + item_dims['width'] > truck.width or
                position[2] + item_dims['height'] > truck.height):
                print("item is outside of truck boundaries")
                return False
            
            # Check for collisions with already placed items in this truck
            for placed in truck.loaded_items:
                placed_item = placed['item']
                placed_pos = placed['position']
                placed_dims = placed_item.get_dimensions()
                
                # Simple AABB collision detection
                if (position[0] < placed_pos[0] + placed_dims['length'] and
                    position[0] + item_dims['length'] > placed_pos[0] and
                    position[1] < placed_pos[1] + placed_dims['width'] and
                    position[1] + item_dims['width'] > placed_pos[1] and
                    position[2] < placed_pos[2] + placed_dims['height'] and
                    position[2] + item_dims['height'] > placed_pos[2]):
                    print("item is colliding with another item: ", placed_item.name, placed_pos)
                    return False
            
            # If we get here, the placement is valid
            return True
        print("id of object or truck is out of bound")
        print("current unplaced items: ", self.unplaced_items)
        return False
    
    def reset(self):
        """Reset the packing engine, moving all placed items back to unplaced."""
        for truck in self.trucks:
            for placed in truck.loaded_items:
                self.unplaced_items.append(placed['item'])
            truck.loaded_items = []
    
    def get_state(self):
        """
        Get the current state of the packing engine as a dictionary.
        
        Returns:
            dict: A dictionary representing the current state
        """
        state = {
            'trucks': [],
            'unplaced_items': []
        }
        
        # Save trucks and their loaded items
        for truck in self.trucks:
            truck_data = {
                'dimensions': {
                    'length': truck.length,
                    'width': truck.width,
                    'height': truck.height,
                    'door_width': truck.door_width,
                    'door_height': truck.door_height
                },
                'loaded_items': []
            }
            
            # Save loaded items in this truck
            for loaded in truck.loaded_items:
                item = loaded['item']
                item_data = self._serialize_item(item)
                item_data['position'] = loaded['position']
                item_data['rotation'] = loaded['rotation']
                truck_data['loaded_items'].append(item_data)
            
            state['trucks'].append(truck_data)
        
        # Save unplaced items
        for item in self.unplaced_items:
            state['unplaced_items'].append(self._serialize_item(item))
        
        return state
    
    def save_state(self, filepath):
        """
        Save the current state of the packing engine to a JSON file.
        
        Args:
            filepath: Path where the JSON file will be saved
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            state = self.get_state()
            
            # Write to file
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving state: {e}")
            return False
    
    def load_state(self, filepath):
        """
        Load a state from a JSON file and apply it to this packing engine.
        
        Args:
            filepath: Path to the JSON state file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return False
            
        try:
            # Clear current state
            self.trucks = []
            self.unplaced_items = []
            
            # Load state from file
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            # Create trucks
            for truck_data in state['trucks']:
                truck = Truck(truck_data['dimensions'])
                
                # Add loaded items to truck
                for item_data in truck_data['loaded_items']:
                    item = self._deserialize_item(item_data)
                    position = item_data['position']
                    rotation = item_data['rotation']
                    truck.add_item(item, position, rotation)
                
                self.trucks.append(truck)
            
            # Create unplaced items
            for item_data in state['unplaced_items']:
                item = self._deserialize_item(item_data)
                self.unplaced_items.append(item)
                
            return True
            
        except Exception as e:
            print(f"Error loading state: {e}")
            return False
    
    def verify_state(self, filepath):
        """
        Verify if the current state matches the state in the given JSON file.
        
        Args:
            filepath: Path to the JSON state file
            
        Returns:
            bool: True if states match, False otherwise
        """
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return False
            
        try:
            # Create a temporary engine to load the file state
            temp_engine = PackingEngine()
            if not temp_engine.load_state(filepath):
                return False
                
            # Compare number of trucks and unplaced items
            if len(self.trucks) != len(temp_engine.trucks) or len(self.unplaced_items) != len(temp_engine.unplaced_items):
                return False
                
            # Compare trucks and their loaded items
            for i, (truck1, truck2) in enumerate(zip(self.trucks, temp_engine.trucks)):
                # Compare truck dimensions
                if (truck1.length != truck2.length or
                    truck1.width != truck2.width or
                    truck1.height != truck2.height or
                    truck1.door_width != truck2.door_width or
                    truck1.door_height != truck2.door_height):
                    return False
                
                # Compare number of loaded items
                if len(truck1.loaded_items) != len(truck2.loaded_items):
                    return False
                
                # Compare each loaded item
                # Note: This assumes items are in the same order, which might not always be true
                # A more robust comparison would sort items or use a different matching strategy
                for j, (item1, item2) in enumerate(zip(truck1.loaded_items, truck2.loaded_items)):
                    if not self._compare_items(item1['item'], item2['item']):
                        return False
                    
                    # Compare position and rotation
                    if (item1['position'] != item2['position'] or
                        item1['rotation'] != item2['rotation']):
                        return False
            
            # Compare unplaced items
            # Again, this assumes items are in the same order
            for i, (item1, item2) in enumerate(zip(self.unplaced_items, temp_engine.unplaced_items)):
                if not self._compare_items(item1, item2):
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error verifying state: {e}")
            return False
    
    def _serialize_item(self, item):
        """Helper method to convert an item to a serializable dictionary."""
        if isinstance(item, BoxItem):
            return {
                'type': 'box',
                'dimensions': item.get_dimensions(),
                'weight': item.weight,
                'name': item.name
            }
        elif isinstance(item, CylindricalItem):
            return {
                'type': 'cylinder',
                'diameter': item.diameter,
                'height': item._height,
                'weight': item.weight,
                'name': item.name
            }
        elif isinstance(item, CompoundItem):
            sub_items = []
            for sub_item in item.items:
                sub_items.append(self._serialize_item(sub_item))
            
            return {
                'type': 'compound',
                'items': sub_items,
                'relative_positions': item.relative_positions,
                'weight': item.weight,
                'name': item.name
            }
        else:
            raise ValueError(f"Unknown item type: {type(item)}")
    
    def _deserialize_item(self, item_data):
        """Helper method to convert a dictionary to an item object."""
        if item_data['type'] == 'box':
            return BoxItem(
                dimensions=item_data['dimensions'],
                weight=item_data['weight'],
                name=item_data['name']
            )
        elif item_data['type'] == 'cylinder':
            return CylindricalItem(
                diameter=item_data['diameter'],
                height=item_data['height'],
                weight=item_data['weight'],
                name=item_data['name']
            )
        elif item_data['type'] == 'compound':
            # Recursively deserialize sub-items
            sub_items = []
            for sub_item_data in item_data['items']:
                sub_items.append(self._deserialize_item(sub_item_data))
            
            return CompoundItem(
                items=sub_items,
                relative_positions=item_data['relative_positions'],
                weight=item_data['weight'],
                name=item_data['name']
            )
        else:
            raise ValueError(f"Unknown item type: {item_data['type']}")
    
    def _compare_items(self, item1, item2):
        """Helper method to compare two items for equality."""
        # Check if items are of the same type
        if type(item1) != type(item2):
            return False
            
        # Check common properties
        if item1.weight != item2.weight or item1.name != item2.name:
            return False
            
        # Type-specific comparisons
        if isinstance(item1, BoxItem):
            return item1.get_dimensions() == item2.get_dimensions()
        elif isinstance(item1, CylindricalItem):
            return item1.diameter == item2.diameter and item1._height == item2._height
        elif isinstance(item1, CompoundItem):
            # Check if they have the same number of sub-items
            if len(item1.items) != len(item2.items):
                return False
                
            # Check relative positions
            if item1.relative_positions != item2.relative_positions:
                return False
                
            # Recursively compare sub-items
            for sub1, sub2 in zip(item1.items, item2.items):
                if not self._compare_items(sub1, sub2):
                    return False
                    
            return True
        
        # Unknown item type
        return False 
