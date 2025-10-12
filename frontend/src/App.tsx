import React, { useState } from 'react';
import './App.css';

// Define the structure of the JSON response we expect from the API
interface PredictionResponse {
  prediction?: 'spam' | 'ham';
  error?: string;
}

function App() {
  const [text, setText] = useState<string>('');
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleTextChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(event.target.value);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!text.trim()) {
      setResult({ error: 'Please enter some text to analyze.' });
      return;
    }

    setIsLoading(true);
    setResult(null);

    try {
      const response = await fetch('http://localhost:5000/predict', { // Flask backend runs on port 5000
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        const errorData: PredictionResponse = await response.json();
        throw new Error(errorData.error || `HTTP error! Status: ${response.status}`);
      }

      const data: PredictionResponse = await response.json();
      setResult(data);

    } catch (error) {
      if (error instanceof Error) {
        setResult({ error: error.message });
      } else {
        setResult({ error: 'An unknown error occurred.' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const getResultClass = () => {
    if (!result) return '';
    if (result.error) return 'error';
    if (result.prediction) return result.prediction;
    return '';
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Spam Detector</h1>
        <p>Enter a message to test if it's spam or not.</p>
      </header>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <textarea
            value={text}
            onChange={handleTextChange}
            placeholder="Type or paste your message here..."
            aria-label="Message input"
          />
        </div>
        <button type="submit" disabled={isLoading || !text.trim()}>
          {isLoading ? 'Analyzing...' : 'Check Message'}
        </button>
      </form>

      <div className="result-section">
        {result && (
          <div className={`result-text ${getResultClass()}`}>
            {result.error ? `Error: ${result.error}` : `Prediction: ${result.prediction?.toUpperCase()}`}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;