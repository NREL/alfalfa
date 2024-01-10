from collections import OrderedDict
from io import StringIO
from uuid import uuid4

import pytest
import requests
from requests_toolbelt import MultipartEncoder


@pytest.mark.api
def test_model_upload_download(base_url):

    # Send request with empty data expecting a 400 error
    response = requests.post(f"{base_url}/models/upload")

    assert response.status_code == 400
    response_body = response.json()
    assert "message" in response_body

    # Send request with proper data expecting a 200
    model_name = "test_model.zip"
    request_body = {"modelName": model_name}
    response = requests.post(f"{base_url}/models/upload", json=request_body)

    assert response.status_code == 200
    response_body = response.json()
    assert "payload" in response_body
    payload = response_body["payload"]
    assert "url" in payload
    assert "modelId" in payload
    model_id = payload["modelId"]

    # upload a model to the s3 bucket with the pre-signed request
    form_data = OrderedDict(payload["fields"])
    file_contents = "This is a test string to be used as a file stand in"
    form_data['file'] = ('filename', StringIO(file_contents))

    encoder = MultipartEncoder(fields=form_data)
    response = requests.post(payload['url'], data=encoder, headers={'Content-Type': encoder.content_type})
    assert response.status_code == 204

    # download model and check it is the same
    response = requests.get(f"{base_url}/models/{model_id}/download")
    assert response.status_code == 200

    contents = b""
    for chunk in response.iter_content():
        contents += chunk
    assert contents.decode('utf-8') == file_contents, "Downloaded model does not match uploaded model"


@pytest.mark.api
def test_model_retrieval(base_url):
    # create a model
    model_name = "test_model.zip"
    request_body = {"modelName": model_name}
    response = requests.post(f"{base_url}/models/upload", json=request_body)
    response_body = response.json()

    model_id = response_body["payload"]["modelId"]
    response_body["payload"]["url"]

    # request all models
    response = requests.get(f"{base_url}/models")

    assert response.status_code == 200
    response_body = response.json()
    assert "payload" in response_body
    payload = response_body["payload"]
    assert len(payload) > 0, "No models in model list"

    contains_model = False
    for model in payload:
        if model["id"] == model_id:
            assert model["modelName"] == model_name
            contains_model = True

    assert contains_model, "Could not find uploaded model in list"

    # request only uploaded model
    response = requests.get(f"{base_url}/models/{model_id}")

    assert response.status_code == 200
    response_body = response.json()
    assert "payload" in response_body
    payload = response_body["payload"]
    assert payload["id"] == model_id
    assert payload["modelName"] == model_name
    assert "created" in payload
    assert "modified" in payload

    # request with invalid model id
    model_id = "not_a_model_id"
    response = requests.get(f"{base_url}/models/{model_id}")

    assert response.status_code == 400
    response_body = response.json()
    assert "message" in response_body


@pytest.mark.api
def test_model_not_found(base_url):
    # request non-existent model
    response = requests.get(f"{base_url}/models/{uuid4()}")

    assert response.status_code == 404
    response_body = response.json()
    assert "message" in response_body

    # download non-existent model
    response = requests.get(f"{base_url}/models/{uuid4()}/download")

    assert response.status_code == 404
    response_body = response.json()
    assert "message" in response_body

    # create run from model which does not exist
    response = requests.post(f"{base_url}/models/{uuid4()}/createRun")

    assert response.status_code == 404
    response_body = response.json()
    assert "message" in response_body
