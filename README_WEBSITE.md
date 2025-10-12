# Message Detection System - Web Application

## 🚀 Quick Start

### Running the Application

1. **Install Dependencies** (if not already installed):
```bash
pip install -r requirements.txt
```

2. **Run the Web Application**:
```bash
python app.py
```

3. **Open Browser**:
Navigate to `http://localhost:5000`

## 🎨 Design Features

### Black & White Theme
- **Minimalist Design**: Clean, professional interface with black and white color scheme
- **High Contrast**: Easy to read with clear visual hierarchy
- **Modern Typography**: Using Inter font for better readability

## 💡 Features

### 1. Single Message Detection
- Enter any message in the text area
- Click "Analyze Message" to check if it's spam or ham
- View confidence level with visual progress bar
- Real-time timestamp for each detection

### 2. Batch Processing
- Process multiple messages at once
- Enter messages one per line
- Get results for all messages simultaneously
- Efficient for bulk checking

### 3. Session Statistics
- **Total Checks**: Number of messages analyzed
- **Spam Count**: Total spam messages detected
- **Ham Count**: Total legitimate messages
- **Spam Rate**: Percentage of spam in your session

### 4. Detection History
- View last 10 detections
- See message preview, result, and confidence
- Clear history option available
- Automatically updates after each detection

### 5. Interactive Features
- **Keyboard Shortcuts**:
  - `Ctrl/Cmd + Enter`: Analyze message
  - `Escape`: Clear input
- **Character Counter**: Shows input length
- **Copy Results**: Click on result label to copy
- **Auto-refresh**: Statistics update every 30 seconds

## 🛠️ API Endpoints

### Main Endpoints:
- `GET /`: Main web interface
- `POST /api/detect`: Single message detection
- `POST /api/batch`: Batch message processing
- `GET /api/stats`: Get session statistics
- `GET /api/history`: Get detection history
- `POST /api/clear-history`: Clear session history

## 📊 How It Works

1. **Input Processing**: 
   - Text is validated and cleaned
   - Empty messages are rejected

2. **ML Detection**:
   - Uses trained ensemble model (if available)
   - Falls back to basic model or mock predictions
   - Returns spam/ham classification with confidence

3. **Result Display**:
   - Visual indicators (black for spam, white/gray for ham)
   - Confidence percentage with progress bar
   - Timestamp for tracking

4. **Session Management**:
   - History stored in session (last 10 items)
   - Statistics calculated in real-time
   - No permanent data storage (privacy-first)

## 🔒 Privacy & Security

- **No Data Storage**: Messages are not permanently stored
- **Session-based**: History only exists during your session
- **Local Processing**: All detection happens on the server
- **CORS Enabled**: Secure cross-origin requests

## 🎯 Use Cases

1. **Email Filtering**: Check suspicious emails
2. **SMS Verification**: Validate text messages
3. **Content Moderation**: Screen user-generated content
4. **Training Data**: Collect feedback for model improvement

## 🚦 Status Indicators

- **Spam**: Black background, white text
- **Ham**: White background, black border
- **Confidence**: Visual bar showing certainty level
- **Loading**: Spinner animation during processing

## 📱 Responsive Design

- Works on desktop, tablet, and mobile
- Adaptive layout for different screen sizes
- Touch-friendly buttons and controls

## ⚡ Performance

- Sub-second response time
- Caching for repeated queries
- Rate limiting to prevent abuse
- Efficient batch processing

## 🔧 Customization

To modify the design:
1. Edit `static/css/style.css` for styling
2. Modify `templates/index.html` for layout
3. Update `static/js/app.js` for behavior

## 📝 Notes

- The model will use mock predictions if ML models are not found
- Session data is temporary and cleared when browser closes
- For production use, implement proper authentication and database storage
