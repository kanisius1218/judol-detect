"""
Advanced Data Cleaning Pipeline for Spam Detection
Handles Indonesian text, slang, and social media content
"""

import re
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import string
from collections import Counter
import unicodedata
import json
from pathlib import Path

class IndonesianTextCleaner:
    """Advanced text cleaning for Indonesian spam/judol detection"""
    
    def __init__(self):
        # Common Indonesian slang and abbreviations
        self.slang_dict = {
            'yg': 'yang', 'dgn': 'dengan', 'utk': 'untuk', 'dr': 'dari',
            'krn': 'karena', 'sdh': 'sudah', 'blm': 'belum', 'jg': 'juga',
            'tdk': 'tidak', 'gak': 'tidak', 'ga': 'tidak', 'gk': 'tidak',
            'bgt': 'banget', 'bngt': 'banget', 'byk': 'banyak', 'org': 'orang',
            'lg': 'lagi', 'udh': 'sudah', 'ud': 'sudah', 'emg': 'memang',
            'gmn': 'gimana', 'gimana': 'bagaimana', 'knp': 'kenapa',
            'mksh': 'makasih', 'tq': 'terima kasih', 'thx': 'terima kasih',
            'min': 'admin', 'gan': 'juragan', 'bro': 'brother', 'sis': 'sister'
        }
        
        # Spam/judol keywords (gambling, adult content, scams)
        self.spam_keywords = [
            # Gambling
            'slot', 'togel', 'poker', 'casino', 'jackpot', 'maxwin', 'gacor',
            'scatter', 'bonus', 'deposit', 'withdraw', 'wd', 'jp', 'jepe',
            'bandar', 'agen', 'situs', 'daftar', 'register', 'promo',
            # Adult content
            'bokep', 'porn', 'sex', 'nude', 'hot', 'sexy', 'panas', 'bugil',
            'telanjang', 'ml', 'vcs', 'open bo', 'bo', 'jablay',
            # Scams
            'cuan', 'profit', 'income', 'passive', 'investasi', 'trading',
            'forex', 'binary', 'crypto', 'bitcoin', 'nft', 'airdrop',
            # URLs and contacts
            'wa.me', 'bit.ly', 't.me', 'telegram', 'whatsapp', 'line',
            'klik', 'link', 'join', 'grup', 'group', 'channel'
        ]
        
        # Suspicious patterns
        self.suspicious_patterns = [
            r'\b\d{10,}\b',  # Long numbers (phone numbers)
            r'[A-Za-z0-9]+\.[A-Za-z]{2,}',  # URLs
            r'@[A-Za-z0-9_]+',  # Mentions
            r'#[A-Za-z0-9_]+',  # Hashtags
            r'[Rr][Pp]\s*\d+',  # Money amounts (Rp)
            r'\d+[kK]',  # Abbreviated thousands
            r'[0-9]{1,3}[,.][0-9]{3}',  # Formatted numbers
        ]
        
    def clean_text(self, text: str) -> str:
        """Complete text cleaning pipeline"""
        if pd.isna(text):
            return ""
            
        text = str(text).lower()
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove phone numbers
        text = re.sub(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,5}[-\s\.]?[0-9]{1,5}', '', text)
        
        # Remove emojis
        text = self.remove_emojis(text)
        
        # Replace slang
        for slang, formal in self.slang_dict.items():
            text = re.sub(r'\b' + slang + r'\b', formal, text)
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove single characters
        text = ' '.join([word for word in text.split() if len(word) > 1])
        
        return text
    
    def remove_emojis(self, text: str) -> str:
        """Remove emojis and emoticons"""
        # Remove emojis
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text)
    
    def extract_features(self, text: str) -> Dict[str, float]:
        """Extract features for spam detection"""
        features = {}
        
        # Basic features
        features['char_count'] = len(text)
        features['word_count'] = len(text.split())
        features['uppercase_ratio'] = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        features['digit_ratio'] = sum(1 for c in text if c.isdigit()) / max(len(text), 1)
        features['special_char_ratio'] = sum(1 for c in text if c in string.punctuation) / max(len(text), 1)
        
        # Spam keyword features
        text_lower = text.lower()
        features['spam_keyword_count'] = sum(1 for keyword in self.spam_keywords if keyword in text_lower)
        features['spam_keyword_ratio'] = features['spam_keyword_count'] / max(features['word_count'], 1)
        
        # Pattern features
        features['has_url'] = 1 if re.search(r'http[s]?://|www\.', text) else 0
        features['has_email'] = 1 if re.search(r'\S+@\S+', text) else 0
        features['has_phone'] = 1 if re.search(r'\b\d{10,}\b', text) else 0
        features['has_money'] = 1 if re.search(r'[Rr][Pp]\s*\d+', text) else 0
        
        # Repetition features
        words = text.split()
        if words:
            word_freq = Counter(words)
            features['max_word_freq'] = max(word_freq.values())
            features['unique_word_ratio'] = len(set(words)) / len(words)
        else:
            features['max_word_freq'] = 0
            features['unique_word_ratio'] = 0
        
        # Suspicious pattern count
        features['suspicious_pattern_count'] = sum(
            1 for pattern in self.suspicious_patterns 
            if re.search(pattern, text)
        )
        
        return features
    
    def is_likely_spam(self, text: str, threshold: float = 0.6) -> Tuple[bool, float]:
        """Quick spam detection based on heuristics"""
        features = self.extract_features(text)
        
        # Calculate spam score
        spam_score = 0.0
        
        # High weight factors
        if features['spam_keyword_ratio'] > 0.1:
            spam_score += 0.4
        if features['has_url']:
            spam_score += 0.2
        if features['has_phone']:
            spam_score += 0.15
        if features['suspicious_pattern_count'] > 2:
            spam_score += 0.25
        
        # Medium weight factors
        if features['uppercase_ratio'] > 0.3:
            spam_score += 0.1
        if features['digit_ratio'] > 0.2:
            spam_score += 0.1
        if features['unique_word_ratio'] < 0.5:
            spam_score += 0.1
        
        return spam_score > threshold, spam_score


