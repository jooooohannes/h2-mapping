import csv
import time
import json
import requests
import pandas as pd
from datetime import datetime, timedelta


class data_row:

    def __init__(self, date_time, ghi, dni, dhi, ta, ws):
        self.date_time = date_time
        self.ghi = ghi
        self.dni = dni
        self.dhi = dhi
        self.ta = ta
        self.ws = ws


class PvGis:

    # Request API
    API_HOURLY_TIME_SERIES = 'http://re.jrc.ec.europa.eu/pvgis5/seriescalc.php'

    # API parameters
    PARAM_LATITUDE = 'lat'
    PARAM_LONGITUDE = 'lon'
    PARAM_RAD_DATABASE = 'raddatabase'
    PARAM_AUTO_HORIZON = 'useHorizon'
    PARAM_USER_HORIZON = 'userHorizon'
    PARAM_START_YEAR = 'startyear'
    PARAM_END_YEAR = 'endyear'
    PARAM_COMPONENTS = 'components'
    PARAM_OUTPUT_FORMAT = 'outputformat'

    # Data headers
    HEADER_DATE_TIME = 'DateTime'
    HEADER_GHI = 'GHI'
    HEADER_DNI = 'DNI'
    HEADER_DHI = 'DHI'
    HEADER_TA = 'TAmb'
    HEADER_WS = 'Ws'

    # PVGIS json keys
    # https://ec.europa.eu/jrc/en/PVGIS/tools/hourly-radiation
    KEY_JSON_OUTPUTS = 'outputs'
    KEY_JSON_HOURLY = 'hourly'
    KEY_JSON_TIME = 'time'
    KEY_JSON_GB = 'Gb(i)'
    KEY_JSON_GD = 'Gd(i)'
    KEY_JSON_GR = 'Gr(i)'
    KEY_JSON_TA = 'T2m'
    KEY_JSON_WS = 'WS10m'
    
    # Request codes
    REQUEST_OK = 200

    # Latitude, in decimal degrees, south is negative
    DEF_LATITUDE = 36
    # Longitude, in decimal degrees, west is negative
    DEF_LONGITUDE = 2
    # 'PVGIS-SARAH' for Europe, Africa and Asia
    # 'PVGIS-NSRDB' for the Americas between 60°N and 20°S
    # 'PVGIS-ERA5' and 'PVGIS-COSMO' for Europe (including high-latitudes)
    # 'PVGIS-CMSAF' for Europe and Africa(will be deprecated)
    DEF_RAD_DATABASE = 'PVGIS-SARAH'
    # Calculate taking into account shadows from high horizon. Value of 1 for "yes"
    DEF_AUTO_HORIZON = 1
    # Height of the horizon at equidistant directions around the point of interest, in degrees.
    # Starting at north and moving clockwise. The series '0,10,20,30,40,15,25,5' would mean
    # the horizon height is 0 due north, 10 for north-east, 20 for east, 30 for south-east, etc
    DEF_USER_HORIZON = ''
    # Starting year of the output of monthly averages (Available from 2007 to 2016)
    DEF_START_DATE = datetime(2016, 1, 1, 00, 00, 00)
    # Final year of the output of monthly averages (Available from 2007 to 2016)
    DEF_END_DATE = datetime(2016, 12, 31, 23, 59, 59)
    # If "1" outputs beam, diffuse and reflected radiation components. Otherwise, it outputs only global values
    DEF_COMPONENTS = 1
    # Date format
    DATE_FORMAT = '%Y%m%d:%H%M'
    # Output formats: 'basic', 'csv' and 'json'
    DEF_OUTPUT_FORMAT = 'json'

    def __init__(self):
        self._latitude = self.DEF_LATITUDE
        self._longitude = self.DEF_LONGITUDE
        self._radDatabase = self.DEF_RAD_DATABASE
        self._autoHorizon = self.DEF_AUTO_HORIZON
        self._userHorizon = self.DEF_USER_HORIZON
        self._startDate = self.DEF_START_DATE
        self._endDate = self.DEF_END_DATE
        self._verbose = False
        self._data_parsed = False
        self._data = None

    @property
    def latitude(self): return self._latitude

    @property
    def longitude(self): return self._longitude

    @property
    def rad_database(self): return self._radDatabase

    @property
    def auto_horizon(self): return self._autoHorizon

    @property
    def user_horizon(self): return self._userHorizon

    @property
    def start_date(self): return self._startDate

    @property
    def end_date(self): return self._endDate

    @property
    def verbose(self): return self._verbose

    @latitude.setter
    def latitude(self, value): self._latitude = value

    @longitude.setter
    def longitude(self, value): self._longitude = value

    @rad_database.setter
    def rad_database(self, value): self._radDatabase = value

    @auto_horizon.setter
    def auto_horizon(self, value): self._autoHorizon = value

    @user_horizon.setter
    def user_horizon(self, value): self._userHorizon = value

    @start_date.setter
    def start_date(self, value): self._startDate = value

    @end_date.setter
    def end_date(self, value): self._endDate = value

    @verbose.setter
    def verbose(self, value): self._verbose = value

    def parse_json(self, value):

        data = []
        pvgis_json = json.loads(value)

        start_date = self.start_date
        end_date = self.end_date
        key_pv_gis_date = self.KEY_JSON_TIME
        date_format = self.DATE_FORMAT
        key_pv_gis_gb = self.KEY_JSON_GB
        key_pv_gis_gd = self.KEY_JSON_GD
        key_pv_gis_gr = self.KEY_JSON_GR
        key_pv_gis_ta = self.KEY_JSON_TA
        key_pv_gis_ws = self.KEY_JSON_WS

        for json_obj in pvgis_json[self.KEY_JSON_OUTPUTS][self.KEY_JSON_HOURLY]:
            date = datetime.strptime(json_obj[key_pv_gis_date], date_format)
            if date > end_date:
                break

            if start_date <= date:
                dni = float(json_obj[key_pv_gis_gb])
                dhi = float(json_obj[key_pv_gis_gd])
                ghi = float(json_obj[key_pv_gis_gr]) + dni + dhi
                ta = float(json_obj[key_pv_gis_ta])
                ws = float(json_obj[key_pv_gis_ws])

                data.append(data_row(date, ghi, dni, dhi, ta, ws))

        # Dictionary
        return data

    def request_hourly_time_series(self):

        if self._verbose:
            print("Processing request")
            start = time.time()

        result = None

        payload = {self.PARAM_LATITUDE:     self.latitude,
                   self.PARAM_LONGITUDE:    self.longitude,
                   self.PARAM_RAD_DATABASE: self.rad_database,
                   self.PARAM_AUTO_HORIZON: self.auto_horizon,
                   self.PARAM_USER_HORIZON: self.user_horizon,
                   self.PARAM_START_YEAR:   self.start_date.year,
                   self.PARAM_END_YEAR:     self.end_date.year,
                   self.PARAM_COMPONENTS:   self.DEF_COMPONENTS,
                   self.PARAM_OUTPUT_FORMAT: self.DEF_OUTPUT_FORMAT}

        if self._verbose:
            print("Request send")

        res = requests.get(self.API_HOURLY_TIME_SERIES, params=payload)

        if self._verbose:
            print('Request:', res.url)

        if res.status_code == self.REQUEST_OK:
            self._data_parsed = True
            self._data = self.parse_json(res.text)
        else:
            self._data_parsed = False

        if self._verbose:
            end = time.time()
            print("Request processed:", timedelta(seconds=end-start))

        return result
    
    def save_csv(self, filename):

        if self._data_parsed:
        
            with open(filename, 'w', newline='') as csvfile:
                
                fieldnames = [self.HEADER_DATE_TIME, self.HEADER_GHI, 
                              self.HEADER_DNI, self.HEADER_DHI, self.HEADER_TA, self.HEADER_WS]        
                csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Write header
                csv_writer.writeheader()
        
                # Write each row
                for data_row in self._data:
                
                    csv_writer.writerow({self.HEADER_DATE_TIME: data_row.date_time,
                                         self.HEADER_GHI: data_row.ghi,
                                         self.HEADER_DNI: data_row.dni,
                                         self.HEADER_DHI: data_row.dhi,
                                         self.HEADER_TA: data_row.ta,
                                         self.HEADER_WS: data_row.ws})
        else:
            print('Not available data')
            
    def pandas_data_frame(self):
        
        if self._data_parsed:
            
            dt = {self.HEADER_DATE_TIME: [d.date_time for d in self._data],
                  self.HEADER_GHI: [d.ghi for d in self._data],
                  self.HEADER_DNI: [d.dni for d in self._data],
                  self.HEADER_DHI: [d.dhi for d in self._data],
                  self.HEADER_TA: [d.ta for d in self._data],
                  self.HEADER_WS: [d.ws for d in self._data]}
            
            return pd.DataFrame(data=dt)
            
        else:
            print('Not available data')


