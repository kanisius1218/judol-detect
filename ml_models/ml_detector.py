"""
ML-Powered Spam Detector
Professional implementation with trained models
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Optional, List
from pathlib import Path
from dataclasses import dataclass


@dataclass
class MLPredictionResult:
    """Result from ML prediction."""
    text: str
    is_spam: bool
    confidence: float
    spam_probability: float
    ham_probability: float
    model_name: str


class MLSpamDetector:
    """
    ML-powered spam detector using trained models.
    
    Features:
    - Trained scikit-learn models
    - TF-IDF vectorization
    - Probability-based confidence
    - Model versioning
    - Fallback to rule-based detection
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        vectorizer_path: Optional[str] = None,
        threshold: float = 0.5,
        model_dir: str = "ml_models"
    ):
        """
        Initialize ML detector.
        
        Args:
            model_path: Path to trained model
            vectorizer_path: Path to vectorizer
            threshold: Probability threshold for spam classification
            model_dir: Directory containing models
        """
        self.threshold = threshold
        self.model_dir = Path(model_dir)
        self.model = None
        self.vectorizer = None
        self.model_name = "unknown"
        
        # Load model
        self._load_model(model_path, vectorizer_path)
    
    def _load_model(
        self,
        model_path: Optional[str],
        vectorizer_path: Optional[str]
    ):
        """Load trained model and vectorizer."""
        try:
            # Use provided paths or default to latest
            if model_path is None:
                model_path = self.model_dir / "spam_detector_latest.joblib"
            if vectorizer_path is None:
                vectorizer_path = self.model_dir / "spam_detector_vectorizer_latest.joblib"
            
            model_path = Path(model_path)
            vectorizer_path = Path(vectorizer_path)
            
            if not model_path.exists() or not vectorizer_path.exists():
                print("No trained model found. Please run train_model.py first.")
                print("    Falling back to rule-based detection.")
                return
            
            # Load model and vectorizer
            self.model = joblib.load(model_path)
            self.vectorizer = joblib.load(vectorizer_path)
            self.model_name = self.model.__class__.__name__
            
            print(f"ML model loaded: {self.model_name}")
            print(f"  Model path: {model_path}")
            print(f"  Vectorizer path: {vectorizer_path}")
            print(f"  Threshold: {self.threshold}")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            print("    Falling back to rule-based detection.")
    
    def predict(self, text: str) -> MLPredictionResult:
        """
        Predict if text is spam using ML model.
        
        Args:
            text: Text to classify
            
        Returns:
            MLPredictionResult with prediction details
        """
        if self.model is None or self.vectorizer is None:
            # Fallback to rule-based
            return self._fallback_prediction(text)
        
        try:
            # Vectorize text
            X = self.vectorizer.transform([text])
            
            # Predict probabilities
            probabilities = self.model.predict_proba(X)[0]
            ham_prob = float(probabilities[0])
            spam_prob = float(probabilities[1])
            
            # Classify
            is_spam = spam_prob >= self.threshold
            confidence = spam_prob if is_spam else ham_prob
            
            return MLPredictionResult(
                text=text,
                is_spam=is_spam,
                confidence=confidence,
                spam_probability=spam_prob,
                ham_probability=ham_prob,
                model_name=self.model_name
            )
            
        except Exception as e:
            print(f"ML prediction error: {e}")
            return self._fallback_prediction(text)
    
    def predict_batch(self, texts: List[str]) -> List[MLPredictionResult]:
        """
        Predict multiple texts efficiently.
        
        Args:
            texts: List of texts to classify
            
        Returns:
            List of MLPredictionResult
        """
        if self.model is None or self.vectorizer is None:
            return [self._fallback_prediction(text) for text in texts]
        
        try:
            # Vectorize all texts
            X = self.vectorizer.transform(texts)
            
            # Predict probabilities for all
            probabilities = self.model.predict_proba(X)
            
            # Create results
            results = []
            for i, text in enumerate(texts):
                ham_prob = float(probabilities[i][0])
                spam_prob = float(probabilities[i][1])
                is_spam = spam_prob >= self.threshold
                confidence = spam_prob if is_spam else ham_prob
                
                results.append(MLPredictionResult(
                    text=text,
                    is_spam=is_spam,
                    confidence=confidence,
                    spam_probability=spam_prob,
                    ham_probability=ham_prob,
                    model_name=self.model_name
                ))
            
            return results
            
        except Exception as e:
            print(f"Batch prediction error: {e}")
            return [self._fallback_prediction(text) for text in texts]
    
    def _fallback_prediction(self, text: str) -> MLPredictionResult:
        """
        Fallback to simple rule-based detection.
        
        Args:
            text: Text to classify
            
        Returns:
            MLPredictionResult with rule-based prediction
        """
        # Simple keyword-based detection
        spam_keywords = [
            'slot', 'gacor', 'maxwin', 'togel', 'casino',
            'deposit', 'bonus', 'jackpot', 'judi', 'withdraw'
        ]
        
        text_lower = text.lower()
        keyword_matches = sum(1 for keyword in spam_keywords if keyword in text_lower)
        
        # Simple scoring
        confidence = min(keyword_matches / len(spam_keywords), 1.0)
        is_spam = confidence >= 0.2
        
        return MLPredictionResult(
            text=text,
            is_spam=is_spam,
            confidence=confidence,
            spam_probability=confidence if is_spam else 0.0,
            ham_probability=1.0 - confidence if not is_spam else 0.0,
            model_name="rule_based_fallback"
        )
    
    def get_feature_importance(self, top_n: int = 20) -> Optional[Dict]:
        """
        Get top N most important features.
        
        Args:
            top_n: Number of top features to return
            
        Returns:
            Dict with feature names and importance scores
        """
        if self.model is None or self.vectorizer is None:
            return None
        
        # Check if model has feature_importances_
        if not hasattr(self.model, 'feature_importances_'):
            return None
        
        try:
            # Get feature names
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Get importances
            importances = self.model.feature_importances_
            
            # Get top N
            indices = np.argsort(importances)[-top_n:][::-1]
            
            return {
                feature_names[i]: float(importances[i])
                for i in indices
            }
            
        except Exception as e:
            print(f"Error getting feature importance: {e}")
            return None
    
    def update_threshold(self, new_threshold: float):
        """
        Update classification threshold.
        
        Args:
            new_threshold: New threshold value (0.0 - 1.0)
        """
        if not 0.0 <= new_threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        
        self.threshold = new_threshold
        print(f"Threshold updated to {new_threshold}")
    
    def get_model_info(self) -> Dict:
        """
        Get information about loaded model.
        
        Returns:
            Dict with model information
        """
        if self.model is None:
            return {
                'loaded': False,
                'model_name': 'none',
                'using_fallback': True
            }
        
        info = {
            'loaded': True,
            'model_name': self.model_name,
            'threshold': self.threshold,
            'using_fallback': False
        }
        
        # Add model-specific info
        if hasattr(self.model, 'n_estimators'):
            info['n_estimators'] = self.model.n_estimators
        if hasattr(self.model, 'max_depth'):
            info['max_depth'] = self.model.max_depth
        
        # Vectorizer info
        if self.vectorizer:
            info['vocabulary_size'] = len(self.vectorizer.vocabulary_)
            info['ngram_range'] = self.vectorizer.ngram_range
        
        return info


