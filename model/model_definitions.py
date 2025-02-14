import torch
import torch.nn as nn
from torch.utils.data import Dataset

class InteractionDataset(Dataset):
    def __init__(self, data, labels):
        self.data = data
        self.labels = labels

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return torch.tensor(self.data[idx], dtype=torch.float32), torch.tensor(self.labels[idx], dtype=torch.float32)

class NeuralNet(nn.Module):
    def __init__(self, input_size = 13):
        super(NeuralNet, self).__init__()
        self.fc1 = nn.Linear(input_size, 64)  # First fully connected layer with 64 neurons
        self.fc2 = nn.Linear(64, 32)  # Second fully connected layer with 32 neurons
        self.fc3 = nn.Linear(32, 1)  # Output layer with 1 neuron for binary classification
        self.sigmoid = nn.Sigmoid()  # Sigmoid activation function for binary classification

    def forward(self, x):
        x = torch.relu(self.fc1(x))  # ReLU activation function for the first layer
        x = torch.relu(self.fc2(x))  # ReLU activation function for the second layer
        x = self.sigmoid(self.fc3(x))  # Sigmoid activation function for the output layer
        return x
