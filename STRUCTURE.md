# 📁 Project Structure

Professional folder organization untuk Multi-Platform Spam Moderator.

## 🗂️ Directory Structure

```
judol-delet-msg/
│
├── 📁 src/                         # Source code (Python modules)
│   ├── __init__.py                 # Package initialization
│   ├── core_detector.py            # Core detection engine (600+ lines)
│   ├── database.py                 # Database manager (500+ lines)
│   ├── youtube_adapter.py          # YouTube integration (400+ lines)
│   ├── instagram_adapter.py        # Instagram integration (400+ lines)
│   ├── analytics.py                # Analytics engine (500+ lines)
│   └── main.py                     # Main orchestrator (600+ lines)
│
├── 📁 docs/                        # Documentation
│   ├── README.md                   # Full documentation (500+ lines)
│   ├── QUICKSTART.md               # Quick start guide
│   ├── CARA_MENCOBA.md             # Testing guide (Bahasa Indonesia)
│   ├── RINGKASAN.md                # Summary (Bahasa Indonesia)
│   ├── IMPROVEMENTS.md             # New features documentation
│   └── PROJECT_SUMMARY.md          # Technical overview
│
├── 📁 config/                      # Configuration files
│   └── config.example.env          # Configuration template
│
├── 📁 tests/                       # Test files
│   └── test_all.py                 # Comprehensive test suite
│
├── 📁 scripts/                     # Utility scripts
│   ├── TEST_BOT.bat                # Test script (Windows)
│   ├── setup.bat                   # Setup script (Windows)
│   └── run.bat                     # Run script (Windows)
│
├── 📁 reports/                     # Generated reports (auto-created)
│   ├── daily_report_YYYY-MM-DD.json
│   ├── daily_report_YYYY-MM-DD.txt
│   ├── weekly_report_YYYY-MM-DD.json
│   └── weekly_report_YYYY-MM-DD.txt
│
├── 📁 logs/                        # Log files (auto-created)
│   └── spam_moderator.log
│
├── 📄 README.md                    # Main README (project overview)
├── 📄 requirements.txt             # Python dependencies
├── 📄 setup.py                     # Setup script for installation
├── 📄 .gitignore                   # Git ignore rules
├── 📄 .env                         # Your configuration (create from example)
└── 📄 STRUCTURE.md                 # This file
```

## 📦 Module Descriptions

### src/ - Source Code

#### core_detector.py
- **Purpose**: Platform-agnostic spam detection engine
- **Size**: 600+ lines
- **Key Classes**: `SpamDetector`, `DetectionResult`
- **Features**:
  - 50+ keywords detection
  - Typo variants detection
  - Pattern recognition (URL, phone, emoji)
  - Confidence scoring system
  - Text normalization

#### database.py
- **Purpose**: Database management dengan SQLite
- **Size**: 500+ lines
- **Key Classes**: `DatabaseManager`
- **Features**:
  - Multi-platform logging
  - Whitelist management
  - Statistics tracking
  - Export to CSV
  - Query optimization

#### youtube_adapter.py
- **Purpose**: YouTube platform integration
- **Size**: 400+ lines
- **Key Classes**: `YouTubeAdapter`
- **Features**:
  - YouTube Data API v3 integration
  - Get video/channel comments
  - Auto-delete spam comments
  - Rate limiting handling
  - Batch processing

#### instagram_adapter.py
- **Purpose**: Instagram platform integration
- **Size**: 400+ lines
- **Key Classes**: `InstagramAdapter`
- **Features**:
  - Facebook Graph API integration
  - Get media and comments
  - Auto-delete spam comments
  - Rate limiting (200 calls/hour)
  - Token verification

#### analytics.py
- **Purpose**: Advanced analytics and reporting
- **Size**: 500+ lines
- **Key Classes**: `AnalyticsEngine`
- **Features**:
  - Trend analysis
  - Top spammers tracking
  - Keyword frequency analysis
  - Hourly patterns
  - Report generation (JSON/text)

#### main.py
- **Purpose**: Main orchestrator and CLI
- **Size**: 600+ lines
- **Key Classes**: `SpamModeratorBot`
- **Features**:
  - Multi-platform management
  - Scheduled moderation
  - Interactive CLI menu
  - Configuration management
  - Statistics dashboard

### docs/ - Documentation

- **README.md**: Complete documentation dengan API setup guides
- **QUICKSTART.md**: Setup dalam 10 menit
- **CARA_MENCOBA.md**: Panduan testing lengkap (Bahasa Indonesia)
- **RINGKASAN.md**: Summary dan overview (Bahasa Indonesia)
- **IMPROVEMENTS.md**: New features dan enhancements
- **PROJECT_SUMMARY.md**: Technical overview dan architecture

### config/ - Configuration

- **config.example.env**: Template untuk configuration
  - General settings (threshold, dry run, interval)
  - YouTube configuration (API key, channel ID)
  - Instagram configuration (access token, user ID)
  - Database settings

### tests/ - Tests

