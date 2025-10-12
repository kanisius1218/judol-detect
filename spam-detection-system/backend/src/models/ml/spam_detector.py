"""
ML Spam Detection Model with advanced feature extraction and ensemble methods.
Implements production-ready model loading, prediction, and confidence scoring.
"""
import pickle
import joblib
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import numpy as np
from sklearn.base import BaseEstimator
from dataclasses import dataclass
import re
import hashlib
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import pandas as pd
from ...core import logger, settings, SpamDetectionError


# Download NLTK data if not present
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)


@dataclass
class PredictionResult:
    """Result of spam prediction."""
    is_spam: bool
    confidence: float
    spam_score: float
    features: Dict[str, Any]
    model_version: str
    processing_time_ms: float
    explanation: Optional[str] = None
    risk_level: str = "low"  # low, medium, high, critical


@dataclass
class BatchPredictionResult:
    """Result of batch spam prediction."""
    predictions: List[PredictionResult]
    total_processed: int
    spam_count: int
    ham_count: int
    average_confidence: float
    processing_time_ms: float
    failed_indices: List[int]


class FeatureExtractor:
    """Extract features from text for spam detection."""
    
    def __init__(self):
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
        
        # Spam indicators
        self.spam_keywords = {
            'financial': ['money', 'cash', 'loan', 'credit', 'debt', 'bank', 'investment'],
            'urgency': ['urgent', 'immediately', 'now', 'hurry', 'quick', 'fast', 'limited'],
            'promotional': ['free', 'offer', 'discount', 'sale', 'deal', 'save', 'bonus'],
            'suspicious': ['click', 'link', 'verify', 'confirm', 'update', 'suspended'],
            'adult': ['xxx', 'adult', 'dating', 'singles', 'hot'],
            'pharmaceutical': ['viagra', 'pills', 'medication', 'pharmacy', 'drug'],
            'lottery': ['winner', 'won', 'prize', 'lottery', 'jackpot', 'million'],
            'phishing': ['paypal', 'ebay', 'amazon', 'account', 'password', 'security']
        }
        
        # Compile regex patterns
        self.url_pattern = re.compile(r'https?://\S+|www\.\S+')
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.phone_pattern = re.compile(r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}')
        self.money_pattern = re.compile(r'[$£€¥]\s?\d+[\.,]?\d*|USD|EUR|GBP')
        self.all_caps_pattern = re.compile(r'\b[A-Z]{2,}\b')
        self.special_char_pattern = re.compile(r'[!@#$%^&*(),.?":{}|<>]')
        self.emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "]+", 
            flags=re.UNICODE
        )
    
    def extract_features(self, text: str) -> Dict[str, Any]:
        """Extract comprehensive features from text."""
        if not text:
            return self._empty_features()
        
        # Basic features
        features = {
            'text_length': len(text),
            'word_count': len(text.split()),
            'avg_word_length': np.mean([len(word) for word in text.split()]) if text.split() else 0,
            'unique_word_count': len(set(text.lower().split())),
            'char_count': len(text.replace(' ', '')),
            'whitespace_count': text.count(' '),
            'line_count': text.count('\n') + 1,
        }
        
        # URL and contact features
        urls = self.url_pattern.findall(text)
        features.update({
            'url_count': len(urls),
            'email_count': len(self.email_pattern.findall(text)),
            'phone_count': len(self.phone_pattern.findall(text)),
            'shortened_url_count': sum(1 for url in urls if any(shortener in url.lower() for shortener in ['bit.ly', 'tinyurl', 'goo.gl', 'ow.ly'])),
        })
        
        # Capitalization features
        if text:
            features['capital_ratio'] = sum(1 for c in text if c.isupper()) / len(text)
            features['all_caps_word_count'] = len(self.all_caps_pattern.findall(text))
            features['title_case_ratio'] = sum(1 for word in text.split() if word.istitle()) / len(text.split())
        else:
            features['capital_ratio'] = 0
            features['all_caps_word_count'] = 0
            features['title_case_ratio'] = 0
        
        # Special character features
        special_chars = self.special_char_pattern.findall(text)
        features['special_char_count'] = len(special_chars)
        features['special_char_ratio'] = len(special_chars) / len(text) if text else 0
        features['exclamation_count'] = text.count('!')
        features['question_count'] = text.count('?')
        features['emoji_count'] = len(self.emoji_pattern.findall(text))
        
        # Money and numbers
        features['money_mention_count'] = len(self.money_pattern.findall(text))
        features['digit_count'] = sum(1 for c in text if c.isdigit())
        features['digit_ratio'] = features['digit_count'] / len(text) if text else 0
        
        # Spam keyword features
        text_lower = text.lower()
        for category, keywords in self.spam_keywords.items():
            features[f'spam_keywords_{category}'] = sum(1 for keyword in keywords if keyword in text_lower)
        
        # Language and grammar features
        try:
            tokens = word_tokenize(text.lower())
            features['token_count'] = len(tokens)
            
            # Remove stopwords
            filtered_tokens = [w for w in tokens if w not in self.stop_words and w.isalnum()]
            features['non_stop_word_count'] = len(filtered_tokens)
            
            # Stemming
            stemmed = [self.stemmer.stem(w) for w in filtered_tokens]
            features['unique_stem_count'] = len(set(stemmed))
            
            # N-gram features
            if len(tokens) >= 2:
                bigrams = [(tokens[i], tokens[i+1]) for i in range(len(tokens)-1)]
                features['unique_bigram_count'] = len(set(bigrams))
            else:
                features['unique_bigram_count'] = 0
            
        except Exception as e:
            logger.warning(f"Error in tokenization: {str(e)}")
            features.update({
                'token_count': features['word_count'],
                'non_stop_word_count': features['word_count'],
                'unique_stem_count': features['unique_word_count'],
                'unique_bigram_count': 0
            })
        
        # Repetition features
        words = text.lower().split()
        if words:
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            features['max_word_frequency'] = max(word_freq.values())
            features['repeated_word_ratio'] = sum(1 for count in word_freq.values() if count > 1) / len(word_freq)
        else:
            features['max_word_frequency'] = 0
            features['repeated_word_ratio'] = 0
        
        # Content hash for duplicate detection
        features['content_hash'] = hashlib.md5(text.encode()).hexdigest()
        
        return features
    
    def _empty_features(self) -> Dict[str, Any]:
        """Return empty feature dict for missing text."""
        feature_names = [
            'text_length', 'word_count', 'avg_word_length', 'unique_word_count',
            'char_count', 'whitespace_count', 'line_count', 'url_count',
            'email_count', 'phone_count', 'shortened_url_count', 'capital_ratio',
            'all_caps_word_count', 'title_case_ratio', 'special_char_count',
            'special_char_ratio', 'exclamation_count', 'question_count',
            'emoji_count', 'money_mention_count', 'digit_count', 'digit_ratio',
            'token_count', 'non_stop_word_count', 'unique_stem_count',
            'unique_bigram_count', 'max_word_frequency', 'repeated_word_ratio'
        ]
        
        features = {name: 0 for name in feature_names}
        
        # Add spam keyword features
        for category in self.spam_keywords.keys():
            features[f'spam_keywords_{category}'] = 0
        
        features['content_hash'] = ''
        
        return features


