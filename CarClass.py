import math
import os
import sys

try:
     tools = os.path.join(os.environ['SUMO_HOME'], "tools")
     sys.path.append(tools)
except:   
     sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary
import traci
import sumolib

class car:
    def __init__(self,pid,listOfReroutes,currRoute):
        self.pid = pid
        self.listOfReroutes = listOfReroutes
        self.currRoute = currRoute
    
    def update_route(self):
        for i in range(0,len(self.listOfReroutes)):
            if(self.listOfReroutes[i][1] == 0):
                newRoute = currRoute 
                newRoute[self.listOfReroutes[i][0]] = self.listOfReroutes[i][2]
                print(newRoute)
                #traci.vehicle.setRoute(...)
            else:
                listOfReroutes[i][1] -= 1

    def node_to_edges(nodes, currEdge):
        edges = []
        edges.append(currEdge)
        for i in range(0, len(nodes)-1):
            edge = str(nodes[i]) + "-" + str(nodes[i + 1])
            edges.append(edge)
        return edges
