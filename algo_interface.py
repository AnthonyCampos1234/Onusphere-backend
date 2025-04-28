from enum import Enum
from typing import List, Optional, Dict, Union

class UnderStackability(Enum):
    SELF = "Self"
    NEVER = "Not"
    CORRUGATED = "Corrugated"
    ANCILLARY = "Ancillary"

class Truck:
    def __init__(self, id: str, 
                 name: str, 
                 sent_from: None, # Maybe add later
                 sent_to: None, # Maybe add later
                 height_in: float, 
                 width_in: float, 
                 depth_in: float, 
                 door_height_in: float, 
                 door_width_in: float):
        self.id = id
        self.name = name
        self.sent_from = sent_from
        self.sent_to = sent_to
        self.height_in = height_in
        self.width_in = width_in
        self.depth_in = depth_in
        self.door_height_in = door_height_in
        self.door_width_in = door_width_in
        
    @classmethod
    def with_dimensions_cm(cls, id: str, name: str, sent_from: None, sent_to: None,
                          cm_height: float, cm_width: float, cm_depth: float,
                          door_height_cm: float, door_width_cm: float) -> 'Truck':
        """Create a truck with dimensions in centimeters instead of inches."""
        # Convert cm to inches (1 inch = 2.54 cm)
        height_in = cm_height / 2.54
        width_in = cm_width / 2.54
        depth_in = cm_depth / 2.54
        door_height_in = door_height_cm / 2.54
        door_width_in = door_width_cm / 2.54
        
        return cls(
            id=id,
            name=name,
            sent_from=sent_from,
            sent_to=sent_to,
            height_in=height_in,
            width_in=width_in,
            depth_in=depth_in,
            door_height_in=door_height_in,
            door_width_in=door_width_in
        )
    
    @classmethod
    def with_dimensions_m(cls, id: str, name: str, sent_from: None, sent_to: None,
                         m_height: float, m_width: float, m_depth: float,
                         door_height_m: float, door_width_m: float) -> 'Truck':
        """Create a truck with dimensions in meters instead of inches."""
        # Convert meters to inches (1 inch = 0.0254 m)
        height_in = m_height / 0.0254
        width_in = m_width / 0.0254
        depth_in = m_depth / 0.0254
        door_height_in = door_height_m / 0.0254
        door_width_in = door_width_m / 0.0254
        
        return cls(
            id=id,
            name=name,
            sent_from=sent_from,
            sent_to=sent_to,
            height_in=height_in,
            width_in=width_in,
            depth_in=depth_in,
            door_height_in=door_height_in,
            door_width_in=door_width_in
        )
    
    @classmethod
    def with_dimensions_ft(cls, id: str, name: str, sent_from: None, sent_to: None,
                          ft_height: float, ft_width: float, ft_depth: float,
                          door_height_ft: float, door_width_ft: float) -> 'Truck':
        """Create a truck with dimensions in feet instead of inches."""
        # Convert feet to inches (1 foot = 12 inches)
        height_in = ft_height * 12
        width_in = ft_width * 12
        depth_in = ft_depth * 12
        door_height_in = door_height_ft * 12
        door_width_in = door_width_ft * 12
        
        return cls(
            id=id,
            name=name,
            sent_from=sent_from,
            sent_to=sent_to,
            height_in=height_in,
            width_in=width_in,
            depth_in=depth_in,
            door_height_in=door_height_in,
            door_width_in=door_width_in
        )

