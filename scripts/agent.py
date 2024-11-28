__author__ = "Aybuke Ozturk Suri, Johvany Gustave"
__copyright__ = "Copyright 2023, IN512, IPSA 2024"
__credits__ = ["Aybuke Ozturk Suri", "Johvany Gustave"]
__license__ = "Apache License 2.0"
__version__ = "1.0.0"

from network import Network
from my_constants import *

from threading import Thread, Lock
import numpy as np
from time import sleep
import random


class Agent:
    """ Class that implements the behavior of each agent based on their perception and communication with other agents """
    def __init__(self, server_ip):
        # DO NOT TOUCH THE FOLLOWING INSTRUCTIONS
        self.network = Network(server_ip=server_ip)
        self.agent_id = self.network.id
        self.running = True
        self.network.send({"header": GET_DATA})
        self.msg = {}
        env_conf = self.network.receive()
        self.nb_agent_expected = 0
        self.nb_agent_connected = 0
        self.x, self.y = env_conf["x"], env_conf["y"]   # initial agent position
        self.w, self.h = env_conf["w"], env_conf["h"]   # environment dimensions

        # Initialize the cell values
        self.cell_val = env_conf["cell_val"]  # initial cell value
        self.prev_cell_val = self.cell_val  # initialize previous cell value
        print(f"Initial cell value: {self.cell_val}")  # Print the initial cell value
        self.current_direction = None  # Direction actuelle du robot

        # Initialize moves dictionary
        self.moves = {0 :(0, 0), # Stand still
                      1 : (-1, 0), # Left
                      2 : (1, 0), # Right
                      3 : (0, -1), # Up
                      4 : (0, 1), # Down
                      5 : (-1, -1), # Up left
                      6 : (1, -1), # Up right
                      7 : (-1, 1), # Down left
                      8 : (1, 1) # Down right
        }
        
        # Start the message handling thread
        Thread(target=self.msg_cb, daemon=True).start()
        self.wait_for_connected_agent()

    def wait_for_connected_agent(self):
        self.network.send({"header": GET_NB_AGENTS})
        check_conn_agent = True
        while check_conn_agent:
            if self.nb_agent_expected == self.nb_agent_connected:
                print("Both agents are connected!")
                check_conn_agent = False

        print(f"Agent initialized at position ({self.x}, {self.y}) with cell value {self.cell_val}.")

    def msg_cb(self):
        """Handle incoming messages."""
        while self.running:
            try:
                msg = self.network.receive()
                print(f"Raw msg : {msg}")
                if not msg:
                    continue

                header = msg.get("header")
                print(f"Header of message : {header}")
                if header == MOVE:
                    print(f"My header is Move")
                    self._update_position(msg)

                    # Handle the status message if present
                    status = msg.get("status")
                    if status:
                        print(f"Status update: {status}")  # Print the status message

                elif header == BROADCAST_MSG:
                    print(f"My header is Broadcast")
                    self._handle_broadcast(msg)
                    print("I received BROADCAST message")
                elif header == GET_NB_AGENTS:
                    print(f"My header is GET_NB_AGENTS")
                    self.nb_agent_expected = msg["nb_agents"]
                elif header == GET_NB_CONNECTED_AGENTS:
                    print(f"My header is GET_NB_CONNECTED_AGENTS")
                    self.nb_agent_connected = msg["nb_connected_agents"]
                else:
                    print(f"Unexpected message header: {header}")

            except ValueError as e:
                print(f"Value error in message processing: {e}")
            except KeyError as e:
                print(f"Key error in message processing: {e}")
            except Exception as e:
                print(f"Error while processing message: {e}")

            print("I finished msg_cb function")

            """Handle incoming messages."""
            while self.running:
                try:
                    msg = self.network.receive()
                    print(f"Raw msg : {msg}")
                    if not msg:
                        continue

                    header = msg.get("header")
                    print(f"Header of message : {header}")
                    if header == MOVE:
                        print(f"My header is Move")
                        self._update_position(msg)
                    elif header == BROADCAST_MSG:
                        print(f"My header is Broadcast")
                        self._handle_broadcast(msg)
                        print("I received BROADCAST message")
                    elif header == GET_NB_AGENTS:
                        print(f"My header is GET_NB_AGENTS")
                        self.nb_agent_expected = msg["nb_agents"]
                    elif header == GET_NB_CONNECTED_AGENTS:
                        print(f"My header is GET_NB_CONNECTED_AGENTS")
                        self.nb_agent_connected = msg["nb_connected_agents"]
                    else:
                        print(f"Unexpected message header: {header}")

                except ValueError as e:
                    print(f"Value error in message processing: {e}")
                except KeyError as e:
                    print(f"Key error in message processing: {e}")
                except Exception as e:
                    print(f"Error while processing message: {e}")

                print("I finished msg_cb function")

    def _update_position(self, msg):
        """Update agent's position and handle cell value changes."""
        print("I'm in update position function")
        self.x, self.y = msg["x"], msg["y"]
        self.prev_cell_val = self.cell_val
        self.cell_val = msg.get("cell_val", self.cell_val)
        print(f"Position updated to ({self.x}, {self.y}), Cell value: {self.cell_val}, Agent ID : {self.agent_id}")

        if self.cell_val != self.prev_cell_val:
            print(f"Cell value changed from {self.prev_cell_val} to {self.cell_val}")
        else:
            print("Cell value unchanged.")

        if self.cell_val == 1:
            self._handle_object_found()
        else:
            pass
        
        print("I finished update position function")

    def _handle_object_found(self):
        """Handle cases where an object is found."""
        print(f"Object found at position ({self.x}, {self.y})")
        self.network.send({"header": GET_ITEM_OWNER, "agent_id": self.agent_id})
        response = self.network.receive()

        if response["header"] == GET_ITEM_OWNER:
            owner = response.get("owner")
            obj_type = response.get("type")
            print(f"Owner : {owner} / Object : {obj_type} / Agent ID : {self.agent_id}")

            if owner is not None:
                print(f"Object belongs to agent {owner}")
                if obj_type == KEY_TYPE:
                    print("This is a key!")
                elif obj_type == BOX_TYPE:
                    print("This is a box!")

                if owner != self.agent_id:
                    self.network.send({
                        "header": BROADCAST_MSG,
                        "to_agent": owner,
                        "position": {"x": self.x, "y": self.y},
                        "msg": f"Object found at ({self.x}, {self.y})"
                    })
                    print(f"Coordinates sent to agent {owner}.")

    def _handle_broadcast(self, msg):
        """Handle broadcast messages."""
        print("Handling BROADCAST message...")
        target_position = msg.get("position")
        sender = msg.get("to_agent")

        if target_position and (sender is None or sender == self.agent_id):
            print(f"Received target position {target_position} for agent {self.agent_id} from {sender}.")
            self.move_to_position(target_position["x"], target_position["y"])
        else:
            print(f"Broadcast message ignored. Sender: {sender}, Position: {target_position}")

    def _wait_for_agents(self):
        """Wait for all agents to connect."""
        self.network.send({"header": GET_NB_AGENTS})
        while self.nb_agent_expected != self.nb_agent_connected:
            sleep(0.1)
        print("All agents are connected!")

    def calculate_direction(self, target_x, target_y):
        """Calculate the direction to move towards a target position."""
        if self.y < target_y:
            return 8 if self.x < target_x else 7 if self.x > target_x else 4
        elif self.y > target_y:
            return 6 if self.x < target_x else 5 if self.x > target_x else 3
        else:
            return 2 if self.x < target_x else 1 if self.x > target_x else 0

    def move_to_position(self, target_x, target_y):
        """Move the agent to a target position using the MOVE header to update position globally."""
        print(f"Starting movement to ({target_x}, {target_y}) from ({self.x}, {self.y})")
        
        while (self.x, self.y) != (target_x, target_y):
            # Calculate the direction and the next position
            direction = self.calculate_direction(target_x, target_y)
            dx, dy = self.moves[direction]
            new_x, new_y = self.x + dx, self.y + dy

            # Check if the move is within bounds
            if 0 <= new_x < self.w and 0 <= new_y < self.h:
                print(f"Moving to ({new_x}, {new_y}) in direction {direction}")
                    
                # Update the position locally
                self.x, self.y = new_x, new_y
                print(f"Local position updated to: ({self.x}, {self.y})")

                # Prepare the global update message
                global_update_msg = {
                    "header": MOVE,
                    "direction": direction,
                    "current_position": {"x": self.x, "y": self.y},  # Include updated position
                    "status": "Updating position in target reaching"  # Add status message
                }
                
                # Print the message before sending it
                print(f"Global update msg: {global_update_msg}")

                # Send MOVE message to update the position globally
                self.network.send(global_update_msg)

                # Add a small delay to allow other threads to process messages
                sleep(0.1)  # Short sleep to allow msg_cb to handle incoming messages
            else:
                print(f"Move out of bounds: ({new_x}, {new_y}). Movement halted.")
                break

            sleep(1)  # Simulate movement delay

        print(f"Reached target position: ({self.x}, {self.y}).")

    def explore_environment(self):
        """Randomly explore the environment."""
        while self.running:
            direction = random.randint(1, 8)
            dx, dy = self.moves[direction]
            target_x, target_y = self.x + dx, self.y + dy

            if 0 <= target_x < self.w and 0 <= target_y < self.h:
                self.move_to_position(target_x, target_y)
            else:
                print(f"Direction {direction} out of bounds.")

            sleep(1)


    #TODO: CREATE YOUR METHODS HERE...      
 
if __name__ == "__main__":
    from random import randint
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--server_ip", help="Ip address of the server", type=str, default="localhost")
    args = parser.parse_args()

    agent = Agent(args.server_ip)
    
    try:
        # Démarrer l'exploration automatique
        #agent.explore_environment()

        # Test de contrôle manuel (si nécessaire)
        while True:
            cmds = {"header": int(input("0 <-> Broadcast msg\n1 <-> Get data\n2 <-> Move\n3 <-> Get nb connected agents\n4 <-> Get nb agents\n5 <-> Get item owner\n"))}
            if cmds["header"] == BROADCAST_MSG:
                cmds["Msg type"] = int(input("1 <-> Key discovered\n2 <-> Box discovered\n3 <-> Completed\n"))
                cmds["position"] = (agent.x, agent.y)
                cmds["owner"] = randint(0, 3)  # TODO: specify the owner of the item
            elif cmds["header"] == MOVE:
                cmds["direction"] = int(input("0 <-> Stand\n1 <-> Left\n2 <-> Right\n3 <-> Up\n4 <-> Down\n5 <-> UL\n6 <-> UR\n7 <-> DL\n8 <-> DR\n"))
            agent.network.send(cmds)
    except KeyboardInterrupt:
        pass
