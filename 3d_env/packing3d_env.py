import gymnasium as gym
import numpy as np
from gymnasium import spaces

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.widgets import Button

class Item:
    def __init__(self, dx: float, dy: float, dz: float, id=None):
        if id < 0:
            raise ValueError("Item id cannot be negative")
        self.id = id
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.volume = dx * dy * dz
        self.is_red_space = False

        self.x = None
        self.y = None
        self.z = None
        self.com_x = None   
        self.com_y = None
        self.com_z = None

    def set_position(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def set_com(self, com_x, com_y, com_z):
        self.com_x = com_x
        self.com_y = com_y
        self.com_z = com_z

    def get_com_top(self):
        if self.com_z is None or self.z is None:
            return None
        return self.com_x, self.com_y, self.z + self.dz
    
    def get_com_bottom(self):
        if self.com_z is None or self.z is None:
            return None
        return self.com_x, self.com_y, self.z
    
    def __str__(self):
        if self.x is None or self.y is None or self.z is None:
            return f"Item {self.id}: {self.dx}x{self.dy}x{self.dz}"
        else:
            return f"Item {self.id}: {self.dx}x{self.dy}x{self.dz} at ({self.x}, {self.y}, {self.z})"
    
class RedSpace(Item):
    def __init__(self, dx: float, dy: float, dz=0.5, id=-1):
        super().__init__(dx, dy, dz, id)
        self.is_red_space = True

class Action:
    """
    Action space:
    (item_idx, vertical_axis_rotation, horizontal_axis_rotation, x, y, z)
    item_idx: index of the item to place
    vertical_axis_rotation: rotation around the vertical axis
    horizontal_axis_rotation: rotation around the horizontal axis
    x: x coordinate
    y: y coordinate
    z: z coordinate

    Stores data for an action. Does not perform action. Simulation performs action.
    """

    def __init__(self, x: float, y: float, z: float, 
                 item_idx: int, 
                 vertical_axis_rotation=False, horizontal_axis_rotation=None):
        
        if (horizontal_axis_rotation is not None):
            raise ValueError("horizontal_axis_rotation is not supported yet")
        
        self.item_idx = item_idx
        self.vertical_axis_rotation = vertical_axis_rotation
        self.horizontal_axis_rotation = horizontal_axis_rotation
        self.x = x
        self.y = y
        self.z = z

class Packing3DEnv(gym.Env):
    def __init__(self, space_size=(10, 10, 10), items=None):
        super(Packing3DEnv, self).__init__()

        self.space_size = space_size
        
        # Handle items
        if items is None:
            self.items = [Item(1, 1, 1)]
        else:
            self.items = items
            
        self.available_items = list(range(len(self.items)))  # Track available items by index

        # Define action space: (item_idx, x, y, z)
        self.action_space = spaces.MultiDiscrete([
            len(self.items),  # Select which item to place
            space_size[0], space_size[1], space_size[2]
        ])

        # Observation space: binary 3D array (0 = empty, 1 = filled)
        self.observation_space = spaces.Box(low=0, high=1, shape=space_size, dtype=np.int8)

        self.grid = None
        self.item_grid = None  # Track which item ID is in each cell

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.grid = np.zeros(self.space_size, dtype=np.int8)
        self.item_grid = np.zeros(self.space_size, dtype=np.int16)  # Store item IDs
        self.available_items = list(range(len(self.items)))  # Reset available items
        return self.grid.copy(), {}

    def step(self, action):
        # Get action parameters
        item_idx = action.item_idx
        x, y, z = action.x, action.y, action.z
        
        # Check if the selected item is available
        if item_idx not in self.available_items:
            return self.grid.copy(), -1, False, False, {"error": "Item not available"}
            
        item = self.items[item_idx]
        dx, dy, dz = item.dx, item.dy, item.dz

        fits = (
            x + dx <= self.space_size[0] and
            y + dy <= self.space_size[1] and
            z + dz <= self.space_size[2]
        )
        if not fits:
            print(f"Item {item.id if item.id is not None else item_idx} does not fit with current orientation at position ({x}, {y}, {z})")
            return self.grid.copy(), -1, False, False, {"error": "Item doesn't fit"}
        
        legal, message = self.placed_legally(item=item, action=action)
        if not legal:
            return self.grid.copy(), -1, False, False, {"error": message}

        region = self.grid[x:x+dx, y:y+dy, z:z+dz]
        if np.any(region):
            return self.grid.copy(), -1, False, False, {"error": "Space already occupied"}

        self.grid[x:x+dx, y:y+dy, z:z+dz] = 1
        # Store the item ID (using the actual item_idx + 1) in the item_grid
        self.item_grid[x:x+dx, y:y+dy, z:z+dz] = item_idx + 1
        
        # Calculate and set the position of the item
        item.set_position(x, y, z)

        # Calculate and set the center of mass for the item
        com_x = x + dx / 2
        com_y = y + dy / 2
        com_z = z + dz / 2
        item.set_com(com_x, com_y, com_z)
        
        # Remove the used item from available items
        self.available_items.remove(item_idx)

        done = len(self.available_items) == 0
        reward = item.volume  # volume of item placed
        return self.grid.copy(), reward, done, False, {"placed_item": item_idx}
    
    def placed_legally(self, item, action):
        message = ""

        # Get item position and dimensions
        x, y, z = action.x, action.y, action.z
        dx, dy, dz = item.dx, item.dy, item.dz
        
        # Check if item is on bottom plane (z=0)
        if z == 0:
            message = "Item is on bottom plane"
            return True, message
            
        # Check if there's an item directly below the center
        center_x = x + dx/2
        center_y = y + dy/2
        # Round to nearest integer since we're checking grid positions
        center_x_int = int(center_x)
        center_y_int = int(center_y)
        
        # Check the grid position directly below the center
        if z > 0 and self.grid[center_x_int, center_y_int, z-1] == 1:
            message = "Item is on top of another (unrestricted) item"
            message = "Item cannot be placed on top of a red space"
            if True: # TODO: Check if the supporting voxel is part of an item that can't have this item placed on it
                # message = "Item is on top of another (unrestricted) item"
                # message = "Item cannot be placed on top of a red space"
                pass # TODO: return an additional message about the item's incorrect placement
            message = "Item is on top of another (unrestricted) item"
            return True, message
        
        message = "Item center of mass cannot be floating"
        return False, message
            
        

    def text_render(self):
        print(f"Current packed volume: {np.sum(self.grid)}")
        
    def render(self, ax=None, show=True):
        """
        Visualize the 3D packing using Matplotlib's 3D tools.
        
        Args:
            ax: Optional matplotlib 3D axis to plot on
            show: Whether to call plt.show() after rendering
        
        Returns:
            The matplotlib figure and axis objects
        """
        
        if ax is None:
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection='3d')
        else:
            fig = ax.figure
            
        # Set the limits of the plot
        ax.set_xlim(0, self.space_size[0])
        ax.set_ylim(0, self.space_size[1])
        ax.set_zlim(0, self.space_size[2])
        
        # Label the axes
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('3D Packing Visualization')
        
        # Draw the outer box as a wireframe
        box_x, box_y, box_z = self.space_size
        for x, y, z in [(0, 0, 0), (box_x, 0, 0), (0, box_y, 0), (0, 0, box_z),
                        (box_x, box_y, 0), (box_x, 0, box_z), (0, box_y, box_z),
                        (box_x, box_y, box_z)]:
            ax.scatter(x, y, z, color='black', alpha=0.5, s=10)
            
        # Draw box edges
        edges = [
            # Bottom face
            [(0, 0, 0), (box_x, 0, 0)], [(box_x, 0, 0), (box_x, box_y, 0)],
            [(box_x, box_y, 0), (0, box_y, 0)], [(0, box_y, 0), (0, 0, 0)],
            # Top face
            [(0, 0, box_z), (box_x, 0, box_z)], [(box_x, 0, box_z), (box_x, box_y, box_z)],
            [(box_x, box_y, box_z), (0, box_y, box_z)], [(0, box_y, box_z), (0, 0, box_z)],
            # Connecting edges
            [(0, 0, 0), (0, 0, box_z)], [(box_x, 0, 0), (box_x, 0, box_z)],
            [(box_x, box_y, 0), (box_x, box_y, box_z)], [(0, box_y, 0), (0, box_y, box_z)]
        ]
        
        for edge in edges:
            ax.plot([edge[0][0], edge[1][0]], [edge[0][1], edge[1][1]], 
                    [edge[0][2], edge[1][2]], color='black', alpha=0.5, linewidth=1)
        
        # Draw filled items
        colors = plt.cm.tab10.colors
        
        # Get unique item IDs (excluding 0 which is empty space)
        unique_items = np.unique(self.item_grid)
        unique_items = unique_items[unique_items > 0]
        
        for item_id in unique_items:
            # Find all cells belonging to this item
            item_cells = np.argwhere(self.item_grid == item_id)
            if len(item_cells) == 0:
                continue
                
            # Find the bounding box of this item
            min_x, min_y, min_z = np.min(item_cells, axis=0)
            max_x, max_y, max_z = np.max(item_cells, axis=0)
            
            # Calculate dimensions
            dx = max_x - min_x + 1
            dy = max_y - min_y + 1
            dz = max_z - min_z + 1
            
            # Get the actual item object
            item_idx = item_id - 1  # Convert from 1-indexed to 0-indexed
            item = self.items[item_idx]
            
            # Draw the item as a cuboid
            color_idx = item_idx % len(colors)
            self._draw_cuboid(ax, min_x, min_y, min_z, dx, dy, dz, colors[color_idx])
            
            # Draw orientation arrows from the origin point
            arrow_length = 0.8  # Scale factor for arrow length
            
            # X-axis arrow (red)
            if dx > 0:
                ax.quiver(min_x, min_y, min_z, arrow_length, 0, 0, color='red', 
                         arrow_length_ratio=0.2, linewidth=2)
            
            # Y-axis arrow (green)
            if dy > 0:
                ax.quiver(min_x, min_y, min_z, 0, arrow_length, 0, color='green', 
                         arrow_length_ratio=0.2, linewidth=2)
            
            # Z-axis arrow (blue)
            if dz > 0:
                ax.quiver(min_x, min_y, min_z, 0, 0, arrow_length, color='blue', 
                         arrow_length_ratio=0.2, linewidth=2)
            
            # Draw center of mass point if available
            if item.com_x is not None and item.com_y is not None and item.com_z is not None:
                ax.scatter(item.com_x, item.com_y, item.com_z, color='black', s=50, marker='o', label='COM')
                
                # Draw top COM point
                top_com = item.get_com_top()
                if top_com is not None:
                    ax.scatter(top_com[0], top_com[1], top_com[2], color='red', s=30, marker='^', label='Top')
                
                # Draw bottom COM point
                bottom_com = item.get_com_bottom()
                if bottom_com is not None:
                    ax.scatter(bottom_com[0], bottom_com[1], bottom_com[2], color='blue', s=30, marker='v', label='Bottom')
        
        # Add a legend (only once)
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), loc='upper right')
        
        if show:
            plt.tight_layout()
            plt.show()
            
        return fig, ax
    
    def _draw_cuboid(self, ax, x, y, z, dx, dy, dz, color):
        """Helper method to draw a cuboid at position (x,y,z) with dimensions (dx,dy,dz)"""
        # Define the 8 vertices of the cuboid
        vertices = [
            [x, y, z], [x+dx, y, z], [x+dx, y+dy, z], [x, y+dy, z],
            [x, y, z+dz], [x+dx, y, z+dz], [x+dx, y+dy, z+dz], [x, y+dy, z+dz]
        ]
        
        # Define the 6 faces using indices to vertices
        faces = [
            [vertices[0], vertices[1], vertices[2], vertices[3]],  # bottom
            [vertices[4], vertices[5], vertices[6], vertices[7]],  # top
            [vertices[0], vertices[1], vertices[5], vertices[4]],  # front
            [vertices[2], vertices[3], vertices[7], vertices[6]],  # back
            [vertices[0], vertices[3], vertices[7], vertices[4]],  # left
            [vertices[1], vertices[2], vertices[6], vertices[5]]   # right
        ]
        
        # Create a Poly3DCollection
        collection = Poly3DCollection(faces, alpha=0.7, linewidths=1, edgecolors='black')
        collection.set_facecolor(color)
        ax.add_collection3d(collection)

    def interactive_render(self, actions=None):
        """
        Create an interactive matplotlib figure with buttons to control the environment
        without resetting the view orientation.
        
        Args:
            actions: Optional list of predefined actions to cycle through with the Next button
        """
        if actions is None:
            actions = []
            
        # Create a figure with subplots - one for 3D visualization
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # Initial rendering
        self.render(ax=ax, show=False)
        
        # Create a class to handle button clicks
        class ActionHandler:
            def __init__(self, env, ax, fig, actions):
                self.env = env
                self.ax = ax
                self.fig = fig
                self.action_idx = 0
                self.done = False
                self.actions = actions
            
            def next_action(self, event=None, show_obs=False):
                if self.done or self.action_idx >= len(self.actions):
                    print("Episode complete or no more predefined actions.")
                    return
                
                # Get current camera view angles before updating
                elev = self.ax.elev
                azim = self.ax.azim
                
                # Take the next action
                action = self.actions[self.action_idx]
                print(f"Placing item: {action.item_idx} at ({action.x}, {action.y}, {action.z})")
                    
                obs, reward, done, truncated, info = self.env.step(action)
                console = f"reward: {reward}\n done: {done}\n truncated: {truncated}\n info: {info}"
                if show_obs:
                    console += f"\nobs: {obs}"
                print(console)              
                # Clear the axis but maintain the view
                self.ax.clear()
                
                # Re-render the environment
                self.env.render(ax=self.ax, show=False)
                
                # Restore the camera view angles
                self.ax.view_init(elev=elev, azim=azim)
                
                # Update the figure
                self.fig.canvas.draw_idle()
                
                # Update state
                self.action_idx += 1
                self.done = done
            
            def custom_action(self, event):
                if self.done:
                    print("Episode already complete.")
                    return
                
                # Get current camera view angles before updating
                elev = self.ax.elev
                azim = self.ax.azim
                
                # Prompt for custom action
                try:
                    print(f"Available items: {self.env.available_items}")
                    item_idx = int(input("Enter item index: "))
                    x = int(input("Enter x coordinate: "))
                    y = int(input("Enter y coordinate: "))
                    z = int(input("Enter z coordinate: "))
                    
                    # Create Action object
                    action = Action(x, y, z, item_idx=item_idx)
                    
                    # Take the action
                    print(f"Taking action: item_idx={item_idx}, x={x}, y={y}, z={z}")
                    obs, reward, done, truncated, info = self.env.step(action)
                    print(f"Reward: {reward}, Done: {done}")
                    if "error" in info:
                        print(f"Error: {info['error']}")
                    
                    # Clear the axis but maintain the view
                    self.ax.clear()
                    
                    # Re-render the environment
                    self.env.render(ax=self.ax, show=False)
                    
                    # Restore the camera view angles
                    self.ax.view_init(elev=elev, azim=azim)
                    
                    # Update the figure
                    self.fig.canvas.draw_idle()
                    
                    # Update state
                    self.done = done
                    
                except ValueError as e:
                    print(f"Error: {e}")
            
            def reset_env(self, event):
                # Get current camera view angles before updating
                elev = self.ax.elev
                azim = self.ax.azim
                
                # Reset the environment
                self.env.reset()
                self.action_idx = 0
                self.done = False
                
                # Clear the axis but maintain the view
                self.ax.clear()
                
                # Re-render the environment
                self.env.render(ax=self.ax, show=False)
                
                # Restore the camera view angles
                self.ax.view_init(elev=elev, azim=azim)
                
                # Update the figure
                self.fig.canvas.draw_idle()
                
                print("Environment reset.")
        
        # Create button axes and buttons
        next_button_ax = plt.axes([0.7, 0.05, 0.1, 0.075])
        custom_button_ax = plt.axes([0.81, 0.05, 0.1, 0.075])
        reset_button_ax = plt.axes([0.59, 0.05, 0.1, 0.075])
        
        handler = ActionHandler(self, ax, fig, actions)
        next_button = Button(next_button_ax, 'Next Action')
        next_button.on_clicked(handler.next_action)
        
        custom_button = Button(custom_button_ax, 'Custom Action')
        custom_button.on_clicked(handler.custom_action)
        
        reset_button = Button(reset_button_ax, 'Reset')
        reset_button.on_clicked(handler.reset_env)
        
        plt.tight_layout()
        plt.show()
        
        return fig, ax, handler

    def get_environment_info(self):
        """
        Returns a string with information about the current state of the environment.
        
        Returns:
            A string containing information about available items and the observation
        """
        # Get available items
        available_items_info = []
        
        for idx in self.available_items:
            item = self.items[idx]
            item_info = f"Item {idx} (ID: {item.id}): {item.dx}x{item.dy}x{item.dz}, Volume: {item.volume}"
            available_items_info.append(item_info)
        
        # Format the observation (3D grid)
        obs_str = "Current Grid State:\n"
        for z in range(self.grid.shape[2]):
            obs_str += f"Layer z={z}:\n"
            for x in range(self.grid.shape[0]):
                row = ""
                for y in range(self.grid.shape[1]):
                    row += "■ " if self.grid[x, y, z] == 1 else "□ "
                obs_str += row + "\n"
            obs_str += "\n"
        
        # Combine all information
        result = "Environment Information:\n"
        result += "=====================\n\n"
        
        result += "Available Items:\n"
        if available_items_info:
            result += "\n".join(available_items_info)
        else:
            result += "No items available (all placed)"
        result += "\n\n"
        
        result += obs_str
        
        return result
