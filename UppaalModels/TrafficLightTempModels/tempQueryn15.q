/*

*/
strategy Opt =minE (totalJammedCars) [<=2*Horizon]: <> trafficLights.DONE

/*

*/
simulate 1 [<=2*Horizon] {  signal[1], signal[2], signal[3], signal[4], signal[5], signal[6], signal[7], signal[8], signal[9], signal[10], signal[11], signal[12], signal[13], signal[14], signal[15], signal[16] } under Opt

