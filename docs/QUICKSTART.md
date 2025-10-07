# 🚀 Quick Start Guide

Panduan cepat untuk setup dan test bot dalam 10 menit!

## ⚡ Quick Setup (YouTube Only - Paling Mudah)

### Step 1: Install Python & Dependencies (3 menit)

```bash
# Check Python
python --version

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Get YouTube API Key (5 menit)

1. Buka https://console.cloud.google.com/
2. Create project baru
3. Enable "YouTube Data API v3"
4. Create Credentials → API Key
5. Copy API key

### Step 3: Get Channel ID (1 menit)

Dari URL channel Anda:
```
https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw
                                 ^^^^^^^^^^^^^^^^^^^^^^^^
                                 Copy bagian ini
```

### Step 4: Configure (1 menit)

```bash
# Copy config template
copy config.example.env .env

# Edit .env
notepad .env
```

Isi:
```env
YOUTUBE_ENABLED=true
YOUTUBE_API_KEY=AIzaSy_YOUR_API_KEY_HERE
YOUTUBE_CHANNEL_ID=UC_YOUR_CHANNEL_ID_HERE
CONFIDENCE_THRESHOLD=40
DRY_RUN=true
```

### Step 5: Test Detection Engine (30 detik)

```bash
python core_detector.py
```

Anda akan melihat test results untuk berbagai jenis spam.

### Step 6: Test YouTube Adapter (30 detik)

Edit `youtube_adapter.py` di bagian bawah, uncomment test code, lalu:

```bash
python youtube_adapter.py
```

---

## 🎯 First Run

### Test Mode (Dry Run)

Set di `.env`:
```env
DRY_RUN=true
```

Ini akan:
- ✅ Check comments
- ✅ Detect spam
- ✅ Log to database
- ❌ TIDAK delete comments

### Production Mode

Setelah yakin detection akurat:

```env
DRY_RUN=false
```

Ini akan:
- ✅ Check comments
- ✅ Detect spam
- ✅ Log to database
- ✅ **DELETE spam comments**

---

## 📊 Check Results

### View Database

```bash
python database.py
```

### Check Logs

Lihat file `spam_moderator.log`

### Statistics

Coming soon - main bot dengan statistics dashboard

---

## 🎨 Customize

### Adjust Sensitivity

Edit `.env`:
```env
# More sensitive (detect more spam, more false positives)
CONFIDENCE_THRESHOLD=30

# Balanced (recommended)
CONFIDENCE_THRESHOLD=40

# Less sensitive (fewer false positives, some spam may pass)
CONFIDENCE_THRESHOLD=50
```

### Add Keywords

Edit `core_detector.py`:
```python
PLATFORM_NAMES = [
    'olxtoto', 'rajabandot', 'kingslot',
    'your_new_platform_here'  # Add here
]
```

---

## 🐛 Common Issues

### "Module not found"

```bash
pip install -r requirements.txt
```

### "API key invalid"

- Check API key di Google Cloud Console
- Pastikan YouTube Data API v3 enabled

### "Permission denied"

- Pastikan Anda owner/manager channel
- Check API key restrictions

---

## 📚 Next Steps

1. ✅ Test dengan dry run
2. ✅ Check database logs
3. ✅ Adjust threshold jika perlu
4. ✅ Add custom keywords
5. ✅ Run production mode
6. ✅ Monitor daily

---

## 🎓 Platform Setup Guides

### YouTube ✅ READY
- See README.md → YouTube API Setup
- Official API, safe to use
- **RECOMMENDED**

### Instagram ⚠️ COMPLEX
- See README.md → Instagram API Setup
- Requires Business account
- Needs Facebook app setup
- **USABLE** but complex

### TikTok ❌ NOT RECOMMENDED
- No official API
- Unofficial methods violate TOS
- Risk of account ban
- **DON'T USE**

---

## 💡 Tips

### 1. Start Small
Test dengan 1 video dulu sebelum full channel

### 2. Monitor Closely
Check deleted comments di database untuk false positives

### 3. Whitelist Trusted Users
Jika ada user yang sering false positive, whitelist mereka

### 4. Regular Updates
Update keywords sesuai spam trends

### 5. Backup Database
```bash
copy spam_moderator.db backup\
```

---

## ✅ Checklist

Setup:
- [ ] Python installed
- [ ] Dependencies installed
- [ ] API key obtained
- [ ] Channel ID obtained
- [ ] .env configured

Testing:
- [ ] Detection engine tested
- [ ] YouTube adapter tested
- [ ] Dry run completed
- [ ] Results checked
- [ ] Threshold adjusted

Production:
- [ ] Dry run disabled
- [ ] Bot running
- [ ] Monitoring active
- [ ] Database backed up

---

**Ready to go!** 🎉

For detailed documentation, see README.md

Version: 1.0.0
