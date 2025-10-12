"""
Advanced Spam ML Trainer with Ensemble Methods
"""

import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.ensemble import (
    RandomForestClassifier, 
    GradientBoostingClassifier,
    VotingClassifier,
    AdaBoostClassifier,
    ExtraTreesClassifier
)
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_recall_fscore_support,
    roc_auc_score,
    matthews_corrcoef,
    cohen_kappa_score
)
from sklearn.pipeline import FeatureUnion

# Import custom feature extractor
from advanced_train_model import AdvancedTextFeatureExtractor, DeepLearningSpamClassifier

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

# Deep Learning
try:
    import tensorflow as tf
    DEEP_LEARNING_AVAILABLE = True
except ImportError:
    DEEP_LEARNING_AVAILABLE = False


class AdvancedSpamMLTrainer:
    """
    Professional ML training pipeline with advanced techniques.
    """
    
    def __init__(self, model_dir: str = "ml_models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        self.vectorizers = {}
        self.models = {}
        self.ensemble_model = None
        self.deep_model = None
        self.metrics = {}
        self.feature_importance = {}
        
    def prepare_advanced_features(
        self,
        texts: List[str],
        labels: List[int]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare advanced features using multiple techniques.
        """
        print("Preparing advanced features...")
        
        # TF-IDF features
        tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            min_df=2,
            max_df=0.8,
            sublinear_tf=True,
            use_idf=True,
            smooth_idf=True,
            strip_accents='unicode'
        )
        
        # Count features
        count_vectorizer = CountVectorizer(
            max_features=3000,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8,
            binary=True
        )
        
        # Character-level features
        char_vectorizer = TfidfVectorizer(
            max_features=2000,
            analyzer='char',
            ngram_range=(2, 4),
            min_df=2,
            max_df=0.8
        )
        
        # Custom features
        custom_extractor = AdvancedTextFeatureExtractor()
        
        # Combine all features
        feature_union = FeatureUnion([
            ('tfidf', tfidf_vectorizer),
            ('count', count_vectorizer),
            ('char', char_vectorizer),
            ('custom', custom_extractor)
        ])
        
        X = feature_union.fit_transform(texts)
        y = np.array(labels)
        
        self.vectorizers['feature_union'] = feature_union
        
        print(f"Feature matrix shape: {X.shape}")
        print(f"Class distribution: {np.bincount(y)}")
        
        return X, y
    
    def train_ensemble_models(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict:
        """
        Train multiple models and create ensemble.
        """
        print("\nTraining ensemble models...")
        
        base_models = []
        
        # 1. Random Forest
        rf = RandomForestClassifier(
            n_estimators=200,
            max_depth=30,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1
        )
        base_models.append(('rf', rf))
        
        # 2. Gradient Boosting
        gb = GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=7,
            min_samples_split=5,
            min_samples_leaf=3,
            subsample=0.8,
            random_state=42
        )
        base_models.append(('gb', gb))
        
        # 3. XGBoost
        if XGBOOST_AVAILABLE:
            xgb_model = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=7,
                learning_rate=0.1,
                objective='binary:logistic',
                use_label_encoder=False,
                random_state=42
            )
            base_models.append(('xgb', xgb_model))
        
        # 4. LightGBM
        if LIGHTGBM_AVAILABLE:
            lgb_model = lgb.LGBMClassifier(
                n_estimators=200,
                max_depth=7,
                learning_rate=0.1,
                num_leaves=31,
                random_state=42,
                verbosity=-1
            )
            base_models.append(('lgb', lgb_model))
        
        # 5. SVM
        svm = SVC(
            kernel='rbf',
            C=10,
            gamma='scale',
            probability=True,
            random_state=42
        )
        base_models.append(('svm', svm))
        
        # 6. Logistic Regression
        lr = LogisticRegression(
            C=1.0,
            max_iter=1000,
            random_state=42,
            n_jobs=-1
        )
        base_models.append(('lr', lr))
        
        # 7. Extra Trees
        et = ExtraTreesClassifier(
            n_estimators=200,
            max_depth=30,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        base_models.append(('et', et))
        
        # 8. AdaBoost
        ada = AdaBoostClassifier(
            n_estimators=100,
            learning_rate=1.0,
            random_state=42
        )
        base_models.append(('ada', ada))
        
        # 9. Neural Network
        mlp = MLPClassifier(
            hidden_layer_sizes=(100, 50),
            activation='relu',
            solver='adam',
            alpha=0.001,
            max_iter=500,
            random_state=42
        )
        base_models.append(('mlp', mlp))
        
        # Train all models
        trained_models = []
        results = {}
        
        for name, model in base_models:
            print(f"  Training {name}...")
            try:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
                
                accuracy = accuracy_score(y_test, y_pred)
                precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary')
                
                results[name] = {
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1,
                    'model': model
                }
                
                trained_models.append((name, model))
                
                print(f"    {name}: Acc={accuracy:.4f}, F1={f1:.4f}")
            except Exception as e:
                print(f"    {name}: Failed - {e}")
        
        # Create voting ensemble
        print("\n  Creating voting ensemble...")
        self.ensemble_model = VotingClassifier(
            estimators=trained_models,
            voting='soft'
        )
        self.ensemble_model.fit(X_train, y_train)
        
        # Evaluate ensemble
        y_pred = self.ensemble_model.predict(X_test)
        y_proba = self.ensemble_model.predict_proba(X_test)[:, 1]
        
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary')
        
        results['ensemble'] = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'model': self.ensemble_model
        }
        
        print(f"\n  Ensemble: Acc={accuracy:.4f}, F1={f1:.4f}")
        
        return results
    
    def train_deep_learning_models(
        self,
        texts_train: List[str],
        y_train: np.ndarray,
        texts_test: List[str],
        y_test: np.ndarray
    ) -> Optional[Dict]:
        """
        Train deep learning models.
        """
        if not DEEP_LEARNING_AVAILABLE:
            print("Deep learning not available")
            return None
        
        print("\nTraining deep learning models...")
        
        dl_classifier = DeepLearningSpamClassifier()
        
        # Prepare sequences
        all_texts = texts_train + texts_test
        dl_classifier.prepare_sequences(all_texts)
        
        X_train_seq = dl_classifier.prepare_sequences(texts_train)
        X_test_seq = dl_classifier.prepare_sequences(texts_test)
        
        # Build and train LSTM model
        print("  Training LSTM model...")
        lstm_model = dl_classifier.build_lstm_model()
        
        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=3,
            restore_best_weights=True
        )
        
        history = lstm_model.fit(
            X_train_seq, y_train,
            batch_size=32,
            epochs=10,
            validation_split=0.2,
            callbacks=[early_stopping],
            verbose=0
        )
        
        # Evaluate
        lstm_pred = (lstm_model.predict(X_test_seq) > 0.5).astype(int).flatten()
        lstm_acc = accuracy_score(y_test, lstm_pred)
        
        print(f"    LSTM Accuracy: {lstm_acc:.4f}")
        
        self.deep_model = lstm_model
        self.dl_classifier = dl_classifier
        
        return {
            'lstm_accuracy': lstm_acc,
            'model': lstm_model,
            'tokenizer': dl_classifier.tokenizer
        }
    
    def comprehensive_evaluation(
        self,
        model,
        X_test: np.ndarray,
        y_test: np.ndarray,
        model_name: str = "Model"
    ) -> Dict:
        """
        Comprehensive model evaluation with multiple metrics.
        """
        print(f"\nEvaluating {model_name}...")
        
        # Predictions
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
        
        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_recall_fscore_support(y_test, y_pred, average='binary')[0],
            'recall': precision_recall_fscore_support(y_test, y_pred, average='binary')[1],
            'f1_score': precision_recall_fscore_support(y_test, y_pred, average='binary')[2],
            'matthews_corrcoef': matthews_corrcoef(y_test, y_pred),
            'cohen_kappa': cohen_kappa_score(y_test, y_pred),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
            'classification_report': classification_report(y_test, y_pred, output_dict=True)
        }
        
        if y_proba is not None:
            metrics['roc_auc'] = roc_auc_score(y_test, y_proba)
        
        # Print summary
        print(f"  Accuracy: {metrics['accuracy']:.4f}")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall: {metrics['recall']:.4f}")
        print(f"  F1-Score: {metrics['f1_score']:.4f}")
        if 'roc_auc' in metrics:
            print(f"  ROC AUC: {metrics['roc_auc']:.4f}")
        print(f"  MCC: {metrics['matthews_corrcoef']:.4f}")
        print(f"  Cohen's Kappa: {metrics['cohen_kappa']:.4f}")
        
        return metrics
    
    def save_advanced_models(self, model_name: str = "advanced_spam_detector"):
        """
        Save all trained models and components.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save ensemble model
        if self.ensemble_model:
            ensemble_path = self.model_dir / f"{model_name}_ensemble_{timestamp}.joblib"
            joblib.dump(self.ensemble_model, ensemble_path)
            print(f"Ensemble model saved to {ensemble_path}")
        
        # Save vectorizers
        if self.vectorizers:
            vectorizer_path = self.model_dir / f"{model_name}_vectorizers_{timestamp}.joblib"
            joblib.dump(self.vectorizers, vectorizer_path)
            print(f"Vectorizers saved to {vectorizer_path}")
        
        # Save deep learning model
        if DEEP_LEARNING_AVAILABLE and self.deep_model:
            dl_path = self.model_dir / f"{model_name}_deep_{timestamp}"
            self.deep_model.save(dl_path)
            
            # Save tokenizer
            tokenizer_path = self.model_dir / f"{model_name}_tokenizer_{timestamp}.joblib"
            joblib.dump(self.dl_classifier.tokenizer, tokenizer_path)
            print(f"Deep learning model saved to {dl_path}")
        
        # Save metrics
        metrics_path = self.model_dir / f"{model_name}_metrics_{timestamp}.json"
        with open(metrics_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        # Save latest versions
        if self.ensemble_model:
            latest_ensemble = self.model_dir / f"{model_name}_ensemble_latest.joblib"
            joblib.dump(self.ensemble_model, latest_ensemble)
        
        if self.vectorizers:
            latest_vectorizer = self.model_dir / f"{model_name}_vectorizers_latest.joblib"
            joblib.dump(self.vectorizers, latest_vectorizer)
        
        print(f"All models saved successfully!")
    
    def train_complete_pipeline(
        self,
        texts: List[str],
        labels: List[int],
        test_size: float = 0.2,
        use_deep_learning: bool = True
    ) -> Dict:
        """
        Complete training pipeline with all advanced techniques.
        """
        print("=" * 80)
        print("ADVANCED ML SPAM DETECTOR TRAINING PIPELINE")
        print("=" * 80)
        
        # Prepare advanced features
        X, y = self.prepare_advanced_features(texts, labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Also split text data for deep learning
        texts_train, texts_test = train_test_split(
            texts, test_size=test_size, random_state=42, stratify=labels
        )
        
        print(f"\nTrain set: {X_train.shape[0]} samples")
        print(f"Test set: {X_test.shape[0]} samples")
        
        # Train ensemble models
        ensemble_results = self.train_ensemble_models(X_train, y_train, X_test, y_test)
        
        # Train deep learning models
        dl_results = None
        if use_deep_learning and DEEP_LEARNING_AVAILABLE:
            dl_results = self.train_deep_learning_models(
                texts_train, y_train, texts_test, y_test
            )
        
        # Comprehensive evaluation of best model
        best_model = self.ensemble_model
        self.metrics = self.comprehensive_evaluation(
            best_model, X_test, y_test, "Ensemble Model"
        )
        
        # Save models
        self.save_advanced_models()
        
        print("\n" + "=" * 80)
        print("TRAINING COMPLETE!")
        print("=" * 80)
        
        return {
            'ensemble_results': ensemble_results,
            'deep_learning_results': dl_results,
            'final_metrics': self.metrics
        }


def load_and_augment_dataset(file_path: str) -> Tuple[List[str], List[int]]:
    """
    Load dataset with data augmentation techniques.
    """
    print(f"Loading and augmenting dataset from {file_path}...")
    
    try:
        df = pd.read_csv(file_path)
        df = df.dropna(subset=['text', 'label'])
        
        texts = df['text'].astype(str).tolist()
        labels = (df['label'].str.lower() == 'spam').astype(int).tolist()
        
        # Data augmentation for spam samples (minority class)
        spam_texts = [t for t, l in zip(texts, labels) if l == 1]
        ham_texts = [t for t, l in zip(texts, labels) if l == 0]
        
        # Simple augmentation techniques
        augmented_spam = []
        for text in spam_texts[:50]:  # Augment first 50 spam samples
            # Add uppercase version
            augmented_spam.append(text.upper())
            # Add version with repeated punctuation
            augmented_spam.append(text + "!!!")
            # Add version with extra spaces
            augmented_spam.append(" ".join(text.split()))
        
        # Add augmented samples
        texts.extend(augmented_spam)
        labels.extend([1] * len(augmented_spam))
        
        print(f"Dataset loaded: {len(texts)} samples (with augmentation)")
        print(f"Spam samples: {sum(labels)}")
        print(f"Ham samples: {len(labels) - sum(labels)}")
        
        return texts, labels
        
    except FileNotFoundError:
        print(f"Error: Dataset file not found at {file_path}")
        # Return sample data for testing
        sample_texts = [
            "WINNER!! You have won $1000 cash prize! Call now!",
            "Hi, how are you doing today?",
            "FREE entry to win $100 weekly! Text WIN to 12345",
            "Thanks for the video, very helpful",
            "SLOT GACOR MAXWIN JACKPOT BESAR!!!",
            "Can you make more content like this?",
            "Togel online terpercaya deposit pulsa",
            "Great tutorial, subscribed!",
        ]
        sample_labels = [1, 0, 1, 0, 1, 0, 1, 0]
        return sample_texts, sample_labels


if __name__ == "__main__":
    # Create trainer
    trainer = AdvancedSpamMLTrainer()
    
    # Load training data
    dataset_path = Path(__file__).parent.parent / 'data' / 'dataset.csv'
    texts, labels = load_and_augment_dataset(str(dataset_path))
    
    # Train model
    results = trainer.train_complete_pipeline(
        texts=texts,
        labels=labels,
        test_size=0.2,
        use_deep_learning=False  # Set to True if TensorFlow is installed
    )
    
    print("\nTraining Results:")
    print(json.dumps(results.get('final_metrics', {}), indent=2))
