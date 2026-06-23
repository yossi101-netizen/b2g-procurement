# KRITIKAAL Backend - Deployment Guide

## Deploy to Render.com

### Prerequisites
1. Create a [Render.com](https://render.com) account
2. Get a [Resend API key](https://resend.com/api-keys)

### Deployment Steps

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Add backend files"
   git push origin main
   ```

2. **Create a new Web Service on Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository containing your backend

3. **Configure the service**
   - **Name**: `KRITIKAAL-backend`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Environment**: `Node`
   - **Build Command**: `npm install`
   - **Start Command**: `npm start`
   - **Plan**: Free (or choose paid for better performance)

4. **Set Environment Variables**
   Go to "Environment" tab and add:
   ```
   NODE_ENV=production
   PORT=5000
   RESEND_API_KEY=re_your_actual_api_key_here
   FROM_EMAIL=noreply@KRITIKAAL.com
   ADMIN_EMAIL=admin@KRITIKAAL.com
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Your backend will be available at: `https://KRITIKAAL-backend.onrender.com`

### Test Your Deployment

Once deployed, test the health endpoint:
```bash
curl https://KRITIKAAL-backend.onrender.com/api/health
```

Expected response:
```json
{
  "status": "ok",
  "message": "KRITIKAAL Backend is running"
}
```

### Frontend Configuration

Your frontend is already configured with the Render URL in `.env`:
```
VITE_API_URL=https://KRITIKAAL-backend.onrender.com
```

### Troubleshooting

**Issue**: Deployment fails
- Check build logs in Render dashboard
- Ensure all dependencies are in package.json
- Verify Node version compatibility

**Issue**: 503 Service Unavailable
- Free tier services spin down after 15 minutes of inactivity
- First request after idle may take 30-50 seconds to wake up
- Consider upgrading to paid tier for always-on service

**Issue**: Email not sending
- Verify RESEND_API_KEY is set correctly
- Check Resend dashboard for sending limits
- Ensure FROM_EMAIL is verified in Resend

### Auto-Deploy

Render automatically redeploys when you push to your main branch:
```bash
git add .
git commit -m "Update backend"
git push origin main
```

### Local Development

For local development, update your frontend `.env`:
```
VITE_API_URL=http://localhost:5000
```

Then run:
```bash
cd backend
npm install
npm start
```

### Notes

- Free tier includes:
  - 750 hours/month
  - Spins down after 15 min inactivity
  - 512 MB RAM
  - Shared CPU

- For production, consider:
  - Paid tier ($7/month+) for always-on
  - Custom domain
  - Automatic SSL
  - Better performance

