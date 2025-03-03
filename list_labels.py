import os
import json

# Directory containing the data files
DATA_DIR = './data'

# Dictionary to store label counts
label_counts = {}

# Iterate through the files in the data directory
for filename in os.listdir(DATA_DIR):
    if filename.endswith('.json'):
        file_path = os.path.join(DATA_DIR, filename)
        with open(file_path, 'r') as f:
            data = json.load(f)
            label = data.get('label')
            if label is not None:
                if label in label_counts:
                    label_counts[label] += 1
                else:
                    label_counts[label] = 1

# Print the label counts
for label, count in label_counts.items():
    print(f'Label: {label}, Count: {count}')
