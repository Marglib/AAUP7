#include <stdint.h>
#include <stdio.h>
#include <math.h>

int calc_edge_weight(int lanes, int cars, int lenght)
{
    double newWeight = 0.0;
    int ret_val = 0;

    if(lanes == 1)
    {
        newWeight = (13.73 * (lenght/200)) + 1.54 * cars * (200/lenght);
    }
    else if (lanes == 2)
    {
        newWeight = (7.37 * (lenght/100)) + 0.17 * cars * (100/lenght);
    }
    
    else if (lanes == 3)
    {
        newWeight = (6.46 * (lenght/100)) + 0.44 * cars * (100/lenght);
    }
    else if (lanes == 4)
    {
        newWeight = (5.69 * (lenght/100)) + 0.84 * cars * (100/lenght);
    }
    ret_val = (int) round(newWeight);
    return ret_val;
}

int get_threshold(int edge_length)
{
    double x = 0.0;
    int threshold = 25;
    int ret = 0;

    x = threshold * (edge_length/100);

    ret = (int) round(x);

    return ret;
}