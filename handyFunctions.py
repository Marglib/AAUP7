import pandas as pd
import matplotlib.pyplot as plt

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



makeResultGraph([testBaseline, testNewData], "AverageDuration")
#print(getPercentageDataFrame(testBaseline,testNewData))
