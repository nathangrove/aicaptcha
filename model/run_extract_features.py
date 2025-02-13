import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from extract_features import extract_features, UserInteractionData

##################
# DEV TOOL
# to test the feature extraction and display what is extracted
# to run this, run `python -m server.run_extract_features` from the root of the repo
##################

def process_file(file_path):
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
    print(f"Features for {file_path}:")
    # pretty print the features
    print(json.dumps(features.__dict__, indent=4))
    print("\n")

def main():
    data_dir = './data'
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(data_dir, filename)
            process_file(file_path)

if __name__ == '__main__':
    main()