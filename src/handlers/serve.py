from flask import send_from_directory, jsonify
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# Serve the static files from the html directory

def serve_index():
    return send_from_directory('./html', 'index.html')


def serve_file(path):
    return send_from_directory('./html', path)


def get_public_key(PUBLIC_KEY):
    if isinstance(PUBLIC_KEY, rsa.RSAPublicKey):
        public_key_pem = PUBLIC_KEY.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
    else:
        public_key_pem = PUBLIC_KEY.decode('utf-8')
    return jsonify({'public_key': public_key_pem})