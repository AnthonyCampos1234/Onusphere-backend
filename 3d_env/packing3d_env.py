import gymnasium as gym
import numpy as np
from gymnasium import spaces

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

class Packing3DEnv(gym.Env):
    def __init__(self, box_size=(5, 5, 5), items=[(2, 2, 1), (1, 1, 3), (2, 1, 2)]):
        super(Packing3DEnv, self).__init__()

        self.box_size = box_size
        self.items = items  # list of (dx, dy, dz)
        self.current_item_idx = 0

        # Define action space: place item at (x, y, z)
        self.action_space = spaces.MultiDiscrete([
            box_size[0], box_size[1], box_size[2]
        ])

        # Observation space: binary 3D array (0 = empty, 1 = filled)
        self.observation_space = spaces.Box(low=0, high=1, shape=box_size, dtype=np.int8)

        self.grid = None

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.grid = np.zeros(self.box_size, dtype=np.int8)
        self.current_item_idx = 0
        return self.grid.copy(), {}

    def step(self, action):
        x, y, z = action
        item = self.items[self.current_item_idx]

        dx, dy, dz = item
        fits = (
            x + dx <= self.box_size[0] and
            y + dy <= self.box_size[1] and
            z + dz <= self.box_size[2]
        )
        if not fits:
            return self.grid.copy(), -1, True, False, {}

        region = self.grid[x:x+dx, y:y+dy, z:z+dz]
        if np.any(region):
            return self.grid.copy(), -1, True, False, {}

        self.grid[x:x+dx, y:y+dy, z:z+dz] = 1
        self.current_item_idx += 1

        done = self.current_item_idx >= len(self.items)
        reward = dx * dy * dz  # volume of item placed
        return self.grid.copy(), reward, done, False, {}

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
        ax.set_xlim(0, self.box_size[0])
        ax.set_ylim(0, self.box_size[1])
        ax.set_zlim(0, self.box_size[2])
        
        # Label the axes
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('3D Packing Visualization')
        
        # Draw the outer box as a wireframe
        box_x, box_y, box_z = self.box_size
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
        
        # Find all filled positions
        filled_positions = np.argwhere(self.grid == 1)
        
        # Group adjacent filled positions into items
        visited = np.zeros_like(self.grid, dtype=bool)
        item_id = 0
        
        for x in range(self.box_size[0]):
            for y in range(self.box_size[1]):
                for z in range(self.box_size[2]):
                    if self.grid[x, y, z] == 1 and not visited[x, y, z]:
                        # Find the extent of this item
                        max_x, max_y, max_z = x, y, z
                        
                        # Try to expand in each dimension
                        while max_x + 1 < self.box_size[0] and self.grid[max_x + 1, y, z] == 1:
                            max_x += 1
                        while max_y + 1 < self.box_size[1] and self.grid[x, max_y + 1, z] == 1:
                            max_y += 1
                        while max_z + 1 < self.box_size[2] and self.grid[x, y, max_z + 1] == 1:
                            max_z += 1
                        
                        # Mark all cells in this item as visited
                        for ix in range(x, max_x + 1):
                            for iy in range(y, max_y + 1):
                                for iz in range(z, max_z + 1):
                                    if self.grid[ix, iy, iz] == 1:
                                        visited[ix, iy, iz] = True
                        
                        # Draw the item as a cuboid
                        dx, dy, dz = max_x - x + 1, max_y - y + 1, max_z - z + 1
                        self._draw_cuboid(ax, x, y, z, dx, dy, dz, colors[item_id % len(colors)])
                        item_id += 1
        
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
