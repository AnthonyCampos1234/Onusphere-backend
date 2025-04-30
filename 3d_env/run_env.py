from packing3d_env import Packing3DEnv, Item, Action
import matplotlib.pyplot as plt
import time
from openai import OpenAI
from packing_agents import EnvironmentController
from packing_agents import PackingAgent
from packing_agents import PackingAgent2

items = [
    Item(2, 2, 2, id=1),
    Item(1, 1, 1, id=2),
    Item(5, 5, 1, id=3),
    Item(3, 3, 3, id=4)
]

actions = [
    Action(x=0, y=0, z=0, item_idx=0),
    Action(x=2, y=0, z=0, item_idx=1),
    Action(x=0, y=0, z=2, item_idx=3),
    Action(x=0, y=2, z=0, item_idx=2)
]

def automation_testing(items, actions):
    env = Packing3DEnv(items=items)
    obs, _ = env.reset()

    # Launch the interactive viewer and get the handler
    fig, ax, handler = env.interactive_render()

    # Give the window time to appear and initialize
    time.sleep(1)

    # Execute each action with a delay
    for i, action in enumerate(actions):
        print(f"Executing action {i+1}/{len(actions)}")
        
        # Execute the action
        obs, reward, done, truncated, info = handler.env.step(action)
        print(f"Reward: {reward}, Done: {done}")
        if "error" in info:
            print(f"Error: {info['error']}")
        
        # Update the visualization
        handler.ax.clear()
        handler.env.render(ax=handler.ax, show=False)
        handler.fig.canvas.draw_idle()
        
        # Pause to let you see the change
        time.sleep(0.5)

    print("All actions executed. You can still use the interactive buttons.")
    
    # Keep the window open until manually closed
    plt.show()

def build_testing(items, actions):

    env = Packing3DEnv(items=items)

    obs, _ = env.reset()
    done = False

    # Launch the interactive viewer
    env.interactive_render(actions)

items2 = [
    Item(2, 2, 2, id=1),
    Item(1, 1, 1, id=2),
    Item(5, 5, 1, id=3),
    Item(3, 3, 3, id=4),
    Item(4, 2, 2, id=5),
    Item(2, 3, 1, id=6),
    Item(3, 3, 2, id=7),
    Item(5, 4, 3, id=8),
    Item(6, 4, 2, id=9),
    Item(2, 2, 1, id=10),
    Item(4, 4, 4, id=11),
    Item(3, 2, 2, id=12),
    Item(1, 2, 1, id=13),
    Item(5, 3, 3, id=14),
    Item(4, 3, 2, id=15),
    Item(2, 1, 1, id=16),
    Item(3, 4, 3, id=17),
    Item(6, 5, 3, id=18),
    Item(2, 3, 2, id=19),
    Item(1, 1, 2, id=20),
    Item(5, 2, 2, id=21),
    Item(4, 2, 3, id=22),
    Item(3, 1, 2, id=23),
    Item(2, 2, 3, id=24),
    Item(5, 4, 4, id=25),
    Item(3, 3, 1, id=26),
    Item(1, 2, 1, id=27),
    Item(6, 3, 2, id=28),
    Item(2, 4, 2, id=29),
    Item(4, 3, 3, id=30)
]


def cli_testing(items, actions):
    env = Packing3DEnv(items=items)
    obs, _ = env.reset()

    # Create a figure with subplots - one for 3D visualization
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Initial rendering
    env.render(ax=ax, show=False)
    plt.draw()
    plt.pause(0.1)  # Small pause to allow the figure to display
    
    # Execute each action with a delay
    for i, action in enumerate(actions):
        print(f"Executing action {i+1}/{len(actions)}")
        
        # Execute the action
        obs, reward, done, truncated, info = env.step(action)
        print(f"Reward: {reward}, Done: {done}")
        if "error" in info:
            print(f"Error: {info['error']}")
        
        # Update the visualization
        ax.clear()
        env.render(ax=ax, show=False)
        plt.draw()
        print(env.get_environment_info())
        plt.pause(2)  # This allows the figure to update and process events
    
    print("All actions executed. Press Enter to close the visualization.")
    input()  # Wait for user input before closing
    plt.close(fig)

if __name__ == "__main__":
    # build_testing(items, actions)
    agent = PackingAgent2(items2)
    agent.start_packing(filename="04-attempt.json")