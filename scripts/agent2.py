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
        self.discover, self.block, self.sent, self.previous_cell_val, self.flag, self.not_discover = 0, 0, 0, 0, 0, 0
        self.items = {}
        self.owner_value, self.type = None, None
        self.path_discover = []
        
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
            elif msg["header"] == GET_ITEM_OWNER:
                print(msg)
                if msg['owner']!=None:
                    self.owner_value = msg["owner"]
                    self.type = msg["type"]
            elif msg["header"] == BROADCAST_MSG:
                print(msg)
                x, y = msg["position"][0], msg["position"][1]
                object_type = msg["Msg type"]
                object_type_str = "Key" if object_type == 0 else "Chest"
                if object_type == 4:
                    object_type_str = "2 items"
                owner = msg["owner"]
                print(x,y,object_type_str, owner)
                self.give_objects(x,y,object_type_str, owner) #give the objects to the good robots
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
        print(f"Current position: ({self.x}, {self.y})")

        cmds = {"header": MOVE}

        def is_navigable(x, y):
            if 0 > x or x >= self.w or 0 > y or y >= self.h:
                return False
            if self.cell_val == 0.35 and (self.matrice[y, x] in [1]):
                return False
            return True

        # Verify if the target is accessible
        if not is_navigable(x_target, y_target):
            print(f"Target ({x_target}, {y_target}) is not reachable.")
            return

        visited = set()

        while self.x != x_target or self.y != y_target:
            visited.add((self.x, self.y))

            possible_moves = []

            # Cardinal moves
            if is_navigable(self.x, self.y - 1) and (self.x, self.y - 1) not in visited:
                possible_moves.append((UP, self.x, self.y - 1))
            if is_navigable(self.x, self.y + 1) and (self.x, self.y + 1) not in visited:
                possible_moves.append((DOWN, self.x, self.y + 1))
            if is_navigable(self.x - 1, self.y) and (self.x - 1, self.y) not in visited:
                possible_moves.append((LEFT, self.x - 1, self.y))
            if is_navigable(self.x + 1, self.y) and (self.x + 1, self.y) not in visited:
                possible_moves.append((RIGHT, self.x + 1, self.y))

            # Diagonal moves
            if is_navigable(self.x - 1, self.y - 1) and (self.x - 1, self.y - 1) not in visited:
                possible_moves.append((UP_LEFT, self.x - 1, self.y - 1))
            if is_navigable(self.x + 1, self.y - 1) and (self.x + 1, self.y - 1) not in visited:
                possible_moves.append((UP_RIGHT, self.x + 1, self.y - 1))
            if is_navigable(self.x - 1, self.y + 1) and (self.x - 1, self.y + 1) not in visited:
                possible_moves.append((DOWN_LEFT, self.x - 1, self.y + 1))
            if is_navigable(self.x + 1, self.y + 1) and (self.x + 1, self.y + 1) not in visited:
                possible_moves.append((DOWN_RIGHT, self.x + 1, self.y + 1))

            if possible_moves:
                # Select the best move based on distance to the target
                best_move = min(
                    possible_moves,
                    key=lambda move: abs(move[1] - x_target) + abs(move[2] - y_target)
                )
                cmds["direction"] = best_move[0]
                print(f"Robot {self.agent_id} moves {best_move[0]} to ({best_move[1]}, {best_move[2]}).")
                self.network.send(cmds)

                # Update the robot's position
                self.x, self.y = best_move[1], best_move[2]
            else:
                print(f"Robot {self.agent_id} is stuck at ({self.x}, {self.y}).")
                return

            time.sleep(0.1)

    def path_agent_0(self, division):
        if division==1:
            a = 2
        if division == 2:
            a = 1
        if self.agent_id == 0:
            descente = np.abs(a-int(self.h/division))-3
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
        if division==1:
            a = 2
        if division == 2:
            a = 1
        if self.agent_id == 1:
            descente = np.abs(a-int(self.h/division))-3
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
        if division==1:
            a = 2
        if division == 2:
            a = 1
        if self.agent_id == 2:
            descente = np.abs(a-int(self.h/division))-3
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
        if division==1:
            a = 2
        if division == 2:
            a = 1
        if self.agent_id == 3:
            descente = np.abs(a-int(self.h/division))-3
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
        #print("flag = ",Agent.global_flag)
        if self.path and self.discover == 0 and self.flag == 0:
            self.move_to(self.path[0][0], self.path[0][1])
            if [self.x, self.y] == [self.path[0][0], self.path[0][1]]:
                self.path.pop(0)

        if self.cell_val not in [0, 0.35] and self.matrice[self.x][self.y] == 100 and self.block == 0 and self.not_discover == 0:
            self.previous_cell_val=self.cell_val
            self.discover = 1

        self.matrice[self.x][self.y] = self.cell_val

        if self.discover == 1:
            self.cell_detection()
        
        if self.not_discover == 1 and self.flag == 0 and self.path == []:
            print("Every boxes have been opened")
            time.sleep(5)

        if self.flag == 1: #if every object has been found
            #time.sleep(0.5)
            self.path = []
            Key = self.items["Key"]
            Chest = self.items["Chest"]
            self.path.append(Key)
            self.path.append(Chest)
            if "test" in self.items: #if the robot already discovered its key
                self.path = []
                self.path.append(Chest)
            #print("PATH = ",self.path)
            self.items = {}
            self.flag = 0   
            self.not_discover = 1
 
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
                self.network.send({"header": GET_ITEM_OWNER})
                time.sleep(0.5) #letting the time for the network to send the msg because I had dome trouble with this
                object_type_str = "Key" if self.type == 0 else "Chest"
                if self.owner_value == self.agent_id:
                    self.items[object_type_str] = [self.x, self.y]
                    print(self.items)
                if self.owner_value == self.agent_id and object_type_str == "Key":
                    self.items["test"] = 1 #if the key owned by the robot x has been found by the robot x
                else:
                    cmds = {"header": BROADCAST_MSG}
                    cmds["Msg type"] = self.type
                    cmds["position"] = (self.x, self.y)
                    cmds["owner"] = self.owner_value
                    self.network.send(cmds)
                self.bounding(self.x, self.y, object_type_str)
                self.previous_cell_val=0
                self.block = 0
                self.discover = 0
                #self.check_all_objects_found()
                return

    def give_objects(self, x, y, object_type, owner):
        if self.agent_id == owner:
            self.items[object_type] = [x,y] 
            print(self.items)
        if object_type == "2 items":
            self.items[owner] = 1
            print(self.items)

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
        while self.nb_agent_connected != self.nb_agent_expected: #Waiting for all agents to connect before launching them
            cmds = {"header": GET_NB_CONNECTED_AGENTS}
            self.network.send(cmds)
            #print("Waiting for agents", self.nb_agent_connected , self.nb_agent_expected)
            time.sleep(0.2)
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

    def check_all_objects_found(self):
        if ("Chest" in self.items and "Key" in self.items) and self.sent == 0:
            cmds = {"header": BROADCAST_MSG}
            cmds["Msg type"] = 4 # To knwo when a robot has the coordiantes of its two items
            cmds["position"] = (100,100) #we don't need it
            cmds["owner"] = self.agent_id
            self.network.send(cmds)
            time.sleep(0.5)
            self.sent = 1 #to send it only 1 time
            self.items[self.agent_id] = 1 #adding the "1" in the dictionnary so we can know that the robot has the coordinates of the 2 items
            print(self.items)
        var = 0
        if self.flag == 0:
            for i in range(self.nb_agent_expected):
                if i in self.items:
                    var += 1
            #print("VAR = ", var)
            if var == self.nb_agent_expected:
                #time.sleep(0.5)
                self.flag = 1
        #print("FLAG = ",self.flag)


if __name__ == "__main__":
    from random import randint
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--server_ip", help="Ip address of the server", type=str, default="localhost")
    args = parser.parse_args()
    agent = Agent(args.server_ip)

    agent.launch()
    #agent.path_agent_0(2)
    try:  
        while True:
            agent.move()
            agent.check_all_objects_found()

    except KeyboardInterrupt:
        pass
# it is always the same location of the agent first location



