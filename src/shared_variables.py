# shared_variables.py

# Initialize request counter
request_counter = 0

# Initialize counter file
counter_file = 'request_counter.txt'

# Define _train function
import os
import torch
import joblib
from model.model_definitions import NeuralNet

def _train_and_reload():
    os.system('python3 model/train.py')
    global model, encoder
    model = torch.load(model_path)
    encoder = joblib.load(encoder_path)
    print("Model and encoder reloaded.")
