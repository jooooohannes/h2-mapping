import pandas as pd
import numpy as np

# Read in chemical plants
df_chem = pd.read_csv('Data/chemicalparksv2.csv', sep=';', encoding='latin-1')

# Read in emissions sources
df_emissions = pd.read_csv('Data/emissions.csv')


