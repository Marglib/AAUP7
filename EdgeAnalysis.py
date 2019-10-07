import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


df = pd.read_csv("edgeData.csv" , dtype={"traveltime": np.float64, "waitingTime": np.float64})
df = df.drop(["Unnamed: 0"], axis=1)

df["density"] = round(df["density"], 1)

df.groupby("density").mean().plot()
#plt.scatter(df.density, df.flow)

#print(normalDF[normalDF["traveltime"] > 200])
#normalGroup.plot()
#normalGroup.drop(["travelTime"],axis = 1).plot()
plt.show()
