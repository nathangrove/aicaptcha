import sys
import os
import pytest
from flask import Flask
import base64
import json


# Ensure the main module is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app as flask_app  # Import your Flask app with a valid Python name

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

def test_public_key(client):
    """Test the public key endpoint."""
    rv = client.get('/api/public_key')
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'public_key' in data

def test_captcha_challenge(client):
    """Test the captcha challenge endpoint."""
    data = {
        'data': base64.b64encode(json.dumps({
            'interactions': {},
            'duration': 1000,
            'viewport': {},
            'loadTimestamp': 1234567890,
            'deviceType': 'desktop'
        }).encode('utf-8')).decode('utf-8'),
        'save': False
    }
    rv = client.post('/api/challenge', json=data)
    assert rv.status_code == 200
    response_data = rv.get_json()
    assert 'token' in response_data