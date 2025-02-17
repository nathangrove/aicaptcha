from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_expects_json import expects_json
import os
import base64
import json
from src.extract_features import extract_features, UserInteractionData
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
from src.validation_schemas import store_schema, update_schema, interaction_payload_schema
from src.handlers.serve import serve_index, serve_file, get_public_key
from src.handlers.challenge import captcha_challenge
from src.handlers.store import store_data
from src.handlers.update import update_label
from src.shared_variables import request_counter, counter_file, _train_and_reload

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
    if request.endpoint in ['serve_index_route', 'serve_file_route', 'get_public_key_route', 'captcha_challenge_route']:
        return  # Skip authentication for these endpoints
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header.split()[1] != AUTH_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 401


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
def serve_index_route():
    return serve_index()

@app.route('/<path:path>', methods=['GET'])
def serve_file_route(path):
    return serve_file(path)

# Endpoint to serve the public key
@app.route('/api/public_key', methods=['GET'])
def get_public_key_route():
    return get_public_key(PUBLIC_KEY)

# Endpoint to collect data and make a decision
@app.route('/api/challenge', methods=['POST'])
@cross_origin()
def captcha_challenge_route():
    return captcha_challenge(PUBLIC_AUTH_TOKEN, interaction_payload_schema, model, encoder, PRIVATE_KEY)

# Endpoint to store data
# A label is required to store the data. You can use an existing tool (reCaptcha, altCaptcha, etc) to generate a label
@app.route('/api/store', methods=['POST'])
@expects_json(store_schema)
def store_data_route():
    return store_data(store_schema)

# Endpoint to update data with a label
@app.route('/api/update', methods=['POST'])
@expects_json(update_schema)
def update_label_route():
    return update_label(update_schema)



def _train_and_reload():
    os.system('python3 model/train.py')
    global model, encoder
    model = torch.load(model_path)
    encoder = joblib.load(encoder_path)
    print("Model and encoder reloaded.")

    
if __name__ == '__main__':
    env = os.getenv('FLASK_ENV', 'development')
    debug_mode = env != 'production'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
