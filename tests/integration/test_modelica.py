from datetime import datetime

import pytest
from alfalfa_client import AlfalfaClient

from tests.integration.conftest import prepare_model


@pytest.mark.integration
def test_modelica_model(alfalfa: AlfalfaClient):
    run_id = alfalfa.submit(prepare_model("wrapped.fmu"))

    alfalfa.start(run_id, datetime(2019, 1, 1, 0, 0), datetime(2019, 1, 1, 0, 5), external_clock=True)
    inputs = alfalfa.get_inputs(run_id)
    outputs = alfalfa.get_outputs(run_id).keys()

    assert "hvac_oveAhu_TSupSet_u" in inputs
    assert "hvac_oveAhu_dpSet_u" in inputs
    assert "hvac_oveAhu_yCoo_u" in inputs
    assert "hvac_oveAhu_yFan_u" in inputs
    assert "hvac_oveAhu_yHea_u" in inputs
    assert "hvac_oveAhu_yOA_u" in inputs
    assert "hvac_oveAhu_yPumCoo_u" in inputs
    assert "hvac_oveAhu_yPumHea_u" in inputs
    assert "hvac_oveAhu_yRet_u" in inputs
    assert "hvac_oveZonActCor_yDam_u" in inputs
    assert "hvac_oveZonActCor_yReaHea_u" in inputs
    assert "hvac_oveZonActEas_yDam_u" in inputs
    assert "hvac_oveZonActEas_yReaHea_u" in inputs
    assert "hvac_oveZonActNor_yDam_u" in inputs
    assert "hvac_oveZonActNor_yReaHea_u" in inputs
    assert "hvac_oveZonActSou_yDam_u" in inputs
    assert "hvac_oveZonActSou_yReaHea_u" in inputs
    assert "hvac_oveZonActWes_yDam_u" in inputs
    assert "hvac_oveZonActWes_yReaHea_u" in inputs
    assert "hvac_oveZonSupCor_TZonCooSet_u" in inputs
    assert "hvac_oveZonSupCor_TZonHeaSet_u" in inputs
    assert "hvac_oveZonSupEas_TZonCooSet_u" in inputs
    assert "hvac_oveZonSupEas_TZonHeaSet_u" in inputs
    assert "hvac_oveZonSupNor_TZonCooSet_u" in inputs
    assert "hvac_oveZonSupNor_TZonHeaSet_u" in inputs
    assert "hvac_oveZonSupSou_TZonCooSet_u" in inputs
    assert "hvac_oveZonSupSou_TZonHeaSet_u" in inputs
    assert "hvac_oveZonSupWes_TZonCooSet_u" in inputs
    assert "hvac_oveZonSupWes_TZonHeaSet_u" in inputs
    assert "chi_reaFloSup_y" in outputs
    assert "chi_reaPChi_y" in outputs
    assert "chi_reaPPumDis_y" in outputs
    assert "chi_reaTRet_y" in outputs
    assert "chi_reaTSup_y" in outputs
    assert "heaPum_reaFloSup_y" in outputs
    assert "heaPum_reaPHeaPum_y" in outputs
    assert "heaPum_reaPPumDis_y" in outputs
    assert "heaPum_reaTRet_y" in outputs
    assert "heaPum_reaTSup_y" in outputs
    assert "hvac_oveAhu_TSupSet_y" in outputs
    assert "hvac_oveAhu_dpSet_y" in outputs
    assert "hvac_oveAhu_yCoo_y" in outputs
    assert "hvac_oveAhu_yFan_y" in outputs
    assert "hvac_oveAhu_yHea_y" in outputs
    assert "hvac_oveAhu_yOA_y" in outputs
    assert "hvac_oveAhu_yPumCoo_y" in outputs
    assert "hvac_oveAhu_yPumHea_y" in outputs
    assert "hvac_oveAhu_yRet_y" in outputs
    assert "hvac_oveZonActCor_yDam_y" in outputs
    assert "hvac_oveZonActCor_yReaHea_y" in outputs
    assert "hvac_oveZonActEas_yDam_y" in outputs
    assert "hvac_oveZonActEas_yReaHea_y" in outputs
    assert "hvac_oveZonActNor_yDam_y" in outputs
    assert "hvac_oveZonActNor_yReaHea_y" in outputs
    assert "hvac_oveZonActSou_yDam_y" in outputs
    assert "hvac_oveZonActSou_yReaHea_y" in outputs
    assert "hvac_oveZonActWes_yDam_y" in outputs
    assert "hvac_oveZonActWes_yReaHea_y" in outputs
    assert "hvac_oveZonSupCor_TZonCooSet_y" in outputs
    assert "hvac_oveZonSupCor_TZonHeaSet_y" in outputs
    assert "hvac_oveZonSupEas_TZonCooSet_y" in outputs
    assert "hvac_oveZonSupEas_TZonHeaSet_y" in outputs
    assert "hvac_oveZonSupNor_TZonCooSet_y" in outputs
    assert "hvac_oveZonSupNor_TZonHeaSet_y" in outputs
    assert "hvac_oveZonSupSou_TZonCooSet_y" in outputs
    assert "hvac_oveZonSupSou_TZonHeaSet_y" in outputs
    assert "hvac_oveZonSupWes_TZonCooSet_y" in outputs
    assert "hvac_oveZonSupWes_TZonHeaSet_y" in outputs
    assert "hvac_reaAhu_PFanSup_y" in outputs
    assert "hvac_reaAhu_PPumCoo_y" in outputs
    assert "hvac_reaAhu_PPumHea_y" in outputs
    assert "hvac_reaAhu_TCooCoiRet_y" in outputs
    assert "hvac_reaAhu_TCooCoiSup_y" in outputs
    assert "hvac_reaAhu_THeaCoiRet_y" in outputs
    assert "hvac_reaAhu_THeaCoiSup_y" in outputs
    assert "hvac_reaAhu_TMix_y" in outputs
    assert "hvac_reaAhu_TRet_y" in outputs
    assert "hvac_reaAhu_TSup_y" in outputs
    assert "hvac_reaAhu_V_flow_ret_y" in outputs
    assert "hvac_reaAhu_V_flow_sup_y" in outputs
    assert "hvac_reaAhu_dp_sup_y" in outputs
    assert "hvac_reaZonCor_CO2Zon_y" in outputs
    assert "hvac_reaZonCor_TSup_y" in outputs
    assert "hvac_reaZonCor_TZon_y" in outputs
    assert "hvac_reaZonCor_V_flow_y" in outputs
    assert "hvac_reaZonEas_CO2Zon_y" in outputs
    assert "hvac_reaZonEas_TSup_y" in outputs
    assert "hvac_reaZonEas_TZon_y" in outputs
    assert "hvac_reaZonEas_V_flow_y" in outputs
    assert "hvac_reaZonNor_CO2Zon_y" in outputs
    assert "hvac_reaZonNor_TSup_y" in outputs
    assert "hvac_reaZonNor_TZon_y" in outputs
    assert "hvac_reaZonNor_V_flow_y" in outputs
    assert "hvac_reaZonSou_CO2Zon_y" in outputs
    assert "hvac_reaZonSou_TSup_y" in outputs
    assert "hvac_reaZonSou_TZon_y" in outputs
    assert "hvac_reaZonSou_V_flow_y" in outputs
    assert "hvac_reaZonWes_CO2Zon_y" in outputs
    assert "hvac_reaZonWes_TSup_y" in outputs
    assert "hvac_reaZonWes_TZon_y" in outputs
    assert "hvac_reaZonWes_V_flow_y" in outputs
    assert "weaSta_reaWeaCeiHei_y" in outputs
    assert "weaSta_reaWeaCloTim_y" in outputs
    assert "weaSta_reaWeaHDifHor_y" in outputs
    assert "weaSta_reaWeaHDirNor_y" in outputs
    assert "weaSta_reaWeaHGloHor_y" in outputs
    assert "weaSta_reaWeaHHorIR_y" in outputs
    assert "weaSta_reaWeaLat_y" in outputs
    assert "weaSta_reaWeaLon_y" in outputs
    assert "weaSta_reaWeaNOpa_y" in outputs
    assert "weaSta_reaWeaNTot_y" in outputs
    assert "weaSta_reaWeaPAtm_y" in outputs
    assert "weaSta_reaWeaRelHum_y" in outputs
    assert "weaSta_reaWeaSolAlt_y" in outputs
    assert "weaSta_reaWeaSolDec_y" in outputs
    assert "weaSta_reaWeaSolHouAng_y" in outputs
    assert "weaSta_reaWeaSolTim_y" in outputs
    assert "weaSta_reaWeaSolZen_y" in outputs
    assert "weaSta_reaWeaTBlaSky_y" in outputs
    assert "weaSta_reaWeaTDewPoi_y" in outputs
    assert "weaSta_reaWeaTDryBul_y" in outputs
    assert "weaSta_reaWeaTWetBul_y" in outputs
    assert "weaSta_reaWeaWinDir_y" in outputs
    assert "weaSta_reaWeaWinSpe_y" in outputs

    for _ in range(5):
        alfalfa.advance(run_id)

    alfalfa.stop(run_id)
