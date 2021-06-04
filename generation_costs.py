import pandas as pd
import numpy as np
import math
import timeit

start = timeit.default_timer()

#Read in level 1 solar plant locations [Longitude, Latitude, kWh/kWp yearly, average W/m2 yearly,
# Wind Power Density, Port code, Port Longitude, Port Latitude, Distance to Port]
df_ren = pd.read_csv('Data/renewables.csv')

year = 2019
type = 'alkaline'
interest = 0.08    #[]
full_load_hours = 6000    #[hours/yr]
opex_factor_solar = 0.015     #[]
capex_wind = 1260    #[Eur/kW]
opex_wind = 8     #[Eur/MWh]
wind_efficiency = 0.4    #[]
blade = 50         #[m]
turbine_size = 2       #[MW]
h2_demand = 50        #[kt/yr]
elec_opex = 0.02      #[]
comp_elec = 4       #[kWh/kg H2]
other_capex_elec = 41.6  #[Eur/kW]
water_cost = 0.07     #[Eur/kg H2]

#Determination of solar parameters
if year == 2019:
    capex_solar = 700    #[Eur/kWp]
    solar_efficiency = 0.64        #[]
elif year == 2050:
    capex_solar = 445  #[Eur/kWp]
    solar_efficiency = 0.74       #[]

#Determination of electrolyser parameters
if type == 'alkaline':
    capex_extra = 2.47  # [Eur/kg h2]
    if year == 2019:
        capex_h2 = 1232    #[Eur/kW]
        lifetime = 8.56    #[years]
        electrolyser_efficiency = 0.67    #[]
    elif year == 2050:
        capex_h2 = 616     #[Eur/kW]
        lifetime = 14.27   #[years]
        electrolyser_efficiency = 0.75     #[]
elif type == 'SOEC':
    capex_extra = 2.47  # [Eur/kg h2]
    if year == 2019:
        capex_h2 = 4928  # [Eur/kW]
        lifetime = 2.28  # [years]
        electrolyser_efficiency = 0.77    #[]
    elif year == 2050:
        capex_h2 = 880  # [Eur/kW]
        lifetime = 9.98  # [years]
        electrolyser_efficiency = 0.84     #[]
else:
    capex_extra = 0.91  # [Eur/kg h2]
    if year == 2019:
        capex_h2 = 1584  # [Eur/kW]
        lifetime = 6.85  # [years]
        electrolyser_efficiency = 0.58     #[]
    elif year == 2050:
        capex_h2 = 792  # [Eur/kW]
        lifetime = 14.27  # [years]
        electrolyser_efficiency = 0.70    #[]
    #7% cost reduction per doubling in installed capacity

#Annualisation of capex function
def annualise(capex,interest,lifetime):
    annualised_capex = capex * (interest/(1-((1+interest)**(-lifetime))))
    return annualised_capex

#Calculate required size of electricity generation  (MWh/yr)
h2_demand_hourly = h2_demand * 1000 / full_load_hours     #[ton/hr]
elec_demand = h2_demand_hourly * 39/electrolyser_efficiency        #[MW]
elec_demand_yearly = h2_demand * 39/electrolyser_efficiency       #[MWh/yr]

#Calculate the capex of the solar array required
df_ren['Solar Array Size'] = elec_demand_yearly * 1000 / df_ren['Solar Energy Potential']    #[kWp]
df_ren['Solar CapEx'] = df_ren['Solar Array Size'] * capex_solar    #[Eur]

#Calculate the capex of wind turbines required
capex_turbine = turbine_size * capex_wind * 1000
df_ren['Wind Turbine Power'] = df_ren['Wind Power Density'] * wind_efficiency * (blade**2) * math.pi / 1e3     #[kW]
df_ren['No. of Turbines']  = elec_demand / df_ren['Wind Turbine Power']                     #[]
df_ren['Wind CapEx'] = df_ren['No. of Turbines'] * capex_turbine            #[Eur]

#Get minimum cost location from solar and wind and calculate cost/yr and cost/kWh
df_ren['Yearly Cost Solar'] = annualise(df_ren['Solar CapEx'],interest,25) + opex_factor_solar * df_ren['Solar CapEx']          #[Eur/yr]
df_ren['Yearly Cost Wind'] = annualise(df_ren['Wind CapEx'],interest,20) + opex_wind * elec_demand_yearly                       #[Eur/yr]
df_ren['Elec Cost Solar'] = df_ren['Yearly Cost Solar'] / elec_demand_yearly                                          #[Eur/MWh]
df_ren['Elec Cost Wind'] = df_ren['Yearly Cost Wind'] / elec_demand_yearly                                            #[Eur/MWh]
df_ren['Cheaper source'] = ['Solar' if x < y else 'Wind' for x, y in zip(df_ren['Yearly Cost Solar'], df_ren['Yearly Cost Wind'])]

#Calculate the cost of the electrolyser
total_capex_h2 = (capex_h2 + other_capex_elec) * elec_demand * 1000    #[Eur]
ann_capex_h2 = annualise(total_capex_h2, interest, lifetime)            #[Eur/yr]
yearly_cost_h2 = ann_capex_h2 + elec_opex * total_capex_h2 + (capex_extra + water_cost) * h2_demand * 1000 * 1000   #[Eur/yr]
electrolysis_per_kg_cost = yearly_cost_h2 / (h2_demand * 1000 * 1000)     #[Eur/kg H2]

#Calculate total generation cost/yr
df_ren['Yearly gen. cost'] = [min(x,y) + yearly_cost_h2 for x, y in zip(df_ren['Yearly Cost Solar'], df_ren['Yearly Cost Wind'])]      #[Eur/yr]
df_ren['Gen. cost per kg H2'] = df_ren['Yearly gen. cost'] / (h2_demand * 1000 * 1000)     #[Eur/kg H2]

stop = timeit.default_timer()

print('Time: ', stop - start)