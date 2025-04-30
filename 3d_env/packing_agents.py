from packing3d_env import Packing3DEnv
import matplotlib.pyplot as plt
from openai import OpenAI
from packing3d_env import Action
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
        print(f"CONTROLLER MESSAGE: Putting item of index {action.item_idx} at position {action.x}, {action.y}, {action.z}")
        obs, reward, done, truncated, info = self.env.step(action)
        self.ax.clear()
        self.env.render(ax=self.ax, show=False)
        plt.draw()
        plt.pause(0.1)  # Small pause to allow the figure to display
        return obs, reward, done, truncated, info
    
    def get_environment_info(self):
        return self.env.get_environment_info()
    
    def get_placed_items(self):
        return self.env.get_placed_items()
    
    def get_remaining_items(self):
        return self.env.get_remaining_items()
        

class PackingAgent2:
    def __init__(self, items, service="openai", model="o4-mini"):
        self.controller = EnvironmentController(items)
        self.service = service
        self.model = model
        self.items = items
        self.conversation_history = []
        
        # Initialize the OpenAI client with API key from environment variables
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def start_packing(self, filename=None):
        """Start the packing process with the AI model"""
        # Initialize the conversation with the model
        system_prompt = """
        You are an AI assistant helping to solve a 3D bin packing problem. 
        You will be given information about a set of items with their dimensions (width, height, depth) and IDs.
        Your task is to place these items one by one in a 3D container without overlapping.
        
        For each step, you should:
        1. Analyze the current state of the environment
        2. Choose the next item to place
        3. Decide on the (x, y, z) coordinates for placement of the corner of the item
        4. Provide your decision in the format: "place {item_id} at ({x}, {y}, {z})." Do not include any other text. No other format will work.
        
        The environment will execute your command and provide feedback on the result.
        If there's an error (like overlapping items), you'll need to try a different placement.
        
        Think step by step and visualize the 3D space to make optimal packing decisions.
        """
        initial_message = f"""
        Here is the initial state of the environment:
        
        {self.controller.get_environment_info()}
        
        Please provide your first placement command.
        """

        # Initialize the conversation history
        self.conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": initial_message}
        ]

        print("SYSTEM PROMPT: " + system_prompt)
        print("INITIAL MESSAGE TO MODEL: " + initial_message)

        while True:
            # Get the response from the model
            response = self.client.chat.completions.create(
            model=self.model,
            messages=self.conversation_history
            )
            # Add this response to the conversation history
            model_response = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": model_response})
            print("FROM MODEL: " + model_response)
            # Parse the response and get a result
            action, error = self.parse_response(model_response)
            if action is None and error is not None:
                # Tell the model their formatting was wrong
                message = f"""
                Error: {error}
                
                Please try again.
                """
                self.conversation_history.append({"role": "user", "content": message})
            else:
                # try to perform the action and get a result and then tell the model the result
                obs, reward, done, truncated, info = self.controller.step(action)
                if filename is not None:
                    self.controller.env.save_state(self.controller.env, filename=filename)
                
                # Get updated environment state after action
                env_info = self.controller.get_environment_info()

                # Tell the model the result
                message = f"""
                {info}

                Reward: {reward}
                
                Current state:
                {env_info}
                Please provide your next placement command.
                """
                self.conversation_history.append({"role": "user", "content": message})
            
            # print the next message to the console
            print("TO MODEL: " + message)

            # If the agent is done, break
            if done:
                print("AGENT SYSTEM MESSAGE: All items have been packed successfully!")
                break



    def parse_response(self, model_response):
        # Look for patterns like "place 3 at (0, 0, 0)"
        match = re.search(r"place (\d+) at \((\d+),\s*(\d+),\s*(\d+)\)", model_response, re.IGNORECASE)
        
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
                return Action(x=x, y=y, z=z, item_idx=item_idx), None
            else:
                error_msg = f"Error: Item with ID {item_id} not found"
                return None, error_msg
        else:
            error_msg = "Could not parse action from model response"
            return None, error_msg
        


