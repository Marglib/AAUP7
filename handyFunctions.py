import pandas as pd
import matplotlib.pyplot as plt
import xml.etree.cElementTree as ET 
from xml.dom import minidom
import numpy as np
import random

testBaseline = pd.read_csv("Results/resultsMerge_start4063_end4083.csv", index_col = False)
testNewData = pd.read_csv("Results/resultsMerge_start4142_end4159.csv", index_col = False)



def getPercentageDataFrame(baseline, newData):
    # if baseline.columns != newData.columns:
    #     print("ERROR: DataFrames columns do not match!")
    #     return None
    if "Unnamed: 0" in baseline.columns:
        baseline = baseline.drop("Unnamed: 0", axis =1)
    if "Unnamed: 0" in newData.columns:
        newData = newData.drop("Unnamed: 0", axis =1)

    df = baseline
    for col in baseline.columns:
        df[col] = (100 - (newData[col] / baseline[col] * 100))

    return df


def makeResultGraph(listOfDataFrames, columnToPlot):
    myLines = []
    xValues = [0.5, 1, 1.25, 1.5, 1.75, 2 ,2.5]
    labels  = ["DTL", "RDTL", "STL", "RSTL"]
    i = 0
    for df in listOfDataFrames:
        if "Unnamed: 0" in df.columns:
            df = df.drop("Unnamed: 0", axis =1)

        if columnToPlot not in df.columns:
            print("Column to plot does not exist in one of the dataframes given")
            return
        print(df)
        df = df[:-2] # drop last two rows of dataframe
        print(df)
        myLines += plt.plot(xValues[:len(df[columnToPlot])], df[columnToPlot], label = labels[i])
        i += 1

    plt.xlabel("Cars per second")
    plt.ylabel(columnToPlot)
    labels = [l.get_label() for l in myLines]
    plt.legend(myLines, labels)

    plt.show()


#------------------------------CREATE rerouter ---------------------------------------------------
def findIncomingEdges(edgesToClose):
    dom = minidom.parse("SUMOfiles/MasterNetFile.net.xml")
    junctions = dom.getElementsByTagName("junction")
   
    result = ""
    for junc in  junctions:
        inclanes = junc.getAttribute("incLanes")
        if ':' in inclanes:
            pass
        else:
            inclanes = inclanes.split(' ')
            incEdges = []
            for lane in inclanes:
                incEdges.append(lane.split('_')[0])

            incEdges = np.unique(incEdges)
            incEdges = list(incEdges)
            for edge in edgesToClose:
                nodes = edge.split("-")
                edgeToCheck = nodes[1] + "-" + nodes[0]

                if edgeToCheck in incEdges:
                    incEdges.remove(edgeToCheck)
                    for IE in incEdges:
                        if result == "":
                            result = IE
                        else:
                            result = result + " " + IE
    return result

def generateRerouter():
    outXML = "rerouterExp4200.set.xml" #must have same name as outCSV
    outCSV = "rerouterExp4200.csv" #must have same name as outXML
    edgesToClose = ["n56-n11", "n11-n56", "n7-n56", "n56-n7","n6-n10","n30-n31"]
    minCloseLength = 100
    maxCloseLength = 500
    simLength = 2000

    
    root = ET.Element("rerouter", id= "generatedReRouter", edges=findIncomingEdges(edgesToClose))
    infoList = []
    for edge in edgesToClose:
        intervalLength = random.randrange(minCloseLength, maxCloseLength +1, 1)
        beginStep = random.randrange(0, simLength - intervalLength, 1)
        stopStep = beginStep + intervalLength
        intervalTag = ET.SubElement(root, "interval", begin = str(beginStep) , end= str(stopStep))
        ET.SubElement(intervalTag, "closingReroute",id=edge)

        d = {
            "edgeID" : edge,
            "beginStep" : beginStep,
            "stopStep" : stopStep
        }
        infoList.append(d)
    
    df = pd.DataFrame(infoList)
    df.to_csv(outCSV, index = False)
    tree = ET.ElementTree(root)
    tree.write(outXML)

generateRerouter()
#makeResultGraph([testBaseline, testNewData], "AverageDuration")
#print(getPercentageDataFrame(testBaseline,testNewData))
