from typing import List, Tuple, Dict, Any, Optional
from simulation.packing_engine import PackingEngine
from simulation.item import Item
from strategy.strategy import PackingStrategy


class GreedyLargestFirstStrategy(PackingStrategy):
    """
    A greedy packing strategy that:
    1. Sorts items by volume (largest first)
    2. Places each item at the front-right corner of the truck
    3. Moves the item back until it can't go further
    4. Moves the item left until it can't go further
    5. Places the item and continues with the next largest item
    6. Moves to the next truck when the current truck is full
    
    This strategy does not rotate items.
    """
    
    def __init__(self, name: str = "GreedyLargestFirst"):
        """Initialize the greedy strategy."""
        super().__init__(name)
        self.sorted_item_indices = []  # Will store indices of items sorted by volume
        self.current_truck_id = 0
        
    def pack(self, engine: PackingEngine) -> bool:
        """
        Execute the packing strategy on the given packing engine.
        
        Args:
            engine: The packing engine containing trucks and items to be packed
            
        Returns:
            bool: True if all items were packed, False otherwise
        """
        # Reset state
        self.current_truck_id = 0
        self.sorted_item_indices = []
        
        # Check if we have trucks and items
        if not engine.trucks or not engine.unplaced_items:
            return False
            
        # Sort items by volume (largest first)
        self._sort_items_by_volume(engine)
        
        # Try to place each item
        items_placed = 0
        total_items = len(engine.unplaced_items)
        
        while self.sorted_item_indices and self.current_truck_id < len(engine.trucks):
            placement = self.get_next_placement(engine)
            
            if placement:
                # Place the item
                success = engine.place_item(
                    placement['item_id'],
                    placement['truck_id'],
                    placement['position'],
                    placement['rotation']
                )
                
                if success:
                    items_placed += 1
                    # Update sorted indices after item removal
                    self._sort_items_by_volume(engine)
                else:
                    # If placement failed, try the next truck
                    self.current_truck_id += 1
            else:
                # No valid placement found, try the next truck
                self.current_truck_id += 1
        
        return items_placed == total_items
    
    def get_next_placement(self, engine: PackingEngine) -> Optional[Dict[str, Any]]:
        """
        Get the next item placement according to the strategy.
        
        Args:
            engine: The packing engine containing trucks and items to be packed
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary with placement information or None
        """
        if not self.sorted_item_indices or self.current_truck_id >= len(engine.trucks):
            return None
            
        # Get the current truck
        truck = engine.trucks[self.current_truck_id]
        
        # Get the largest unplaced item
        item_id = self.sorted_item_indices[0]
        item = engine.unplaced_items[item_id]
        item_dims = item.get_dimensions()
        
        # Start at the front-right corner
        position = [0, truck.width - item_dims['width'], 0]
        rotation = [0, 0, 0]  # No rotation
        
        # Try to move the item back (increasing x) as far as possible
        max_x = int(truck.length - item_dims['length'])
        for x in range(0, max_x + 1):
            position[0] = x
            if not self._is_valid_placement(engine, item_id, self.current_truck_id, position, rotation):
                # Move back one step if we've gone too far
                position[0] = max(0, x - 1)
                break
        
        # Try to move the item left (decreasing y) as far as possible
        min_y = 0
        for y in range(int(position[1]), min_y - 1, -1):
            position[1] = y
            if not self._is_valid_placement(engine, item_id, self.current_truck_id, position, rotation):
                # Move right one step if we've gone too far
                position[1] = min(truck.width - item_dims['width'], y + 1)
                break
        
        # Final validation
        if self._is_valid_placement(engine, item_id, self.current_truck_id, position, rotation):
            return {
                'item_id': item_id,
                'truck_id': self.current_truck_id,
                'position': position,
                'rotation': rotation
            }
        
        return None
    
    def _sort_items_by_volume(self, engine: PackingEngine) -> None:
        """
        Sort unplaced items by volume (largest first) and store their indices.
        
        Args:
            engine: The packing engine containing items to be sorted
        """
        # Calculate volume for each item
        volumes = []
        for i, item in enumerate(engine.unplaced_items):
            dims = item.get_dimensions()
            volume = dims['length'] * dims['width'] * dims['height']
            volumes.append((i, volume))
        
        # Sort by volume (largest first)
        volumes.sort(key=lambda x: x[1], reverse=True)
        
        # Store sorted indices
        self.sorted_item_indices = [i for i, _ in volumes]
    
    def _is_valid_placement(self, engine: PackingEngine, item_id: int, truck_id: int, 
                           position: List[float], rotation: List[float]) -> bool:
        """
        Check if a placement is valid without actually placing the item.
        
        Args:
            engine: The packing engine
            item_id: Index of the item in unplaced_items
            truck_id: Index of the target truck
            position: [x, y, z] position
            rotation: Rotation values
            
        Returns:
            bool: True if placement is valid, False otherwise
        """
        return engine.validate_placement(item_id, truck_id, position, rotation)
