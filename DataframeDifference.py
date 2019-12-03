import os
import sys
import random
import optparse
import subprocess
import math
import pandas as pd

def dataframeDiff(df1, df2):
    resultsdf = df1.set_index('Unnamed: 0').subtract(df2.set_index('Unnamed: 0'), fill_value=0)

    resultsdf = round(resultsdf, 3)
    resultsdf.to_csv('results/diff_smartroute_onlysmartTL.csv')

def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--df1", type="string",
                         dest="df1", default="", help="put first file dataframe")
    optParser.add_option("--df2", type="string",
                         dest="df2", default="", help="put second file dataframe")
    options, args = optParser.parse_args()
    return options

if __name__ == "__main__":
    options = get_options()

    dataframe1 = pd.read_csv(options.df1, index_col=None, header=0)
    dataframe2 = pd.read_csv(options.df2, index_col=None, header=0)


    dataframeDiff(dataframe1, dataframe2)