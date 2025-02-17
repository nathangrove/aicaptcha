from flask import request, jsonify
from flask_expects_json import expects_json
import os
import json
from src.shared_variables import request_counter, counter_file, _train_and_reload

def update_label(update_schema):
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
