import math


# Annualisation of capex function
def annualise(capex, interest, lifetime):
    """Annualises the fixed CapEx of an investment. Takes as input the fixed Capex (Eur), interest and lifetime (
    yrs). """

    annualised_capex = capex * (interest / (1 - ((1 + interest) ** (-lifetime))))
    return annualised_capex


def generation_costs(df_ren, h2_demand, year=2020, type='alkaline', interest=0.08, full_load_hours=6000):
    """Calculates the cost of H2 generation on a yearly and per kg basis. Requires the main dataframe as input.
    Optional inputs are the H2 demand (kt/yr) year (2019 or 2050), electrolyser type (alkaline, SOEC, or other),
    interest rate, and full load hours (hours/yr). """

    opex_factor_solar = 0.015  # []
    opex_wind = 8  # [Eur/MWh]
    wind_efficiency = 0.4  # []
    blade = 50  # [m]
    turbine_size = 2  # [MW]
    elec_opex = 0.02  # [% of elec CapEx]
    comp_elec = 4  # [kWh/kg H2]
    other_capex_elec = 41.6  # [Eur/kW]
    water_cost = 0.07  # [Eur/kg H2]

    if 2020 <= year <= 2050:
        year_diff = year - 2020
    elif year < 2020:
        year_diff = 0
    elif year > 2050:
        year_diff = 30

    # Determination of wind parameters

    if year <= 2030:
        capex_wind = 1260 * (0.9775 ** year_diff)   #[Eur/kW]
    else:
        capex_wind = 1260 * (0.9775 ** 10) * (0.9985 ** (year - 2030))

    # Determination of solar parameters
    capex_solar = 700 * (0.9986 ** year_diff)  # [Eur/kWp]
    solar_efficiency = 0.64 + 0.003333 * year_diff  # []

    # Determination of electrolyser parameters
    if type == 'alkaline':
        capex_extra = 2.47  # [Eur/kg h2]
        capex_h2 = 830 * (0.98 ** year_diff) # [Eur/kW]
        lifetime_hours = 75000 + 1667 * year_diff  # [hours]
        electrolyser_efficiency = 0.67 + 0.002666 * year_diff  # []
    elif type == 'SOEC':
        capex_extra = 2.47  # [Eur/kg h2]
        capex_h2 = 1131 * (0.98 ** year_diff) # [Eur/kW]
        lifetime_hours = 20000 + 2167 * year_diff  # [hours]
        electrolyser_efficiency = 0.77 + 0.002666 * year_diff  # []
    else:
        capex_extra = 0.91  # [Eur/kg h2]
        capex_h2 = 994 * (0.98 ** year_diff)  # [Eur/kW]
        lifetime_hours = 60000 + 2250 * year_diff   # [hours]
        electrolyser_efficiency = 0.58 + 0.004 * year_diff  # []
        # 7% cost reduction per doubling in installed capacity
    lifetime = lifetime_hours / full_load_hours

    # Calculate required size of electricity generation  (MWh/yr)
    h2_demand_hourly = h2_demand * 1000 / full_load_hours  # [ton/hr]
    elec_demand = h2_demand_hourly * 39 / electrolyser_efficiency + comp_elec * h2_demand_hourly  # [MW]
    elec_demand_yearly = h2_demand * 1000 * 39 / electrolyser_efficiency + comp_elec * h2_demand * 1000  # [MWh/yr]

    # Calculate the capex of the solar array required
    df_ren['Solar Array Size'] = elec_demand_yearly * 1000 / df_ren['Solar Energy Potential']  # [kWp]
    df_ren['Solar CapEx'] = df_ren['Solar Array Size'] * capex_solar  # [Eur]

    # Calculate the capex of wind turbines required
    capex_turbine = turbine_size * capex_wind * 1000
    df_ren['Wind Turbine Power'] = df_ren['Wind Power Density'] * wind_efficiency * (blade ** 2) * math.pi / 1e6  # [MW]
    df_ren['No. of Turbines'] = elec_demand / df_ren['Wind Turbine Power']  # []
    df_ren['Wind CapEx'] = df_ren['No. of Turbines'] * capex_turbine  # [Eur]

    # Get minimum cost location from solar and wind and calculate cost/yr and cost/kWh
    df_ren['Yearly Cost Solar'] = annualise(df_ren['Solar CapEx'], interest, 25) + opex_factor_solar * df_ren[
        'Solar CapEx']  # [Eur/yr]
    df_ren['Yearly Cost Wind'] = annualise(df_ren['Wind CapEx'], interest,
                                           20) + opex_wind * elec_demand_yearly  # [Eur/yr]
    df_ren['Elec Cost Solar'] = df_ren['Yearly Cost Solar'] / elec_demand_yearly  # [Eur/MWh]
    df_ren['Elec Cost Wind'] = df_ren['Yearly Cost Wind'] / elec_demand_yearly  # [Eur/MWh]
    df_ren['Cheaper source'] = ['Solar' if x < y else 'Wind' for x, y in
                                zip(df_ren['Yearly Cost Solar'], df_ren['Yearly Cost Wind'])]

    # Calculate the cost of the electrolyser
    total_capex_h2 = (capex_h2 + other_capex_elec) * elec_demand * 1000  # [Eur]
    yearly_cost_h2 = annualise(total_capex_h2, interest, lifetime) + elec_opex * total_capex_h2 + (
                capex_extra + water_cost) * h2_demand * 1000 * 1000  # [Eur/yr]

    # Calculate total generation cost/yr
    df_ren['Yearly gen. cost'] = [min(x, y) + yearly_cost_h2 for x, y in
                                  zip(df_ren['Yearly Cost Solar'], df_ren['Yearly Cost Wind'])]  # [Eur/yr]
    df_ren['Gen. cost per kg H2'] = df_ren['Yearly gen. cost'] / (h2_demand * 1000 * 1000)  # [Eur/kg H2]

    return df_ren
