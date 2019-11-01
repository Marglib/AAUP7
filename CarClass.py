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
import re

class car:
    def __init__(self,pid,listOfReroutes,currRouteIn):
        self.pid = pid
        self.listOfReroutes = listOfReroutes
        self.currRoute = [x for x in currRouteIn if x != -1]
    
    def update_route(self):
        for i in range(0,len(self.listOfReroutes)):
            if(self.listOfReroutes[i][1] == 0):
                newRoute = currRoute 
                newRoute[self.listOfReroutes[i][0]] = self.listOfReroutes[i][2]
                newRouteAsEdges = nodes_to_edges(newRoute,traci.vehicle.getRoadId(pid))
                try:
                    traci.vehicle.setRoute(newRouteAsEdges)
                except:
                    pass
            else:
                listOfReroutes[i][1] -= 1

    def nodes_to_edges(nodes, currEdge):
        edges = []
        edges.append(currEdge)
        for i in range(0, len(nodes)-1):
            edge = "n" + str(nodes[i]) + "-" + "n" + str(nodes[i + 1])
            edges.append(edge)
        return edges

    def to_string(self):
        print("pid:" + str(self.pid))
        print("reroutes:" + str(self.listOfReroutes))
        print("currRoute:" + str(self.currRoute))