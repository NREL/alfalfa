import numpy as np
from symfit import parameters, variables, log, Fit, Model
from sympy import *
import os

class CaseModels():
    def __init__(self, csv_medium_door, csv_medium_open, csv_low_01, csv_low_02):
        self.csv_medium_door = csv_medium_door
        self.csv_medium_open = csv_medium_open
        self.csv_low_01 = csv_low_01
        self.csv_low_02 = csv_low_02
        self.csv_path_base = os.path.dirname(os.path.abspath(__file__))


    def read_case_data(self, csv_file):
        """csv_file needs to follow the format for columns: foodT, caseT, saT, raT, zoneT, zoneHumid"""
        """this function will be used a lot to read data for different cases"""
        csv_file_full_path = os.path.join(self.csv_path_base, csv_file)
        with open(csv_file_full_path, encoding='utf-8', mode='r') as f:
            mydata = f.readlines()

        mydata = np.asarray(mydata)
        foodT = []
        caseT = []
        saT = []
        raT = []
        zoneT = []
        zoneW=[]
        for i in range(len(mydata)):
            x = mydata[i]
            tmp = x.split(',')
            if i > 2:
                foodT.append(float(tmp[0]))
                caseT.append(float(tmp[1]))
                saT.append(float(tmp[2]))
                raT.append(float(tmp[3]))
                zoneT.append(float(tmp[4]))
                zoneW.append( float(tmp[5]) )

        foodT = np.asarray(foodT)
        caseT = np.asarray(caseT)
        saT = np.asarray(saT)
        raT = np.asarray(raT)
        zoneT = np.asarray(zoneT)
        zoneW = np.asarray(zoneW)

        if 'mt-door' in csv_file:
            from scipy.signal import savgol_filter
            foodT = savgol_filter(foodT, 51, 3)

        return (foodT, caseT, saT, raT, zoneT, zoneW)


    def read_case_medium_door(self):
        if self.csv_medium_door ==None:
            self.csv_medium_door= "mt-door_data.csv"

        (self.medium_door_foodT, self.medium_door_caseT, self.medium_door_saT,
         self.medium_door_raT, self.medium_door_zoneT, self.medium_door_zoneW ) = \
            self.read_case_data(self.csv_medium_door)

        from scipy.signal import savgol_filter
        self.medium_door_foodT = savgol_filter(self.medium_door_foodT, 51, 3)

        return (self.medium_door_foodT, self.medium_door_caseT, self.medium_door_saT,
         self.medium_door_raT, self.medium_door_zoneT, self.medium_door_zoneW)


    def read_case_medium_open(self):
        if self.csv_medium_open==None:
            self.csv_medium_open = "mt-open_data.csv"

        (self.medium_open_foodT, self.medium_open_caseT, self.medium_open_saT,
         self.medium_open_raT, self.medium_open_zoneT, self.medium_open_zoneW ) = \
            self.read_case_data(self.csv_medium_open)

        return(self.medium_open_foodT, self.medium_open_caseT, self.medium_open_saT,
         self.medium_open_raT, self.medium_open_zoneT, self.medium_open_zoneW)


    def read_case_low_01(self):
        if self.csv_low_01==None:
            self.csv_low_01 = "lt1_data.csv"

        (self.low_01_foodT, self.low_01_caseT, self.low_01_saT,
         self.low_01_raT, self.low_01_zoneT, self.low_01_zoneW ) = \
            self.read_case_data(self.csv_low_01)

        return (self.low_01_foodT, self.low_01_caseT, self.low_01_saT,
         self.low_01_raT, self.low_01_zoneT, self.low_01_zoneW)


    def read_case_low_02(self):
        if self.csv_low_02==None:
            self.csv_low_02 = "lt2_data.csv"

        (self.low_02_foodT, self.low_02_caseT, self.low_02_saT,
         self.low_02_raT, self.low_02_zoneT, self.low_02_zoneW ) = \
            self.read_case_data(self.csv_low_02)

        return (self.low_02_foodT, self.low_02_caseT, self.low_02_saT,
         self.low_02_raT, self.low_02_zoneT, self.low_02_zoneW )


    def case_medium_door(self):
        """learn the foodT, based on sat/rat/zoneT/zoneW"""

        x_sat, x_rat, x_case_t, x_zone_t, food_t = variables('x_sat, x_rat, x_case_t, x_zone_t, food_t')
        a, b, c, d = parameters('a, b, c, d')

        z_component = a * x_sat + b * x_rat + c * x_case_t + d * exp(-x_zone_t*0.1)
        model_dict = {
            food_t: z_component,
        }

        self.fit_medium_door = Fit(model_dict, x_sat=self.medium_door_saT, x_rat = self.medium_door_raT, \
                  x_case_t= self.medium_door_caseT, x_zone_t = self.medium_door_zoneT,  \
                  food_t = self.medium_door_foodT)
        self.fit_result_medium_door = self.fit_medium_door.execute()

        return (self.fit_medium_door, self.fit_result_medium_door)


    def predict_case_medium_door(self, sat, rat, case_t, zone_t):
        model = self.fit_medium_door.model(x_sat=sat,  x_rat= rat, x_case_t=case_t,
                              x_zone_t = zone_t,   **self.fit_result_medium_door.params)
        print('hey foodT: ', model.food_t)
        return model.food_t


    def case_medium_open(self):
        """learn the foodT, based on sat/rat/zoneT/zoneW"""
        x_sat, x_rat, x_case_t, x_zone_t, x_zone_w, food_t = \
            variables('x_sat, x_rat, x_case_t, x_zone_t, x_zone_w, food_t')
        a, b, c, d, e = parameters('a, b, c, d, e')

        z_component = a * x_sat + b * x_rat + c * x_case_t + d * exp(-x_zone_t*0.001) + e * cos(-x_zone_w*0.01)
        model_dict = {
            food_t: z_component,
        }

        self.fit_medium_open = Fit(model_dict, x_sat=self.medium_open_saT, x_rat=self.medium_open_raT,
                                   x_case_t=self.medium_open_caseT, x_zone_t=self.medium_open_zoneT,
                  x_zone_w=self.medium_open_zoneW, food_t=self.medium_open_foodT)
        self.fit_result_medium_open = self.fit_medium_open.execute()

        return ( self.fit_medium_open, self.fit_result_medium_open)


    def predict_case_medium_open(self, sat, rat, case_t, zone_t, zone_w):
        model = self.fit_medium_open.model(x_sat=sat, x_rat=rat, x_case_t=case_t, x_zone_t=zone_t,
                           x_zone_w= zone_w, **self.fit_result_medium_open.params)

        return model.food_t


    def case_low_01(self):
        """learn the foodT, based on sat/rat/zoneT/zoneW"""

        x_sat, x_rat, x_case_t, x_zone_t,  food_t = \
            variables('x_sat, x_rat, x_case_t, x_zone_t, food_t')
        a, b, c, d = parameters('a, b, c, d')

        z_component = a * x_sat + b * x_rat + c * x_case_t + d * sin(-x_zone_t*0.01)
        model_dict = {
            food_t: z_component,
        }

        self.fit_low_01 = Fit(model_dict, x_sat=self.low_01_saT, x_rat=self.low_01_raT,
                              x_case_t=self.low_01_caseT, x_zone_t=self.low_01_zoneT,
                   food_t=self.low_01_foodT)
        self.fit_result_low_01 = self.fit_low_01.execute()

        return (self.fit_low_01, self.fit_result_low_01)


    def predict_case_low_01(self,sat, rat, case_t, zone_t, zone_w):
        model = self.fit_low_01.model(x_sat=sat, x_rat=rat, x_case_t=case_t, x_zone_t=zone_t,
                            **self.fit_result_low_01.params)

        return model.food_t


    def case_low_02(self):
        """learn the foodT, based on sat/rat/zoneT/zoneW"""

        x_sat, x_rat, x_case_t, x_zone_t, food_t = \
            variables('x_sat, x_rat, x_case_t, x_zone_t, food_t')
        a, b, c, d = parameters('a, b, c, d')

        z_component = a * x_sat + b * x_rat + c * x_case_t + d * sin(-x_zone_t*0.01)
        model_dict = {
            food_t: z_component,
        }

        self.fit_low_02 = Fit(model_dict, x_sat=self.low_02_saT, x_rat=self.low_02_raT,
                              x_case_t=self.low_02_caseT, x_zone_t=self.low_02_zoneT,
                  food_t=self.low_02_foodT)
        self.fit_result_low_02 = self.fit_low_02.execute()

        return (self.fit_low_02, self.fit_result_low_02)

    def predict_case_low_02(self, sat, rat, case_t, zone_t, zone_w):
        model = self.fit_low_02.model(x_sat=sat, x_rat=rat, x_case_t=case_t, x_zone_t=zone_t, \
                           **self.fit_result_low_02.params)

        return model.food_t
