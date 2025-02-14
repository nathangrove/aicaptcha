import sys
import os
import pytest
from flask import Flask
import base64
import json
import jwt

sys.path.append(os.path.abspath("."))  # Add current directory

# Ensure the main module is in the path
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

def test_captcha_challenge_save(client):
    """Test the captcha challenge save endpoint and check if it writes to disk."""
    data = {
        'data': base64.b64encode(json.dumps({
            'interactions': {},
            'duration': 1000,
            'viewport': {},
            'loadTimestamp': 1234567890,
            'deviceType': 'desktop'
        }).encode('utf-8')).decode('utf-8'),
        'save': True
    }
    rv = client.post('/api/challenge', json=data)
    assert rv.status_code == 200
    response_data = rv.get_json()
    assert 'token' in response_data
    token_data = jwt.decode(response_data['token'], options={"verify_signature": False})
    assert 'interaction_id' in token_data
    interaction_id = token_data['interaction_id']
    file_path = os.path.join('data', f'{interaction_id}.json')
    assert os.path.exists(file_path)
    # Clean up the file after test
    os.remove(file_path)

def test_captcha_challenge_score(client):
    """Test the captcha challenge score in the token."""
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
    token_data = jwt.decode(response_data['token'], options={"verify_signature": False})
    assert 'score' in token_data
    assert token_data['score'] == 0.5

def test_update_label(client):
    """Test the update label endpoint."""
    # First, create a challenge to get an interaction_id
    data = {
        'data': base64.b64encode(json.dumps({
            'interactions': {},
            'duration': 1000,
            'viewport': {},
            'loadTimestamp': 1234567890,
            'deviceType': 'desktop'
        }).encode('utf-8')).decode('utf-8'),
        'save': True
    }
    rv = client.post('/api/challenge', json=data)
    assert rv.status_code == 200
    response_data = rv.get_json()
    assert 'token' in response_data
    token_data = jwt.decode(response_data['token'], options={"verify_signature": False})
    assert 'interaction_id' in token_data
    interaction_id = token_data['interaction_id']
    # Now, update the label for the created interaction
    update_data = {
        'interaction_id': interaction_id,
        'label': 'new_label'
    }
    rv = client.post('/api/update', json=update_data)
    assert rv.status_code == 200
    response_data = rv.get_json()
    assert response_data['message'] == 'Label updated successfully'
    # Verify the label was updated in the file
    file_path = os.path.join('data', f'{interaction_id}.json')
    with open(file_path, 'r') as f:
        saved_data = json.load(f)
    assert saved_data['label'] == 'new_label'
    # Clean up the file after test
    os.remove(file_path)
    # verify that request_counter.txt is created
    assert os.path.exists('request_counter.txt')
    with open('request_counter.txt', 'r') as f:
        count = int(f.read().strip())
    assert count == 1
    os.remove('request_counter.txt')

def test_store_endpoint(client):
    """Test the store endpoint to ensure it writes a data file."""
    data = {
        'data': base64.b64encode(json.dumps({
            'interactions': {},
            'duration': 1000,
            'viewport': {},
            'loadTimestamp': 1234567890,
            'deviceType': 'desktop'
        }).encode('utf-8')).decode('utf-8'),
        'save': True
    }
    rv = client.post('/api/store', json=data)
    assert rv.status_code == 200
    response_data = rv.get_json()
    assert 'message' in response_data
    assert response_data['message'] == 'Data stored successfully'
    assert 'interaction_id' in response_data
    interaction_id = response_data['interaction_id']
    file_path = os.path.join('data', f'{interaction_id}.json')
    assert os.path.exists(file_path)
    # Clean up the file after test
    os.remove(file_path)
