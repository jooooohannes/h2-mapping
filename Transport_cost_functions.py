import pandas as pd
import numpy as np

# Costs by material

def nh3_costs(pipe_dist=99.57142,  ship_dist=9609.63606, truck_dist=-83, centralised=True):

    conversion = 1.02
    if centralised:
        reconversion = 0.85
    else:
        reconversion = 1.13
    export = 0.11
    ship = -3.503E-08 * ship_dist ** 2 + 2.417E-04 * ship_dist + 9.122E-01
    pipe = 0.0007 * pipe_dist - 0.0697
    truck = 0.0008 * truck_dist + 0.0664

    return conversion + export + ship + pipe + truck + reconversion

def h2_gas_costs(pipe_dist=-102.75, truck_dist=-106):

    pipe = 0.0004 * pipe_dist + 0.0424
    truck = 0.003 * truck_dist + 0.3319

    return pipe + truck

def lohc_costs(ship_dist=12677.60177, truck_dist=-94.78571, centralised=True):

    conversion = 0.41
    if centralised:
        reconversion = 1.10
    else:
        reconversion = 2.35
    export = 0.10
    ship = -2.990E-09 * ship_dist ** 2 + 3.319E-05 * ship_dist + 1.054E-01
    truck = 0.0014 * truck_dist + 0.1327

    return conversion + export + ship + truck + reconversion

def h2_liq_costs(ship_dist=-2479.15936, truck_dist=-22.11666, centralised=True):

    conversion = 1.03
    if centralised:
        reconversion = 0.02
    else:
        reconversion = 0.02
    export = 0.88
    ship = -2.633E-09 * ship_dist ** 2 + 4.357E-05 * ship_dist + 1.242E-01
    truck = 0.006 * truck_dist + 0.1327

    return conversion + export + ship + truck + reconversion

