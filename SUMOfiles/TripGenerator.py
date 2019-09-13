from xml.dom import minidom
import os
import sys
import random

argumentList = sys.argv
if(len(argumentList) != 3):
    sys.exit("Please give 2 arguements: numberOfTrips and fileName.")


try:
    numberOfTrips = int(argumentList[1])
    fileName = argumentList[2]
except ValueError as verr:
    sys.exit("Value has to be an integers")
except Exception as ex:
    sys.exit("Stuff went wrong it seems")

edgeFile = 'EdgeFile.edg.xml'
routeFile = 'RouteFileTemplate.rou.xml'


fromNodes = []
toNodes = []
numberOfTrips = 50
# parse an xml file by name
mydoc = minidom.parse(edgeFile)

edges = mydoc.getElementsByTagName('edge')

for elem in edges:
    fromNodes.append(elem.attributes['from'].value)
    toNodes.append(elem.attributes['to'].value)

def removeIntersectionNodes(listOfNodes):
    return [i for i in listOfNodes if listOfNodes.count(i) <= 1]

fromNodes = removeIntersectionNodes(fromNodes)
toNodes = removeIntersectionNodes(toNodes)

fromEdges = []
toEdges = []

for edge in edges:
    if(edge.attributes['from'].value in fromNodes):
        fromEdges.append(edge.attributes['id'].value)
    if(edge.attributes['to'].value in fromNodes):
        toEdges.append(edge.attributes['id'].value)

print("well done friend")





fo = open(routeFile, "r+")
routeFileAsString = fo.read()
fo.close()

toReplace = "//TRIPS_PLACEHOLDER"
value = ""
for i in range(0, numberOfTrips):
    value += "<trip id=\"" + str(i) + "\" depart=\"" + str(i) + "\" from=\"" + random.choice(fromEdges) + "\" to=\"" + random.choice(toEdges) + "\"/>\n"

routeFileAsString = str.replace(routeFileAsString, toReplace, value, 1)

modelName = fileName + '.rou.xml'
text_file = open(modelName, "w")
text_file.write(routeFileAsString)
text_file.close()




