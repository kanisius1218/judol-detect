"""
Advanced ML Model Training Pipeline with Deep Learning
Professional implementation with state-of-the-art techniques
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Scikit-learn imports
from sklearn.model_selection import (
    train_test_split, 
    cross_val_score, 
    GridSearchCV,
    StratifiedKFold,
    RandomizedSearchCV
)
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.ensemble import (
    RandomForestClassifier, 
    GradientBoostingClassifier,
    VotingClassifier,
    AdaBoostClassifier,
    ExtraTreesClassifier
)
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB, ComplementNB
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_recall_fscore_support,
    roc_auc_score,
    roc_curve,
    precision_recall_curve,
    average_precision_score,
    matthews_corrcoef,
    cohen_kappa_score,
    log_loss
)
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import TruncatedSVD, LatentDirichletAllocation
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.base import BaseEstimator, TransformerMixin

# Deep Learning imports
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, callbacks
    from tensorflow.keras.preprocessing.text import Tokenizer
    from tensorflow.keras.preprocessing.sequence import pad_sequences
    from tensorflow.keras.layers import (
        Embedding, LSTM, GRU, Bidirectional, 
        Dense, Dropout, Conv1D, GlobalMaxPooling1D,
        Attention, MultiHeadAttention, LayerNormalization
    )
    DEEP_LEARNING_AVAILABLE = True
except ImportError:
    DEEP_LEARNING_AVAILABLE = False
    print("TensorFlow not available. Deep learning features disabled.")

# XGBoost and LightGBM
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
# from wordcloud import WordCloud  # Optional, commented out

# NLP Libraries
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer, WordNetLemmatizer
import string
import re
from collections import Counter

# Download NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
except:
    pass


class AdvancedTextFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    Advanced text feature extraction with multiple techniques.
    """
    
    def __init__(self):
        self.stemmer = PorterStemmer()
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.stop_words.update(set(stopwords.words('indonesian')) if 'indonesian' in stopwords.fileids() else set())
        
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        """Extract advanced features from text."""
        features = []
        
        for text in X:
            if isinstance(text, str):
                feature_dict = self._extract_features(text)
                features.append(list(feature_dict.values()))
            else:
                features.append([0] * 20)  # Default features
        
        return np.array(features)
    
    def _extract_features(self, text):
        """Extract comprehensive features from text."""
        features = {}
        
        # Basic statistics
        features['char_count'] = len(text)
        features['word_count'] = len(text.split())
        features['avg_word_length'] = np.mean([len(word) for word in text.split()]) if text.split() else 0
        
        # Special characters
        features['exclamation_count'] = text.count('!')
        features['question_count'] = text.count('?')
        features['uppercase_ratio'] = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        features['digit_ratio'] = sum(1 for c in text if c.isdigit()) / max(len(text), 1)
        features['special_char_ratio'] = sum(1 for c in text if c in string.punctuation) / max(len(text), 1)
        
        # URL and email detection
        features['has_url'] = 1 if re.search(r'http[s]?://|www\.', text) else 0
        features['has_email'] = 1 if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text) else 0
        features['has_phone'] = 1 if re.search(r'\b\d{10,15}\b', text) else 0
        
        # Emoji detection
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            "]+", flags=re.UNICODE)
        features['emoji_count'] = len(emoji_pattern.findall(text))
        
        # Repetition patterns
        features['repeated_chars'] = len(re.findall(r'(.)\1{2,}', text))
        features['repeated_words'] = self._count_repeated_words(text)
        
        # Sentiment indicators
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'disgusting', 'horrible', 'spam']
        features['positive_word_count'] = sum(1 for word in text.lower().split() if word in positive_words)
        features['negative_word_count'] = sum(1 for word in text.lower().split() if word in negative_words)
        
        # Spam indicators
        spam_words = ['free', 'win', 'winner', 'cash', 'prize', 'bonus', 'click', 'limited', 'offer', 'guaranteed']
        features['spam_word_count'] = sum(1 for word in text.lower().split() if word in spam_words)
        
        # Linguistic diversity
        words = text.lower().split()
        features['unique_word_ratio'] = len(set(words)) / max(len(words), 1)
        
        # N-gram features
        features['bigram_count'] = len(list(zip(words, words[1:]))) if len(words) > 1 else 0
        
        return features
    
    def _count_repeated_words(self, text):
        """Count repeated consecutive words."""
        words = text.lower().split()
        if len(words) < 2:
            return 0
        
        count = 0
        for i in range(len(words) - 1):
            if words[i] == words[i + 1]:
                count += 1
        return count


class DeepLearningSpamClassifier:
    """
    Deep Learning models for spam detection.
    """
    
    def __init__(self, max_words=10000, max_length=200):
        self.max_words = max_words
        self.max_length = max_length
        self.tokenizer = None
        self.model = None
        
    def build_lstm_model(self, embedding_dim=128):
        """Build LSTM model for text classification."""
        if not DEEP_LEARNING_AVAILABLE:
            return None
        
        model = models.Sequential([
            layers.Embedding(self.max_words, embedding_dim, input_length=self.max_length),
            layers.SpatialDropout1D(0.2),
            layers.LSTM(128, dropout=0.2, recurrent_dropout=0.2, return_sequences=True),
            layers.LSTM(64, dropout=0.2, recurrent_dropout=0.2),
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
        )
        
        return model
    
    def build_cnn_model(self, embedding_dim=128):
        """Build CNN model for text classification."""
        if not DEEP_LEARNING_AVAILABLE:
            return None
        
        model = models.Sequential([
            layers.Embedding(self.max_words, embedding_dim, input_length=self.max_length),
            layers.Conv1D(128, 5, activation='relu'),
            layers.GlobalMaxPooling1D(),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def build_transformer_model(self, embedding_dim=128):
        """Build Transformer-based model for text classification."""
        if not DEEP_LEARNING_AVAILABLE:
            return None
        
        inputs = layers.Input(shape=(self.max_length,))
        
        # Embedding layer
        embedding = layers.Embedding(self.max_words, embedding_dim)(inputs)
        
        # Multi-head attention
        attention = layers.MultiHeadAttention(
            num_heads=4,
            key_dim=embedding_dim
        )(embedding, embedding)
        
        # Add & Norm
        attention = layers.LayerNormalization()(attention + embedding)
        
        # Feed forward
        ff = layers.Dense(256, activation='relu')(attention)
        ff = layers.Dense(embedding_dim)(ff)
        ff = layers.LayerNormalization()(ff + attention)
        
        # Global pooling
        pooling = layers.GlobalAveragePooling1D()(ff)
        
        # Classification layers
        dense = layers.Dense(64, activation='relu')(pooling)
        dropout = layers.Dropout(0.5)(dense)
        outputs = layers.Dense(1, activation='sigmoid')(dropout)
        
        model = models.Model(inputs=inputs, outputs=outputs)
        
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def prepare_sequences(self, texts):
        """Convert texts to sequences for deep learning."""
        if self.tokenizer is None:
            self.tokenizer = Tokenizer(num_words=self.max_words)
            self.tokenizer.fit_on_texts(texts)
        
        sequences = self.tokenizer.texts_to_sequences(texts)
        return pad_sequences(sequences, maxlen=self.max_length)
