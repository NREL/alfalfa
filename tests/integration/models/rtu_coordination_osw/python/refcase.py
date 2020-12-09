import numpy as np
import pysindy as ps
from scipy.integrate import odeint
from scipy.interpolate import interp1d
import csv
from scipy.signal import savgol_filter
from mycurvefit import *
from pyenergyplus.plugin import EnergyPlusPlugin

class CaseModel(EnergyPlusPlugin):

    def __init__(self):

        super().__init__()
        self.need_to_get_handles = True

        self.zone_mean_air_temp_hndl = None
        self.case_avail_sch_hndl = None
        self.alfalfa_fan_hndl = None
        self.alfalfa_fan_enable_hndl = None
        self.t_food_hndl = None
        self.t_case_hndl = None
        self.clg_setpt_hndl = None

        self.t_zone = float()
        self.comp_on = bool()
        self.alfalfa_fan = int()
        self.alfalfa_fan_enable = int()
        self.t_food = float()
        self.t_case = float()
        self.comp_time = int()

        self.t_food = 34
        self.t_case = 36
        self.comp_time = 1

    def read_measurement_data(csv_file):
        with open(csv_file) as csvfile:
            reader = csv.DictReader(csvfile)
            T_food = []
            T_air = []
            T_sa = []
            T_evap = []
            T_cond = []
            T_amb = []
            T_SST = []
            T_SCT = []
            csvfile.seek(0)
            reader = csv.DictReader(csvfile)
            for row in reader:
                T_food.append( np.float64( row['Sim 3']) )
                T_air.append(np.float64(row['Case T-Stat Bulb Temp']))
                T_sa.append( np.float64(row['Case Air Discharge Temp']) )
                T_evap.append(np.float64(row['Evap Coil Outlet Temp at TXV Bulb']))
                T_cond.append(np.float64(row['Liquid Temp Enter TXV']))
                T_amb.append(np.float64(row['Cond Air Inlet Temp']))
                T_SST.append(np.float64(row['Saturated Suction']))
                T_SCT.append(np.float64(row['Saturated Liquid']))


        T_food = np.asarray(T_food)
        T_air = np.asarray(T_air)
        T_sa = np.asarray(T_sa)
        T_evap = np.asarray(T_evap)
        T_cond = np.asarray(T_cond)
        T_amb = np.asarray(T_amb)
        T_SST = np.asarray(T_SST)
        T_SCT = np.asarray(T_SCT)


        t_train = np.arange(0, len(T_food) * 60, 60)
        t_finer = np.arange(0, len(T_food) * 60, 1)
        T_food = interpolate(t_train, T_food, t_finer)
        T_air = interpolate(t_train, T_air, t_finer)
        T_sa = interpolate(t_train, T_sa, t_finer)
        T_evap = interpolate(t_train, T_evap, t_finer)
        T_cond = interpolate(t_train, T_cond, t_finer)
        T_amb = interpolate(t_train, T_amb, t_finer)
        T_SST = interpolate(t_train, T_SST, t_finer)
        T_SCT = interpolate(t_train, T_SCT, t_finer)


        return (T_food, T_air, T_sa, T_evap, T_cond, T_amb, T_SST, T_SCT)

    def polyfit_SAT_SSTSCT(self, coeff, sat):
        """
        (1)get the SST or SCT from given SAT;
        (2)polynomial is 4th order
        """
        temp = coeff[0] * sat**4 + coeff[1] * sat**3 +coeff[2] * sat**2 +coeff[3] * sat**1 + coeff[4]
        return np.asarray(temp)

    def model_supply_air(self, compressor_on, compressorON_time):
        """
        purpose: a regression model to estimate supply-air-temperature of refrigeration case
        input: compressor_on, discrete value, 0 or 1, unit = none
               compressorON_time is the time compressor on, unit = minutes
        output: supply air temperature, unit = Fahrenheit degree
        """
        # note: coefficients below are from linear regression
        coeff_compressorON = -2.632
        coeff_compressorON_Time = -0.08039
        coeff_compressorON_Time_square = 0.0002817
        intercept = 38.67
        sat = coeff_compressorON * compressor_on + coeff_compressorON_Time * compressorON_time + \
              coeff_compressorON_Time_square * compressorON_time**2 + intercept
        if sat > 80:
            sat = 75
        #print(f'sat={sat}')

        return np.array(sat)

    def food_modeling_learn(T_food, T_air, T_sa, T_amb, T_SST, T_SCT, time_step):
        """
        Note: To learn the coefficients of ODE equations.
              We need historical data here.
        Input variables:
            T_food: is the historical food temperature, 1d numpy array.
            T_air: is the historical case internal air temperature, 1d numpy array.
            T_sa: is the historical case internal supply air temperature, 1d numpy array.
            T_amb: is the historical zone air temperature, 1d numpy array.
            T_SST: is the historical saturated suction  temperature,
                    or the refrigerant temperature at evaporator outlet, 1d numpy array.
            T_SCT: is the historical saturated condensing  temperature,
                    or the refrigerant temperature at condenser outlet, 1d numpy array,
            time_step: time step size, in seconds.
                Note1: [T_sa, T_amb, T_SST, T_SCT] are the control inputs.
                Note2: [T_sa, T_amb] is the minimum required control inputs.
                Note3: the control inputs might need a trial to be determined, based on the quality of data.
        Output variables:
           coeff: contains the coefficients of ODE equations. 2d array
        """
        # step-1: collect variables to be used/learnt for identification.
        x_train = np.concatenate((T_food.reshape(-1, 1), T_air.reshape(-1, 1)), axis=1)

        # step-2: time step and range
        dt = time_step

        # step-3: control variables to be used
        control_vars = np.concatenate( ( T_amb.reshape(-1, 1), T_sa.reshape(-1, 1), T_SST.reshape(-1,1), T_SCT.reshape(-1,1) ), axis=1)
        #print( "learning: control-vars shape: ", control_vars.shape)
        # step-4: do system identification to get coefficients of the ODEmodel
        threshold = 0.00000000000001
        poly_order = 1 # the order =1 is predetermined
        model = ps.SINDy(
            optimizer=ps.STLSQ(threshold=threshold),
            feature_library=ps.PolynomialLibrary(degree=poly_order),
        )

        model.fit(x_train, u=control_vars, t=dt)
        # model.print()
        coeff = model.coefficients()  # this is what i am trying to get from system-identification
        #print("Initial learnt coefficient: ", coeff)

        # step-5: write to csv file
        with open('coeff_case3_final_001.csv', 'w') as fh:
            writer = csv.writer(fh, delimiter=',')
            writer.writerow(['b', 'x0','x1','u0','u1','u2','u3'])
            writer.writerows(coeff)

        return coeff


    def read_coeff_coolingcase(self, csv_filename):
        """read csv file for coefficients
           dx0/dt = b0 + a0 * x0 + a1 * x1 + c0 * u0 + c1 * u1
           dx1/dt = k0 + w0 * x0 + w1 * x1 + h0 * u0 + h1 * u1
           where x0, x1 are the variables to be solved. x0 == Tfood, x1 ==Tair
           b0, a0, a1, c0, c1, c2, c3 are the coefficients for x0
           k0, w0, w1, h0, h1, h2, h3 are the coefficients for x1
           u0, u1, u2, u3 are the control inputs.
        """
        with open(csv_filename,'r') as f:
            x = f.readlines()
            coeff= np.zeros( (2, len(x[2].split(',')) ))

            for i, z in enumerate(x[2].split(',')):
                coeff[0,i] = float(z)
            for j, v in enumerate(x[4].split(',')):
                coeff[1,j] = float(v)

            return coeff

    def read_coeff_SAT_SST(self, csv_filename):
        """read csv file for coefficients: SAT-SST
           y = p4*x^4 + p3*x^3 + p2*x^2 + p1*x^1 + p0*x^0
           where x0, x1 are the variables to be solved. x0 == Tfood, x1 ==Tair
           p4, p3, p2, p1, p0 are the coefficients of polynomial curve fitting
        """
        with open(csv_filename,'r') as f:
            x = f.readlines()
            #print(x)
            coeff= np.zeros( (1, len(x[0].split(',')) ))

            for i, z in enumerate(x[2].split(',')):
                coeff[0,i] = float(z)
            #print('Yanfei: coeff check: ', coeff)
            return coeff.flatten()

    def read_coeff_SAT_SCT(self, csv_filename):
        """read csv file for coefficients: SAT-SCT
           y = p4*x^4 + p3*x^3 + p2*x^2 + p1*x^1 + p0*x^0
           where x0, x1 are the variables to be solved. x0 == Tfood, x1 ==Tair
           p4, p3, p2, p1, p0 are the coefficients of polynomial curve fitting
        """
        with open(csv_filename,'r') as f:
            x = f.readlines()
            #print(x)
            coeff= np.zeros( (1, len(x[0].split(',')) ))

            for i, z in enumerate(x[2].split(',')):
                coeff[0,i] = float(z)
            #print('Yanfei: coeff check: ', coeff)
            return coeff.flatten()


    def interpolate(t, x, t_new):
        # interpolate data
        f = interp1d(t, x, axis=0, kind='cubic', fill_value='extrapolate')
        new_x = f(t_new)
        # add noise to data
        #new_x = new_x + np.random.uniform(-0.1, 0.1, 1)
        # smooth data by filtering
        #new_x = savgol_filter(new_x, 21, 3)

        return new_x


    def food_modeling_validate():
        # step-1: collect all essential data
        file_base = "C:/Users/YLI3/Yanfei_Projects/Emerson/EmersonData/"
        csv_file_measurement = file_base + 'Selected_112164 4 Foot Open Case_SC CDU_ 24Hr.csv'
        (T_food, T_air, T_sa, T_evap, T_cond, T_zone, T_SST, T_SCT) = read_measurement_data(csv_file_measurement)
        # print("read tfood measurement data: ", T_food.shape)
        csv_file_coeff = 'coeff_case3_final_001.csv'
        coeff = read_coeff_coolingcase(csv_file_coeff)

        # step-2: initial condition, T_air and T_food
        x0_init= [T_food[0], T_air[0]]

        # step-3: time step and range
        dt = 1 # seconds

        f_sat_sst = fit_sat_sst(T_sa, T_SST)
        f_sat_sct = fit_sat_sct(T_sa, T_SCT)
        #print('sat-sst curve fitting: ', f_sat_sst)
        #print('sat-sct curve fitting: ', f_sat_sct)

        SST_repr = []
        SCT_repr = []
        for i, x in enumerate(T_sa):
            SST_repr.append(f_sat_sst(T_sa[i]))
            SCT_repr.append(f_sat_sct(T_sa[i]))

        SST_repr = np.asarray(SST_repr)
        SCT_repr = np.asarray(SCT_repr)

        read_coeff_SAT_SST("coeff_SAT_SCT_emerson_001.csv")

        # step-4: control variables to be used
        control_inputs = np.concatenate( ( T_zone.reshape(-1, 1), T_sa.reshape(-1, 1), SST_repr.reshape(-1,1), SCT_repr.reshape(-1,1) ), axis=1)
        #control_inputs = np.concatenate( (T_zone.reshape(-1,1), T_sa.reshape(-1,1)), axis=1)
        #print("validate control inputs: ", control_inputs.shape)
        ###########################################################################################
        # step-6: set up ODE
        ###########################################################################################
        def diff_fun(x, t, coeff, control_inputs):
            # construct the ODE equations.
            dt = 1 # attention: dt=1 after interpolation
            i = int(t/dt)
            if i>=len(control_inputs[:,0]):
                i=len(control_inputs[:,0])-1
            u0 = control_inputs[i,0]
            u1 = control_inputs[i,1]
            u2 = control_inputs[i,2]
            u3 = control_inputs[i,3]
            # variables to solve
            x0 = x[0] # Tfood
            x1 = x[1] # Tair
            dxdt = [
                coeff[0, 0] + coeff[0, 1] * x0 + coeff[0, 2] * x1 + coeff[0, 3] * u0 + coeff[0, 4] * u1 + coeff[0, 5] * u2 + coeff[0, 6] * u3,
                coeff[1, 0] + coeff[1, 1] * x0 + coeff[1, 2] * x1 + coeff[1, 3] * u0 + coeff[1, 4] * u1 + coeff[1, 5] * u2 + coeff[1, 6] * u3,
                ]
            return dxdt

        ###########################################################################################
        # step-7: solve ODE equations with learnt coefficients
        ###########################################################################################
        # x_test is a 2D array, with predicted results: T_air, T_food
        t_valid = np.linspace(0, len(T_food)*dt, len(T_food))
        # print("t_valid: ", t_valid)

        x_validate = odeint(diff_fun, x0_init, t_valid, args=(coeff, control_inputs) )

        return x_validate


    def food_modeling_solve(self, state, T_food_init: float, T_air_init: float, T_zone_cur: float, compressor_on: bool, compressorON_time: int, steps_cur: int) -> tuple:
        """
        Input variables:
           T_food_init: is the initial food temperature; T_food,n-1
           T_air_init: is the initial air temperature in the case, or setpoint; T_case_air,n-1
           T_zone_cur: is the current zone temperature; T_zone,n
           compressor_on: compressor on or off; comp_bool,n (1=on, 0=off)
           compressorON_time: minutes; sum of comp_bool,i ... comp_bool,n-1 (i resets each time compressor shuts off)
           steps_cur: current time steps, in minutes; always 1
        Output variables:
           T_food: predicted food temperature;
           T_air: predicted air temperature;
        """

        # step-1: collect all essential data
        csv_file_coeff = 'coeff_case3_final_001.csv'
        coeff_case = self.read_coeff_coolingcase(csv_file_coeff)

        T_sa_cur = self.model_supply_air(compressor_on, compressorON_time)

        coeff_SATSST = self.read_coeff_SAT_SST('coeff_SAT_SST_emerson_001.csv')
        coeff_SATSCT = self.read_coeff_SAT_SCT('coeff_SAT_SCT_emerson_001.csv')

        SST_cur = self.polyfit_SAT_SSTSCT(coeff_SATSST, T_sa_cur)
        SCT_cur = self.polyfit_SAT_SSTSCT(coeff_SATSCT, T_sa_cur)
        #print("Yanfei polyfit check: ", SST_cur, SCT_cur)

        # step-2: initial condition, T_air and T_food
        x0_train = [T_food_init, T_air_init]

        # step-3: time step and range
        dt = 60 # seconds, because timestep from EnergyPlus is 1 minute.
        t_cur = steps_cur * dt
        T_zone_cur = np.asarray(T_zone_cur)
        # step-4: control variables to be used
        control_inputs = np.concatenate( (T_zone_cur.reshape(-1,1), T_sa_cur.reshape(-1,1), \
                                          SST_cur.reshape(-1,1), SCT_cur.reshape(-1,1)), axis=1)
        # print("Yanfei control inputs: ", control_inputs.shape)
        ###########################################################################################
        # step-6: set up ODE
        ###########################################################################################
        def diff_fun(x, t, coeff, control_inputs):
            # construct the ODE equations.
            dt = 1 # attention: dt=1 after interpolation
            i = int(t/dt)
            if i>=len(control_inputs[:,0]):
                i=len(control_inputs[:,0])-1
            u0 = control_inputs[i,0]
            u1 = control_inputs[i,1]
            u2 = control_inputs[i,2]
            u3 = control_inputs[i,3]

            # variables to solve
            x0 = x[0] # Tfood
            x1 = x[1] # Tair
            dxdt = [
                coeff[0, 0] + coeff[0, 1] * x0 + coeff[0, 2] * x1 + coeff[0, 3] * u0 + coeff[0, 4] * u1 +\
                coeff[0, 5] * u2 + coeff[0, 6] * u3,
                coeff[1, 0] + coeff[1, 1] * x0 + coeff[1, 2] * x1 + coeff[1, 3] * u0 + coeff[1, 4] * u1 + \
                coeff[1, 5] * u2 + coeff[1, 6] * u3,
                ]
            return dxdt

        ###########################################################################################
        # step-7: solve ODE equations with learnt coefficients
        ###########################################################################################
        # x_test is a 2D array, with predicted results: T_air, T_food
        t_solve = np.linspace(0, t_cur, num=60)
        #print ("t_solve shape: ", t_solve.shape )
        #print("t-solve: ", t_solve)
        x_solve = odeint(diff_fun, x0_train, t_solve, args=(coeff_case, control_inputs) )


        return (x_solve[-1,0], x_solve[-1,1])

    def rtu_cyc(self, state) -> int:

        time = self.api.exchange.current_time(state)

        if len(str(time)) <= 5:
            result = 1
        else:
            result = 0

        return result

    def on_begin_timestep_before_predictor(self, state) -> int:

        if not self.api.exchange.api_data_fully_ready(state):
            return 0

        if self.need_to_get_handles:
            self.zone_mean_air_temp_hndl = self.api.exchange.get_variable_handle(state, "Zone Mean Air Temperature", "Zn1")
            self.case_avail_sch_hndl = self.api.exchange.get_variable_handle(state, "Schedule Value", "Case Avail Sch")
            self.alfalfa_fan_hndl = self.api.exchange.get_variable_handle(state, "EMS", "FanOnOff")
            self.alfalfa_fan_enable_hndl = self.api.exchange.get_variable_handle(state, "EMS", "FanOnOff_Enable")
            self.t_food_hndl = self.api.exchange.get_global_handle(state, "t_food")
            self.t_case_hndl = self.api.exchange.get_global_handle(state, "t_case")
            self.clg_setpt_hndl = self.api.exchange.get_actuator_handle(state, "Schedule:Constant", "Schedule Value", "Clg Setpt Sch")
            self.need_to_get_handles = False

        self.alfalfa_fan_enable = 1
        self.alfalfa_fan = self.rtu_cyc(state)

        if self.alfalfa_fan:
            self.api.exchange.set_actuator_value(state, self.clg_setpt_hndl, 15)
        else:
            self.api.exchange.set_actuator_value(state, self.clg_setpt_hndl, 50)

        self.t_zone = self.api.exchange.get_variable_value(state, self.zone_mean_air_temp_hndl)
        self.t_zone = (self.t_zone * (9/5)) + 32
        self.comp_on = self.api.exchange.get_variable_value(state, self.case_avail_sch_hndl)

        if self.comp_on == 0:
            self.comp_time = 0
        else:
            self.comp_time = self.comp_time + self.comp_on

        self.t_food, self.t_case = self.food_modeling_solve(self, self.t_food, self.t_case, self.t_zone, self.comp_on, self.comp_time, 1)

        self.api.exchange.set_global_value(state, self.t_food_hndl, self.t_food)
        self.api.exchange.set_global_value(state, self.t_case_hndl, self.t_case)

        return 0
