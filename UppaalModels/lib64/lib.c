#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <math.h>

int calc_edge_weight(int lanes, int cars, int length)
{
    double newWeight = 0.0;
    double len = (double) length;
    double c = (double) cars;
    int ret_val = 0;

    if(lanes == 1)
    {
        newWeight = (13.73 * (len/200.0)) + 1.54 * c * (200.0/len);
    }
    else if (lanes == 2)
    {
        newWeight = (7.37 * (len/100.0)) + 0.17 * c * (100.0/len);
    }
    
    else if (lanes == 3)
    {
        newWeight = (6.46 * (len/100.0)) + 0.44 * c * (100.0/len);
    }
    else if (lanes == 4)
    {
        newWeight = (5.69 * (len/100.0)) + 0.84 * c * (100.0/len);
    }
    ret_val = (int) round(newWeight);
    return ret_val;
}

int get_threshold(int edge_length)
{
    double x = 0.0;
    double threshold = 15.0;
    int ret = 0;
    double y = (double) edge_length;

    x = threshold * (y/100.0);

    ret = (int) round(x);

    return ret;
}