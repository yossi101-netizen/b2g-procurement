#!/bin/bash

# DEPLOYMENT SCRIPT - Run this to deploy your changes
# This removes email confirmation and deploys direct booking emails

echo "========================================="
echo "DEPLOYING BACKEND WITHOUT CONFIRMATION"
echo "========================================="
echo ""

# Stage all changes
echo "📦 Staging all changes..."
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "Remove email confirmation flow - send direct booking emails

- Deleted confirmationController.js (no longer needed)
- Deleted old booking and email service files
- Updated emailService.js with direct thank-you email
- Removed confirmation button and link from emails
- Updated routes to send emails immediately
- No confirmation token generation

This deployment fixes the issue where users were seeing a
confirmation button in emails. Now they receive a direct
thank you message with no action required."

# Push to repository
echo "🚀 Pushing to repository..."
git push origin main

echo ""
echo "========================================="
echo "✅ CODE PUSHED TO GITHUB"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "FOR RENDER:"
echo "1. Go to https://dashboard.render.com"
echo "2. Select your backend service"
echo "3. Click 'Manual Deploy' → 'Deploy latest commit'"
echo "4. Wait 2-3 minutes for deployment"
echo ""
echo "FOR HOSTINGER:"
echo "1. Upload backend folder via FTP/File Manager"
echo "2. Restart Node.js application in control panel"
echo ""
echo "========================================="
echo "After deployment, test by submitting a booking"
echo "You should receive an email with:"
echo "- 'THANK YOU FOR BOOKING A CALL WITH US'"
echo "- NO confirmation button"
echo "- NO confirmation link"
echo "========================================="
