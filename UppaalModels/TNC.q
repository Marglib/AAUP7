/*

*/
strategy Opt =minE (totalTravelTime) [<=2*horizon]: <> Simulator.DONE
/*

*/
simulate 1 [<=2*horizon] { //HOLDER_QUERY } under Opt