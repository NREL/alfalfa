# Author: Nicholas Long / Sourav Dey

import datetime
import json
import os
import sys
import time
from unittest import TestCase

import pytest
from alfalfa_client.alfalfa_client import AlfalfaClient
from alfalfa_client.historian import Historian

from alfalfa_worker.lib.thermal_comfort import ThermalComfort
from alfalfa_worker.lib.unit_conversions import deg_k_to_c


# This test case is a single zone VAV with basic control. The file comes from the
# RL project repo here: https://github.com/nllong/alfalfa-rl-project/
def compute_control(y, reward, time, heating_setpoint, cooling_setpoint):
    """
    y has any of the accessible model outputs such as the cooling power etc.
    costs are the caclulated costs for the latest timestep, including PMV

    :param y: Temperature of zone, K
    :param heating_setpoint: Temperature Setpoint, C
    :return: dict, control input to be used for the next step {<input_name> : <input_value>}
    """
    # Controller parameters
    setpoint = heating_setpoint + 273.15
    k_fan = 3.5
    # Compute control
    e = setpoint - y['TRooAir_y']  # 275-273 = 2 deg C
    value = min(max(k_fan * e, 0), 0.45)

    result = {
        'u': {
            'oveUSetFan_u': value
        },
        'historian': {
            'oveTSetRooHea_u': heating_setpoint + 273.15,  # + random.randint(-4, 1),
            'oveTSetRooCoo_u': cooling_setpoint + 273.15,  # + random.randint(-1, 4)
            'oveUSetFan_u': y['senUSetFan_y'],
        }
    }

    return result


def compute_rewards(y, timestamp):
    # Assumptions:
    #   Occupied hours: 8 - 18
    #   TRadiant is 1.5 degC lower than room drybulb -- rough assumption. Need from model.
    #   met is 1.2 (office filing seated)
    #   clo is 1 clo for winter
    #   vel is 0.2 m/s
    #   rh is 50

    power = y['PCoo_y'] + y['PHea_y'] + y['PFan_y'] + y['PPum_y']

    if datetime.time(8, 00) < timestamp.time() < datetime.time(18, 00):
        pmv, ppd = ThermalComfort.pmv_ppd(y['TRooAir_y'] - 273.15, y['TRooRad_y'] - 273.15, 1.20, 1, 0.2, 50)
    else:
        pmv = 0
        ppd = 0

    # calculate scalar - both energy and ppd should be minimized, but reward is maximized
    # power is between 0 and ~ 7000. Assume max at 10,000 W. 7000/10000 = 0.7 * 10 = 7 E [0, 10]
    # ppd is between 0 and 100 E [0,100]
    # reward E [-100, 0]
    reward = -1 * (power / 1000 + ppd)

    all_data = {
        'pmv': pmv,
        'ppd': ppd,
        'power': power,
        'reward': reward,
    }

    return reward, all_data


def initialize_control(heating_setpoint, cooling_setpoint):
    """Initialize the control input u.

    Parameters
    ----------
    None

    Returns
    -------
    u : dict
        Defines the control input to be used for the next step.
        {<input_name> : <input_value>}

    """

    result = {
        'u': {
            'oveTSetRooHea_u': heating_setpoint + 273.15,
            'oveTSetRooCoo_u': cooling_setpoint + 273.15,
        },
        'historian': {
            'oveTSetRooHea_u': heating_setpoint + 273.15,
            'oveTSetRooCoo_u': cooling_setpoint + 273.15,
            'oveUSetFan_u': 0.2,
        }
    }
    return result


