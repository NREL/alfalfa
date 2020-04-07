# -*- coding: utf-8 -*-
"""
    Dummy conftest.py for alfalfa.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    https://pytest.org/latest/plugins.html
"""

import pytest


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    monkeypatch.setenv('WEB_REGISTRY_URI', '313781303390.dkr.ecr.us-east-1.amazonaws.com/queue/web')
    monkeypatch.setenv('WORKER_REGISTRY_URI', '313781303390.dkr.ecr.us-east-1.amazonaws.com/queue/worker')
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'user')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'password')
    monkeypatch.setenv('NODE_ENV', 'production')
    monkeypatch.setenv('S3_URL', 'http://localhost:9000')
    monkeypatch.setenv('REDIS_HOST', 'redis')
    monkeypatch.setenv('S3_BUCKET', 'alfalfa')
    monkeypatch.setenv('JOB_QUEUE_URL', 'http://localhost:4100/queue/local-queue1')
    monkeypatch.setenv('MONGO_URL', 'mongodb://localhost:27017/')
    monkeypatch.setenv('MONGO_DB_NAME', 'alfalfa')
    monkeypatch.setenv('REGION', 'us-west-1')
