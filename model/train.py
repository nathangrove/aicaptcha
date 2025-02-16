import sys
import os
import torch
import json
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
import joblib
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.extract_features import UserInteractionData, extract_features
from model.model_definitions import InteractionDataset, NeuralNet

# Function to load data from the data directory
def load_data(data_dir):
    X = []
    y = []
    device_types = []
    print(f"Loading data from {data_dir}")  # Debug statement to check the data directory    
    for filename in os.listdir(data_dir):
        try:
            if filename.endswith('.json'):
                file_path = os.path.join(data_dir, filename)
                print(f"Processing file: {file_path}")  # Debug statement to check the file being processed
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    interaction_data = data['interaction_data']
                    user_interaction_data = UserInteractionData(
                        mouse_movements=interaction_data.get('mouseMovements', []),
                        key_presses=interaction_data.get('keyPresses', []),
                        scroll_events=interaction_data.get('scrollEvents', []),
                        form_interactions=interaction_data.get('formInteractions', []),
                        touch_events=interaction_data.get('touchEvents', []),
                        mouse_clicks=interaction_data.get('mouseClicks', []),
                        duration=data['duration']
                    )
                    features = extract_features(user_interaction_data)
                    feature_values = list(features.__dict__.values())

                    device_types.append(data['user_agent']['device'])
                    if 'label' in data and data['label'] is not None:
                        y.append(data['label'])  # Convert label to float
                        X.append(feature_values)
                    else:
                        print(f"Warning: 'label' key not found or is None in {file_path}. Skipping this file.")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from file {file_path}: {e}")
            continue
        except KeyError as e:
            print(f"KeyError: {e} in file {file_path}")
            continue
    print(f"Loaded {len(X)} samples.")  # Debug statement to check the number of loaded samples

    # One-hot encode device types
    encoder = OneHotEncoder(sparse_output=False)
    device_types_encoded = encoder.fit_transform([[dt] for dt in device_types])
    joblib.dump(encoder, 'model/onehot_encoder.pkl')  # Save the one-hot encoder

    # Append one-hot encoded device types to features
    X = [x + list(device_types_encoded[i]) for i, x in enumerate(X)]

    return X, y

# Main function to train and evaluate the neural network
def main():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    X, y = load_data(data_dir)
    
    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Create DataLoader for training and testing sets
    train_dataset = InteractionDataset(X_train, y_train)
    test_dataset = InteractionDataset(X_test, y_test)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)  # Batch size of 32 for training
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)  # Batch size of 32 for testing
    
    # Initialize the neural network
    input_size = len(X[0])
    model = NeuralNet(input_size)
    print(f"Training neural network with input size: {input_size}")  # Debug statement to check the input size
    print(f"Training set size: {len(X_train)}")  # Debug statement to check the training set size
    print(f"Number of features: {len(X[0])}")  # Debug statement to check the number of features
    print(f"Number of params: {sum(p.numel() for p in model.parameters())}")  # Debug statement to check the number of parameters
    criterion = nn.BCELoss()  # Binary Cross-Entropy Loss for binary classification
    optimizer = optim.Adam(model.parameters(), lr=0.001)  # Adam optimizer with learning rate of 0.001
    
    # Train the neural network
    num_epochs = 20  # Number of epochs for training
    for epoch in range(num_epochs):
        model.train()
        for data, labels in train_loader:
            optimizer.zero_grad()  # Zero the gradients
            outputs = model(data)  # Forward pass
            loss = criterion(outputs.squeeze(), labels)  # Compute the loss
            loss.backward()  # Backward pass
            optimizer.step()  # Update the weights
        
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')  # Print the loss for each epoch
    
    # Evaluate the neural network
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for data, labels in test_loader:
            outputs = model(data)
            predicted = (outputs.squeeze() > 0.5).float()  # Convert probabilities to binary predictions
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    
    accuracy = correct / total  # Compute the accuracy
    print(f'Model accuracy: {accuracy * 100:.2f}%')  # Print the accuracy
    
    # Save the trained model weights and the one-hot encoder
    torch.save(model.state_dict(), 'model/neural_net_model_weights.pth')  # Save the model weights
    print('Model weights and one-hot encoder saved to model/neural_net_model_weights.pth and model/onehot_encoder.pkl')

if __name__ == '__main__':
    main()