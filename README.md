# AI CAPTCHA Project

This project aims to create an AI-based CAPTCHA system that can distinguish between human and bot interactions based on user interaction data. This is NOT intended to be a production system, just a playground for me to learn more about neural nets and how to use them. The system uses a neural network model to analyze features extracted from the data of a user interacting with a page and make predictions. The project includes a Flask application to serve the CAPTCHA and handle API requests, as well as scripts for training the AI model.

## Goals for this project
1. Design and train a model that is 95% accurate
2. Have a model that is small enough to run on CPU on most servers without utilizing massive compute resources

## Project Structure

- `main.py`: The main Flask application file.
- `main_test.py`: Unit tests for the Flask application.
- `extract_features.py`: Contains functions for extracting features from user interaction data.
- `data/`: Directory to store interaction data.
- `html/`: Directory to store static HTML files.
- `requirements.txt`: List of dependencies required for the project.

## Setup

1. Clone the repository:
    ```sh
    git clone https://github.com/nathangrove/aicaptcha.git
    cd aicaptcha
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Run the Flask application:
    ```sh
    python main.py
    ```

## Training the AI Model

To train the AI model, you can run the training script manually. This is not required to use the server, as the server will automatically train the model every 10,000 requests.

### Collected Metrics & Extracted Features

The following metrics and features are collected and extracted from user interaction data anonamously:

1. **Average Mouse Speed**: The average speed of mouse movements.
2. **Average Key Press Interval**: The average time interval between key presses.
3. **Average Scroll Speed**: The average speed of scroll events.
4. **Form Completion Time**: The total time taken to complete the form.
5. **Interaction Count**: The total number of interactions (mouse movements, key presses, scroll events, etc.).
6. **Mouse Linearity**: A measure of how linear the mouse movements are.
7. **Average Touch Pressure**: The average pressure applied during touch events (for touch devices).
8. **Average Touch Movement**: The average movement during touch events (for touch devices).
9. **Average Click Duration**: The average duration of mouse clicks.
10. **Average Touch Duration**: The average duration of touch events (for touch devices).
11. **Duration**: The total duration of the interaction session.
12. **Device Type**: One-hot encoded device type (e.g., desktop, mobile, tablet).

These features are used to train the neural network model to distinguish between human and bot interactions.

### Manual Training

1. Ensure you have the necessary data in the `data/` directory.
2. Run the training script:
    ```sh
    python model/train_nn.py
    ```
3. The trained model and one-hot encoder will be saved in the `model/` directory as `neural_net_model_weights.pth` and `onehot_encoder.pkl` respectively.

### Automatic Training

The server will automatically train the model every 10,000 requests stored. You do not need to manually trigger the training process unless you want to train the model with new data immediately.

## Endpoints

### `GET /captcha.js`

Serves the client side captcha code that will gather the interaction data.

### `GET /api/public_key`

Returns the public key used for verifying JWT tokens.

### `POST /api/challenge`

Collects user interaction data, extracts features, and makes a prediction to determine if the user is a human or a bot. The score is returned to you along with a tracable `interaction_id` within a signed JWT. If the `save` parameter was passed in with the call, it will save the interaction for later training.

### `POST /api/store`

Stores user interaction data along with an optional label for later training.

### `POST /api/update`

Updates the label for a specific interaction. If you are gathering data to train on, you can use an existing captcha service as the ground for your labels.


## Lifecycles


### Manually acquiring a token

This is useful when using client side frameworks.

1. Load the `captcha.js` file on the form.
2. Initialize the AICaptcha class
3. Before the form is submitted, call the `executeAsync()` function
4. Submit the token with your data to the server.

### Automatically acquiring a token

This method is the easiest for simple HTML forms.

1. Load the `captcha.js` file on the form.
2. Initialize the AICaptcha and pass `autoIntercept: true` to the config
3. The token will be acquired and submitted with the form data to the server

### Processing the token on the server

Once the token is submitted to your sever with the data, you will need to verify the legitamacy of the token and the score in the token.

1. Call the `/api/public_key` endpoint to get the public key used for signing the token
2. Have your server logic determine what to do based on the score within the token (JWT)
3. (Optional) Use an alternative (already proven) CAPTCHA service or other means of determination to update the interaction data (`/api/update`) for the server to retrain on.

## Client Side Code Examples

### Vanilla JavaScript Example

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI CAPTCHA Example</title>
</head>
<body>
    <form id="example-form" action="/submit" method="POST">
        <!-- Your form fields go here -->
        <button type="submit">Submit</button>
    </form>

    <script type="module">
        import { AICaptcha } from './captcha.js';
        
        // Initialize with automatic form interception
        const aiCaptcha = new AICaptcha({
            publicKey: 'your-public-key-here',
            autoIntercept: true
        });
    </script>
</body>
</html>
```

### React Example

```jsx
import { useAICaptcha } from './captcha.js';

function MyForm() {
    const { execute, token } = useAICaptcha({
        publicKey: 'your-public-key-here'
    });

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        try {
            const captchaToken = await execute();
            
            // Your form submission logic here
            const formData = new FormData(e.target);
            formData.append('captcha_token', captchaToken);
            
            // Send to your server
            const response = await fetch('/api/submit', {
                method: 'POST',
                body: formData
            });
            
        } catch (error) {
            console.error('Captcha verification failed:', error);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            {/* Your form fields */}
            <button type="submit">Submit</button>
        </form>
    );
}
```

### Manual Token Acquisition

```javascript
import { AICaptcha } from './captcha.js';

// Initialize without automatic interception
const aiCaptcha = new AICaptcha({
    publicKey: 'your-public-key-here',
    autoIntercept: false
});

// Get token when needed
const token = await aiCaptcha.executeAsync();
```

## Server Side Code Example (Node.js)

```javascript
const express = require('express');
const jwt = require('jsonwebtoken');
const axios = require('axios');
const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

const PUBLIC_KEY_URL = 'http://localhost:5000/api/public_key';
let publicKey = '';

// Fetch the public key
const fetchPublicKey = async () => {
    try {
        const response = await axios.get(PUBLIC_KEY_URL);
        publicKey = response.data.public_key;
    } catch (error) {
        console.error('Error fetching public key:', error);
    }
};

fetchPublicKey();

app.post('/submit', async (req, res) => {
    const token = req.body.captcha_token;
    
    if (!token) {
        return res.status(400).json({ error: 'CAPTCHA token is missing' });
    }

    try {
        const decoded = jwt.verify(token, publicKey);
        
        if (decoded.score > 0.5) {
            // Process form submission for human user
            res.json({ success: true, message: 'Form submitted successfully' });
        } else {
            res.status(403).json({ error: 'CAPTCHA verification failed' });
        }
    } catch (error) {
        console.error('Error verifying CAPTCHA token:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

app.listen(3000, () => console.log('Server running on port 3000'));
```

## TODO
- Capture the form length and use (duration / form length) and replace the `duration` feature used during training.