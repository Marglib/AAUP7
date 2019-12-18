# Rerouting Model for Urban Traffic #

This project consists of a [Uppaal](http://www.uppaal.org/) model for rerouting vehicles and a [SUMO](https://www.dlr.de/ts/en/desktopdefault.aspx/tabid-9883/16931_read-41000/) simulation of urban traffic to test the rerouting.

It also contains some a Python solution for establishing communication between the uppaal model and sumo.

### Experiment ID's
The experiment ID's are described [here](results/IndexLookUp.txt)

### Controllers

* `Default` - The standard controller doing nothing
* `SimpleRerouting`- The controller doing simple rerouting 
* `TrafficNetworkController` - The main controller for rerouting using uppaal

### Traffic Lights
* `Default` - The standard SUMO traffic light
* `smart` - Traffic light controller using UPPAAL

## Getting started

To run the Python scripts, ensure you have the following libraries installed:

The solution is run on `Python 3.6`

```
matplotlib
networkx
Numpy
```

### Generating a network

To generate a new sumo network use the following command:

```
$ netconvert --node-files SimpleRerouteNodes.nod.xml --edge-files SimpleRerouteEdges.edg.xml -t TypeFile.type.xml -o SimpleRerouteNet.net.xml
```
* `--node-files`- The node file to use for generation
* `--edgefiles` - The edge file to use for generation
* `-t` - The type file to use for the generation
* `-o` - The name of the generated sumo net 

### Generating trips

To generate trips enter the SUMOfiles folder and enter the following command: 

```
$ python3 TripGenerator.py --trips 50 --time 50 --useProbFile --edgeFile ~/AAUP7/SUMOfiles/MasterEdgeFile.edg.xml -o MasterTripFile
```
* `--trips` - The amount of vehicle trips to generate
* `--time` - The simulation steps that vehicles following the trips will spawn
* `--useProbFile`- Flag that tells the generator to use probabilities for where trips are generated. **Do not use with `--standard`**
* `--standard` - Flag that tells the generator not use use any probabilites when generating trips. **Do not use with `--useProbFile`**
* `--edgeFile` - The file containing the edges of the network to generate trips from
* `-o` - The name of the generated tripfile 


### Creating verifierpath.py
In order to be able to run the simulation you must first create a file name verifierpath.py in the AAUP7 folder. This file should contain the following:

```
import sys
import os
from os.path import expanduser

veri = '/path/to/uppaal64-4.1.20-stratego-6/bin-Linux/verifyta'
veriStratego = '/path/to/uppaal-stratego-4-1-20-3/bin-Linux/verifyta'
```

### Running the simulation

To run the simulation make sure you are withing the AAUP7 folder and run the following command

```
$ python3 Runnerscript.py --sumocfg SUMOfiles/ConfigMasterFile.sumocfg --expid 1 --port 8873 --controller TrafficNetworkController --trafficlight smart
```
* `--expid` - should be set according to the ID's in the [Experiment ID's section](#experiment-ids) 
* `--controller` - The controller parameter should be set to the controller you want to run. [See the controller section](#controllers) for an overview of possible controllers.
* `sumocfg`- The config file to use for the run. **Ensure that the config file is using the correct tripfile and netfile**
* `--trafficlight` - The trafficlight parameter should be set to the traffic light you want to use. [See the traffic light section](#traffic-lights) for an overview of possible traffic lights.



