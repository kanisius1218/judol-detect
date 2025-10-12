# Google OAuth Setup

## Quick Setup

1. **Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Create new project
   - Enable Google+ API

2. **Create OAuth Credentials**
   - Go to APIs & Services > Credentials
   - Create OAuth 2.0 Client ID
   - Application type: Web application
   - Add redirect URI: http://localhost:5001/auth/callback

3. **Get Credentials**
   ```
   GOOGLE_CLIENT_ID=your-client-id-here
   GOOGLE_CLIENT_SECRET=your-client-secret-here
   ```

4. **Set Environment Variables**
   Create `.env` file:
   ```
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   SECRET_KEY=your-secret-key
   ```

5. **Run Application**
   ```bash
   python app_advanced.py
   ```

## Features After Login
- Auto-delete spam/judi messages
- Personal dashboard
- Detection history
- Export data