class Pallet:
    def __init__(self, id: str, 
                 name, # Not necessary for algorithm
                 sent_from: None, # Maybe add later
                 sent_to: None, # Maybe add later
                 inch_height: float, 
                 inch_width: float, 
                 inch_depth: float, 
                 weight_kgs: float, 
                 stackabilities: List[UnderStackability]):
        self.id = id
        self.name = name
        self.sent_from = sent_from
        self.sent_to = sent_to
        self.inch_height = inch_height
        self.inch_width = inch_width
        self.inch_depth = inch_depth
        self.weight_kgs = weight_kgs
        if stackabilities is None or len(stackabilities) == 0:
            self.stackabilities = [UnderStackability.NEVER]
        else:
            if UnderStackability.NEVER in stackabilities:
                raise ValueError("Pallets are either stackable NEVER, or sometimes. Not both.")
            else:
                self.stackabilities = stackabilities
    
    @classmethod
    def with_dimensions_cm(cls, id: str, name: str, cm_height: float, cm_width: float, 
                          cm_depth: float, weight_kgs: float, 
                          stackabilities: Optional[List[UnderStackability]] = None) -> 'Pallet':
        """Create a pallet with dimensions in centimeters instead of inches."""
        # Convert cm to inches (1 inch = 2.54 cm)
        inch_height = cm_height / 2.54
        inch_width = cm_width / 2.54
        inch_depth = cm_depth / 2.54
        
        return cls(
            id=id,
            name=name,
            sent_from=None,
            sent_to=None,
            inch_height=inch_height,
            inch_width=inch_width,
            inch_depth=inch_depth,
            weight_kgs=weight_kgs,
            stackabilities=stackabilities
        )
    
    @classmethod
    def with_weight_lbs(cls, id: str, name: str, inch_height: float, inch_width: float,
                       inch_depth: float, weight_lbs: float,
                       stackabilities: Optional[List[UnderStackability]] = None) -> 'Pallet':
        """Create a pallet with weight in pounds instead of kilograms."""
        # Convert lbs to kgs (1 kg = 2.20462 lbs)
        weight_kgs = weight_lbs / 2.20462
        
        return cls(
            id=id,
            name=name,
            sent_from=None,
            sent_to=None,
            inch_height=inch_height,
            inch_width=inch_width,
            inch_depth=inch_depth,
            weight_kgs=weight_kgs,
            stackabilities=stackabilities
        )
    
    @classmethod
    def with_weight_lbs_dimensions_cm(cls, id: str, name: str, cm_height: float, cm_width: float,
                       cm_depth: float, weight_lbs: float,
                       stackabilities: Optional[List[UnderStackability]] = None) -> 'Pallet':
        """Create a pallet with weight in pounds and dimensions in centimeters."""
        # Convert cm to inches (1 inch = 2.54 cm)
        inch_height = cm_height / 2.54
        inch_width = cm_width / 2.54
        inch_depth = cm_depth / 2.54
        
        # Convert lbs to kgs (1 kg = 2.20462 lbs)
        weight_kgs = weight_lbs / 2.20462
        
        return cls(
            id=id,
            name=name,
            sent_from=None,
            sent_to=None,
            inch_height=inch_height,
            inch_width=inch_width,
            inch_depth=inch_depth,
            weight_kgs=weight_kgs,
            stackabilities=stackabilities
        )

class Order:
    def __init__(self, id: str, 
                 name: str, 
                 sent_from: None, # Maybe add later
                 sent_to: None, # Maybe add later
                 pallets: List[Pallet],
                 trucks: List[Truck]):
        self.id = id
        self.name = name
        self.sent_from = sent_from
        self.sent_to = sent_to
        self.pallets = pallets
        self.trucks = trucks

    @classmethod
    def with_pallets_and_trucks(cls, id: str, name: str, 
                               pallets_dict: Dict[Pallet, int], 
                               trucks_dict: Dict[Truck, int]) -> 'Order':
        """
        Create an order with dictionaries mapping pallets and trucks to their quantities.
        
        Args:
            id: Order identifier
            name: Order name
            pallets_dict: Dictionary with Pallet objects as keys and quantities as values
            trucks_dict: Dictionary with Truck objects as keys and quantities as values
            
        Returns:
            A new Order instance with expanded pallets and trucks lists
        """
        # Expand the dictionaries into lists
        pallets = []
        for pallet, quantity in pallets_dict.items():
            pallets.extend([pallet] * quantity)
            
        trucks = []
        for truck, quantity in trucks_dict.items():
            trucks.extend([truck] * quantity)
            
        return cls(id, name, None, None, pallets, trucks)
