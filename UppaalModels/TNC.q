/*

*/
strategy Opt =minE (totalTravelTime) [<=horizon]: <> Simulator.End
/*

*/

simulate 1 [<=horizon] { //HOLDER_QUERY } under Opt