class DatasetEnhancer:
    """Enhance and expand dataset for better training"""
    
    def __init__(self):
        self.cleaner = IndonesianTextCleaner()
        
    def augment_text(self, text: str, label: str) -> List[str]:
        """Generate variations of text for data augmentation"""
        variations = [text]
        
        if label == 'spam':
            # Add variations with different spam patterns
            variations.append(text.upper())  # All caps version
            variations.append(f"PROMO!!! {text}")
            variations.append(f"{text} 💰💰💰")
            variations.append(f"⚠️ {text} ⚠️")
            
            # Add URL variations
            if 'link' not in text.lower():
                variations.append(f"{text} klik link di bio")
            
            # Add contact variations
            if 'wa' not in text.lower() and 'whatsapp' not in text.lower():
                variations.append(f"{text} hub WA 08123456789")
        
        else:  # ham
            # Add normal conversation variations
            variations.append(f"Menurut saya, {text}")
            variations.append(f"{text}. Terima kasih")
            variations.append(f"Bagus sekali! {text}")
        
        return variations
    
    def balance_dataset(self, df: pd.DataFrame, text_col: str = 'text', label_col: str = 'label') -> pd.DataFrame:
        """Balance dataset by oversampling minority class"""
        spam_df = df[df[label_col] == 'spam']
        ham_df = df[df[label_col] == 'ham']
        
        # Determine minority and majority classes
        if len(spam_df) < len(ham_df):
            minority_df = spam_df
            majority_df = ham_df
            minority_label = 'spam'
        else:
            minority_df = ham_df
            majority_df = spam_df
            minority_label = 'ham'
        
        # Augment minority class
        augmented_texts = []
        augmented_labels = []
        
        for _, row in minority_df.iterrows():
            variations = self.augment_text(row[text_col], minority_label)
            augmented_texts.extend(variations)
            augmented_labels.extend([minority_label] * len(variations))
        
        # Create augmented dataframe
        augmented_df = pd.DataFrame({
            text_col: augmented_texts,
            label_col: augmented_labels
        })
        
        # Combine with majority class
        balanced_df = pd.concat([majority_df, augmented_df], ignore_index=True)
        
        return balanced_df.sample(frac=1).reset_index(drop=True)  # Shuffle
    
    def clean_dataset(self, df: pd.DataFrame, text_col: str = 'text') -> pd.DataFrame:
        """Clean entire dataset"""
        print(f"Cleaning {len(df)} samples...")
        
        # Remove duplicates
        df = df.drop_duplicates(subset=[text_col])
        
        # Clean text
        df['cleaned_text'] = df[text_col].apply(self.cleaner.clean_text)
        
        # Remove empty texts
        df = df[df['cleaned_text'].str.len() > 0]
        
        # Extract features
        feature_dicts = df['cleaned_text'].apply(self.cleaner.extract_features).tolist()
        feature_df = pd.DataFrame(feature_dicts)
        
        # Combine with original dataframe
        df = pd.concat([df, feature_df], axis=1)
        
        print(f"Cleaned dataset: {len(df)} samples remaining")
        
        return df
    
    def generate_synthetic_spam(self, count: int = 1000) -> List[Dict[str, str]]:
        """Generate synthetic spam messages for training"""
        templates = [
            "SLOT GACOR {keyword} MAXWIN {number}X DAFTAR SEKARANG {url}",
            "Promo {keyword} bonus {number}% untuk member baru {contact}",
            "Investasi {keyword} profit {number}% per hari GUARANTEED",
            "{keyword} TERPERCAYA sejak {year} WD BERAPAPUN DIBAYAR",
            "Join grup {keyword} GRATIS {url} dapatkan {number}jt",
            "BUKTI WD {number} JUTA dari {keyword} cek {url}",
            "{keyword} {keyword2} SCATTER NAGA HITAM JP {number}M",
            "Butuh {keyword}? Hub {contact} fast respon 24jam",
        ]
        
        keywords = ['slot', 'togel', 'casino', 'forex', 'crypto', 'bitcoin', 'trading']
        keywords2 = ['gacor', 'maxwin', 'jackpot', 'profit', 'cuan', 'untung']
        
        synthetic_data = []
        
        for _ in range(count):
            template = np.random.choice(templates)
            message = template.format(
                keyword=np.random.choice(keywords),
                keyword2=np.random.choice(keywords2),
                number=np.random.randint(10, 999),
                year=np.random.randint(2015, 2024),
                url=f"bit.ly/{np.random.randint(1000, 9999)}",
                contact=f"wa.me/62{np.random.randint(8000000000, 8999999999)}"
            )
            
            synthetic_data.append({
                'text': message,
                'label': 'spam'
            })
        
        return synthetic_data
    
    def generate_synthetic_ham(self, count: int = 1000) -> List[Dict[str, str]]:
        """Generate synthetic normal messages"""
        templates = [
            "Video nya bagus sekali, terima kasih sudah berbagi",
            "Saya setuju dengan pendapat anda tentang {topic}",
            "Kapan upload video {topic} lagi min?",
            "Mantap penjelasannya, jadi paham tentang {topic}",
            "Request dong bahas tentang {topic} lebih detail",
            "Keren banget {topic} nya, sukses terus channel nya",
            "Terima kasih ilmunya tentang {topic}, sangat bermanfaat",
            "Saya sudah coba {topic} dan hasilnya memuaskan",
        ]
        
        topics = ['tutorial', 'review', 'tips', 'cara', 'panduan', 'belajar', 'masakan']
        
        synthetic_data = []
        
        for _ in range(count):
            template = np.random.choice(templates)
            message = template.format(
                topic=np.random.choice(topics)
            )
            
            synthetic_data.append({
                'text': message,
                'label': 'ham'
            })
        
        return synthetic_data


