from flask import request, jsonify, make_response
from flask_cors import cross_origin
from jsonschema import validate, ValidationError
from src.extract_features import extract_features, UserInteractionData
from user_agents import parse
import torch
import uuid
import json
import jwt
from datetime import datetime, timezone
import logging
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def captcha_challenge(PUBLIC_AUTH_TOKEN, interaction_payload_schema, model, encoder, PRIVATE_KEY):
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header.split()[1] != PUBLIC_AUTH_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 401

    interaction_payload = request.json.get('data')
    save_interaction = request.json.get('save', False)
    if not interaction_payload:
        return jsonify({'error': 'No data provided'}), 400

    # Validate the interaction payload
    try:
        validate(instance=interaction_payload, schema=interaction_payload_schema)
    except json.JSONDecodeError:
        logging.error('Invalid JSON format')
        return jsonify({'error': 'Invalid JSON format'}), 400
    except ValidationError as e:
        logging.error(f'JSON validation error: {e.message}')
        return jsonify({'error': f'JSON validation error: {e.message}'}), 400

    interaction_data = interaction_payload.get('interactions')
    duration = interaction_payload.get('duration')
    viewport = interaction_payload.get('viewport')
    load_timestamp = interaction_payload.get('loadTimestamp')
    device_type = interaction_payload.get('deviceType')

    # Get user agent from headers
    user_agent_string = request.headers.get('User-Agent')

    # Parse user agent
    user_agent = parse(user_agent_string)
    
    # Convert interaction data to UserInteractionData object
    user_interaction_data = UserInteractionData(
        mouse_movements=interaction_data.get('mouseMovements', []),
        key_presses=interaction_data.get('keyPresses', []),
        scroll_events=interaction_data.get('scrollEvents', []),
        form_interactions=interaction_data.get('formInteractions', []),
        touch_events=interaction_data.get('touchEvents', []),
        mouse_clicks=interaction_data.get('mouseClicks', []),
        duration=duration
    )

    # Extract features
    features = extract_features(user_interaction_data)

    # One-hot encode device type
    if encoder is not None and hasattr(user_agent, 'device') and hasattr(user_agent.device, 'family'):
        device_type_encoded = encoder.transform([[user_agent.device.family]]).flatten()
    else:
        device_type_encoded = [0]

    # Convert features to tensor
    features_tensor = torch.tensor([
        features.avg_mouse_speed,
        features.avg_key_press_interval,
        features.avg_scroll_speed,
        features.form_completion_time,
        features.interaction_count,
        features.mouse_linearity,
        features.avg_touch_pressure,
        features.avg_touch_movement,
        features.avg_click_duration,
        features.avg_touch_duration,
        features.duration
    ] + list(device_type_encoded), dtype=torch.float32).unsqueeze(0)

    # Make prediction
    with torch.no_grad():
        if model is not None:
            prediction = model(features_tensor)
        else:
            prediction = torch.tensor([0.5])

    # Check for session_id cookie
    session_id = request.cookies.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())

    # Generate interaction_id
    interaction_id = str(uuid.uuid4())

    # Save interaction data if requested
    if save_interaction:
        timestamp = datetime.now(timezone.utc)
        data_to_save = {
            'session_id': session_id,
            'interaction_id': interaction_id,
            'timestamp': timestamp.isoformat(),
            'interaction_data': interaction_data,
            'duration': duration,
            'label': prediction.item(),
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

    # Serialize the private key to PEM format
    if isinstance(PRIVATE_KEY, rsa.RSAPrivateKey):
        PRIVATE_KEY_PEM = PRIVATE_KEY.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
    else:
        PRIVATE_KEY_PEM = PRIVATE_KEY.decode('utf-8')

    # Create JWT with the challenge response and interaction ID
    token = jwt.encode({'score': prediction.item(), 'interaction_id': interaction_id}, PRIVATE_KEY_PEM, algorithm='RS256')

    response = make_response(jsonify({'token': token}))
    response.set_cookie('session_id', session_id)
    return response