if __name__ == "__main__":
    # Test the detector with data from our dataset
    detector = MLSpamDetector()
    
    # Load the dataset to test against
    try:
        dataset_path = Path(__file__).parent.parent / 'data' / 'dataset.csv'
        df = pd.read_csv(dataset_path)
        
        # Get 5 random spam and 5 random ham comments
        spam_samples = df[df['label'] == 'spam'].sample(n=5, random_state=42)
        ham_samples = df[df['label'] == 'ham'].sample(n=5, random_state=42)
        test_df = pd.concat([spam_samples, ham_samples])
        
    except Exception as e:
        print(f"Could not load dataset for testing: {e}")
        test_df = pd.DataFrame({
            'text': [
                "slot gacor maxwin deposit 10rb",
                "great video! thanks for sharing",
                "togel online angka jitu",
                "i really enjoyed this content",
                "link alternatif situs judi"
            ],
            'label': ['spam', 'ham', 'spam', 'ham', 'spam']
        })

    print("\n" + "=" * 70)
    print("ML SPAM DETECTOR TEST ON DATASET SAMPLES")
    print("=" * 70)
    
    for index, row in test_df.iterrows():
        text = row['text']
        true_label = row['label']
        
        result = detector.predict(text)
        
        prediction_status = "CORRECT" if (result.is_spam and true_label == 'spam') or (not result.is_spam and true_label == 'ham') else "WRONG"
        
        print(f"\nText: {text}")
        print(f"True Label: {true_label.upper()}")
        print(f"Prediction: {'SPAM' if result.is_spam else 'HAM'} (Confidence: {result.confidence:.2f})")
        print(f"Result: {prediction_status}")
    
    print("\n" + "=" * 70)