def process_and_save_dataset(input_file: str, output_file: str):
    """Main function to process and enhance dataset"""
    
    enhancer = DatasetEnhancer()
    
    # Load existing dataset
    if Path(input_file).exists():
        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} samples from {input_file}")
    else:
        print("Creating new dataset...")
        df = pd.DataFrame(columns=['text', 'label'])
    
    # Generate synthetic data
    print("Generating synthetic data...")
    synthetic_spam = enhancer.generate_synthetic_spam(2000)
    synthetic_ham = enhancer.generate_synthetic_ham(2000)
    
    synthetic_df = pd.DataFrame(synthetic_spam + synthetic_ham)
    
    # Combine datasets
    df = pd.concat([df, synthetic_df], ignore_index=True)
    
    # Clean dataset
    df = enhancer.clean_dataset(df)
    
    # Balance dataset
    df = enhancer.balance_dataset(df)
    
    # Add metadata
    df['source'] = df.apply(
        lambda x: 'synthetic' if x.name >= len(df) - len(synthetic_df) else 'original',
        axis=1
    )
    
    # Save enhanced dataset
    df.to_csv(output_file, index=False)
    print(f"Saved enhanced dataset to {output_file}")
    
    # Print statistics
    print("\nDataset Statistics:")
    print(f"Total samples: {len(df)}")
    print(f"Spam samples: {len(df[df['label'] == 'spam'])}")
    print(f"Ham samples: {len(df[df['label'] == 'ham'])}")
    print(f"Average text length: {df['cleaned_text'].str.len().mean():.2f}")
    print(f"Features extracted: {len([col for col in df.columns if col not in ['text', 'label', 'cleaned_text', 'source']])}")
    
    return df


if __name__ == "__main__":
    # Process dataset
    input_file = "data/spam_dataset.csv"
    output_file = "data/enhanced_spam_dataset.csv"
    
    df = process_and_save_dataset(input_file, output_file)
    
    # Save sample for inspection
    df.head(20).to_csv("data/dataset_sample.csv", index=False)
    print("\nSample saved to data/dataset_sample.csv")
