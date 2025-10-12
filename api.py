
import joblib
from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for the React frontend (running on localhost:3000)
CORS(app, resources={r"/predict": {"origins": "http://localhost:3000"}})

# --- Load Model and Vectorizer ---
# We load the model and vectorizer once when the server starts
# to avoid reloading them on every request, which is inefficient.
MODEL = None
VECTORIZER = None

try:
    base_dir = Path(__file__).parent
    model_path = base_dir / "ml_models" / "spam_detector_latest.joblib"
    vectorizer_path = base_dir / "ml_models" / "spam_detector_vectorizer_latest.joblib"

    if model_path.exists() and vectorizer_path.exists():
        MODEL = joblib.load(model_path)
        VECTORIZER = joblib.load(vectorizer_path)
        print("Model and vectorizer loaded successfully.")
    else:
        print("Error: Model or vectorizer file not found.")
        MODEL = None # Ensure it's None if loading fails

except Exception as e:
    print(f"Error loading model: {e}")
    MODEL = None # Ensure it's None if loading fails
# --------------------------------

@app.route('/predict', methods=['POST'])
def predict():
    """
    Prediction endpoint.
    Receives a JSON payload with 'text' and returns a prediction.
    """
    # Check if the model was loaded correctly
    if MODEL is None or VECTORIZER is None:
        return jsonify({'error': 'Model is not available on the server.'}), 500

    # Get JSON data from the request
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Invalid input: JSON with a "text" field is required.'}), 400

    text = data['text']
    if not isinstance(text, str) or not text.strip():
        return jsonify({'error': 'Invalid input: "text" field must be a non-empty string.'}), 400

    try:
        # Vectorize the input text and make a prediction
        text_vector = VECTORIZER.transform([text])
        prediction = MODEL.predict(text_vector)

        # Convert prediction (0 or 1) to a human-readable label
        result = 'spam' if prediction[0] == 1 else 'ham'

        # Return the result as JSON
        return jsonify({'prediction': result})

    except Exception as e:
        # Handle any errors during prediction
        print(f"Prediction error: {e}")
        return jsonify({'error': 'An error occurred during prediction.'}), 500

if __name__ == '__main__':
    # Run the Flask app
    # The host '0.0.0.0' makes it accessible from the network
    app.run(host='0.0.0.0', port=5000, debug=True)

