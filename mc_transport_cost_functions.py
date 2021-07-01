import pandas as pd
import numpy as np


# Costs by material

def nh3_costs(pipe_dist=99.57142, ship_dist=1.926, truck_dist=-83.0, convert=True, centralised=True, pipeline=True, max_pipeline_dist=2000):
    """Calculates the transport cost of NH3. Requires as input the distance that NH3 will be piped, shipped and
    trucked, as well as a boolean variable denominating if the distribution point is centralised or not."""

    if convert == True:
        conversion = 1.02
        export = 0.11
        if centralised:
            reconversion = 0.85
        else:
            reconversion = 1.13
    else:
        conversion = 0
        reconversion = 0
        export = 0

    ship = 2.323E-02 * np.log(ship_dist) - 1.523E-02
    if max_pipeline_dist > pipe_dist > 400:
        pipe = 0.0007 * pipe_dist - 0.0697
    elif pipe_dist < 400:
        pipe = 0.0007 * 400 - 0.0697
    else:
        pipe = np.nan

    if pipeline == False:
        pipe = np.nan

    truck = 0.0008 * truck_dist + 0.0664

    return conversion + export + ship + pipe + truck + reconversion


def h2_gas_costs(pipe_dist=-102.75, truck_dist=-106.0, pipeline=True, max_pipeline_dist=2000):
    """Calculates the transport cost of H2 gas. Requires as input the distance that H2 will be piped and
    trucked."""

    if max_pipeline_dist > pipe_dist > 400:
        pipe = 0.0004 * pipe_dist + 0.0424
    elif pipe_dist < 400:
        pipe = 0.0004 * 400 + 0.0424
    else:
        pipe = np.nan

    if pipeline == False:
        pipe = np.nan

    truck = 0.003 * truck_dist + 0.3319

    return pipe + truck


def lohc_costs(ship_dist=4.9699, truck_dist=-94.78571, convert=True, centralised=True):
    """Calculates the transport cost of LOHC. Requires as input the distance that LOHC will be shipped and
    trucked, as well as a boolean variable denominating if the distribution point is centralised or not."""

    if convert == True:
        conversion = 0.41
        export = 0.10
        if centralised:
            reconversion = 1.10
        else:
            reconversion = 2.35
    else:
        conversion = 0
        reconversion = 0
        export = 0

    ship = 3.404E-02 * np.log(ship_dist) - 5.458E-02
    truck = 0.0014 * truck_dist + 0.1327

    return conversion + export + ship + truck + reconversion


def h2_liq_costs(ship_dist=0.1915, truck_dist=-22.11666, convert=True, centralised=True):
    """Calculates the transport cost of liquid H2. Requires as input the distance that H2 will be shipped and
    trucked, as well as a boolean variable denominating if the distribution point is centralised or not."""

    if convert == True:
        conversion = 1.03
        export = 0.88
        if centralised:
            reconversion = 0.02
        else:
            reconversion = 0.02
    else:
        conversion = 0
        reconversion = 0
        export = 0

    ship = 1.353E-01 * np.log(ship_dist) + 2.236E-01
    truck = 0.006 * truck_dist + 0.1327

    return conversion + export + ship + truck + reconversion
