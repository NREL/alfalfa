from pyenergyplus.plugin import EnergyPlusPlugin
import case_models as cm
import case_cooling_to_zone as c2z

class CaseModel(EnergyPlusPlugin):

    def __init__(self):

        super().__init__()
        self.psych = None
        self.need_to_get_handles = True

        self.t_zone_hndl = None
        self.rh_zone_hndl = None
        self.mt1_case_avail_sch_hndl = None
        self.mt1_case_credit_sch_hndl = None
        self.mt1_t_supply_hndl = None
        self.mt1_t_return_hndl = None
        self.mt1_t_case_hndl = None
        self.mt1_t_food_hndl = None
        self.mt2_case_avail_sch_hndl = None
        self.mt2_case_credit_sch_hndl = None
        self.mt2_t_supply_hndl = None
        self.mt2_t_return_hndl = None
        self.mt2_t_case_hndl = None
        self.mt2_t_food_hndl = None
        self.lt1_case_avail_sch_hndl = None
        self.lt1_case_credit_sch_hndl = None
        self.lt1_t_supply_hndl = None
        self.lt1_t_return_hndl = None
        self.lt1_t_case_hndl = None
        self.lt1_t_food_hndl = None
        self.lt2_case_avail_sch_hndl = None
        self.lt2_case_credit_sch_hndl = None
        self.lt2_t_supply_hndl = None
        self.lt2_t_return_hndl = None
        self.lt2_t_case_hndl = None
        self.lt2_t_food_hndl = None

        self.t_zone = float()
        self.rh_zone = float()
        self.mt1_case_on = bool()
        self.mt1_t_supply = float()
        self.mt1_t_return = float()
        self.mt1_t_case = float()
        self.mt1_t_food = float()
        self.mt1_q_case = float()
        self.mt2_case_on = bool()
        self.mt2_t_supply = float()
        self.mt2_t_return = float()
        self.mt2_t_case = float()
        self.mt2_t_food = float()
        self.mt2_q_case = float()
        self.lt1_case_on = bool()
        self.lt1_t_supply = float()
        self.lt1_t_return = float()
        self.lt1_t_case = float()
        self.lt1_t_food = float()
        self.lt1_q_case = float()
        self.lt2_case_on = bool()
        self.lt2_t_supply = float()
        self.lt2_t_return = float()
        self.lt2_t_case = float()
        self.lt2_t_food = float()
        self.lt2_q_case = float()

        self.mt1_q_case_nom = -1 * 1456.754 * 2.445
        self.mt2_q_case_nom = -1 * 168.889 * 3.896
        self.lt1_q_case_nom = -1 * 382.321 * 2.349
        self.lt2_q_case_nom = -1 * 382.321 * 2.349

        self.case_model = cm.CaseModels("mt-door_data.csv","mt-open_data.csv","lt1_data.csv","lt2_data.csv")
        self.case_model.read_case_medium_door()
        self.case_model.read_case_medium_open()
        self.case_model.read_case_low_01()
        self.case_model.read_case_low_02()
        self.case_model.case_medium_door()
        self.case_model.case_medium_open()
        self.case_model.case_low_01()
        self.case_model.case_low_02()

    def on_begin_timestep_before_predictor(self,state) -> int:

        if not self.psych:
            self.psych = self.api.functional.psychrometrics(state)

        if not self.api.exchange.api_data_fully_ready(state):
            return 0

        if self.need_to_get_handles:
            self.t_zone_hndl = self.api.exchange.get_variable_handle(state,"Zone Air Temperature","Zn1")
            self.rh_zone_hndl = self.api.exchange.get_variable_handle(state,"Zone Air Relative Humidity","Zn1")
            self.mt1_case_avail_sch_hndl = self.api.exchange.get_variable_handle(state,"Schedule Value","MT1 Avail Sch")
            self.mt1_case_credit_sch_hndl = self.api.exchange.get_actuator_handle(state,"Schedule:Constant","Schedule Value","MT1 Credit Sch")
            self.mt1_t_supply_hndl = self.api.exchange.get_global_handle(state,"mt1_t_supply")
            self.mt1_t_return_hndl = self.api.exchange.get_global_handle(state,"mt1_t_return")
            self.mt1_t_case_hndl = self.api.exchange.get_global_handle(state,"mt1_t_case")
            self.mt1_t_food_hndl = self.api.exchange.get_global_handle(state,"mt1_t_food")
            self.mt2_case_avail_sch_hndl = self.api.exchange.get_variable_handle(state,"Schedule Value","MT2 Avail Sch")
            self.mt2_case_credit_sch_hndl = self.api.exchange.get_actuator_handle(state,"Schedule:Constant","Schedule Value","MT2 Credit Sch")
            self.mt2_t_supply_hndl = self.api.exchange.get_global_handle(state,"mt2_t_supply")
            self.mt2_t_return_hndl = self.api.exchange.get_global_handle(state,"mt2_t_return")
            self.mt2_t_case_hndl = self.api.exchange.get_global_handle(state,"mt2_t_case")
            self.mt2_t_food_hndl = self.api.exchange.get_global_handle(state,"mt2_t_food")
            self.lt1_case_avail_sch_hndl = self.api.exchange.get_variable_handle(state,"Schedule Value","LT1 Avail Sch")
            self.lt1_case_credit_sch_hndl = self.api.exchange.get_actuator_handle(state,"Schedule:Constant","Schedule Value","LT1 Credit Sch")
            self.lt1_t_supply_hndl = self.api.exchange.get_global_handle(state,"lt1_t_supply")
            self.lt1_t_return_hndl = self.api.exchange.get_global_handle(state,"lt1_t_return")
            self.lt1_t_case_hndl = self.api.exchange.get_global_handle(state,"lt1_t_case")
            self.lt1_t_food_hndl = self.api.exchange.get_global_handle(state,"lt1_t_food")
            self.lt2_case_avail_sch_hndl = self.api.exchange.get_variable_handle(state,"Schedule Value","LT2 Avail Sch")
            self.lt2_case_credit_sch_hndl = self.api.exchange.get_actuator_handle(state,"Schedule:Constant","Schedule Value","LT2 Credit Sch")
            self.lt2_t_supply_hndl = self.api.exchange.get_global_handle(state,"lt2_t_supply")
            self.lt2_t_return_hndl = self.api.exchange.get_global_handle(state,"lt2_t_return")
            self.lt2_t_case_hndl = self.api.exchange.get_global_handle(state,"lt2_t_case")
            self.lt2_t_food_hndl = self.api.exchange.get_global_handle(state,"lt2_t_food")

            self.need_to_get_handles = False

        self.t_zone = self.api.exchange.get_variable_value(state,self.t_zone_hndl)
        self.rh_zone = self.api.exchange.get_variable_value(state,self.rh_zone_hndl)
        self.mt1_case_on = self.api.exchange.get_variable_value(state,self.mt1_case_avail_sch_hndl)
        self.mt2_case_on = self.api.exchange.get_variable_value(state,self.mt2_case_avail_sch_hndl)
        self.lt1_case_on = self.api.exchange.get_variable_value(state,self.lt1_case_avail_sch_hndl)
        self.lt2_case_on = self.api.exchange.get_variable_value(state,self.lt2_case_avail_sch_hndl)

        self.t_zone = (self.t_zone * (9/5)) + 32

        if self.mt1_case_on == 0:
            self.mt1_t_supply = 68
            self.mt1_t_return = 54
            self.mt1_t_case = self.mt1_t_return
        elif self.mt1_case_on == 1:
            self.mt1_t_supply = 36
            self.mt1_t_return = 44
            self.mt1_t_case = self.mt1_t_supply + ((self.mt1_t_return - self.mt1_t_supply) / 2)

        if self.mt2_case_on == 0:
            self.mt2_t_supply = 39.5
            self.mt2_t_return = self.mt2_t_supply - 0.5
            self.mt2_t_case = self.mt2_t_return - 2
        elif self.mt2_case_on == 1:
            self.mt2_t_supply = 36
            self.mt2_t_return = 37
            self.mt2_t_case = self.mt2_t_supply + ((self.mt2_t_return - self.mt2_t_supply) / 2)

        if self.lt1_case_on == 0:
            self.lt1_t_supply = 55
            self.lt1_t_return = 35
            self.lt1_t_case = 40
        elif self.lt1_case_on == 1:
            self.lt1_t_supply = -20
            self.lt1_t_return = -16
            self.lt1_t_case = -21

        if self.lt2_case_on == 0:
            self.lt2_t_supply = 12
            self.lt2_t_return = 20
            self.lt2_t_case = -2
        elif self.lt2_case_on == 1:
            self.lt2_t_supply = -12
            self.lt2_t_return = -14
            self.lt2_t_case = -15

        self.mt1_t_food = self.case_model.predict_case_medium_open(self.mt1_t_supply,self.mt1_t_return,self.mt1_t_case,self.t_zone,self.rh_zone)[0]
        self.mt2_t_food = self.case_model.predict_case_medium_door(self.mt2_t_supply,self.mt2_t_return,self.mt2_t_case,self.t_zone)[0]
        self.lt1_t_food = self.case_model.predict_case_low_01(self.lt1_t_supply,self.lt1_t_return,self.lt1_t_case,self.t_zone,self.rh_zone)[0]
        self.lt2_t_food = self.case_model.predict_case_low_02(self.lt2_t_supply,self.lt2_t_return,self.lt2_t_case,self.t_zone,self.rh_zone)[0]

        self.mt1_q_case = c2z.case_cooling_to_zone(((self.mt1_t_case - 32) * (5/9)),((self.t_zone - 32) * (5/9)))
        self.mt2_q_case = c2z.case_cooling_to_zone(((self.mt2_t_case - 32) * (5/9)),((self.t_zone - 32) * (5/9)))
        self.lt1_q_case = c2z.case_cooling_to_zone(((self.lt1_t_case - 32) * (5/9)),((self.t_zone - 32) * (5/9)))
        self.lt2_q_case = c2z.case_cooling_to_zone(((self.lt2_t_case - 32) * (5/9)),((self.t_zone - 32) * (5/9)))

        self.api.exchange.set_actuator_value(state,self.mt1_case_credit_sch_hndl,(self.mt1_q_case / self.mt1_q_case_nom))
        self.api.exchange.set_global_value(state,self.mt1_t_supply_hndl,self.mt1_t_supply)
        self.api.exchange.set_global_value(state,self.mt1_t_return_hndl,self.mt1_t_return)
        self.api.exchange.set_global_value(state,self.mt1_t_case_hndl,self.mt1_t_case)
        self.api.exchange.set_global_value(state,self.mt1_t_food_hndl,self.mt1_t_food)
        self.api.exchange.set_actuator_value(state,self.mt2_case_credit_sch_hndl,(self.mt2_q_case / self.mt2_q_case_nom))
        self.api.exchange.set_global_value(state,self.mt2_t_supply_hndl,self.mt2_t_supply)
        self.api.exchange.set_global_value(state,self.mt2_t_return_hndl,self.mt2_t_return)
        self.api.exchange.set_global_value(state,self.mt2_t_case_hndl,self.mt2_t_case)
        self.api.exchange.set_global_value(state,self.mt2_t_food_hndl,self.mt2_t_food)
        self.api.exchange.set_actuator_value(state,self.lt1_case_credit_sch_hndl,(self.lt1_q_case / self.lt1_q_case_nom))
        self.api.exchange.set_global_value(state,self.lt1_t_supply_hndl,self.lt1_t_supply)
        self.api.exchange.set_global_value(state,self.lt1_t_return_hndl,self.lt1_t_return)
        self.api.exchange.set_global_value(state,self.lt1_t_case_hndl,self.lt1_t_case)
        self.api.exchange.set_global_value(state,self.lt1_t_food_hndl,self.lt1_t_food)
        self.api.exchange.set_actuator_value(state,self.lt2_case_credit_sch_hndl,(self.lt2_q_case / self.lt2_q_case_nom))
        self.api.exchange.set_global_value(state,self.lt2_t_supply_hndl,self.lt2_t_supply)
        self.api.exchange.set_global_value(state,self.lt2_t_return_hndl,self.lt2_t_return)
        self.api.exchange.set_global_value(state,self.lt2_t_case_hndl,self.lt2_t_case)
        self.api.exchange.set_global_value(state,self.lt2_t_food_hndl,self.lt2_t_food)

        return 0
