__author__ = "Aybuke Ozturk Suri, Johvany Gustave"
__copyright__ = "Copyright 2023, IN512, IPSA 2024"
__credits__ = ["Aybuke Ozturk Suri", "Johvany Gustave"]
__license__ = "Apache License 2.0"
__version__ = "1.0.0"

from network import Network
from my_constants import *
import time
from threading import Thread
import numpy as np
from time import sleep
from random import randint, choice
import matplotlib.pyplot as plt



class Agent:
    """ Class that implements the behaviour of each agent based on their perception and communication with other agents """
    def __init__(self, server_ip):
        #TODO: DEINE YOUR ATTRIBUTES HERE
        self.path = []
        self.discover = 0
        self.block = 0
        self.path_discover = []
        self.robot_data = {0: {}, 1: {}, 2: {}, 3: {}}
        #DO NOT TOUCH THE FOLLOWING INSTRUCTIONS
        self.network = Network(server_ip=server_ip)
        self.agent_id = self.network.id
        self.running = True
        self.network.send({"header": GET_DATA})
        self.msg = {}
        env_conf = self.network.receive()
        self.nb_agent_expected = 0
        self.nb_agent_connected = 0
        self.x, self.y = env_conf["x"], env_conf["y"]   #initial agent position
        self.w, self.h = env_conf["w"], env_conf["h"]   #environment dimensions
        self.matrice = np.ones((self.w, self.h))*100
        self.cell_val = env_conf["cell_val"] #value of the cell the agent is located in
        self.previous_cell_val = 0
        print(self.cell_val)
        Thread(target=self.msg_cb, daemon=True).start()
        print("hello")
        self.wait_for_connected_agent()

        
    def msg_cb(self): 
        """ Method used to handle incoming messages """
        while self.running:
            msg = self.network.receive()
            self.msg = msg
            if msg["header"] == MOVE:
                self.x, self.y =  msg["x"], msg["y"]
                self.prev_cell_val = self.cell_val 
                self.cell_val = msg.get("cell_val", self.cell_val)
                print(self.x, self.y)
            elif msg["header"] == GET_NB_AGENTS:
                self.nb_agent_expected = msg["nb_agents"]
            elif msg["header"] == GET_NB_CONNECTED_AGENTS:
                self.nb_agent_connected = msg["nb_connected_agents"]

            print("hellooo: ", msg)
            print("agent_id ", self.agent_id)
            

    def wait_for_connected_agent(self):
        self.network.send({"header": GET_NB_AGENTS})
        check_conn_agent = True
        while check_conn_agent:
            if self.nb_agent_expected == self.nb_agent_connected:
                print("both connected!")
                check_conn_agent = False
                 
    #TODO: CREATE YOUR METHODS HERE...
    
    def move_to(self, x_target, y_target):
        #print(f"Robot {self.agent_id} moving to target ({x_target}, {y_target}).")
        print(f"Current position: ({self.x}, {self.y})")
        #print(f"Environment matrix:\n{self.matrice}")

        cmds = {"header": MOVE}

        def is_navigable(x, y):
            if 0 > x or x >= self.w and 0 > y or y>= self.h:
                #print(y, self.h)
                #print("1")
                return False
            if self.cell_val == 0.35 and (self.matrice[y, x] in [1]):
                #print("2")
                return False
            return True

        # Vérifie si la cible est accessible
        if not is_navigable(x_target, y_target):
            print(f"Target ({x_target}, {y_target}) is not reachable.")
            return

        visited = set()

        while self.x != x_target or self.y != y_target:
            visited.add((self.x, self.y))

            possible_moves = []
            if is_navigable(self.x, self.y - 1) and (self.x, self.y - 1) not in visited:
                possible_moves.append((UP, self.x, self.y - 1))
            if is_navigable(self.x, self.y + 1) and (self.x, self.y + 1) not in visited:
                possible_moves.append((DOWN, self.x, self.y + 1))
            if is_navigable(self.x - 1, self.y) and (self.x - 1, self.y) not in visited:
                possible_moves.append((LEFT, self.x - 1, self.y))
            if is_navigable(self.x + 1, self.y) and (self.x + 1, self.y) not in visited:
                possible_moves.append((RIGHT, self.x + 1, self.y))

            if possible_moves:
                best_move = min(
                    possible_moves,
                    key=lambda move: abs(move[1] - x_target) + abs(move[2] - y_target)
                )
                cmds["direction"] = best_move[0]
                print(f"Robot {self.agent_id} moves {best_move[0]} to ({best_move[1]}, {best_move[2]}).")
                self.network.send(cmds)
            else:
                print(f"Robot {self.agent_id} is stuck at ({self.x}, {self.y}).")
                return

            time.sleep(0.1)

    def path_agent_0(self, division):
        if self.agent_id == 0:
            descente = np.abs(2-int(self.h/division))-3
            self.path.append([2,2])
            while(self.path[-1][0]<((self.w/2)+2)):
                for i in range(descente):
                    self.path.append([self.path[-1][0],self.path[-1][1]+1]) #Down
                    if self.cell_val != 0:
                        self.discover = 1
                    if (self.path[-1][0]>((self.w/2))):
                        return 0
                for i in range(5):
                    self.path.append([self.path[-1][0]+1,self.path[-1][1]]) #Right
                    if (self.path[-1][0]>((self.w/2))):
                        return 0
                for i in range(descente):
                    self.path.append([self.path[-1][0],self.path[-1][1]-1]) #Up
                    if self.cell_val != 0:
                        self.discover = 1
                    if (self.path[-1][0]>((self.w/2))):
                        return 0
                for i in range(5):
                    self.path.append([self.path[-1][0]+1,self.path[-1][1]]) #Right
                    if self.cell_val != 0:
                        self.discover = 1
                    if (self.path[-1][0]>((self.w/2))):
                        return 0
        print(self.path)

    def path_agent_1(self, division):
        if self.agent_id == 1:
            descente = np.abs(2-int(self.h/division))-3
            self.path.append([self.w-3,2])
            while(self.path[-1][0]>((self.w/2)-2)):
                for i in range(descente):
                    self.path.append([self.path[-1][0],self.path[-1][1]+1]) #Down
                    if (self.path[-1][0]<((self.w/2))):
                        return 0
                for i in range(5):
                    self.path.append([self.path[-1][0]-1,self.path[-1][1]]) #Left
                    if (self.path[-1][0]<((self.w/2))):
                        return 0
                for i in range(descente):
                    self.path.append([self.path[-1][0],self.path[-1][1]-1]) #Up
                    if (self.path[-1][0]<((self.w/2))):
                        return 0
                for i in range(5):
                    self.path.append([self.path[-1][0]-1,self.path[-1][1]]) #Left
                    if (self.path[-1][0]<((self.w/2))):
                        return 0
        print(self.path)

    def path_agent_2(self, division):
        if self.agent_id == 2:
            descente = np.abs(2-int(self.h/division))-3
            self.path.append([2,self.h-3])
            while(self.path[-1][0]<((self.w/2)-2)):
                for i in range(descente):
                    self.path.append([self.path[-1][0],self.path[-1][1]-1]) #Up
                    if (self.path[-1][0]>((self.w/2))):
                        return 0
                for i in range(5):
                    self.path.append([self.path[-1][0]+1,self.path[-1][1]]) #Right
                    if (self.path[-1][0]>((self.w/2))):
                        return 0
                for i in range(descente):
                    self.path.append([self.path[-1][0],self.path[-1][1]+1]) #Down
                    if (self.path[-1][0]>((self.w/2))):
                        return 0
                for i in range(5):
                    self.path.append([self.path[-1][0]+1,self.path[-1][1]]) #Right
                    if (self.path[-1][0]>((self.w/2))):
                        return 0
        print(self.path)

    def path_agent_3(self, division):
        if self.agent_id == 3:
            descente = np.abs(2-int(self.h/division))-3
            self.path.append([self.w-3,self.h-3])
            while(self.path[-1][0]>((self.w/2)-2)):
                for i in range(descente):
                    self.path.append([self.path[-1][0],self.path[-1][1]-1]) #Up
                    if (self.path[-1][0]<((self.w/2))):
                        return 0
                for i in range(5):
                    self.path.append([self.path[-1][0]-1,self.path[-1][1]]) #Left
                    if (self.path[-1][0]<((self.w/2))):
                        return 0
                for i in range(descente):
                    self.path.append([self.path[-1][0],self.path[-1][1]+1]) #Down
                    if (self.path[-1][0]<((self.w/2))):
                        return 0
                for i in range(5):
                    self.path.append([self.path[-1][0]-1,self.path[-1][1]]) #Left
                    if (self.path[-1][0]<((self.w/2))):
                        return 0
        print(self.path)

    
    def move(self):
        print(self.path_discover)

        if self.path and self.discover == 0:
            self.move_to(self.path[0][0], self.path[0][1])
            if [self.x, self.y] == [self.path[0][0], self.path[0][1]]:
                self.path.pop(0)

        if self.cell_val not in [0, 0.35] and self.matrice[self.x][self.y] == 100 and self.block == 0:
            self.previous_cell_val=self.cell_val
            self.discover = 1

        self.matrice[self.x][self.y] = self.cell_val

        if self.discover == 1:
            self.cell_detection()

        
    def cell_detection(self):
        self.block = 1
        directions = [
            [self.x + 1, self.y], [self.x + 1, self.y + 1], [self.x, self.y + 1],
            [self.x - 1, self.y + 1], [self.x - 1, self.y], [self.x - 1, self.y - 1],
            [self.x, self.y - 1], [self.x + 1, self.y - 1]
        ]

        for direction in directions:
            x, y = direction

            if 0 <= x < self.w and 0 <= y < self.h:
                self.move_to(x, y)
                self.matrice[x][y] = self.cell_val
                print(f"PREV: {self.previous_cell_val} - ACTUAL: {self.cell_val}")

                if self.cell_val > self.previous_cell_val:
                    self.previous_cell_val = self.cell_val
                    print(f"New highest value detected: {self.previous_cell_val}")
                    self.cell_detection2()
                    return

    def cell_detection2(self):
        directions = [
            [self.x + 1, self.y], [self.x + 1, self.y + 1], [self.x, self.y + 1],
            [self.x - 1, self.y + 1], [self.x - 1, self.y], [self.x - 1, self.y - 1],
            [self.x, self.y - 1], [self.x + 1, self.y - 1]
        ]
        for direction in directions:
            if self.cell_val == 1:
                print("Found object!")
                self.discover = 0
                owner, object_type = self.owner()
                #print("##### owner : ", owner, " Type : ", object_type)
                object_type_str = "Key" if object_type == 0 else "Chest"
                self.bounding(self.x, self.y, object_type_str)
                self.previous_cell_val=0
                self.block = 0
                print(self.x, self.y, object_type_str, owner)
                #self.give_objects(self.x, self.y, object_type_str, owner)
                return

    def give_objects(self, x, y, object_type, owner):
      
        # Assign the object to the robot
        self.robot_data[owner][object_type] = [x, y]
        
        # Print the current state of the robot data
        for robot_id, objects in self.robot_data.items():
            print(f"Robot {robot_id + 1}: {objects}")



    def plot_matrix(self):
        # Assuming self.matrice is a 2D array (list of lists)
        matrix = np.array(self.matrice)  # Convert the matrix to a numpy array for easy plotting
        
        plt.imshow(matrix, cmap='viridis', interpolation='nearest')  # You can change the colormap as needed
        plt.colorbar()  # Show color scale bar
        plt.title("Matrix Visualization")  # Title of the plot
        plt.show()  # Display the plot
                        
    def bounding(self, object_x, object_y, object_type):
        """
        Modify the matrix around a discovered object (chest or key) to assign appropriate bounding values,
        handling edge cases such as corners and edges.

        Args:
            object_x (int): The x-coordinate of the object.
            object_y (int): The y-coordinate of the object.
            object_type (str): The type of object ("chest" or "key").
        """
        # Define bounding patterns for different objects
        bounding_patterns = {
            "Chest": {
                0.6: [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)],  # Immediate neighbors
                0.3: [(-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2), (-2, -1), (2, -1), (-2, 0), (2, 0), (-2, 1), ( 2, 1), (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2)],  # Diagonal neighbors
                1: [(0, 0)],  # The chest itself
            },
            "Key": {
                0.5: [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)],  # Immediate neighbors
                0.25: [(-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2), (-2, -1), (2, -1), (-2, 0), (2, 0), (-2, 1), ( 2, 1), (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2)],  # Diagonal neighbors
                1: [(0, 0)],  # The key itself
            },
        }

        # Select the pattern based on the object type
        if object_type not in bounding_patterns:
            raise ValueError(f"Unknown object type: {object_type}")

        pattern = bounding_patterns[object_type]

        # Apply the pattern to the matrix
        for value, offsets in pattern.items():
            for dx, dy in offsets:
                neighbor_x, neighbor_y = object_x + dx, object_y + dy
                # Check if the neighbor is within matrix bounds
                if 0 <= neighbor_x < len(self.matrice) and 0 <= neighbor_y < len(self.matrice[0]):
                    self.matrice[neighbor_x][neighbor_y] = value

    def launch(self):#setting up the robots depending on the number of robots expected
        if self.nb_agent_expected == 2:
            self.path_agent_0(1)
            self.path_agent_1(1)
        if self.nb_agent_expected == 3:
            self.path_agent_0(2)
            self.path_agent_1(1)
            self.path_agent_2(2)
        if self.nb_agent_expected == 4:
            self.path_agent_0(2)
            self.path_agent_1(2)
            self.path_agent_2(2)
            self.path_agent_3(2)

    def owner(self):
        cmds = {"header": GET_ITEM_OWNER}
        response = self.network.send(cmds)  # Send request to server
        if isinstance(response, dict) and 'owner' in response and 'type' in response:
            return response['owner'], response['type']  # Return both owner and type
        return None, None  # Fallback if owner or type not found



if __name__ == "__main__":
    from random import randint
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--server_ip", help="Ip address of the server", type=str, default="localhost")
    args = parser.parse_args()
    
    agent = Agent(args.server_ip)

    agent.launch()
    #agent.path_agent_0(2)
    try:    #Manual control test0
        while True:
            agent.move()
            
            """cmds = {"header": int(input("0 <-> Broadcast msg\n1 <-> Get data\n2 <-> Move\n3 <-> Get nb connected agents\n4 <-> Get nb agents\n5 <-> Get item owner\n"))}
            if cmds["header"] == BROADCAST_MSG:
                cmds["Msg type"] = int(input("1 <-> Key discovered\n2 <-> Box discovered\n3 <-> Completed\n"))
                cmds["position"] = (agent.x, agent.y)
                cmds["owner"] = randint(0,3) # TODO: specify the owner of the item
            elif cmds["header"] == MOVE:
                cmds["direction"] = int(input("0 <-> Stand\n1 <-> Left\n2 <-> Right\n3 <-> Up\n4 <-> Down\n5 <-> UL\n6 <-> UR\n7 <-> DL\n8 <-> DR\n"))
            """

    except KeyboardInterrupt:
        pass
# it is always the same location of the agent first location