@pytest.mark.integration
class TestSimpleFMUControl(TestCase):

    @pytest.mark.skip
    def test_control(self):
        alfalfa = AlfalfaClient(url='http://localhost')

        # Denver weather
        # 1/1/2019 00:00:00  - Note that we have to start at 1/1 right now.
        datetime.datetime(2019, 1, 1, 0, 0, 0)
        start_time = datetime.datetime(2019, 1, 2, 0, 0, 0)
        end_time = datetime.datetime(2019, 1, 3, 0, 0, 0)

        step = 300  # 5 minutes
        sim_steps = int((end_time - start_time).total_seconds() / step)  # total time (in seconds) / 5 minute steps

        heating_setpoint = 21
        cooling_setpoint = 25
        u = initialize_control(heating_setpoint, cooling_setpoint)

        file = os.path.join(os.path.dirname(__file__), 'files', 'single_zone_vav.fmu')
        print(f"Uploading test case {file}")
        site = alfalfa.submit(file)

        print('Starting simulation')
        # all simulations start at time = 0 right now.
        alfalfa.start(
            site,
            external_clock="true",
            end_datetime=end_time,
        )

        historian = Historian(5)
        historian.add_point('timestamp', 'Time', None)
        historian.add_point('T1', 'degC', 'TRooAir_y', f_conversion=deg_k_to_c)
        historian.add_point('T1_Rad', 'degC', 'TRooRad_y', f_conversion=deg_k_to_c)
        historian.add_point('Toutdoor', 'degC', 'TOutdoorDB_y', f_conversion=deg_k_to_c)
        historian.add_point('CoolingPower', 'W', 'PCoo_y')
        historian.add_point('HeatingPower', 'W', 'PHea_y')
        historian.add_point('FanPower', 'W', 'PFan_y')
        historian.add_point('PumpPower', 'W', 'PPum_y')
        historian.add_point('TotalHVACPower', 'W', 'power')
        historian.add_point('TotalHVACEnergy', 'Ws', 'ECumuHVAC_y')  # I think this is in Watt-seconds! (sorry)
        historian.add_point('HeatingSetpoint', '', 'senTSetRooHea_y', f_conversion=deg_k_to_c)
        historian.add_point('CoolingSetpoint', '', 'senTSetRooCoo_y', f_conversion=deg_k_to_c)
        historian.add_point('FanControlInput', '', 'senUSetFan_y')
        historian.add_point('u_CoolingSetpoint', '', 'oveTSetRooCoo_u', f_conversion=deg_k_to_c)
        historian.add_point('u_HeatingSetpoint', '', 'oveTSetRooHea_u', f_conversion=deg_k_to_c)
        historian.add_point('u_FanOverride', '', 'oveUSetFan_u')
        historian.add_point('PMV', '', 'pmv')
        historian.add_point('PPD', '', 'ppd')
        historian.add_point('Reward', '', 'reward')
        print('Stepping through time')
        for i in range(sim_steps):
            current_time = start_time + datetime.timedelta(seconds=(i * step))
            alfalfa.setInputs(site, u['u'])
            alfalfa.advance([site])
            model_outputs = alfalfa.outputs(site)
            sys.stdout.flush()

            reward_scalar, all_rewards = compute_rewards(model_outputs, current_time)
            historian.add_data(all_rewards)

            # if datetime.time(8, 00) < current_time.time() < datetime.time(18, 00):
            #     heating_setpoint = 21 + 273.15
            #     cooling_setpoint = 25 + 273.15
            # else:
            #     heating_setpoint = 16 + 273.15
            #     cooling_setpoint = 29 + 273.15
            u = compute_control(model_outputs, reward_scalar, current_time, heating_setpoint, cooling_setpoint)
            historian.add_data(u['historian'])

            print(f'Running time: {current_time.strftime("%m/%d/%Y %H:%M:%S")}')
            historian.add_datum('timestamp', current_time)
            historian.add_data(model_outputs)

            # throttle the requests a bit
            time.sleep(0.05)

        alfalfa.stop(site)

        # storage for results
        file_basename = os.path.splitext(os.path.basename(__file__))[0]
        result_dir = os.path.join(os.path.dirname(__file__), 'output', file_basename)
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
        historian.save_csv(result_dir, 'data.csv')
        historian.save_pickle(result_dir, 'data.pkl')
        print(historian.to_df().describe())
        kpis = historian.evaluate_performance()
        with open(f'{result_dir}/kpis_result.json', 'w') as f:
            f.write(json.dumps(kpis, indent=2))
        print(kpis)

        self.assertTrue(os.path.exists(f'{result_dir}/data.csv'))
        self.assertTrue(os.path.exists(f'{result_dir}/kpis_result.json'))
        self.assertAlmostEqual(kpis["total_hours"], 24, delta=1)
        self.assertAlmostEqual(kpis["total_hours_occupied"], 10, delta=1)
        self.assertAlmostEqual(kpis["total_hvac_energy"], 40, delta=5)
        self.assertAlmostEqual(kpis["total_hvac_energy_occupied"], 4, delta=2)
        self.assertAlmostEqual(kpis["average_ppd_occupied"], 65, delta=5)
