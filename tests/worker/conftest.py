
import pytest


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'user')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'password')
    monkeypatch.setenv('NODE_ENV', 'production')
    monkeypatch.setenv('S3_URL', 'http://localhost:9000')
    monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379/0')
    monkeypatch.setenv('S3_BUCKET', 'alfalfa')
    monkeypatch.setenv('JOB_QUEUE', 'Alfalfa Job Queue')
    monkeypatch.setenv('MONGO_URL', 'mongodb://admin:password@localhost:27017/alfalfa_test?authSource=admin')
    monkeypatch.setenv('S3_REGION', 'us-west-1')
