"""
ML Model Training Pipeline for Spam Detection
Modern implementation with scikit-learn
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_recall_fscore_support,
    roc_auc_score,
    roc_curve
)
import matplotlib.pyplot as plt
import seaborn as sns


class SpamMLTrainer:
    """
    Professional ML training pipeline for spam detection.
    
    Features:
    - Multiple model comparison
    - Hyperparameter tuning
    - Cross-validation
    - Model evaluation
    - Model persistence
    - Feature importance analysis
    """
    
    def __init__(self, model_dir: str = "ml_models"):
        """
        Initialize trainer.
        
        Args:
            model_dir: Directory to save models
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        self.vectorizer = None
        self.model = None
        self.metrics = {}
        self.training_history = []
        
    def prepare_training_data(
        self,
        texts: List[str],
        labels: List[int]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for training with TF-IDF vectorization.
        
        Args:
            texts: List of text samples
            labels: List of labels (0=not spam, 1=spam)
            
        Returns:
            Tuple of (X_vectorized, y)
        """
        print("📊 Preparing training data...")
        
        # Initialize vectorizer with professional parameters
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),  # Unigram, bigram, trigram
            min_df=2,
            max_df=0.8,
            stop_words='english',
            sublinear_tf=True,
            strip_accents='unicode'
        )
        
        # Transform texts to TF-IDF features
        X = self.vectorizer.fit_transform(texts)
        y = np.array(labels)
        
        print(f"✓ Feature matrix shape: {X.shape}")
        print(f"✓ Vocabulary size: {len(self.vectorizer.vocabulary_)}")
        print(f"✓ Class distribution: {np.bincount(y)}")
        
        return X, y
    
    def train_multiple_models(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict:
        """
        Train and compare multiple models.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_test: Test features
            y_test: Test labels
            
        Returns:
            Dict with model comparison results
        """
        print("\n🤖 Training multiple models...")
        
        models = {
            'Random Forest': RandomForestClassifier(
                n_estimators=100,
                max_depth=20,
                random_state=42,
                n_jobs=-1
            ),
            'Gradient Boosting': GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            ),
            'SVM': SVC(
                kernel='rbf',
                C=1.0,
                gamma='scale',
                probability=True,
                random_state=42
            ),
            'Logistic Regression': LogisticRegression(
                max_iter=1000,
                random_state=42,
                n_jobs=-1
            ),
            'Naive Bayes': MultinomialNB(alpha=0.1)
        }
        
        results = {}
        
        for name, model in models.items():
            print(f"\n  Training {name}...")
            
            # Train
            model.fit(X_train, y_train)
            
            # Predict
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
            
            # Metrics
            accuracy = accuracy_score(y_test, y_pred)
            precision, recall, f1, _ = precision_recall_fscore_support(
                y_test, y_pred, average='binary'
            )
            
            results[name] = {
                'model': model,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'predictions': y_pred,
                'probabilities': y_proba
            }
            
            print(f"    Accuracy: {accuracy:.4f}")
            print(f"    Precision: {precision:.4f}")
            print(f"    Recall: {recall:.4f}")
            print(f"    F1-Score: {f1:.4f}")
        
        return results
    
    def hyperparameter_tuning(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        model_type: str = 'random_forest'
    ):
        """
        Perform hyperparameter tuning using GridSearchCV.
        
        Args:
            X_train: Training features
            y_train: Training labels
            model_type: Type of model to tune
        """
        print(f"\n🔧 Hyperparameter tuning for {model_type}...")
        
        if model_type == 'random_forest':
            model = RandomForestClassifier(random_state=42, n_jobs=-1)
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [10, 20, 30],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
        elif model_type == 'svm':
            model = SVC(probability=True, random_state=42)
            param_grid = {
                'C': [0.1, 1, 10],
                'gamma': ['scale', 'auto', 0.1, 0.01],
                'kernel': ['rbf', 'linear']
            }
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        grid_search = GridSearchCV(
            model,
            param_grid,
            cv=5,
            scoring='f1',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        print(f"✓ Best parameters: {grid_search.best_params_}")
        print(f"✓ Best F1 score: {grid_search.best_score_:.4f}")
        
        return grid_search.best_estimator_
    
    def evaluate_model(
        self,
        model,
        X_test: np.ndarray,
        y_test: np.ndarray,
        save_plots: bool = True
    ) -> Dict:
        """
        Comprehensive model evaluation.
        
        Args:
            model: Trained model
            X_test: Test features
            y_test: Test labels
            save_plots: Whether to save evaluation plots
            
        Returns:
            Dict with evaluation metrics
        """
        print("\n📈 Evaluating model...")
        
        # Predictions
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
        
        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, support = precision_recall_fscore_support(
            y_test, y_pred, average='binary'
        )
        
        metrics = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
            'classification_report': classification_report(y_test, y_pred, output_dict=True)
        }
        
        if y_proba is not None:
            metrics['roc_auc'] = float(roc_auc_score(y_test, y_proba))
        
        print(f"✓ Accuracy: {accuracy:.4f}")
        print(f"✓ Precision: {precision:.4f}")
        print(f"✓ Recall: {recall:.4f}")
        print(f"✓ F1-Score: {f1:.4f}")
        if 'roc_auc' in metrics:
            print(f"✓ ROC AUC: {metrics['roc_auc']:.4f}")
        
        # Save plots
        if save_plots:
            self._save_evaluation_plots(y_test, y_pred, y_proba, metrics)
        
        self.metrics = metrics
        return metrics
    
    def _save_evaluation_plots(
        self,
        y_test: np.ndarray,
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray],
        metrics: Dict
    ):
        """Save evaluation plots."""
        plot_dir = self.model_dir / 'plots'
        plot_dir.mkdir(exist_ok=True)
        
        # Confusion Matrix
        plt.figure(figsize=(8, 6))
        cm = confusion_matrix(y_test, y_pred)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False)
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        plt.savefig(plot_dir / 'confusion_matrix.png', dpi=300)
        plt.close()
        
        # ROC Curve
        if y_proba is not None:
            plt.figure(figsize=(8, 6))
            fpr, tpr, _ = roc_curve(y_test, y_proba)
            plt.plot(fpr, tpr, label=f"ROC curve (AUC = {metrics['roc_auc']:.4f})")
            plt.plot([0, 1], [0, 1], 'k--', label='Random')
            plt.xlim([0.0, 1.0])
            plt.ylim([0.0, 1.05])
            plt.xlabel('False Positive Rate')
            plt.ylabel('True Positive Rate')
            plt.title('ROC Curve')
            plt.legend(loc="lower right")
            plt.grid(alpha=0.3)
            plt.tight_layout()
            plt.savefig(plot_dir / 'roc_curve.png', dpi=300)
            plt.close()
        
        print(f"✓ Plots saved to {plot_dir}")
    
    def save_model(self, model_name: str = "spam_detector"):
        """
        Save trained model and vectorizer.
        
        Args:
            model_name: Name for the saved model
        """
        if self.model is None or self.vectorizer is None:
            raise ValueError("No model or vectorizer to save!")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save model
        model_path = self.model_dir / f"{model_name}_{timestamp}.joblib"
        joblib.dump(self.model, model_path)
        
        # Save vectorizer
        vectorizer_path = self.model_dir / f"{model_name}_vectorizer_{timestamp}.joblib"
        joblib.dump(self.vectorizer, vectorizer_path)
        
        # Save metrics
        metrics_path = self.model_dir / f"{model_name}_metrics_{timestamp}.json"
        with open(metrics_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        # Save latest symlinks
        latest_model = self.model_dir / f"{model_name}_latest.joblib"
        latest_vectorizer = self.model_dir / f"{model_name}_vectorizer_latest.joblib"
        
        # Copy to latest
        joblib.dump(self.model, latest_model)
        joblib.dump(self.vectorizer, latest_vectorizer)
        
        print(f"\n✓ Model saved to {model_path}")
        print(f"✓ Vectorizer saved to {vectorizer_path}")
        print(f"✓ Metrics saved to {metrics_path}")
    
    def train_best_model(
        self,
        texts: List[str],
        labels: List[int],
        test_size: float = 0.2,
        tune_hyperparameters: bool = False
    ) -> Dict:
        """
        Full training pipeline - prepare data, train, evaluate, save.
        
        Args:
            texts: List of text samples
            labels: List of labels
            test_size: Test set size
            tune_hyperparameters: Whether to perform hyperparameter tuning
            
        Returns:
            Dict with training results
        """
        print("=" * 70)
        print("ML SPAM DETECTOR TRAINING PIPELINE")
        print("=" * 70)
        
        # Prepare data
        X, y = self.prepare_training_data(texts, labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        print(f"\nTrain set: {X_train.shape[0]} samples")
        print(f"Test set: {X_test.shape[0]} samples")
        
        # Train multiple models and compare
        results = self.train_multiple_models(X_train, y_train, X_test, y_test)
        
        # Select best model based on F1 score
        best_model_name = max(results.items(), key=lambda x: x[1]['f1_score'])[0]
        best_model = results[best_model_name]['model']
        
        print(f"\n🏆 Best model: {best_model_name}")
        
        # Hyperparameter tuning for best model (optional)
        if tune_hyperparameters and best_model_name in ['Random Forest', 'SVM']:
            model_type = 'random_forest' if best_model_name == 'Random Forest' else 'svm'
            best_model = self.hyperparameter_tuning(X_train, y_train, model_type)
        
        self.model = best_model
        
        # Evaluate
        metrics = self.evaluate_model(best_model, X_test, y_test)
        
        # Save
        self.save_model()
        
        print("\n" + "=" * 70)
        print("TRAINING COMPLETE!")
        print("=" * 70)
        
        return {
            'best_model': best_model_name,
            'metrics': metrics,
            'all_results': {k: {
                'accuracy': v['accuracy'],
                'precision': v['precision'],
                'recall': v['recall'],
                'f1_score': v['f1_score']
            } for k, v in results.items()}
        }


def create_training_dataset() -> Tuple[List[str], List[int]]:
    """
    Create training dataset from known spam/ham examples.
    
    Returns:
        Tuple of (texts, labels)
    """
    # Spam examples (label=1)
    spam_examples = [
        "slot gacor maxwin 1000x deposit 10rb",
        "daftar link slot88 bonus new member 100%",
        "togel online angka jitu prediksi akurat",
        "casino online deposit via dana gopay",
        "judi bola parlay menang terus",
        "slot pragmatic jackpot besar pasti menang",
        "link alternatif situs judi terpercaya",
        "bonus freespin buy spin scatter hitam",
        "rtp slot tinggi gacor hari ini",
        "withdraw cepat tanpa ribet proses instant",
        # Add more spam examples...
    ]
    
    # Ham examples (label=0)
    ham_examples = [
        "great video! really enjoyed watching this",
        "thanks for sharing this tutorial",
        "can you make more videos like this?",
        "subscribed! love your content",
        "very informative and well explained",
        "this helped me a lot, thank you!",
        "amazing work, keep it up!",
        "i learned something new today",
        "please do more videos on this topic",
        "best explanation i've found online",
        # Add more ham examples...
    ]
    
    texts = spam_examples + ham_examples
    labels = [1] * len(spam_examples) + [0] * len(ham_examples)
    
    return texts, labels


if __name__ == "__main__":
    # Create trainer
    trainer = SpamMLTrainer()
    
    # Create or load training data
    texts, labels = create_training_dataset()
    
    # Train model
    results = trainer.train_best_model(
        texts=texts,
        labels=labels,
        test_size=0.2,
        tune_hyperparameters=False
    )
    
    print("\n📊 Training Results:")
    print(json.dumps(results['all_results'], indent=2))
