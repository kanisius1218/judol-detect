#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Detection Engine with Machine Learning Integration
Professional implementation with enterprise features
"""

import re
import logging
import hashlib
import numpy as np
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class AdvancedDetectionResult:
    """Enhanced detection result with comprehensive metadata."""
    is_spam: bool
    confidence: float
    detected_keywords: List[str]
    detected_patterns: List[str]
    reason: str
    score: float
    ml_confidence: Optional[float] = None
    rule_confidence: Optional[float] = None
    risk_level: str = "low"  # low, medium, high, critical
    detection_method: str = "hybrid"  # rule-based, ml, hybrid
    processing_time: float = 0.0
    threat_categories: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    detection_timestamp: datetime = field(default_factory=datetime.now)
    fingerprint: Optional[str] = None


class AdvancedSpamDetector:
    """
    Enterprise-grade spam detection engine with advanced features.
    
    Features:
    - Multi-layer detection (rules + ML)
    - Dynamic pattern learning
    - Contextual analysis
    - Performance optimization
    - Thread-safe operations
    - Caching mechanisms
    - Real-time pattern updates
    - Behavioral analysis
    """
    
    # Enhanced keyword database with severity levels
    KEYWORD_DATABASE = {
        'critical': {
            'gambling': ['slot gacor', 'togel online', 'judi online', 'casino online', 'bandar togel'],
            'financial': ['deposit pulsa', 'withdraw instant', 'bonus deposit', 'cashback 100%'],
            'urgent': ['daftar sekarang', 'klaim bonus', 'promo terbatas', 'hari ini saja'],
        },
        'high': {
            'platforms': ['pragmatic', 'pg soft', 'habanero', 'spadegaming', 'joker123'],
            'rewards': ['jackpot', 'maxwin', 'scatter', 'freespin', 'wild symbol'],
            'numbers': ['rtp tinggi', 'winrate 99%', 'pasti menang', 'gampang menang'],
        },
        'medium': {
            'general': ['online', 'terpercaya', 'resmi', 'official', 'terbaik'],
            'action': ['join', 'bergabung', 'mainkan', 'coba', 'buktikan'],
        },
        'low': {
            'common': ['gratis', 'mudah', 'cepat', 'aman', 'nyaman'],
        }
    }
    
    # Advanced pattern templates
    PATTERN_TEMPLATES = {
        'url_shortener': r'(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|ow\.ly|short\.link)',
        'suspicious_url': r'(?:http[s]?://)?(?:www\.)?[\w\-]+\.(?:tk|ml|ga|cf)',
        'phone_indo': r'(?:\+62|62|08)\s*\d{2,4}[\s\-]?\d{3,4}[\s\-]?\d{3,5}',
        'telegram': r'(?:t\.me/|@)[a-zA-Z0-9_]{5,32}',
        'whatsapp': r'wa\.me/\d{10,15}',
        'email_suspicious': r'[\w\.\-]+@(?:gmail|yahoo|hotmail)\.(?:com|co\.id)',
        'money_amount': r'(?:Rp|IDR|USD|\$)\s*[\d\.,]+(?:k|rb|jt|juta)?',
        'percentage': r'\d{1,3}(?:\.\d{1,2})?%',
        'repeated_char': r'(.)\1{3,}',
        'excessive_caps': r'[A-Z]{5,}',
        'suspicious_spacing': r'(?:\b\w\s){3,}',
    }
    
    def __init__(
        self,
        confidence_threshold: float = 40.0,
        enable_ml: bool = True,
        enable_caching: bool = True,
        cache_size: int = 1000,
        thread_workers: int = 4
    ):
        """
        Initialize advanced detector with professional configuration.
        
        Args:
            confidence_threshold: Minimum confidence for spam detection
            enable_ml: Enable machine learning integration
            enable_caching: Enable result caching
            cache_size: Maximum cache size
            thread_workers: Number of parallel workers
        """
        self.confidence_threshold = confidence_threshold
        self.enable_ml = enable_ml
        self.enable_caching = enable_caching
        self.cache_size = cache_size
        self.thread_workers = thread_workers
        
        # Initialize components
        self._init_patterns()
        self._init_statistics()
        self._init_caching()
        self._init_threading()
        
        # Machine learning model placeholder
        self.ml_model = None
        if enable_ml:
            self._load_ml_model()
        
        logger.info(
            f"Advanced detector initialized: "
            f"threshold={confidence_threshold}%, "
            f"ml={enable_ml}, "
            f"cache={enable_caching}"
        )
    
    def _init_patterns(self):
        """Initialize and compile regex patterns."""
        self.compiled_patterns = {}
        for name, pattern in self.PATTERN_TEMPLATES.items():
            try:
                self.compiled_patterns[name] = re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                logger.error(f"Failed to compile pattern {name}: {e}")
    
    def _init_statistics(self):
        """Initialize statistics tracking."""
        self.stats = {
            'total_processed': 0,
            'spam_detected': 0,
            'false_positives': 0,
            'processing_time': [],
            'keyword_hits': defaultdict(int),
            'pattern_hits': defaultdict(int),
        }
        self.stats_lock = threading.Lock()
    
    def _init_caching(self):
        """Initialize caching system."""
        if self.enable_caching:
            self._cache = {}
            self._cache_lock = threading.Lock()
    
    def _init_threading(self):
        """Initialize threading pool."""
        self.executor = ThreadPoolExecutor(max_workers=self.thread_workers)
    
    def _load_ml_model(self):
        """Load machine learning model if available."""
        try:
            model_path = Path("ml_models/spam_detector_latest.joblib")
            if model_path.exists():
                import joblib
                self.ml_model = joblib.load(model_path)
                logger.info("ML model loaded successfully")
            else:
                logger.warning("ML model not found, using rule-based detection only")
                self.enable_ml = False
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            self.enable_ml = False
    
    @lru_cache(maxsize=1000)
    def _normalize_text_advanced(self, text: str) -> str:
        """
        Advanced text normalization with multiple techniques.
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove zero-width characters
        text = re.sub(r'[\u200b-\u200f\u202a-\u202e\ufeff]', '', text)
        
        # Replace lookalike characters (homoglyphs)
        homoglyphs = {
            '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
            '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',
            'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd', 'ｅ': 'e',
            'ｆ': 'f', 'ｇ': 'g', 'ｈ': 'h', 'ｉ': 'i', 'ｊ': 'j',
            'ｋ': 'k', 'ｌ': 'l', 'ｍ': 'm', 'ｎ': 'n', 'ｏ': 'o',
            'ｐ': 'p', 'ｑ': 'q', 'ｒ': 'r', 'ｓ': 's', 'ｔ': 't',
            'ｕ': 'u', 'ｖ': 'v', 'ｗ': 'w', 'ｘ': 'x', 'ｙ': 'y',
            'ｚ': 'z', 'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd',
            'ε': 'e', 'ζ': 'z', 'η': 'h', 'θ': 'th', 'ι': 'i',
            'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x',
            'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's', 'τ': 't',
            'υ': 'u', 'φ': 'f', 'χ': 'x', 'ψ': 'ps', 'ω': 'w',
        }
        
        for fake, real in homoglyphs.items():
            text = text.replace(fake, real)
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove special characters for analysis
        text_clean = re.sub(r'[^\w\s]', ' ', text)
        text_clean = ' '.join(text_clean.split())
        
        return text_clean
    
    def _calculate_text_entropy(self, text: str) -> float:
        """
        Calculate Shannon entropy of text.
        
        Args:
            text: Input text
            
        Returns:
            Entropy value
        """
        if not text:
            return 0.0
        
        # Calculate character frequency
        char_freq = defaultdict(int)
        for char in text:
            char_freq[char] += 1
        
        # Calculate entropy
        entropy = 0.0
        text_len = len(text)
        
        for freq in char_freq.values():
            probability = freq / text_len
            if probability > 0:
                entropy -= probability * np.log2(probability)
        
        return entropy
    
    def _detect_behavioral_patterns(self, text: str) -> Dict[str, Any]:
        """
        Detect behavioral patterns in text.
        
        Args:
            text: Input text
            
        Returns:
            Behavioral analysis results
        """
        patterns = {
            'urgency_level': 0,
            'aggression_level': 0,
            'deception_indicators': 0,
            'social_engineering': 0,
        }
        
        # Urgency indicators
        urgency_words = ['sekarang', 'segera', 'cepat', 'terbatas', 'hari ini', 'buruan']
        patterns['urgency_level'] = sum(1 for word in urgency_words if word in text.lower())
        
        # Aggression indicators
        if re.search(r'[A-Z]{5,}', text):  # Excessive capitals
            patterns['aggression_level'] += 2
        if text.count('!') > 2:  # Multiple exclamations
            patterns['aggression_level'] += 1
        
        # Deception indicators
        deception_phrases = ['pasti untung', 'tanpa rugi', 'guaranteed', '100% aman']
        patterns['deception_indicators'] = sum(1 for phrase in deception_phrases if phrase in text.lower())
        
        # Social engineering
        social_phrases = ['klik sekarang', 'daftar gratis', 'khusus untuk anda', 'penawaran eksklusif']
        patterns['social_engineering'] = sum(1 for phrase in social_phrases if phrase in text.lower())
        
        return patterns
    
    def _calculate_risk_level(self, confidence: float, patterns: Dict[str, Any]) -> str:
        """
        Calculate risk level based on confidence and patterns.
        
        Args:
            confidence: Detection confidence
            patterns: Detected patterns
            
        Returns:
            Risk level (low, medium, high, critical)
        """
        risk_score = confidence
        
        # Adjust based on behavioral patterns
        behavioral = patterns.get('behavioral', {})
        risk_score += behavioral.get('urgency_level', 0) * 5
        risk_score += behavioral.get('aggression_level', 0) * 3
        risk_score += behavioral.get('deception_indicators', 0) * 10
        risk_score += behavioral.get('social_engineering', 0) * 7
        
        if risk_score >= 80:
            return "critical"
        elif risk_score >= 60:
            return "high"
        elif risk_score >= 40:
            return "medium"
        else:
            return "low"
    
    def _generate_fingerprint(self, text: str) -> str:
        """
        Generate unique fingerprint for text.
        
        Args:
            text: Input text
            
        Returns:
            MD5 fingerprint
        """
        normalized = self._normalize_text_advanced(text)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def detect_advanced(
        self,
        text: str,
        author: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AdvancedDetectionResult:
        """
        Advanced spam detection with multiple layers.
        
        Args:
            text: Text to analyze
            author: Author information
            context: Additional context
            
        Returns:
            AdvancedDetectionResult with comprehensive analysis
        """
        start_time = datetime.now()
        
        # Check cache first
        fingerprint = self._generate_fingerprint(text)
        if self.enable_caching and fingerprint in self._cache:
            cached_result = self._cache[fingerprint]
            cached_result.metadata['cache_hit'] = True
            return cached_result
        
        # Initialize results
        detected_keywords = []
        detected_patterns = []
        threat_categories = []
        score = 0
        reasons = []
        
        # Normalize text
        normalized = self._normalize_text_advanced(text)
        
        # Layer 1: Keyword Analysis with severity
        for severity, categories in self.KEYWORD_DATABASE.items():
            severity_multiplier = {'critical': 2.0, 'high': 1.5, 'medium': 1.0, 'low': 0.5}[severity]
            
            for category, keywords in categories.items():
                for keyword in keywords:
                    if keyword in normalized:
                        detected_keywords.append(keyword)
                        threat_categories.append(category)
                        score += 20 * severity_multiplier
                        
                        # Update statistics
                        with self.stats_lock:
                            self.stats['keyword_hits'][keyword] += 1
        
        # Layer 2: Pattern Detection
        pattern_scores = {
            'url_shortener': 15,
            'suspicious_url': 20,
            'phone_indo': 15,
            'telegram': 15,
            'whatsapp': 10,
            'email_suspicious': 10,
            'money_amount': 10,
            'percentage': 5,
            'repeated_char': 5,
            'excessive_caps': 5,
            'suspicious_spacing': 10,
        }
        
        for pattern_name, pattern in self.compiled_patterns.items():
            if pattern.search(text):
                detected_patterns.append(pattern_name)
                score += pattern_scores.get(pattern_name, 5)
                
                # Update statistics
                with self.stats_lock:
                    self.stats['pattern_hits'][pattern_name] += 1
        
        # Layer 3: Behavioral Analysis
        behavioral = self._detect_behavioral_patterns(text)
        if any(behavioral.values()):
            score += sum(behavioral.values()) * 5
            detected_patterns.append('behavioral_indicators')
        
        # Layer 4: Text Entropy Analysis
        entropy = self._calculate_text_entropy(text)
        if entropy < 2.0:  # Low entropy (repetitive)
            score += 10
            detected_patterns.append('low_entropy')
        elif entropy > 5.5:  # High entropy (random)
            score += 5
            detected_patterns.append('high_entropy')
        
        # Layer 5: Machine Learning (if enabled)
        ml_confidence = None
        if self.enable_ml and self.ml_model:
            try:
                ml_prediction = self.ml_model.predict_proba([text])[0]
                ml_confidence = ml_prediction[1] * 100  # Spam probability
                
                # Weighted combination
                rule_confidence = min(score, 100)
                confidence = (rule_confidence * 0.6 + ml_confidence * 0.4)
                detection_method = "hybrid"
            except Exception as e:
                logger.error(f"ML prediction failed: {e}")
                confidence = min(score, 100)
                detection_method = "rule-based"
        else:
            confidence = min(score, 100)
            detection_method = "rule-based"
        
        # Determine if spam
        is_spam = confidence >= self.confidence_threshold
        
        # Calculate risk level
        risk_level = self._calculate_risk_level(
            confidence,
            {'behavioral': behavioral}
        )
        
        # Build reason string
        if detected_keywords:
            reasons.append(f"{len(detected_keywords)} keywords")
        if detected_patterns:
            reasons.append(f"{len(detected_patterns)} patterns")
        if behavioral and any(behavioral.values()):
            reasons.append("behavioral indicators")
        
        reason = "; ".join(reasons) if reasons else "No indicators"
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create result
        result = AdvancedDetectionResult(
            is_spam=is_spam,
            confidence=confidence,
            detected_keywords=list(set(detected_keywords))[:10],
            detected_patterns=list(set(detected_patterns))[:10],
            reason=reason,
            score=score,
            ml_confidence=ml_confidence,
            rule_confidence=min(score, 100),
            risk_level=risk_level,
            detection_method=detection_method,
            processing_time=processing_time,
            threat_categories=list(set(threat_categories)),
            metadata={
                'text_length': len(text),
                'entropy': entropy,
                'behavioral': behavioral,
                'author': author,
                'context': context or {},
                'cache_hit': False,
            },
            fingerprint=fingerprint
        )
        
        # Update statistics
        with self.stats_lock:
            self.stats['total_processed'] += 1
            if is_spam:
                self.stats['spam_detected'] += 1
            self.stats['processing_time'].append(processing_time)
        
        # Cache result
        if self.enable_caching:
            with self._cache_lock:
                if len(self._cache) >= self.cache_size:
                    # Remove oldest entry
                    self._cache.pop(next(iter(self._cache)))
                self._cache[fingerprint] = result
        
        # Log if spam
        if is_spam:
            logger.warning(
                f"SPAM DETECTED: confidence={confidence:.1f}%, "
                f"risk={risk_level}, method={detection_method}, "
                f"author={author}"
            )
        
        return result
    
    def batch_detect(
        self,
        texts: List[str],
        parallel: bool = True
    ) -> List[AdvancedDetectionResult]:
        """
        Batch detection with parallel processing.
        
        Args:
            texts: List of texts to analyze
            parallel: Use parallel processing
            
        Returns:
            List of detection results
        """
        if not parallel:
            return [self.detect_advanced(text) for text in texts]
        
        # Parallel processing
        futures = []
        with ThreadPoolExecutor(max_workers=self.thread_workers) as executor:
            for text in texts:
                future = executor.submit(self.detect_advanced, text)
                futures.append(future)
            
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=5)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Batch detection error: {e}")
                    results.append(None)
        
        return [r for r in results if r is not None]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics.
        
        Returns:
            Statistics dictionary
        """
        with self.stats_lock:
            avg_time = np.mean(self.stats['processing_time']) if self.stats['processing_time'] else 0
            
            return {
                'total_processed': self.stats['total_processed'],
                'spam_detected': self.stats['spam_detected'],
                'detection_rate': (
                    self.stats['spam_detected'] / self.stats['total_processed'] * 100
                    if self.stats['total_processed'] > 0 else 0
                ),
                'avg_processing_time': avg_time,
                'top_keywords': dict(
                    sorted(
                        self.stats['keyword_hits'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:10]
                ),
                'top_patterns': dict(
                    sorted(
                        self.stats['pattern_hits'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:10]
                ),
                'cache_size': len(self._cache) if self.enable_caching else 0,
                'ml_enabled': self.enable_ml,
                'threshold': self.confidence_threshold,
            }
    
    def update_threshold(self, new_threshold: float):
        """
        Update confidence threshold.
        
        Args:
            new_threshold: New threshold value
        """
        if 0 <= new_threshold <= 100:
            self.confidence_threshold = new_threshold
            logger.info(f"Threshold updated to {new_threshold}%")
        else:
            raise ValueError("Threshold must be between 0 and 100")
    
    def clear_cache(self):
        """Clear detection cache."""
        if self.enable_caching:
            with self._cache_lock:
                self._cache.clear()
            logger.info("Cache cleared")
    
    def shutdown(self):
        """Shutdown detector and cleanup resources."""
        self.executor.shutdown(wait=True)
        self.clear_cache()
        logger.info("Detector shutdown complete")


# Testing function
def test_advanced_detector():
    """Test advanced detection features."""
    detector = AdvancedSpamDetector(
        confidence_threshold=40,
        enable_ml=False,  # ML disabled for testing
        enable_caching=True
    )
    
    test_cases = [
        "SLOT GACOR MAXWIN 1000X JACKPOT BESAR!!!",
        "Togel online terpercaya WA: 0812-3456-7890",
        "Great video, thanks for sharing!",
        "DAFTAR SEKARANG BONUS 100% DEPOSIT PULSA",
        "Can you make more content like this?",
    ]
    
    print("=" * 80)
    print("ADVANCED SPAM DETECTOR TEST")
    print("=" * 80)
    
    for text in test_cases:
        result = detector.detect_advanced(text, author="TestUser")
        
        print(f"\nText: {text[:50]}...")
        print(f"Is Spam: {result.is_spam}")
        print(f"Confidence: {result.confidence:.1f}%")
        print(f"Risk Level: {result.risk_level}")
        print(f"Method: {result.detection_method}")
        print(f"Processing Time: {result.processing_time:.4f}s")
        print(f"Keywords: {result.detected_keywords}")
        print(f"Patterns: {result.detected_patterns}")
        print(f"Categories: {result.threat_categories}")
        print("-" * 80)
    
    # Show statistics
    stats = detector.get_statistics()
    print("\nSTATISTICS:")
    print(json.dumps(stats, indent=2))
    
    # Cleanup
    detector.shutdown()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_advanced_detector()
