/*

*/
strategy Opt =minE (totalTravelTime) [<=horizon]: <> Simulator.End
/*

*/

simulate 1 [<=horizon] { totalTravelTime } under Opt