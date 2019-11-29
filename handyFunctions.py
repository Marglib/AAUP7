import pandas as pd

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



