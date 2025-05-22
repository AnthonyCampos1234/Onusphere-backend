from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
from simulation.packing_engine import PackingEngine
from simulation.item import Item


class PackingStrategy(ABC):
    """
    Abstract base class for packing strategies.
    
    This class serves as a wrapper for algorithms that determine
    how items should be packed into trucks.
    """
    
    def __init__(self, name: str = "BaseStrategy"):
        """
        Initialize a packing strategy.
        
        Args:
            name: A descriptive name for the strategy
        """
        self.name = name
    
    @abstractmethod
    def pack(self, engine: PackingEngine) -> bool:
        """
        Execute the packing strategy on the given packing engine.
        
        Args:
            engine: The packing engine containing trucks and items to be packed
            
        Returns:
            bool: True if packing was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_next_placement(self, engine: PackingEngine) -> Optional[Dict[str, Any]]:
        """
        Get the next item placement according to the strategy.
        
        Args:
            engine: The packing engine containing trucks and items to be packed
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary containing placement information:
                {
                    'item_id': int,       # Index of the item in unplaced_items
                    'truck_id': int,      # Index of the target truck
                    'position': List[float],  # [x, y, z] position
                    'rotation': List[float]   # Rotation values
                }
                or None if no valid placement is found
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this strategy.
        
        Returns:
            Dict[str, Any]: Dictionary containing strategy metadata
        """
        return {
            'name': self.name,
            'type': self.__class__.__name__
        }
