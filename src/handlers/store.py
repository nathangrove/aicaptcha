from flask import request, jsonify, make_response
from flask_expects_json import expects_json
import base64
import json
import uuid
from datetime import datetime, timezone
from user_agents import parse
import os
from main import request_counter, counter_file, model_path, encoder_path, model, encoder


def store_data(store_schema):
    global request_counter
    data = request.json.get('data')
    session_id = request.json.get('session_id')
    if not data:
        return jsonify({'error': 'Data is required'}), 400

    # Decode the base64 data
    decoded_data = base64.b64decode(data)
    interaction_payload = json.loads(decoded_data)

    interaction_data = interaction_payload.get('interactions')
    duration = interaction_payload.get('duration')
    viewport = interaction_payload.get('viewport')
    load_timestamp = interaction_payload.get('loadTimestamp')
    label = interaction_payload.get('label')

    # Get user agent from headers
    user_agent_string = request.headers.get('User-Agent')

    # Check for session_id cookie if not provided in the body
    if not session_id:
        session_id = request.cookies.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())

    # Generate interaction_id
    interaction_id = str(uuid.uuid4())

    # Parse user agent
    user_agent = parse(user_agent_string)

    # Save interaction data to a JSON file
    timestamp = datetime.now(timezone.utc)
    data_to_save = {
        'session_id': session_id,
        'interaction_id': interaction_id,
        'timestamp': timestamp.isoformat(),
        'interaction_data': interaction_data,
        'duration': duration,
        'label': label,
        'user_agent': {
            'browser': user_agent.browser.family,
            'browser_version': user_agent.browser.version_string,
            'os': user_agent.os.family,
            'os_version': user_agent.os.version_string,
            'device': user_agent.device.family
        },
        'viewport': viewport,
        'load_timestamp': load_timestamp
    }
    with open(f'data/{interaction_id}.json', 'w') as f:
        json.dump(data_to_save, f)

    # Increment request counter
    if label is not None:
        _increment_request_counter()

    response = make_response(jsonify({'message': 'Data stored successfully', 'interaction_id': interaction_id}))
    response.set_cookie('session_id', session_id)
    return response


def _increment_request_counter():
    global request_counter, counter_file
    request_counter += 1
    with open(counter_file, 'w') as f:
        f.write(str(request_counter))
    if request_counter >= 10000:
        request_counter = 0
        with open(counter_file, 'w') as f:
            f.write(str(request_counter))
        _train_and_reload()


def _train_and_reload():
    os.system('python3 model/train.py')
    global model, encoder
    model = torch.load(model_path)
    encoder = joblib.load(encoder_path)
    print("Model and encoder reloaded.")