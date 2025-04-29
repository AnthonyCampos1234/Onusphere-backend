from packing3d_env import Packing3DEnv
import matplotlib.pyplot as plt
from openai import OpenAI
from packing3d_env import Action

class EnvironmentController:
        def __init__(self, items):
            self.env = Packing3DEnv(items=items)
            obs, _ = self.env.reset()

            # Create a figure with subplots - one for 3D visualization
            self.fig = plt.figure(figsize=(12, 10))
            self.ax = self.fig.add_subplot(111, projection='3d')
            
            # Initial rendering
            self.env.render(ax=self.ax, show=False)
            plt.draw()
            plt.pause(0.1)  # Small pause to allow the figure to display

        def step(self, action):
            print(f"Putting item {action.item_idx} at position {action.x}, {action.y}, {action.z}")
            obs, reward, done, truncated, info = self.env.step(action)
            self.ax.clear()
            self.env.render(ax=self.ax, show=False)
            plt.draw()
            plt.pause(0.1)  # Small pause to allow the figure to display
        
        def get_environment_info(self):
            return self.env.get_environment_info()
        
class PackingAgent:
    def __init__(self, items, service="openai", model="o1"):
        self.controller = EnvironmentController(items)
        self.service = service
        self.model = model
        self.items = items
        self.conversation_history = []
        
        # Initialize the OpenAI client
        self.client = OpenAI()
        
    def start_packing(self):
        """Start the packing process with the AI model"""
        # Initialize the conversation with the model
        self._initialize_conversation()
        
        # Continue the conversation until all items are packed or we can't proceed
        while True:
            # Get environment info to check if we're done
            env_info = self.controller.get_environment_info()
            # Check if there are no more available items
            if len(self.controller.env.available_items) == 0:
                print("All items have been packed successfully!")
                break
                
            # Get the next action from the model
            action = self._get_next_action()
            
            # If the model couldn't provide a valid action, break
            if action is None:
                print("Could not determine next action. Ending packing process.")
                break
                
            # Execute the action and get the result
            try:
                self.controller.step(action)
                # Get updated environment state after action
                env_info = self.controller.get_environment_info()
                # Send the result back to the model
                self._send_result_to_model(env_info, success=True)
            except Exception as e:
                # If there was an error, inform the model
                self._send_result_to_model({"error": str(e)}, success=False)
    
    def _initialize_conversation(self):
        """Start the conversation with the model and explain the task"""
        system_prompt = """
        You are an AI assistant helping to solve a 3D bin packing problem. 
        You will be given information about a set of items with their dimensions (width, height, depth) and IDs.
        Your task is to place these items one by one in a 3D container without overlapping.
        
        For each step, you should:
        1. Analyze the current state of the environment
        2. Choose the next item to place
        3. Decide on the (x, y, z) coordinates for placement
        4. Provide your decision in the format: "place item {item_id} at position ({x}, {y}, {z})"
        
        The environment will execute your command and provide feedback on the result.
        If there's an error (like overlapping items), you'll need to try a different placement.
        
        Think step by step and visualize the 3D space to make optimal packing decisions.
        """
        
        # Create initial message with environment state
        env_info = self.controller.get_environment_info()
        items_description = "\n".join([f"Item {item.id}: {item.width}x{item.height}x{item.depth}" 
                                        for item in self.items])
        
        initial_message = f"""
        Here is the initial state of the environment:
        
        Container dimensions: {env_info['container_dimensions']}
        
        Available items:
        {items_description}
        
        Please provide your first placement command.
        """
        
        # Start the conversation
        self.conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": initial_message}
        ]
        
        # Get the first response from the model
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.conversation_history
        )
        
        # Add the model's response to the conversation history
        model_response = response.choices[0].message.content
        self.conversation_history.append({"role": "assistant", "content": model_response})
        print("AI: " + model_response)
    
    def _get_next_action(self):
        """Parse the model's response to get the next action"""
        # Get the last message from the model
        last_message = self.conversation_history[-1]["content"]
        
        # Try to parse the action from the message
        try:
            # Look for patterns like "place item 3 at position (0, 0, 0)"
            import re
            match = re.search(r"place item (\d+) at position \((\d+),\s*(\d+),\s*(\d+)\)", last_message, re.IGNORECASE)
            
            if match:
                item_id = int(match.group(1))
                x, y, z = int(match.group(2)), int(match.group(3)), int(match.group(4))
                
                # Find the item index based on the item ID
                item_idx = None
                for i, item in enumerate(self.items):
                    if item.id == item_id:
                        item_idx = i
                        break
                
                if item_idx is not None:
                    return Action(x=x, y=y, z=z, item_idx=item_idx)
                else:
                    print(f"Error: Item with ID {item_id} not found")
                    return None
            else:
                print("Could not parse action from model response")
                return None
        except Exception as e:
            print(f"Error parsing action: {e}")
            return None
    
    def _send_result_to_model(self, env_info, success=True):
        """Send the result of the action back to the model"""
        if success:
            # Create a message describing the current state
            placed_items = env_info.get("placed_items", [])
            remaining_items = env_info.get("remaining_items", [])
            
            placed_desc = "\n".join([f"Item {item['id']}: {item['width']}x{item['height']}x{item['depth']} at position ({item['x']}, {item['y']}, {item['z']})" 
                                    for item in placed_items])
            
            remaining_desc = "\n".join([f"Item {item['id']}: {item['width']}x{item['height']}x{item['depth']}" 
                                        for item in remaining_items])
            
            message = f"""
            Action executed successfully!
            
            Current state:
            Placed items:
            {placed_desc}
            
            Remaining items:
            {remaining_desc}
            
            Please provide your next placement command.
            """
        else:
            # Create a message describing the error
            error = env_info.get("error", "Unknown error")
            message = f"""
            Error executing the action: {error}
            
            Please try a different placement.
            """
        
        # Add the message to the conversation history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Get the next response from the model
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.conversation_history
        )
        
        # Add the model's response to the conversation history
        model_response = response.choices[0].message.content
        self.conversation_history.append({"role": "assistant", "content": model_response})
        print("AI: " + model_response)

def ai_packing_demo(items):
    agent = PackingAgent(items)
    agent.start_packing()
    plt.show()  # Keep the visualization window open
