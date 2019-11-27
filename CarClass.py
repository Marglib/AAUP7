import math
import os
import sys
import random

try:
     tools = "/user/d704e19/sumo/tools" 
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
        self.currRoute = currRouteIn
        self.rerouted = False
<<<<<<< HEAD
        self.routeChange = 0   
 
=======
        self.routeChange = 0 #Used to check the difference between the currroute and the newroute
    
>>>>>>> UppaalModel
    def update_route(self):
        newRoute = self.currRoute 

        for i in range(0,len(self.listOfReroutes)):
            newRoute[self.listOfReroutes[i][0]] = self.listOfReroutes[i][1]
        newRoute = [x for x in newRoute if x != -1]
        currRouteLen = len([x for x in self.currRoute if x != -1])
        
        newRouteAsEdges = self.nodes_to_edges(newRoute[traci.vehicle.getRouteIndex(self.pid):])
        try:
            if self.decision(0.9):
                traci.vehicle.setRoute(self.pid,newRouteAsEdges)
                print("new route: " + str(newRouteAsEdges))
            else:
                print("The car chose not to follow the suggested route")
            self.rerouted = True
            self.routeChange = abs(len(newRoute) - currRouteLen)
        except:
            print("Could not reroute car " + str(self.pid) + "with route " + str(newRouteAsEdges))      

    def nodes_to_edges(self, nodes):
        edges = []
        for i in range(0, len(nodes)-1):
            edge = "n" + str(nodes[i]) + "-" + "n" + str(nodes[i + 1])
            edges.append(edge)
        return edges
    
    def decision(self,probability):
        return random.random() < probability

    def to_string(self):
        print("pid:" + str(self.pid))
        print("reroutes:" + str(self.listOfReroutes))
        print("currRoute:" + str(self.currRoute))

    def kill(self):
        del self