class SpamDetector:
    """Main spam detection model with ensemble methods."""
    
    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or settings.MODEL_PATH
        self.model = None
        self.feature_extractor = FeatureExtractor()
        self.model_version = settings.MODEL_VERSION
        self.threshold = settings.MODEL_CONFIDENCE_THRESHOLD
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Load model
        self.load_model()
    
    def load_model(self) -> bool:
        """Load the ML model from disk."""
        try:
            if self.model_path.exists():
                # Try joblib first (preferred for sklearn models)
                try:
                    self.model = joblib.load(self.model_path)
                except:
                    # Fallback to pickle
                    with open(self.model_path, 'rb') as f:
                        self.model = pickle.load(f)
                
                logger.info(f"Model loaded successfully from {self.model_path}")
                return True
            else:
                logger.warning(f"Model file not found at {self.model_path}, using fallback classifier")
                self._create_fallback_model()
                return False
                
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self._create_fallback_model()
            return False
    
    def _create_fallback_model(self):
        """Create a simple rule-based fallback model."""
        logger.info("Creating fallback rule-based model")
        
        class FallbackModel:
            """Simple rule-based spam classifier."""
            
            def predict_proba(self, features_df):
                """Predict spam probability based on rules."""
                probabilities = []
                
                for _, features in features_df.iterrows():
                    score = 0
                    
                    # URL-based rules
                    if features.get('url_count', 0) > 3:
                        score += 0.3
                    if features.get('shortened_url_count', 0) > 0:
                        score += 0.4
                    
                    # Keyword-based rules
                    spam_keyword_total = sum(
                        features.get(f'spam_keywords_{cat}', 0) 
                        for cat in ['financial', 'urgency', 'promotional', 'suspicious', 
                                    'adult', 'pharmaceutical', 'lottery', 'phishing']
                    )
                    score += min(spam_keyword_total * 0.15, 0.6)
                    
                    # Formatting-based rules
                    if features.get('all_caps_word_count', 0) > 5:
                        score += 0.2
                    if features.get('exclamation_count', 0) > 3:
                        score += 0.15
                    if features.get('special_char_ratio', 0) > 0.1:
                        score += 0.1
                    
                    # Money mentions
                    if features.get('money_mention_count', 0) > 0:
                        score += 0.25
                    
                    # Normalize score
                    score = min(max(score, 0), 1)
                    
                    # Return as [ham_probability, spam_probability]
                    probabilities.append([1 - score, score])
                
                return np.array(probabilities)
        
        self.model = FallbackModel()
    
    async def predict(self, text: str) -> PredictionResult:
        """Predict if text is spam."""
        start_time = datetime.utcnow()
        
        try:
            # Validate input
            if not text or len(text.strip()) == 0:
                return self._create_empty_prediction()
            
            if len(text) > settings.MODEL_MAX_INPUT_LENGTH:
                text = text[:settings.MODEL_MAX_INPUT_LENGTH]
            
            # Extract features
            features = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.feature_extractor.extract_features,
                text
            )
            
            # Prepare features for model
            feature_df = pd.DataFrame([features])
            
            # Select only numerical features for the model
            numerical_features = [col for col in feature_df.columns 
                                 if col != 'content_hash' and isinstance(feature_df[col].iloc[0], (int, float))]
            model_input = feature_df[numerical_features]
            
            # Get prediction
            probabilities = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.model.predict_proba,
                model_input
            )
            
            # Extract spam probability (assuming binary classification: [ham, spam])
            spam_probability = probabilities[0][1] if len(probabilities[0]) > 1 else probabilities[0][0]
            
            # Determine if spam
            is_spam = spam_probability >= self.threshold
            
            # Calculate risk level
            risk_level = self._calculate_risk_level(spam_probability)
            
            # Generate explanation
            explanation = self._generate_explanation(features, spam_probability)
            
            # Calculate processing time
            processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return PredictionResult(
                is_spam=is_spam,
                confidence=float(spam_probability) if is_spam else float(1 - spam_probability),
                spam_score=float(spam_probability),
                features=features,
                model_version=self.model_version,
                processing_time_ms=processing_time_ms,
                explanation=explanation,
                risk_level=risk_level
            )
            
        except Exception as e:
            logger.error(f"Error in spam prediction: {str(e)}")
            raise SpamDetectionError(
                message="Failed to predict spam",
                reason=str(e)
            )
    
    async def predict_batch(self, texts: List[str]) -> BatchPredictionResult:
        """Predict spam for multiple texts."""
        start_time = datetime.utcnow()
        predictions = []
        failed_indices = []
        
        # Process in parallel with limited concurrency
        tasks = []
        for i, text in enumerate(texts):
            task = self._predict_with_index(text, i)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to process text at index {i}: {str(result)}")
                failed_indices.append(i)
                predictions.append(self._create_empty_prediction())
            else:
                predictions.append(result)
        
        # Calculate statistics
        spam_count = sum(1 for p in predictions if p.is_spam)
        ham_count = len(predictions) - spam_count - len(failed_indices)
        avg_confidence = np.mean([p.confidence for p in predictions if p.confidence > 0])
        
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return BatchPredictionResult(
            predictions=predictions,
            total_processed=len(texts),
            spam_count=spam_count,
            ham_count=ham_count,
            average_confidence=float(avg_confidence),
            processing_time_ms=processing_time_ms,
            failed_indices=failed_indices
        )
    
    async def _predict_with_index(self, text: str, index: int) -> PredictionResult:
        """Predict with index tracking for error handling."""
        try:
            return await self.predict(text)
        except Exception as e:
            raise Exception(f"Index {index}: {str(e)}")
    
    def _calculate_risk_level(self, spam_probability: float) -> str:
        """Calculate risk level based on spam probability."""
        if spam_probability >= 0.95:
            return "critical"
        elif spam_probability >= 0.85:
            return "high"
        elif spam_probability >= 0.70:
            return "medium"
        else:
            return "low"
    
    def _generate_explanation(self, features: Dict[str, Any], spam_probability: float) -> str:
        """Generate human-readable explanation for the prediction."""
        explanations = []
        
        if spam_probability >= self.threshold:
            explanations.append(f"High spam probability: {spam_probability:.2%}")
            
            # Check major spam indicators
            if features.get('url_count', 0) > 2:
                explanations.append(f"Contains {features['url_count']} URLs")
            
            if features.get('money_mention_count', 0) > 0:
                explanations.append("Contains money-related terms")
            
            spam_keyword_total = sum(
                features.get(f'spam_keywords_{cat}', 0) 
                for cat in self.feature_extractor.spam_keywords.keys()
            )
            if spam_keyword_total > 3:
                explanations.append(f"Contains {spam_keyword_total} spam keywords")
            
            if features.get('all_caps_word_count', 0) > 3:
                explanations.append("Excessive use of capital letters")
            
        else:
            explanations.append(f"Low spam probability: {spam_probability:.2%}")
            explanations.append("Content appears legitimate")
        
        return " | ".join(explanations)
    
    def _create_empty_prediction(self) -> PredictionResult:
        """Create empty prediction for invalid input."""
        return PredictionResult(
            is_spam=False,
            confidence=0.0,
            spam_score=0.0,
            features={},
            model_version=self.model_version,
            processing_time_ms=0.0,
            explanation="Empty or invalid input",
            risk_level="low"
        )
    
    def update_model(self, new_model_path: Path) -> bool:
        """Update the model with a new version."""
        try:
            # Backup current model
            backup_path = self.model_path.with_suffix('.backup')
            if self.model_path.exists():
                import shutil
                shutil.copy2(self.model_path, backup_path)
            
            # Load new model
            old_model = self.model
            old_path = self.model_path
            
            self.model_path = new_model_path
            if self.load_model():
                logger.info(f"Model updated successfully to {new_model_path}")
                return True
            else:
                # Rollback
                self.model = old_model
                self.model_path = old_path
                logger.error("Failed to update model, rolled back to previous version")
                return False
                
        except Exception as e:
            logger.error(f"Error updating model: {str(e)}")
            return False
