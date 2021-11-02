import numpy as np


def normalize(min, max, array):
    """Normalizes 'value' between min and max."""

    normalized = (array - min) / (max - min)

    return normalized


def define_gen_parameters(year, iterations, type='alkaline'):
    """Defines distributions for the parameters for the monte carlo simulation."""

    if 2020 <= year <= 2050:
        year_diff = year - 2020
    elif year < 2020:
        year_diff = 0
    elif year > 2050:
        year_diff = 30

    # Determination of electrolyser parameters
    if type == 'alkaline':
        capex_extra = np.random.triangular(2.30, 2.47, 2.65, (iterations, 1))  # [Eur/kg h2]
        capex_h2 = np.random.triangular(477, 830, 1060, (iterations, 1))  # [Eur/kW]
        capex_growth = np.where(capex_h2 < 830, 0.98 + normalize(477, 830, capex_h2) * (0.995 - 0.98),
                                0.975 + normalize(830, 1060, capex_h2) * (0.98 - 0.975))
        capex_h2 = capex_h2 * (capex_growth ** year_diff)  # [Eur/kW]
        lifetime_hours = 75000 + 1667 * year_diff  # [hours]
        electrolyser_efficiency = np.random.uniform(0.67, 0.7, (iterations, 1)) + 0.002666 * year_diff  # []
    elif type == 'SOEC':
        capex_extra = np.random.triangular(2.30, 2.47, 2.65, (iterations, 1))  # [Eur/kg h2]
        capex_h2 = np.random.triangular(566, 1131, 1912, (iterations, 1))  # [Eur/kW]
        capex_growth = np.where(capex_h2 < 1131, 0.98 + normalize(566, 1131, capex_h2) * (0.995 - 0.98),
                                0.975 + normalize(1131, 1912, capex_h2) * (0.98 - 0.975))
        capex_h2 = capex_h2 * (capex_growth ** year_diff)  # [Eur/kW]
        lifetime_hours = 20000 + 2167 * year_diff  # [hours]
        electrolyser_efficiency = np.random.uniform(0.77, 0.81, (iterations, 1)) + 0.002666 * year_diff  # []
    else:
        capex_extra = np.random.triangular(0.8, 0.91, 1, (iterations, 1))  # [Eur/kg h2]
        capex_h2 = np.random.triangular(322, 994, 1731, (iterations, 1))  # [Eur/kW]
        capex_growth = np.where(capex_h2 < 994, 0.98 + normalize(322, 993, capex_h2) * (0.995 - 0.98),
                                0.975 + normalize(994, 1731, capex_h2) * (0.98 - 0.975))
        capex_h2 = capex_h2 * (capex_growth ** year_diff)  # [Eur/kW]
        lifetime_hours = 60000 + 2250 * year_diff  # [hours]
        electrolyser_efficiency = np.random.uniform(0.58, 0.6, (iterations, 1)) + 0.004 * year_diff  # []

    elec_opex = np.random.uniform(0.01, 0.03, (iterations, 1))  # [% of elec CapEx]
    other_capex_elec = np.random.triangular(30, 41.6, 50, (iterations, 1))  # [Eur/kW]
    water_cost = np.random.triangular(0.05, 0.07, 0.09, (iterations, 1))  # [Eur/kg H2]

    # Determination of wind power parameters
    if year <= 2030:
        capex_wind = np.random.triangular(1200, 1260, 1500, (iterations, 1)) * (0.9775 ** year_diff)   #[Eur/kW]
    else:
        capex_wind = np.random.triangular(1200, 1260, 1500, (iterations, 1)) * (0.9775 ** 10) * (
                0.9985 ** (year - 2030))
    opex_wind = np.random.triangular(6, 8, 10, (iterations, 1))  # [Eur/MWh]

    # Determination of solar parameters
    capex_solar = np.random.triangular(500, 700, 1100, (iterations, 1)) * (0.9986 ** year_diff)  # [Eur/kWp]
    opex_factor_solar = np.random.triangular(0.01, 0.015, 0.02, (iterations, 1))  # []

    return year_diff, capex_extra, capex_h2, lifetime_hours, electrolyser_efficiency, elec_opex, other_capex_elec, water_cost, capex_wind, opex_wind, capex_solar, opex_factor_solar
