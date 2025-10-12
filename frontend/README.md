# Spam Detection System - TypeScript Frontend

A modern, responsive TypeScript React application for spam/ham message detection with a clean black & white design.

## Features

- **Single Message Detection**: Real-time spam/ham classification
- **Batch Processing**: Analyze multiple messages at once
- **Statistics Dashboard**: Track detection metrics
- **Detection History**: View recent detections
- **Keyboard Shortcuts**: Ctrl+Enter to detect, Esc to clear
- **Character Counter**: Track message length
- **Copy Results**: Easy result sharing
- **CSV Export**: Download batch results
- **File Upload**: Import messages from text files
- **Responsive Design**: Works on all devices
- **Black & White Theme**: Clean, minimalist interface

## Tech Stack

- **React 18** with TypeScript
- **Axios** for API calls
- **React Icons** for UI icons
- **React Hot Toast** for notifications
- **Chart.js** for data visualization
- **Inter Font** for typography

## Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Update `.env` with your backend URL:
```
REACT_APP_API_URL=http://localhost:5000
```

## Development

Start the development server:
```bash
npm start
```

The app will run on [http://localhost:3000](http://localhost:3000)

## Build

Build for production:
```bash
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable React components
│   │   ├── MessageInput.tsx
│   │   ├── ResultDisplay.tsx
│   │   ├── StatsCard.tsx
│   │   ├── HistoryList.tsx
│   │   └── BatchDetection.tsx
│   ├── services/         # API service layer
│   │   └── api.ts
│   ├── types/           # TypeScript type definitions
│   │   └── index.ts
│   ├── App.tsx          # Main application component
│   ├── App.css          # Black & white theme styles
│   └── index.tsx        # Application entry point
├── public/
├── package.json
└── tsconfig.json
```

## API Integration

The frontend connects to the Flask backend API with these endpoints:

- `POST /api/detect` - Single message detection
- `POST /api/batch` - Batch message processing
- `GET /api/stats` - Session statistics
- `GET /api/history` - Detection history
- `POST /api/clear-history` - Clear history

## Keyboard Shortcuts

- **Ctrl + Enter**: Submit message for detection
- **Escape**: Clear input field

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

MIT
