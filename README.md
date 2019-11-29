# Rerouting Controller for Urban Traffic #

This project consists of a [Uppaal](http://www.uppaal.org/) model for rerouting vehicles and a [SUMO](https://www.dlr.de/ts/en/desktopdefault.aspx/tabid-9883/16931_read-41000/) simulation of urban traffic to test the rerouting.

It also contains some a Python solution for establishing communication between the uppaal model and sumo.

### Experiment ID's

* 1 - Used for just running a test
The indeces for the different experiments:
* 100s - Giant experiments
    - 100 - smart tl and TNC on a 20000-10000trip file
    - 101 - No nothing
    - 102 - Smart tl alone
* 200s - Capacity experiments
    
* 300s - simple rerouting experiments
    - 301 - 1000 time steps with 1000 trips for a default controller
    - 302 - 1000 time steps with 2000 trips for a default controller

    - 311 - 1000 time steps with 1000 trips for a simplererouting controller
    - 312 - 1000 time steps with 2000 trips for a simplererouting controller

* 600s - Small experiments to check performance
    - 600-604 - No controller & smart trafficlight
    - 605-609 - TNC & smart trafficlight
    - 610-614 - No nothing

* 4000-4099 - Smart traffic lights and simple Uppaal implementation - Old Controller
    - 4000-4020 - All results for smart tl and TrafficNetworkController
        - 4000-4002 - Load 1000-2000 - smartroute
        - 4003-4005 - Load 2000-2000 - smartroute
        - 4006-4008 - Load 2500-2000 - smartroute
        - 4009-4011 - Load 3000-2000 - smartroute
        - 4012-4014 - Load 3500-2000 - smartroute
        - 4015-4017 - Load 4000-2000 - smartroute
        - 4018-4020 - Load 5000-2000 - smartroute - No results
    - 4021 - 4041 - All results for TrafficNetworkController and default trafficlights
        - 4021-4023 - Load 1000-2000 - route
        - 4024-4026 - Load 2000-2000 - route
        - 4027-4029 - Load 2500-2000 - route
        - 4030-4032 - Load 3000-2000 - route
        - 4033-4035 - Load 3500-2000 - route
        - 4036-4038 - Load 4000-2000 - route
        - 4039-4041 - Load 5000-2000 - route - No results
    - 4042 - 4062 - All results for smart trafficlights and default controller
        - 4042-4044 - Load 1000-2000 - smart
        - 4045-4047 - Load 2000-2000 - smart
        - 4048-4050 - Load 2500-2000 - smart
        - 4051-4053 - Load 3000-2000 - smart
        - 4054-4056 - Load 3500-2000 - smart
        - 4057-4059 - Load 4000-2000 - smart
        - 4060-4062 - Load 5000-2000 - smart
    - 4063 - 4083 - All results for no controller and default trafficlights
        - 4063-4065 - Load 1000-2000 - none
        - 4066-4068 - Load 2000-2000 - none
        - 4069-4071 - Load 2500-2000 - none
        - 4072-4074 - Load 3000-2000 - none
        - 4075-4077 - Load 3500-2000 - none
        - 4078-4080 - Load 4000-2000 - none
        - 4081-4083 - Load 5000-2000 - none

* 4100-4199 - Smart trafficlight and TNC_OneChoice
    - 4100-4117 - All results for smart tl and TrafficNetworkController
        - 4100-4102 - Load 1000-2000 - smartroute
        - 4103-4105 - Load 2000-2000 - smartroute
        - 4106-4108 - Load 2500-2000 - smartroute
        - 4109-4111 - Load 3000-2000 - smartroute
        - 4112-4114 - Load 3500-2000 - smartroute
        - 4115-4117 - Load 4000-2000 - smartroute
    - 4121 - 4038 - All results for TrafficNetworkController and default trafficlights
        - 4121-4123 - Load 1000-2000 - route
        - 4124-4126 - Load 2000-2000 - route
        - 4127-4129 - Load 2500-2000 - route
        - 4130-4132 - Load 3000-2000 - route
        - 4133-4135 - Load 3500-2000 - route
        - 4136-4138 - Load 4000-2000 - route
    - 4142 - 4159 - All results for smart trafficlights and default controller
        - 4142-4144 - Load 1000-2000 - smart
        - 4145-4147 - Load 2000-2000 - smart
        - 4148-4150 - Load 2500-2000 - smart
        - 4151-4153 - Load 3000-2000 - smart
        - 4154-4156 - Load 3500-2000 - smart
        - 4157-4159 - Load 4000-2000 - smart

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


### Running the simulation

To run the simulation make sure you are withing the AAUP7 folder and run the following command

```
$ python3 Runnerscript.py --sumocfg SUMOfiles/ConfigMasterFile.sumocfg --expid 1 --port 8873 --controller TrafficNetworkController
```
* `--expid` - should be set according to the ID's in the [Experiment ID's section](#experiment-ids) 
* `--controller` - The controller parameter should be set to the controller you want to run. [See the controller section](#controllers) for an overview of possible controllers.
* `sumocfg`- The config file to use for the run. **Ensure that the config file is using the correct tripfile and netfile**
* `--trafficlight` - The trafficlight parameter should be set to the traffic light you want to use. [See the traffic light section](#traffic_lights) for an overview of possible traffic lights.



