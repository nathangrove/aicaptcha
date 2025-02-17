from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_expects_json import expects_json
import os
import base64
import json
from extract_features import extract_features, UserInteractionData
from datetime import datetime
import uuid
from user_agents import parse
import torch
import joblib
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from model.model_definitions import NeuralNet
from datetime import datetime, timezone
from dotenv import load_dotenv
import logging
from jsonschema import validate, ValidationError
from flask_cors import cross_origin

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Load the static tokens from environment variables
AUTH_TOKEN = os.getenv('AUTH_TOKEN')
PUBLIC_AUTH_TOKEN = os.getenv('PUBLIC_AUTH_TOKEN')

# Configure logging
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %name)s - %levelname)s - %message)s', handlers=[logging.FileHandler('access.log'), logging.StreamHandler()])

# Middleware to log responses
@app.after_request
def log_response_info(response):
    try:
        logging.info('%s - - [%s] "%s %s %s" %s "%s" "%s" %s %s',
            request.remote_addr,
            datetime.now().strftime('%d/%b/%Y:%H:%M:%S %z'),
            request.method,
            request.path,
            request.scheme.upper(),
            request.environ.get('SERVER_PROTOCOL'),
            request.headers.get('Referer', '-'),
            request.headers.get('User-Agent', '-'),
            response.status_code,
            request.content_length)
    except Exception as e:
        logging.error(f"Error logging response info")
    return response

# Middleware to check for the static token in the Authorization header
@app.before_request
def check_authentication():
    if request.endpoint in ['serve_index', 'serve_file', 'get_public_key', 'captcha_challenge']:
        return  # Skip authentication for these endpoints
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header.split()[1] != AUTH_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 401

# JSON schema for request validation
store_schema = {
    'type': 'object',
    'properties': {
        'data': {'type': 'string'},
        'session_id': {'type': 'string'}
    },
    'required': ['data']
}

update_schema = {
    'type': 'object',
    'properties': {
        'interaction_id': {'type': 'string'},
        'label': {'type': 'number'}
    },
    'required': ['interaction_id', 'label']
}

# JSON schema for interaction payload validation
interaction_payload_schema = {
    'type': 'object',
    'properties': {
        'interactions': {
            'type': 'object',
            'properties': {
                'mouseMovements': {
                    'type': 'array', 
                    'items': {
                        'type': 'object', 
                        'properties': {
                            'type': {
                                'type': 'string'
                            },
                            'x': {
                                'type': 'number'
                            }, 
                            'y': {
                                'type': 'number'
                            }, 
                            'time': {
                                'type': 'number'
                            }
                        }
                    }
                },
                'keyPresses': {
                    'type': 'array', 
                    'items': {
                        'type': 'object', 
                        'properties': {
                            'key': {
                                'type': 'string'
                            }, 
                            'time': {
                                'type': 'number'
                            }
                        }
                    }
                },
                'scrollEvents': {
                    'type': 'array', 
                    'items': {
                        'type': 'object', 
                        'properties': {
                            'deltaX': {
                                'type': 'number'
                            }, 
                            'deltaY': {
                                'type': 'number'
                            }, 
                            'time': {
                                'type': 'number'
                            }
                        }
                    }
                },
                'formInteractions': {
                    'type': 'array', 
                    'items': {
                        'type': 'object', 
                        'properties': {
                            'field': {
                                'type': 'string'
                            },
                            'time' :{
                                'type':'number'
                            }
                        }
                    }
                }
            }
        },
        'duration': {'type': 'number'},
        'loadTimestamp': {'type': 'number'},
        'userAgent': {'type': 'string'},
        'viewPort': {'type': 'object', 'properties': {'width': {'type': 'number'}, 'height': {'type': 'number'}}},
    },
    'required': ['interactions', 'duration', 'viewport', 'loadTimestamp']
}

# Load the trained model and the one-hot encoder
model_path = 'model/neural_net_model_weights.pth'
encoder_path = 'model/onehot_encoder.pkl'
if os.path.exists(model_path) and os.path.exists(encoder_path):
    encoder = joblib.load(encoder_path)
    model = NeuralNet()
    model.load_state_dict(torch.load(model_path))
    model.eval()
else:
    model = None
    encoder = None
    print("Model or encoder not found. Defaulting to dummy prediction.")

# Load the private key for signing JWT
# if the key is not found, let's creat them
if not os.path.exists('signing-keys'):
    # create keys
    PRIVATE_KEY = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    PUBLIC_KEY = PRIVATE_KEY.public_key()
else:
    # Load the private key for signing JWT
    with open('signing-keys/private_key.pem', 'rb') as f:
        PRIVATE_KEY = f.read()
    # Load the public key for serving
    with open('signing-keys/public_key.pem', 'rb') as f:
        PUBLIC_KEY = f.read()

# Initialize request counter
counter_file = 'request_counter.txt'
if os.path.exists(counter_file):
    with open(counter_file, 'r') as f:
        request_counter = int(f.read().strip())
else:
    request_counter = 0

# Serve the static files from the html directory
@app.route('/', methods=['GET'])
def serve_index():
    return send_from_directory('./html', 'index.html')

@app.route('/<path:path>', methods=['GET'])
def serve_file(path):
    return send_from_directory('./html', path)

# Endpoint to serve the public key
@app.route('/api/public_key', methods=['GET'])
def get_public_key():
    if isinstance(PUBLIC_KEY, rsa.RSAPublicKey):
        public_key_pem = PUBLIC_KEY.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
    else:
        public_key_pem = PUBLIC_KEY.decode('utf-8')
    return jsonify({'public_key': public_key_pem})

# Endpoint to collect data and make a decision
@app.route('/api/challenge', methods=['POST'])
@cross_origin()
def captcha_challenge():
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

# Endpoint to store data
# A label is required to store the data. You can use an existing tool (reCaptcha, altCaptcha, etc) to generate a label
@app.route('/api/store', methods=['POST'])
@expects_json(store_schema)
def store_data():
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

# Endpoint to update data with a label
@app.route('/api/update', methods=['POST'])
@expects_json(update_schema)
def update_label():
    interaction_id = request.json.get('interaction_id')
    new_label = request.json.get('label')
    if not interaction_id or new_label is None:
        return jsonify({'error': 'Interaction ID and label are required'}), 400

    # Find the file
    file_path = f'data/{interaction_id}.json'
    if not os.path.exists(file_path):
        return jsonify({'error': 'Interaction ID not found'}), 404

    # Load the existing data
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Update the label
    data['label'] = new_label

    # Save the updated data back to the file
    with open(file_path, 'w') as f:
        json.dump(data, f)

    _increment_request_counter()

    return jsonify({'message': 'Label updated successfully'})


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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
