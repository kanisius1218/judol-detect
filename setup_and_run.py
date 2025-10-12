"""
Complete Setup and Run Script for Spam Detection System
Includes data cleaning, model training, and application launch
"""

import os
import sys
import subprocess
import time
from pathlib import Path
import pandas as pd

def install_requirements():
    """Install Python requirements"""
    print("📦 Installing Python requirements...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✅ Requirements installed\n")

def setup_directories():
    """Create necessary directories"""
    print("📁 Setting up directories...")
    directories = [
        "data",
        "ml_models",
        "reports",
        "logs",
        "config"
    ]
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
    print("✅ Directories created\n")

def clean_and_prepare_data():
    """Run data cleaning pipeline"""
    print("🧹 Cleaning and preparing dataset...")
    try:
        from data_cleaning_pipeline import process_and_save_dataset
        
        # Process dataset
        input_file = "data/spam_dataset.csv"
        output_file = "data/enhanced_spam_dataset.csv"
        
        # Create sample dataset if doesn't exist
        if not Path(input_file).exists():
            print("Creating sample dataset...")
            sample_data = pd.DataFrame({
                'text': [
                    'SLOT GACOR MAXWIN DAFTAR SEKARANG',
                    'Video nya bagus sekali, terima kasih',
                    'JOIN GRUP TELEGRAM GRATIS CUAN 100%',
                    'Kapan upload video lagi min?',
                    'WA.ME/628123456789 BONUS DEPOSIT 100%',
                    'Mantap penjelasannya, jadi paham',
                ],
                'label': ['spam', 'ham', 'spam', 'ham', 'spam', 'ham']
            })
            sample_data.to_csv(input_file, index=False)
        
        df = process_and_save_dataset(input_file, output_file)
        print(f"✅ Dataset prepared: {len(df)} samples\n")
        return True
    except Exception as e:
        print(f"⚠️ Error preparing data: {e}\n")
        return False

def train_model():
    """Train the spam detection model"""
    print("🤖 Training spam detection model...")
    try:
        # Import and run training
        from train_advanced_model import main as train_main
        train_main()
        print("✅ Model trained successfully\n")
        return True
    except Exception as e:
        print(f"⚠️ Error training model: {e}")
        print("Using pre-trained model if available\n")
        return False

def setup_youtube_auth():
    """Setup YouTube API authentication"""
    print("🔐 Setting up YouTube API...")
    
    client_secret_path = Path("client_secret.json")
    example_path = Path("client_secret.json.example")
    
    if not client_secret_path.exists() and example_path.exists():
        print("📋 To use YouTube features:")
        print("1. Go to https://console.cloud.google.com")
        print("2. Create a new project or select existing")
        print("3. Enable YouTube Data API v3")
        print("4. Create OAuth 2.0 credentials")
        print("5. Download and save as 'client_secret.json'\n")
        
        use_youtube = input("Do you have YouTube API credentials? (y/n): ")
        if use_youtube.lower() == 'y':
            print("Please place your client_secret.json in the project root\n")
            input("Press Enter when ready...")
    
    return client_secret_path.exists()

def start_backend():
    """Start Flask backend server"""
    print("🚀 Starting backend server...")
    backend_process = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)  # Wait for server to start
    print("✅ Backend running on http://localhost:5000\n")
    return backend_process

def start_frontend():
    """Start React frontend"""
    print("🎨 Starting frontend...")
    frontend_dir = Path("frontend")
    
    if frontend_dir.exists():
        # Check if node_modules exists
        if not (frontend_dir / "node_modules").exists():
            print("Installing frontend dependencies...")
            subprocess.run(["npm", "install"], cwd=frontend_dir, shell=True)
        
        # Start frontend
        frontend_process = subprocess.Popen(
            ["npm", "start"],
            cwd=frontend_dir,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("✅ Frontend running on http://localhost:3000\n")
        return frontend_process
    else:
        print("⚠️ Frontend directory not found\n")
        return None

def run_youtube_cleaner():
    """Run YouTube spam cleaner"""
    print("🎥 Starting YouTube Spam Cleaner...")
    subprocess.run([sys.executable, "youtube_spam_cleaner.py"])

def main_menu():
    """Main menu for the application"""
    print("\n" + "="*50)
    print("🎯 SPAM DETECTION SYSTEM")
    print("="*50)
    
    processes = []
    
    while True:
        print("\n📋 Main Menu:")
        print("1. Complete Setup (First Time)")
        print("2. Start Web Application")
        print("3. Run YouTube Cleaner")
        print("4. Train New Model")
        print("5. Clean Dataset")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ")
        
        if choice == '1':
            print("\n🔧 Running Complete Setup...")
            install_requirements()
            setup_directories()
            clean_and_prepare_data()
            train_model()
            setup_youtube_auth()
            print("✅ Setup complete!")
            
        elif choice == '2':
            print("\n🌐 Starting Web Application...")
            backend = start_backend()
            processes.append(backend)
            
            frontend = start_frontend()
            if frontend:
                processes.append(frontend)
            
            print("\n✅ Application is running!")
            print("📍 Backend: http://localhost:5000")
            print("📍 Frontend: http://localhost:3000")
            print("\nPress Ctrl+C to stop servers")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n⏹️ Stopping servers...")
                for p in processes:
                    p.terminate()
                processes = []
                
        elif choice == '3':
            if setup_youtube_auth():
                run_youtube_cleaner()
            else:
                print("⚠️ YouTube API credentials not found")
                
        elif choice == '4':
            clean_and_prepare_data()
            train_model()
            
        elif choice == '5':
            clean_and_prepare_data()
            
        elif choice == '6':
            print("\n👋 Goodbye!")
            for p in processes:
                p.terminate()
            break
            
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Application terminated")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
