import tarfile
import time
from datetime import datetime
from uuid import uuid4

import pytest
import requests


@pytest.mark.api
def test_run_create(base_url, model_id):
    # create run from model
    response = requests.post(f"{base_url}/models/{model_id}/createRun")

    assert response.status_code == 200
    response_body = response.json()
    assert "payload" in response_body
    payload = response_body["payload"]
    assert "runId" in payload


@pytest.mark.api
def test_run_retrieval(base_url, run_id):
    # request all runs
    response = requests.get(f"{base_url}/runs")

    assert response.status_code == 200
    response_body = response.json()
    assert "payload" in response_body
    payload = response_body["payload"]

    contains_run = False

    for run in payload:
        if run["id"] == run_id:
            contains_run = True

    assert contains_run, "Could not find run in list"

    # request run information
    response = requests.get(f"{base_url}/runs/{run_id}")

    assert response.status_code == 200
    response_body = response.json()
    assert "payload" in response_body
    payload = response_body["payload"]

    assert "id" in payload
    assert "name" in payload
    assert "status" in payload
    assert "datetime" in payload
    assert "simType" in payload
    assert "errorLog" in payload

    # delete run
    response = requests.delete(f"{base_url}/runs/{run_id}")

    assert response.status_code == 204

    # request run information (expect 404)
    response = requests.get(f"{base_url}/runs/{run_id}")

    assert response.status_code == 404
    response_body = response.json()
    assert "message" in response_body


@pytest.mark.api
def test_run_not_found(base_url):
    # request run which does not exist
    response = requests.get(f"{base_url}/runs/{uuid4()}")

    assert response.status_code == 404
    response_body = response.json()
    assert "message" in response_body

    # delete run which does not exist
    response = requests.delete(f"{base_url}/runs/{uuid4()}")

    assert response.status_code == 404
    response_body = response.json()
    assert "message" in response_body

    # start run which does not exist
    response = requests.post(f"{base_url}/runs/{uuid4()}/start")

    assert response.status_code == 404
    response_body = response.json()
    assert "message" in response_body

    # request time from run which does not exist
    response = requests.get(f"{base_url}/runs/{uuid4()}/time")

    assert response.status_code == 404
    response_body = response.json()
    assert "message" in response_body

    # advance run which does not exist
    response = requests.post(f"{base_url}/runs/{uuid4()}/advance")

    assert response.status_code == 404
    response_body = response.json()
    assert "message" in response_body

    # stop run which does not exist
    response = requests.post(f"{base_url}/runs/{uuid4()}/stop")

    assert response.status_code == 404
    response_body = response.json()
    assert "message" in response_body

    # download run which does not exist
    response = requests.get(f"{base_url}/runs/{uuid4()}/download")

    assert response.status_code == 404
    response_body = response.json()
    assert "message" in response_body


@pytest.mark.api
def test_run_start_stop(base_url, run_id):
    # start run with invalid arguments
    response = requests.post(f"{base_url}/runs/{run_id}/start")

    assert response.status_code == 400
    response_body = response.json()
    assert "message" in response_body

    start_datetime = datetime(2020, 1, 1, 0, 0)

    # start run
    request_body = {
        'startDatetime': str(start_datetime),
        'endDatetime': str(datetime(2020, 1, 1, 23, 59, 59)),
        'externalClock': True
    }

    response = requests.post(f"{base_url}/runs/{run_id}/start", json=request_body)

    assert response.status_code == 204

    # get status and wait for "RUNNING"
    timeout = time.time() + 60
    while True:
        response = requests.get(f"{base_url}/runs/{run_id}")

        assert response.status_code == 200
        response_body = response.json()
        assert "payload" in response_body
        payload = response_body["payload"]
        assert "status" in payload
        status = payload["status"]

        if status == "RUNNING":
            break
        if time.time() > timeout:
            pytest.fail("Timed out waiting for run to start")

    # get time of run
    response = requests.get(f"{base_url}/runs/{run_id}/time")

    assert response.status_code == 200
    response_body = response.json()
    assert "payload" in response_body
    payload = response_body["payload"]
    assert "time" in payload

    assert start_datetime == datetime.strptime(payload["time"], '%Y-%m-%d %H:%M:%S')

    # advance run
    response = requests.post(f"{base_url}/runs/{run_id}/advance")

    assert response.status_code == 204

    # stop run
    response = requests.post(f"{base_url}/runs/{run_id}/stop")

    assert response.status_code == 204

    # get status and wait for "STOPPING"
    timeout = time.time() + 60
    while True:
        response = requests.get(f"{base_url}/runs/{run_id}")

        assert response.status_code == 200
        response_body = response.json()
        assert "payload" in response_body
        payload = response_body["payload"]
        assert "status" in payload
        status = payload["status"]

        if status.lower() == "stopping" or status.lower() == "complete":
            break
        if time.time() > timeout:
            pytest.fail("Timed out waiting for run to stop")

    # stop already stopped run
    response = requests.post(f"{base_url}/runs/{run_id}/stop")

    assert response.status_code == 204


@pytest.mark.api
def test_run_download(base_url, run_id, tmp_path):
    run_file = tmp_path / f"{run_id}.tar.gz"
    # download run
    response = requests.get(f"{base_url}/runs/{run_id}/download")

    assert response.status_code == 200
    with run_file.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    assert tarfile.is_tarfile(str(run_file)), "Downloaded file is not a valid tar.gz"
