# 🤖 Multi-Platform Spam Moderator

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production--Ready-success.svg)]()
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/yourusername/judol-delet-msg/graphs/commit-activity)

Bot otomatis untuk mendeteksi dan menghapus spam komentar judi online di **YouTube** dan **Instagram**.

## ✨ Features

- 🔍 **AI-Powered Detection** - 50+ keywords, typo detection, pattern recognition
- 🗑️ **Auto-Delete Spam** - Otomatis hapus spam comments
- 📊 **Advanced Analytics** - Comprehensive reporting dan insights
- 🎯 **Multi-Platform** - YouTube & Instagram support
- ⏰ **Scheduled Moderation** - Automated checking dengan configurable interval
- 💾 **Database Logging** - Track semua spam yang terdeteksi
- ✅ **Whitelist System** - Trusted users tidak kena deteksi
- 🧪 **Dry Run Mode** - Test tanpa delete

## 📁 Project Structure

```
judol-delet-msg/
├── src/                    # Source code
│   ├── core_detector.py    # Detection engine
│   ├── database.py         # Database manager
│   ├── youtube_adapter.py  # YouTube integration
│   ├── instagram_adapter.py # Instagram integration
│   ├── analytics.py        # Analytics engine
│   └── main.py            # Main orchestrator
├── docs/                   # Documentation
│   ├── README.md          # Full documentation
│   ├── QUICKSTART.md      # Quick start guide
│   ├── CARA_MENCOBA.md    # Testing guide (ID)
│   ├── RINGKASAN.md       # Summary (ID)
│   ├── IMPROVEMENTS.md    # New features
│   └── PROJECT_SUMMARY.md # Technical overview
├── config/                 # Configuration
│   └── config.example.env # Config template
├── tests/                  # Tests
│   └── test_all.py        # Test suite
├── scripts/                # Utility scripts
│   └── TEST_BOT.bat       # Windows test script
├── reports/                # Generated reports
├── logs/                   # Log files
├── requirements.txt        # Dependencies
└── .gitignore             # Git ignore rules
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy config template
copy config\config.example.env .env

# Edit with your API keys
notepad .env
```

### 3. Test

```bash
# Run test suite
python tests\test_all.py

# Or use batch script (Windows)
scripts\TEST_BOT.bat
```

### 4. Run

```bash
# Interactive menu
python src\main.py

# Run once
python src\main.py --once

# Scheduled mode
python src\main.py --scheduled
```

## 📊 Platform Status

| Platform | Status | Documentation |
|----------|--------|---------------|
| **YouTube** | ✅ Production-Ready | [Setup Guide](docs/README.md#youtube-api-setup) |
| **Instagram** | ✅ Production-Ready | [Setup Guide](docs/README.md#instagram-api-setup) |
| **TikTok** | ❌ Not Recommended | No official API |

## 📚 Documentation

- **[Full Documentation](docs/README.md)** - Complete guide dengan API setup
- **[Quick Start](docs/QUICKSTART.md)** - Setup dalam 10 menit
- **[Testing Guide](docs/CARA_MENCOBA.md)** - Cara test bot (Bahasa Indonesia)
- **[Improvements](docs/IMPROVEMENTS.md)** - New features dan enhancements
- **[Project Summary](docs/PROJECT_SUMMARY.md)** - Technical overview

## 🎯 Usage Examples

### Run Interactive Menu

```bash
python src\main.py
```

Menu options:
1. Run moderation once
2. Run scheduled moderation
3. View statistics
4. Test detection
5. Configuration
6. Exit

### Generate Reports

```bash
# Daily report
python src\analytics.py --daily --output reports\daily_report

# Weekly report
python src\analytics.py --weekly --output reports\weekly_report
```

### View Statistics

```bash
# Last 7 days
python src\main.py --stats --days 7

# Last 30 days
python src\main.py --stats --days 30
```

## ⚙️ Configuration

Edit `.env` file:

```env
# General
CONFIDENCE_THRESHOLD=40
DRY_RUN=false
CHECK_INTERVAL_MINUTES=5

# YouTube
YOUTUBE_ENABLED=true
YOUTUBE_API_KEY=your_api_key_here
YOUTUBE_CHANNEL_ID=your_channel_id_here

# Instagram
INSTAGRAM_ENABLED=true
INSTAGRAM_ACCESS_TOKEN=your_token_here
INSTAGRAM_USER_ID=your_user_id_here
```

## 🔍 Detection System

### Confidence Scoring

- **Keyword Match**: +20-40 points
- **URL/Link**: +15 points
- **Phone Number**: +15 points
- **Spam Emoji**: +10 points
- **Pattern Recognition**: +5-10 points

**Threshold**: Confidence ≥ 40% = SPAM

### Keywords

50+ keywords including:
- Main: slot, togel, casino, betting, judol
- Slot: gacor, maxwin, jackpot, scatter
- Togel: togel online, angka jitu, prediksi
- Transaction: deposit, withdraw, bonus

## 📈 Analytics

### Available Reports

- **Daily Report**: Summary untuk hari ini
- **Weekly Report**: Comprehensive 7-day analysis
- **Trend Analysis**: Spam trends over time
- **Top Spammers**: Most active spammers
- **Keyword Frequency**: Most detected keywords
- **Hourly Patterns**: Spam activity by hour

### Export Formats

- JSON (machine-readable)
- Text (human-readable)

## 🐛 Troubleshooting

### Common Issues

**"Module not found"**
```bash
pip install -r requirements.txt
```

**"API key invalid"**
- Check API key di console
- Verify API is enabled
- Check key restrictions

**"Permission denied"**
- Ensure bot has admin permissions
- Check API scopes

See [Full Documentation](docs/README.md#troubleshooting) for more.

## 📊 Project Statistics

- **Total Code**: 5000+ lines
- **Documentation**: 2500+ lines  
- **Files**: 25+ files
- **Platforms**: 2 (YouTube, Instagram)
- **Detection Methods**: 10+
- **Keywords**: 50+
- **Test Coverage**: Comprehensive
- **Languages**: Python 3.8+

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Make changes
4. Submit pull request

## 📄 License

MIT License - Free to use and modify

## 🎓 Credits

Developed for safer social media communities.

## 📞 Support

- **Issues**: Check [Troubleshooting](docs/README.md#troubleshooting)
- **Documentation**: See [docs/](docs/) folder
- **Examples**: See [docs/CARA_MENCOBA.md](docs/CARA_MENCOBA.md)

---

**Version**: 2.0.0  
**Status**: ✅ Production-Ready  
**Last Updated**: 2025-10-07

**Made with ❤️ for safer communities**
