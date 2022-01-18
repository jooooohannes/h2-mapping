import math


# Annualisation of capex function
def annualise(capex, interest, lifetime):
    """Annualises the fixed CapEx of an investment. Takes as input the fixed Capex (Eur), interest and lifetime (
    yrs). """

    annualised_capex = capex * (interest / (1 - ((1 + interest) ** (-lifetime))))
    return annualised_capex


def mc_generation_costs(df_ren, h2_demand, year_diff, capex_extra, capex_h2, lifetime_hours, electrolyser_efficiency,
                        elec_opex,
                        other_capex_elec, water_cost,
                        capex_wind, opex_wind, capex_solar, opex_factor_solar,
                        interest=0.08, full_load_hours=2000):
    """Calculates the cost of H2 generation on a yearly and per kg basis. Requires the main dataframe as input.
    Optional inputs are the H2 demand (kt/yr) year (2019 or 2050), electrolyser type (alkaline, SOEC, or other),
    interest rate, and full load hours (hours/yr). """

    wind_efficiency = 0.4  # []
    blade = 50  # [m]
    turbine_size = 2  # [MW]
    comp_elec = 4  # [MWh/ton H2]

    # Determination of solar parameters
    solar_efficiency = 0.64 + 0.003333 * year_diff  # []

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
