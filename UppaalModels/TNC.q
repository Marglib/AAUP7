/*

*/
strategy Opt =minE (totalTravelTime) [<=2*horizon]: <> Simulator.DONE
/*

*/
E<> Simulator.End under Opt

//simulate 1 [<=2*horizon] { //HOLDER_QUERY } under Opt