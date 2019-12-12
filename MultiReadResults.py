import os
import sys
import random
import optparse
import subprocess
import math
import pandas as pd

from ReadResultFile import generate_results

destFileString = ""

def generate_multi_results():
    resultFiles = []
    startID = 4284
    endID = 4304
    for i in range(startID,endID+1):
        resultDestFile = "results/Results_" + str(i)+ ".csv"
        resultFiles.append(resultDestFile)
        generate_results(resultDestFile, "results/tripinfo" + str(i) + ".xml", "results/queueinfo" + str(i) + ".xml", "results/emission" + str(i) + ".xml", i) #emission file empty for now
    
    return resultFiles, startID, endID

def get_stats(resultFiles, startID, endID):
    li = []
    for filename in resultFiles:
        df = pd.read_csv(filename, index_col=None, header=0)
        li.append(df)

    frame = pd.concat(li, axis=0, ignore_index=True)
    #Group every third
    frame = frame.groupby(frame.index // 3)

    results = []
    for grp in frame.groups:
        results.append(frame.get_group(grp).mean())

    resultFrame = pd.DataFrame(results)
    resultFrame.loc['mean'] = resultFrame.mean()
    resultFrame.loc['max'] = resultFrame.max()
    #1 significant digit
    resultFrame = round(resultFrame,1)
    
    destFileString = "results/resultsMerge_start" + str(startID) + "_end" + str(endID)+ ".csv"
    resultFrame.to_csv(destFileString)

    return resultFrame, destFileString

def prep_table(frame, destFileString):

    #Drops useless columns and rows
    frame = frame.drop(['ExperimentID', 'AverageQueueLengthExp', 'maxQueueLengthExp','95thPercentileLengthExp'], axis=1)
    frame = frame.drop(['mean', 'max'], axis=0)

    #Rename to what we use in the paper
    frame = frame.rename(columns={"AverageDuration" : "ATT", "AverageTimeLoss":"AD", "AverageWaitingTime":"AWT", "AverageQueueLength":"AQL", "maxDuration":"MTT", "maxTimeLoss":"MD", "maxWaitingTime":"MWT", "maxQueueLength":"MQL","95thPercentileLength":"95%"})
    
    #Comment in if you want it in a csv file
    #frame.to_csv(os.path.splitext(destFileString)[0] + "_latexrdy.csv")

    return frame

def to_latex_table(frame):
    latexTable = frame.to_latex(index=True)

    #remove lines
    latexTable = latexTable.replace("\\midrule", "")
    latexTable = latexTable.replace("\\toprule", "")
    latexTable = latexTable.replace("\\bottomrule", "")
    #Add title row
    latexTable = latexTable.replace("\\begin{tabular}{lrrrrrrrrr}", "\\begin{tabular}{lrrrrrrrrr}\n\\multicolumn{10}{c}{\\textbf{Title}}\\\\ \\hline")

    #Make column names bold
    latexTable = latexTable.replace("ATT", "\\textbf{ATT}")
    latexTable = latexTable.replace("AD", "\\textbf{AD}")
    latexTable = latexTable.replace("AWT", "\\textbf{AWT}")
    latexTable = latexTable.replace("AQL", "\\textbf{AQL}")
    latexTable = latexTable.replace("MTT", "\\textbf{MTT}")
    latexTable = latexTable.replace("MD", "\\textbf{MD}")
    latexTable = latexTable.replace("MWT", "\\textbf{MWT}")
    latexTable = latexTable.replace("MQL", "\\textbf{MQL}")
    latexTable = latexTable.replace("95\\%", "\\textbf{95\\%}")
    latexTable = latexTable.replace("\\end{tabular}", "\\hline\\end{tabular}")

    #add begin{table} and end{table} + caption and label
    latexTable = "\\begin{table}[H]\n\\centering\n" + latexTable + "\n\\caption{Caption}\n\\label{tab:my_table}\n\\end{table}"

    print(latexTable)

    



if __name__ == "__main__":
    resultFiles, startID, endID = generate_multi_results()
    frame, destFileString = get_stats(resultFiles, startID, endID)
    preppedFrame = prep_table(frame, destFileString)
    to_latex_table(preppedFrame)
