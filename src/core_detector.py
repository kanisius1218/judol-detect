#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Detection Engine - Platform Agnostic
Deteksi spam judi online untuk semua platform (YouTube, TikTok, Instagram)
"""

import re
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """Result dari spam detection."""
    is_spam: bool
    confidence: int  # 0-100
    detected_keywords: List[str]
    detected_patterns: List[str]
    reason: str
    score: int


class SpamDetector:
    """
    Core spam detection engine yang platform-agnostic.
    
    Mendeteksi spam judi online dengan:
    - Keyword matching (50+ keywords)
    - Typo variants detection
    - Pattern recognition (URL, phone, emoji, dll)
    - Text normalization
    - Confidence scoring system
    """
    
    # ========================================================================
    # KEYWORDS DATABASE
    # ========================================================================
    
    # Keywords utama judi online
    MAIN_KEYWORDS = [
        'slot', 'togel', 'casino', 'betting', 'judol', 'judi online',
        'judi', 'taruhan', 'bandar', 'gambling', 'bet'
    ]
    
    # Keywords spesifik slot
    SLOT_KEYWORDS = [
        'gacor', 'maxwin', 'jackpot', 'jp', 'scatter', 'freespin', 'free spin',
        'rtp', 'slot gacor', 'pragmatic', 'pg soft', 'pgsoft', 'habanero',
        'spadegaming', 'joker123', 'slot online', 'wild symbol', 'bonus round',
        'multiplier', 'gates of olympus', 'starlight princess', 'sweet bonanza'
    ]
    
    # Keywords togel
    TOGEL_KEYWORDS = [
        'togel online', 'pasaran', 'hongkong', 'singapore', 'sidney', 'sydney',
        'keluaran', 'angka jitu', 'prediksi togel', 'togel hari ini', 'hk', 'sgp',
        'sdy', 'result', 'prize', '4d', '3d', '2d', 'bocoran', 'rumus', 'shio',
        'colok bebas', 'colok jitu', 'kepala ekor'
    ]
    
    # Keywords transaksi
    TRANSACTION_KEYWORDS = [
        'deposit', 'withdraw', 'wd', 'depo', 'minimal deposit', 'min deposit',
        'bonus', 'promo', 'daftar sekarang', 'klaim bonus', 'bonus new member',
        'cashback', 'rebate', 'turnover', 'rollingan', 'register now',
        'sign up', 'join now', 'claim bonus'
    ]
    
    # Nama platform populer
    PLATFORM_NAMES = [
        'olxtoto', 'rajabandot', 'kingslot', 'sultantoto', 'dewatogel',
        'nagaslot', 'garuda slot', 'zeus slot', 'olympus', 'rajatoto',
        'bandartoto', 'totomacau', 'macau', 'ligaslot', 'ligaciputra'
    ]
    
    # ========================================================================
    # TYPO VARIANTS MAPPING
    # ========================================================================
    
    TYPO_MAP = {
        '0': 'o',
        '1': 'i',
        '3': 'e',
        '4': 'a',
        '5': 's',
        '7': 't',
        '8': 'b',
        'ο': 'o',  # Greek omicron
        'о': 'o',  # Cyrillic o
        'а': 'a',  # Cyrillic a
        'е': 'e',  # Cyrillic e
        'і': 'i',  # Cyrillic i
        'ѕ': 's',  # Cyrillic s
        'ᴏ': 'o',  # Small capital o
        'ɑ': 'a',  # Latin alpha
        'ɡ': 'g',  # Latin g
        'ı': 'i',  # Dotless i
        'ⅼ': 'l',  # Roman numeral l
    }
    
    # ========================================================================
    # SPAM INDICATORS
    # ========================================================================
    
    # Spam emoji yang sering dipakai
    SPAM_EMOJIS = [
        '🎰', '💰', '🔥', '💎', '🎲', '🏆', '⚡', '💸', '🤑', 
        '💵', '💴', '💶', '💷', '🎁', '🎉', '💯', '🎊', '🌟'
    ]
    
    # ========================================================================
    # CONFIGURATION
    # ========================================================================
    
    def __init__(self, confidence_threshold: int = 40):
        """
        Initialize spam detector.
        
        Args:
            confidence_threshold: Minimum confidence untuk dianggap spam (0-100)
        """
        self.confidence_threshold = confidence_threshold
        
        # Compile regex patterns untuk performa
        self._compile_patterns()
        
        logger.info(f"SpamDetector initialized with threshold: {confidence_threshold}%")
    
    def _compile_patterns(self) -> None:
        """Compile semua regex patterns untuk performa."""
        
        # URL patterns
        self.url_pattern = re.compile(
            r'(?:http[s]?://|www\.|bit\.ly|tinyurl\.com|t\.co|goo\.gl|'
            r'ow\.ly|short\.link|cutt\.ly|tiny\.cc|is\.gd|rb\.gy)',
            re.IGNORECASE
        )
        
        # Phone patterns (Indonesia & international)
        self.phone_pattern = re.compile(
            r'(?:\+62|62|08|\+60|60|01)\s*\d[\s\d\-\(\)]{7,}',
            re.IGNORECASE
        )
        
        # Telegram patterns
        self.telegram_pattern = re.compile(
            r'(?:t\.me/|@\w+|telegram\.me/)',
            re.IGNORECASE
        )
        
        # WhatsApp patterns
        self.whatsapp_pattern = re.compile(
            r'(?:wa\.me/|whatsapp|wa\s)',
            re.IGNORECASE
        )
        
        # Email patterns
        self.email_pattern = re.compile(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            re.IGNORECASE
        )
        
        # Repeated characters (3+)
        self.repeated_chars_pattern = re.compile(r'(.)\1{2,}')
        
        # Suspicious spacing (S L O T)
        self.spacing_pattern = re.compile(r'(?:[a-z]\s){3,}', re.IGNORECASE)
    
    # ========================================================================
    # TEXT NORMALIZATION
    # ========================================================================
    
    def normalize_text(self, text: str) -> str:
        """
        Normalisasi text untuk deteksi yang lebih akurat.
        
        Args:
            text: Text yang akan dinormalisasi
            
        Returns:
            str: Text yang sudah dinormalisasi
        """
        if not text:
            return ""
        
        # Lowercase
        text = text.lower()
        
        # Remove zero-width characters
        text = re.sub(r'[\u200b-\u200f\u202a-\u202e\ufeff]', '', text)
        
        # Replace lookalike characters
        for fake_char, real_char in self.TYPO_MAP.items():
            text = text.replace(fake_char, real_char)
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        return text
    
    # ========================================================================
    # MAIN DETECTION METHOD
    # ========================================================================
    
    def detect(self, text: str, author: Optional[str] = None) -> DetectionResult:
        """
        Deteksi apakah text adalah spam judi online.
        
        Args:
            text: Text yang akan dideteksi (comment/message)
            author: Username/nama author (optional, untuk logging)
            
        Returns:
            DetectionResult: Object berisi hasil deteksi
        """
        if not text or len(text.strip()) == 0:
            return DetectionResult(
                is_spam=False,
                confidence=0,
                detected_keywords=[],
                detected_patterns=[],
                reason='Empty text',
                score=0
            )
        
        # Normalize text
        normalized_text = self.normalize_text(text)
        
        # Initialize scoring
        score = 0
        detected_keywords = []
        detected_patterns = []
        reasons = []
        
        # ====================================================================
        # 1. KEYWORD MATCHING
        # ====================================================================
        
        all_keywords = (
            self.MAIN_KEYWORDS +
            self.SLOT_KEYWORDS +
            self.TOGEL_KEYWORDS +
            self.TRANSACTION_KEYWORDS +
            self.PLATFORM_NAMES
        )
        
        keyword_matches = []
        for keyword in all_keywords:
            if keyword.lower() in normalized_text:
                keyword_matches.append(keyword)
        
        # Score berdasarkan jumlah keyword
        if len(keyword_matches) >= 3:
            score += 40  # Multiple keywords = very suspicious
            reasons.append(f'{len(keyword_matches)} keywords matched')
        elif len(keyword_matches) == 2:
            score += 30
            reasons.append('2 keywords matched')
        elif len(keyword_matches) == 1:
            score += 20
            reasons.append('1 keyword matched')
        
        detected_keywords.extend(keyword_matches[:5])  # Limit to 5 for display
        
        # ====================================================================
        # 2. PATTERN RECOGNITION
        # ====================================================================
        
        # URL Detection (+15 points)
        if self.url_pattern.search(text):
            score += 15
            detected_patterns.append('URL')
            reasons.append('contains URL')
        
        # Phone Number Detection (+15 points)
        if self.phone_pattern.search(text):
            score += 15
            detected_patterns.append('phone')
            reasons.append('contains phone number')
        
        # Telegram Link Detection (+15 points)
        if self.telegram_pattern.search(text):
            score += 15
            detected_patterns.append('telegram')
            reasons.append('contains Telegram link')
        
        # WhatsApp Detection (+10 points)
        if self.whatsapp_pattern.search(text):
            score += 10
            detected_patterns.append('whatsapp')
            reasons.append('contains WhatsApp')
        
        # Email Detection (+10 points)
        if self.email_pattern.search(text):
            score += 10
            detected_patterns.append('email')
            reasons.append('contains email')
        
        # ====================================================================
        # 3. SPAM INDICATORS
        # ====================================================================
        
        # Spam Emoji Detection (+10 points if 3+)
        emoji_count = sum(text.count(emoji) for emoji in self.SPAM_EMOJIS)
        if emoji_count >= 3:
            score += 10
            detected_patterns.append('spam_emojis')
            reasons.append(f'excessive emojis ({emoji_count})')
        
        # Excessive Numbers (+10 points if 10+ digits)
        digit_count = sum(c.isdigit() for c in text)
        if digit_count >= 10:
            score += 10
            detected_patterns.append('excessive_numbers')
            reasons.append(f'excessive numbers ({digit_count})')
        
        # Aggressive Caps + Exclamation (+5 points)
        caps_count = sum(c.isupper() for c in text)
        exclamation_count = text.count('!')
        if len(text) > 0 and caps_count > len(text) * 0.5 and exclamation_count >= 2:
            score += 5
            detected_patterns.append('aggressive_caps')
            reasons.append('aggressive caps and exclamation')
        
        # Repeated Characters (+5 points)
        if self.repeated_chars_pattern.search(text):
            score += 5
            detected_patterns.append('repeated_chars')
            reasons.append('repeated characters')
        
        # Suspicious Spacing (+5 points)
        if self.spacing_pattern.search(text):
            score += 5
            detected_patterns.append('suspicious_spacing')
            reasons.append('suspicious spacing')
        
        # ====================================================================
        # 4. CALCULATE FINAL RESULT
        # ====================================================================
        
        # Calculate confidence percentage (cap at 100)
        confidence = min(score, 100)
        
        # Determine if spam based on threshold
        is_spam = confidence >= self.confidence_threshold
        
        # Build reason string
        reason_str = '; '.join(reasons) if reasons else 'No spam indicators'
        
        # Log detection
        if is_spam:
            logger.warning(
                f"SPAM DETECTED: confidence={confidence}%, "
                f"author={author}, keywords={detected_keywords}"
            )
        else:
            logger.debug(
                f"Not spam: confidence={confidence}%, author={author}"
            )
        
        return DetectionResult(
            is_spam=is_spam,
            confidence=confidence,
            detected_keywords=list(set(detected_keywords)),
            detected_patterns=list(set(detected_patterns)),
            reason=reason_str,
            score=score
        )
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def set_threshold(self, threshold: int) -> None:
        """
        Update confidence threshold.
        
        Args:
            threshold: New threshold value (0-100)
        """
        if 0 <= threshold <= 100:
            self.confidence_threshold = threshold
            logger.info(f"Threshold updated to {threshold}%")
        else:
            raise ValueError("Threshold must be between 0 and 100")
    
    def add_keywords(self, keywords: List[str], category: str = 'main') -> None:
        """
        Tambah keywords baru ke detector.
        
        Args:
            keywords: List keywords yang akan ditambahkan
            category: Kategori keywords (main, slot, togel, transaction, platform)
        """
        category_map = {
            'main': self.MAIN_KEYWORDS,
            'slot': self.SLOT_KEYWORDS,
            'togel': self.TOGEL_KEYWORDS,
            'transaction': self.TRANSACTION_KEYWORDS,
            'platform': self.PLATFORM_NAMES
        }
        
        if category in category_map:
            category_map[category].extend(keywords)
            logger.info(f"Added {len(keywords)} keywords to {category} category")
        else:
            raise ValueError(f"Invalid category: {category}")
    
    def get_stats(self) -> Dict:
        """
        Get detector statistics.
        
        Returns:
            Dict: Statistics tentang detector
        """
        return {
            'threshold': self.confidence_threshold,
            'total_keywords': (
                len(self.MAIN_KEYWORDS) +
                len(self.SLOT_KEYWORDS) +
                len(self.TOGEL_KEYWORDS) +
                len(self.TRANSACTION_KEYWORDS) +
                len(self.PLATFORM_NAMES)
            ),
            'categories': {
                'main': len(self.MAIN_KEYWORDS),
                'slot': len(self.SLOT_KEYWORDS),
                'togel': len(self.TOGEL_KEYWORDS),
                'transaction': len(self.TRANSACTION_KEYWORDS),
                'platform': len(self.PLATFORM_NAMES)
            }
        }


# ============================================================================
# TESTING FUNCTION
# ============================================================================

def test_detector():
    """Test function untuk detector."""
    detector = SpamDetector(confidence_threshold=40)
    
    test_cases = [
        "SLOT GACOR MAXWIN! Daftar di https://slotgacor.com 🎰💰🔥",
        "Togel online terpercaya! Minimal deposit 10rb. WA: 0812-3456-7890",
        "Halo guys, gimana kabarnya?",
        "Ada yang tau cara booking slot parkir?",
        "🎰🎰🎰 JACKPOT BESAR 💰💰💰 Daftar sekarang!"
    ]
    
    print("=" * 70)
    print("SPAM DETECTOR TEST")
    print("=" * 70)
    
    for i, text in enumerate(test_cases, 1):
        result = detector.detect(text)
        print(f"\nTest {i}:")
        print(f"Text: {text[:60]}...")
        print(f"Is Spam: {result.is_spam}")
        print(f"Confidence: {result.confidence}%")
        print(f"Keywords: {result.detected_keywords}")
        print(f"Patterns: {result.detected_patterns}")
        print("-" * 70)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run test
    test_detector()
