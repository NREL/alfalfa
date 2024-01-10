from datetime import datetime
from uuid import uuid4

import pytest
import requests


@pytest.mark.api
def test_point_retrieval(base_url, run_id, alfalfa_client):
    alfalfa_client.start(run_id, datetime(2020, 1, 1, 0, 0), datetime(2020, 1, 2, 0, 0), external_clock=True)
    # get points
    response = requests.get(f"{base_url}/runs/{run_id}/points")

    assert response.status_code == 200
    response_body = response.json()
    assert "payload" in response_body
    payload = response_body["payload"]
    assert len(payload) > 0, "No points in payload"

    outputs = []
    bidirectionals = []
    inputs = []

    for point in payload:
        assert "id" in point
        assert "name" in point
        assert "type" in point
        assert "value" not in point

        if point["type"] == "OUTPUT":
            outputs.append(point)
        elif point["type"] == "BIDIRECTIONAL":
            bidirectionals.append(point)
        elif point["type"] == "INPUT":
            inputs.append(point)

    # get points of a specific type
    request_body = {
        'pointTypes': ["OUTPUT"]
    }
    response = requests.post(f"{base_url}/runs/{run_id}/points", json=request_body)

    assert response.status_code == 200
    response_body = response.json()
    assert "payload" in response_body
    payload = response_body["payload"]
    assert len(payload) == len(outputs), "Filter did not return correct number of points"

    for point in payload:
        assert point in outputs, "Filter did not return correct points"

    # get points by list
    request_body = {
        'points': [point["id"] for point in inputs]
    }
    response = requests.post(f"{base_url}/runs/{run_id}/points", json=request_body)

    assert response.status_code == 200
    response_body = response.json()
    assert "payload" in response_body
    payload = response_body["payload"]
    assert len(payload) == len(inputs), "Filter did not return correct number of points"

    for point in payload:
        assert point in inputs, "Filter did not return correct points"

    # Wait for run to be running and advance one timestep
    alfalfa_client.wait(run_id, "RUNNING")
    alfalfa_client.advance(run_id)

    # get the values from each output individually
    for point in outputs + bidirectionals:
        response = requests.get(f"{base_url}/runs/{run_id}/points/{point['id']}")

        assert response.status_code == 200
        response_body = response.json()
        assert "payload" in response_body
        payload = response_body["payload"]
        assert "value" in payload

    # get all non outputs individually
    for point in inputs:
        response = requests.get(f"{base_url}/runs/{run_id}/points/{point['id']}")

        assert response.status_code == 200
        response_body = response.json()
        assert "payload" in response_body
        payload = response_body["payload"]
        assert point == payload, "Point data changed or incorrect"

    # get values for all output points
    response = requests.get(f"{base_url}/runs/{run_id}/points/values")

    assert response.status_code == 200
    response_body = response.json()
    assert "payload" in response_body
    payload = response_body["payload"]
    assert len(payload) == len(outputs + bidirectionals), "Mismatch in output points"

    expected_ids = [point["id"] for point in (outputs + bidirectionals)]

    for id in payload:
        assert id in expected_ids, "Point not expected in response"

    # get point values for all bidirectional points
    request_body = {
        'pointTypes': ["BIDIRECTIONAL"]
    }
    response = requests.post(f"{base_url}/runs/{run_id}/points/values", json=request_body)

    assert response.status_code == 200
    response_body = response.json()
    assert "payload" in response_body
    payload = response_body["payload"]
    assert len(payload) == len(bidirectionals), "Filter did not return correct number of points"

    expected_ids = [point["id"] for point in bidirectionals]

    for id in payload:
        assert id in expected_ids, "Filter returned incorrect point"

    # get point values for all outputs by id
    request_body = {
        'points': [point["id"] for point in outputs]
    }
    response = requests.post(f"{base_url}/runs/{run_id}/points/values", json=request_body)

    assert response.status_code == 200
    response_body = response.json()
    assert "payload" in response_body
    payload = response_body["payload"]
    assert len(payload) == len(outputs), "Filter did not return correct number of points"

    expected_ids = [point["id"] for point in outputs]

    for id in payload:
        assert id in expected_ids, "Filter returned incorrect point"