- **test_all.py**: Comprehensive test suite
  - Core detector tests
  - Database tests
  - Module import tests
  - Configuration tests

### scripts/ - Utility Scripts

- **TEST_BOT.bat**: Quick test script (Windows)
- **setup.bat**: Setup dan install dependencies (Windows)
- **run.bat**: Run bot dengan menu (Windows)

### reports/ - Generated Reports

Auto-created folder untuk menyimpan reports:
- Daily reports (JSON dan text)
- Weekly reports (JSON dan text)
- Custom reports

### logs/ - Log Files

Auto-created folder untuk log files:
- `spam_moderator.log`: Main application log
- Rotating logs (jika dikonfigurasi)

## 🎯 File Purposes

### Root Files

| File | Purpose |
|------|---------|
| `README.md` | Main project overview dan quick start |
| `requirements.txt` | Python dependencies list |
| `setup.py` | Setup script untuk installation |
| `.gitignore` | Git ignore rules |
| `.env` | Your configuration (create dari config.example.env) |
| `STRUCTURE.md` | This file - project structure documentation |

## 📊 Statistics

- **Total Files**: 20+ files
- **Total Code**: 5000+ lines
- **Total Documentation**: 2000+ lines
- **Total Size**: ~200KB
- **Modules**: 6 main modules
- **Documentation Files**: 6 files
- **Test Files**: 1 comprehensive suite
- **Scripts**: 3 utility scripts

## 🚀 Usage Patterns

### Development

```bash
# Install in development mode
pip install -e .

# Run tests
python tests\test_all.py

# Run main bot
python src\main.py
```

### Production

```bash
# Setup
scripts\setup.bat

# Run
scripts\run.bat

# Or direct
python src\main.py --scheduled
```

### Testing

```bash
# Quick test
scripts\TEST_BOT.bat

# Full test
python tests\test_all.py

# Test detection
python src\main.py
# Select option 4 (Test detection)
```

### Analytics

```bash
# Generate reports
python src\analytics.py --daily --output reports\daily_report
python src\analytics.py --weekly --output reports\weekly_report

# View stats
python src\main.py --stats --days 7
```

## 🔧 Maintenance

### Adding New Platform

1. Create new adapter in `src/` (e.g., `tiktok_adapter.py`)
2. Follow pattern dari `youtube_adapter.py` atau `instagram_adapter.py`
3. Update `src/__init__.py` untuk export
4. Update `src/main.py` untuk integrate
5. Add configuration di `config/config.example.env`
6. Update documentation

### Adding New Feature

1. Identify appropriate module
2. Add feature dengan proper docstrings
3. Add tests di `tests/`
4. Update documentation
5. Update version di `setup.py` dan `src/__init__.py`

### Updating Documentation

1. Update relevant file di `docs/`
2. Update main `README.md` jika perlu
3. Keep `STRUCTURE.md` updated

## 📝 Best Practices

### Code Organization

- ✅ Keep modules focused dan single-purpose
- ✅ Use proper docstrings
- ✅ Follow PEP 8 style guide
- ✅ Add type hints
- ✅ Handle errors gracefully

### Documentation

- ✅ Update docs saat add features
- ✅ Include usage examples
- ✅ Document API changes
- ✅ Keep README.md concise

### Testing

- ✅ Test before commit
- ✅ Add tests untuk new features
- ✅ Use dry run mode untuk testing
- ✅ Verify dengan real data

### Version Control

- ✅ Use meaningful commit messages
- ✅ Don't commit `.env` file
- ✅ Don't commit `logs/` dan `reports/`
- ✅ Keep `.gitignore` updated

## 🎓 Navigation Guide

### For Users

1. Start with main `README.md`
2. Follow `docs/QUICKSTART.md` untuk setup
3. Use `docs/CARA_MENCOBA.md` untuk testing
4. Check `docs/README.md` untuk detailed guides

### For Developers

1. Review `STRUCTURE.md` (this file)
2. Check `docs/PROJECT_SUMMARY.md` untuk architecture
3. Review source code di `src/`
4. Check `tests/` untuk test examples

### For Contributors

1. Read `README.md` dan `STRUCTURE.md`
2. Review existing code patterns
3. Follow best practices
4. Update documentation

## 🔄 Migration from Old Structure

If you had files in root:

```bash
# Old structure
judol-delet-msg/
├── core_detector.py
├── database.py
├── main.py
└── ...

# New structure (files moved to appropriate folders)
judol-delet-msg/
├── src/
│   ├── core_detector.py
│   └── ...
├── docs/
└── ...
```

**No code changes needed!** Just update import paths jika ada.

## ✅ Checklist

### Setup Checklist
- [ ] All folders created
- [ ] Files organized properly
- [ ] Dependencies installed
- [ ] Configuration created (.env)
- [ ] Tests passing

### Development Checklist
- [ ] Code follows structure
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] Version updated
- [ ] Ready for commit

---

**Structure Version**: 2.0.0  
**Last Updated**: 2025-10-07  
**Status**: ✅ Professional Structure Complete
