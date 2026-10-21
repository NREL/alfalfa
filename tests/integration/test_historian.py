import os
from datetime import datetime
from urllib.parse import urlparse

import pytest
import requests
from alfalfa_client.alfalfa_client import AlfalfaClient
from influxdb import InfluxDBClient

from tests.integration.conftest import prepare_model

# Point known to be present in tests/integration/models/wrapped.fmu's outputs,
# see test_modelica.py.
FMU_OUTPUT_POINT = "chi_reaTSup_y"


@pytest.fixture
def historian_config(alfalfa_host: str):
    """Fetch the Alfalfa web app's historian config. Used to detect whether
    the historian (InfluxDB + Grafana) stack is enabled for this environment,
    so historian-specific tests can self-skip when it is not."""
    response = requests.get(f"{alfalfa_host}/api/v2/config", timeout=10)
    response.raise_for_status()
    return response.json()["payload"]


@pytest.fixture
def skip_if_historian_disabled(historian_config):
    if not historian_config["historianEnabled"]:
        pytest.skip("Historian is not enabled for this environment (HISTORIAN_ENABLE != 'true')")


@pytest.fixture
def influx_client(alfalfa_host: str, skip_if_historian_disabled):
    influx_host = urlparse(alfalfa_host).hostname or "localhost"
    client = InfluxDBClient(
        host=influx_host,
        port=8086,
        username=os.environ.get("INFLUXDB_USERNAME", "admin"),
        password=os.environ.get("INFLUXDB_PASSWORD", "password"),
        database=os.environ.get("INFLUXDB_DB", "alfalfa"),
    )
    yield client
    client.close()


@pytest.mark.integration
def test_historian_config_endpoint(historian_config):
    """The web app's /api/v2/config endpoint should always report a valid
    historian config shape, whether or not the historian is enabled, since
    it drives the Historian nav button's visibility."""
    assert "historianEnabled" in historian_config
    assert "grafanaUrl" in historian_config
    assert isinstance(historian_config["historianEnabled"], bool)


@pytest.mark.integration
def test_grafana_reachable_and_datasource_provisioned(historian_config, skip_if_historian_disabled):
    """When the historian is enabled, Grafana should be reachable and have
    its InfluxDB datasource auto-provisioned (see
    grafana/provisioning/datasources/all.yml)."""
    grafana_url = historian_config["grafanaUrl"]
    assert grafana_url, "grafanaUrl should be set when historian is enabled"

    health = requests.get(f"{grafana_url}/api/health", timeout=10)
    assert health.status_code == 200
    assert health.json().get("database") == "ok"

    auth = (
        os.environ.get("GF_SECURITY_ADMIN_USER", "admin"),
        os.environ.get("GF_SECURITY_ADMIN_PASSWORD", "password"),
    )
    datasources_response = requests.get(f"{grafana_url}/api/datasources", auth=auth, timeout=10)
    assert datasources_response.status_code == 200

    influx_datasources = [ds for ds in datasources_response.json() if ds["type"] == "influxdb"]
    assert influx_datasources, "Expected an InfluxDB datasource to be provisioned in Grafana"
    assert influx_datasources[0]["isDefault"] is True


@pytest.mark.integration
def test_simulation_points_written_to_influxdb(alfalfa: AlfalfaClient, influx_client: InfluxDBClient):
    """Run a short FMU simulation and confirm its output points land in
    InfluxDB tagged with the point name/units/source that the auto-
    provisioned Grafana dashboard groups by and aliases series with."""
    run_id = alfalfa.submit(prepare_model("wrapped.fmu"))
    try:
        alfalfa.start(run_id, datetime(2019, 1, 1, 0, 0), datetime(2019, 1, 1, 0, 5), external_clock=True)

        for _ in range(3):
            alfalfa.advance(run_id)

        result = influx_client.query(f'SELECT * FROM "{run_id}" WHERE "name" = \'{FMU_OUTPUT_POINT}\'')
        points = list(result.get_points())

        assert points, f"Expected historian points for run {run_id}, found none"
        assert points[0]["name"] == FMU_OUTPUT_POINT
        assert points[0]["source"] == "alfalfa"
        assert "id" in points[0]
        assert "value" in points[0]
    finally:
        alfalfa.stop(run_id)
