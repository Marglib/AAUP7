import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression

# -------------------------- read and concatinate data ----------------------------------
df1 = pd.read_csv("allEdges1000Trips.csv" , dtype={"travelTime": np.float64, "waitingTime": np.float64})
df2 = pd.read_csv("allEdges2000Trips.csv" , dtype={"travelTime": np.float64, "waitingTime": np.float64})
df3 = pd.read_csv("allEdges3000Trips.csv" , dtype={"travelTime": np.float64, "waitingTime": np.float64})

df = pd.concat([df1, df2])
df = pd.concat([df, df3])

#---------------------------------------------end--------------------------------------

#drop unwanted column
df = df.drop(["Unnamed: 0"], axis=1)
df = df[df["roadLength"] <= 300]
print(df)

#store a pandas group for use on liniar regression
groupsForRegression = []



# ---------------  group and plot data -----------------
myLines = []
for i in range(1,5):
    temp = df[df["numberOfLanes"] == i]
    temp = temp.drop(["waitingTime", "roadLength", "edgeID", "numberOfLanes"], axis=1)
    temp = temp[temp["traveltime"] <= temp.traveltime.quantile(0.80) ] #set the n'th percentil to look at
    groupsForRegression.append(temp.groupby("numberOfCars").mean())
    myLines += plt.plot( temp.groupby("numberOfCars").mean(),  label = "LN_" + str(i))

plt.xlabel("numberOfCars")
plt.ylabel("travelTime")
labels = [l.get_label() for l in myLines]
plt.legend(myLines, labels)

#----------------------------- End ----------------------------

plt.show()


linear_regressor = LinearRegression()
myLines = []
counter = 1
for group in groupsForRegression:

    #-----------------------train and predict regression------------------    
    x_train =  group.index.values.reshape(-1,1)
    y_train = [ val[0] for val in group.values]
    linear_regressor = LinearRegression() 
    linear_regressor.fit(x_train, y_train)

    y_pred = linear_regressor.predict(x_train)
    #-----------------------end --------------------------------

    myLines += plt.plot( x_train, y_pred,  label = "LN_" + str(counter)+"_coef="+str(linear_regressor.coef_) + "+ " + str(y_pred[0]) + "with_R2score= " + str(round(linear_regressor.score(x_train, y_train), 2)))
    counter+=1


plt.xlabel("numberOfCars")
plt.ylabel("travelTime")
labels = [l.get_label() for l in myLines]
plt.legend(myLines, labels)

plt.show()




def getnPercentile(n, queueLengthList):
	lst = list(map(float, queueLengthList))
	lst.sort()
	listLength = len(lst)
	index = listLength * (n/100)

	return 	(lst[math.floor(index)] + lst[math.ceil(index)]) / 2


#df["numberOfCars"] = round( df["numberOfCars"], 0)
#df = df[df["traveltime"] <= 20 ]
#df.groupby("numberOfCars").mean().plot()
#df2.groupby("numberOfCars").mean().plot()
#plt.scatter(df.numberOfCars, df.flow)
#plt.scatter(df.numberOfCars, df.travelTime , label = "main" )
#plt.scatter(df2.numberOfCars, df2.travelTime, label = "normal")

#print(normalDF[normalDF["traveltime"] > 200])
#normalGroup.plot()
#normalGroup.drop(["travelTime"],axis = 1).plot()
