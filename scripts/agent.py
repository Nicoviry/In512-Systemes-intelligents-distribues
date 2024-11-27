__author__ = "Aybuke Ozturk Suri, Johvany Gustave"
__copyright__ = "Copyright 2023, IN512, IPSA 2024"
__credits__ = ["Aybuke Ozturk Suri", "Johvany Gustave"]
__license__ = "Apache License 2.0"
__version__ = "1.0.0"

from network import Network
from my_constants import *

from threading import Thread
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

    def msg_cb(self): 
        """ Method used to handle incoming messages """
        while self.running:
            try:
                msg = self.network.receive()

                if not msg:
                    continue  # Si le message est vide ou None, continue

                self.msg = msg

                # Si le message contient un header MOVE
                if msg["header"] == MOVE:
                    self.x, self.y = msg["x"], msg["y"]
                    self.prev_cell_val = self.cell_val  # store the previous cell value before updating
                    self.cell_val = msg.get("cell_val", self.cell_val)  # Update the cell value if available in the message
                    print(f"New position: ({self.x}, {self.y}), Cell value: {self.cell_val}")

                    # Compare previous and current cell values
                    if self.cell_val != self.prev_cell_val:
                        print(f"Cell value has changed! Previous: {self.prev_cell_val}, Current: {self.cell_val}")
                    else:
                        print("Cell value is the same as before.")

                    if self.cell_val == 1:
                        print("Object found at position:", (self.x, self.y))
                        self.network.send({"header": GET_ITEM_OWNER, "agent_id": self.agent_id})
                        item_owner_response = self.network.receive()  # Wait for the server's response
                        
                        if item_owner_response["header"] == GET_ITEM_OWNER:
                            item_owner = item_owner_response.get("owner", None)
                            item_type = item_owner_response.get("type", None)

                            if item_owner is not None:
                                print(f"Object belongs to agent with ID: {item_owner}")
                                if item_type == KEY_TYPE:
                                    print("This is a key!")
                                elif item_type == BOX_TYPE:
                                    print("This is a box!")

                                if item_owner != self.agent_id:
                                    self.network.send({
                                        "header": BROADCAST_MSG,
                                        "to_agent": item_owner,
                                        "position": {"x": self.x, "y": self.y},
                                        "msg": f"Object found at ({self.x}, {self.y})"
                                    })
                                    print(f"Coordinates of the object sent to agent {item_owner}.")

                elif msg["header"] == BROADCAST_MSG:
                    # Handle broadcast messages for received positions
                    target_position = msg.get("position")
                    sender = msg.get("to_agent")
                    
                    if target_position and sender == self.agent_id:
                        print(f"Received target position {target_position} from agent {msg.get('from_agent')}.")
                        
                        # Interrompre l'exploration et se diriger vers la cible
                        self.running = False  # Stop the random exploration loop
                        self.move_to_position(target_position["x"], target_position["y"])
                        self.running = True  # Resume exploration after reaching the target
                        print('Arrived')

                # Pour les autres messages non gérés
                elif msg["header"] == GET_NB_AGENTS:
                    self.nb_agent_expected = msg["nb_agents"]
                elif msg["header"] == GET_NB_CONNECTED_AGENTS:
                    self.nb_agent_connected = msg["nb_connected_agents"]

                print("hellooo: ", msg)
                print("agent_id ", self.agent_id)
            
            except Exception as e:
                print(f"Error while processing the message: {e}")
                continue  # Si une erreur se produit, passez au message suivant

    def wait_for_connected_agent(self):
        self.network.send({"header": GET_NB_AGENTS})
        check_conn_agent = True
        while check_conn_agent:
            if self.nb_agent_expected == self.nb_agent_connected:
                print("Both agents are connected!")
                check_conn_agent = False

    def move_to_position(self, target_x, target_y):
        """ Move the robot automatically to the target position (considering map bounds). """
        print(f"Moving to position: ({target_x}, {target_y})")

        while (self.x, self.y) != (target_x, target_y):
            print(f"Current position: ({self.x}, {self.y})")  # Log current position

            direction = None
            if self.y < target_y:  # Move down
                if self.x < target_x:  # Move diagonally down-right
                    direction = 8
                elif self.x > target_x:  # Move diagonally down-left
                    direction = 7
                else:  # Move straight down
                    direction = 4
            elif self.y > target_y:  # Move up
                if self.x < target_x:  # Move diagonally up-right
                    direction = 6
                elif self.x > target_x:  # Move diagonally up-left
                    direction = 5
                else:  # Move straight up
                    direction = 3
            else:  # Same row
                if self.x < target_x:  # Move right
                    direction = 2
                elif self.x > target_x:  # Move left
                    direction = 1

            # Get the proposed new position
            dx, dy = self.moves[direction] if direction else (0, 0)
            new_x, new_y = self.x + dx, self.y + dy

            # Check if the move is within bounds
            if 0 <= new_x < self.w and 0 <= new_y < self.h:
                print(f"Moving in direction {direction}: New position will be ({new_x}, {new_y})")
                self.network.send({"header": MOVE, "direction": direction})
                # After the move, update the agent's position
                self.x, self.y = new_x, new_y  # Update position manually
            else:
                print(f"Attempted move out of bounds: ({new_x}, {new_y}). Skipping move.")

            # Wait for position update
            sleep(0.5)
            print(self.msg["header"])

    def explore_environment(self):
        """ Agent starts exploring the environment randomly or based on cell values. """
        while self.running:
            # Si aucune direction n'est définie (début) ou si un changement de direction est requis
            if self.current_direction is None:
                self.current_direction = random.randint(1, 8)  # Choisir une direction initiale aléatoire

            dx, dy = self.moves[self.current_direction]  # Obtenir les déplacements correspondants à la direction
            target_x = self.x + dx
            target_y = self.y + dy

            # Vérifier si le mouvement proposé est à l'extérieur des limites de la carte
            if not (0 <= target_x < self.w and 0 <= target_y < self.h):
                print(f"Out of bounds! Changing direction. Current: ({self.x}, {self.y}), Target: ({target_x}, {target_y})")
                self.current_direction = random.randint(1, 8)  # Rechoisir une direction aléatoire
                continue  # Passer à la prochaine itération

            # Si la valeur de la cellule actuelle est supérieure à la précédente, continuer dans la même direction
            if self.cell_val > self.prev_cell_val:
                print(f"Cell value increased. Continuing in direction {self.current_direction}.")
            else:
                # Sinon, choisir une nouvelle direction aléatoire
                self.current_direction = random.randint(1, 8)
                print(f"Cell value did not increase. Changing to direction {self.current_direction}.")

            # Déplacer le robot vers la nouvelle position
            print(f"Moving to position: ({target_x}, {target_y}) in direction {self.current_direction}.")
            self.move_to_position(target_x, target_y)

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