@pytest.mark.api
def test_point_writes(base_url, run_id):
    # get all points
    response = requests.get(f"{base_url}/runs/{run_id}/points")

    assert response.status_code == 200
    response_body = response.json()
    assert "payload" in response_body
    payload = response_body["payload"]

    outputs = []
    bidirectionals = []
    inputs = []

    for point in payload:
        if point["type"] == "OUTPUT":
            outputs.append(point)
        elif point["type"] == "BIDIRECTIONAL":
            bidirectionals.append(point)
        elif point["type"] == "INPUT":
            inputs.append(point)

    all_points = payload

    # write to points individually
    for point in all_points:
        request_body = {
            'value': 5
        }
        response = requests.put(f"{base_url}/runs/{run_id}/points/{point['id']}", json=request_body)

        if point in outputs:
            assert response.status_code == 400
            response_body = response.json()
            assert "message" in response_body
        else:
            assert response.status_code == 204

    # write to point with invalid value
    request_body = {
        'value': "hello"
    }
    response = requests.put(f"{base_url}/runs/{run_id}/points/{inputs[0]['id']}", json=request_body)

    assert response.status_code == 400
    response_body = response.json()
    assert "message" in response_body

    # write to all valid points
    request_body = {
        'points': dict([(point["id"], 5) for point in (inputs + bidirectionals)])
    }
    response = requests.put(f"{base_url}/runs/{run_id}/points/values", json=request_body)

    assert response.status_code == 204

    # write to all points (some invalid)
    request_body = {
        'points': dict([(point["id"], 5) for point in all_points])
    }
    response = requests.put(f"{base_url}/runs/{run_id}/points/values", json=request_body)

    assert response.status_code == 400
    response_body = response.json()
    assert "message" in response_body
    assert "payload" in response_body
    payload = response_body["payload"]
    assert len(payload) == len(outputs), "Error cardinality mismatch"


@pytest.mark.api
def test_point_not_found(base_url, run_id):
    # request point which does not exist
    response = requests.get(f"{base_url}/runs/{run_id}/points/{uuid4()}")

    assert response.status_code == 404
    response_body = response.json()
    assert "message" in response_body

    # write point which does not exist
    request_body = {
        'value': 5
    }
    response = requests.put(f"{base_url}/runs/{run_id}/points/{uuid4()}", json=request_body)

    assert response.status_code == 404
    response_body = response.json()
    assert "message" in response_body

    # request points for run which does not exist
    response = requests.get(f"{base_url}/runs/{uuid4()}/points")

    assert response.status_code == 404
    response_body = response.json()
    assert "message" in response_body

    # request certain points for run which does not exist
    request_body = {
        'pointTypes': ["OUTPUT"]
    }
    response = requests.post(f"{base_url}/runs/{uuid4()}/points", json=request_body)

    assert response.status_code == 404
    response_body = response.json()
    assert "message" in response_body

    # request point values for run which does not exist
    response = requests.get(f"{base_url}/runs/{uuid4()}/points/values")

    assert response.status_code == 404
    response_body = response.json()
    assert "message" in response_body

    # request certain point values for run which does not exist
    request_body = {
        'pointTypes': ["INPUT"]
    }
    response = requests.post(f"{base_url}/runs/{uuid4()}/points/values", json=request_body)

    assert response.status_code == 404
    response_body = response.json()
    assert "message" in response_body

    # write point values for run which does not exist
    request_body = {
        'point_name': 10
    }
    response = requests.put(f"{base_url}/runs/{uuid4()}/points/values", json=request_body)

    assert response.status_code == 404
    response_body = response.json()
    assert "message" in response_body