class PackingAgent:
    def __init__(self, items, service="openai", model="o1"):
        self.controller = EnvironmentController(items)
        self.service = service
        self.model = model
        self.items = items
        self.conversation_history = []
        
        # Initialize the OpenAI client with API key from environment variables
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def start_packing(self):
        """Start the packing process with the AI model"""
        # Initialize the conversation with the model
        self._initialize_conversation()
        
        # Continue the conversation until all items are packed or we can't proceed
        while True:
            # Get environment info to check if we're done
            self.items = self.controller.get_remaining_items()

            # Check if there are no more available items
            if len(self.items) == 0:
                print("AGENT SYSTEM MESSAGE: All items have been packed successfully!")
                break
                
            # Get the next action from the model
            action, error = self._get_next_action()
            
            # If the model couldn't provide a valid action, break
            if action is None:
                print("AGENT SYSTEM MESSAGE: Could not determine next action.\n Error: " + error + "\nEnding packing process.")
                break
                
            # Execute the action and get the result
            obs, reward, done, truncated, info = self.controller.step(action)
            if reward >= 0:
                # Get updated environment state after action
                env_info = self.controller.get_environment_info()
                # Send the result back to the model
                self._send_result_to_model(env_info, success=True)
            else:
                # If there was an error, inform the model
               self._send_result_to_model({"error": info}, success=False)
          
    
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
        4. Provide your decision in the format: "place {item_id} at ({x}, {y}, {z})." Do not include any other text. No other format will work.
        
        The environment will execute your command and provide feedback on the result.
        If there's an error (like overlapping items), you'll need to try a different placement.
        
        Think step by step and visualize the 3D space to make optimal packing decisions.
        """
        
        # Create initial message with environment state
        env_info = self.controller.get_environment_info()
        items_description = "\n".join([f"Item {item.id}: {item.dx}x{item.dy}x{item.dz}" 
                                        for item in self.items])
        
        initial_message = f"""
        Here is the initial state of the environment:
        
        {env_info}
        
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
        print("SYSTEM PROMPT: " + system_prompt)
        print("INITIAL MESSAGE: " + initial_message)
        print("AI: " + model_response)
    
    def _get_next_action(self):
        """Parse the model's response to get the next action"""
        # Get the last message from the model
        last_message = self.conversation_history[-1]["content"]
        print("FROM MODEL: " + last_message)
        
        # Try to parse the action from the message
        try:
            # Look for patterns like "place 3 at (0, 0, 0)"
            match = re.search(r"place (\d+) at \((\d+),\s*(\d+),\s*(\d+)\)", last_message, re.IGNORECASE)
            
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
                    return Action(x=x, y=y, z=z, item_idx=item_idx), None
                else:
                    error_msg = f"Error: Item with ID {item_id} not found"
                    print("AGENT SYSTEM MESSAGE: " + error_msg)
                    return None, error_msg
            else:
                error_msg = "Could not parse action from model response"
                print("AGENT SYSTEM MESSAGE: " + error_msg)
                return None, error_msg
        except Exception as e:
            error_msg = f"Error parsing action: {e}"
            print("AGENT SYSTEM MESSAGE: " + error_msg)
            return None, error_msg
    
    def _send_result_to_model(self, env_info, success=True):
        """Send the result of the action back to the model"""
        if success:
            
            message = f"""
            Action executed successfully!
            
            Current state:
            {env_info}
            Please provide your next placement command.
            """
            print("TO MODEL: " + message)
        else:
            # Create a message describing the error
            error = env_info.get("error", "Unknown error")
            message = f"""
            Error executing the action: {error}
            
            Please try a different placement.
            """
            print("TO MODEL: " + message)
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

def ai_packing_demo(items):
    agent = PackingAgent(items)
    agent.start_packing()
    plt.show()  # Keep the visualization window open
