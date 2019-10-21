/*

*/
strategy Opt =minE (totalJammedCars) [<=2*Horizon]: <> trafficLights.DONE

/*

*/
simulate 1 [<=2*Horizon] { //HOLDER_QUERY } under Opt

