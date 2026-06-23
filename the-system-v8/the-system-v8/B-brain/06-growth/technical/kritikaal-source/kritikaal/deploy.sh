#!/bin/bash

# ============================================
# Kritikaal Deployment Script (Linux/Mac)
# ============================================
# This script deploys your updated backend to remove email confirmation flow

echo "🚀 Kritikaal Deployment Script"
echo "================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

echo "📋 Step 1: Checking for uncommitted changes..."

# Check git status
if [[ -n $(git status --porcelain) ]]; then
    echo "✅ Found changes to commit"
    echo ""
    
    # Show changed files
    echo "📝 Changed files:"
    git status --short
    echo ""
    
    # Add all changes
    echo "📋 Step 2: Adding all changes to git..."
    git add .
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to add changes"
        exit 1
    fi
    echo "✅ Changes added"
    echo ""
    
    # Commit changes
    echo "📋 Step 3: Committing changes..."
    git commit -m "Remove email confirmation flow - direct emails only"
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to commit changes"
        exit 1
    fi
    echo "✅ Changes committed"
    echo ""
    
    # Push to GitHub
    echo "📋 Step 4: Pushing to GitHub..."
    git push origin main
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to push changes"
        echo "ℹ️  You may need to pull first: git pull origin main"
        exit 1
    fi
    echo "✅ Changes pushed to GitHub"
    echo ""
    
else
    echo "ℹ️  No uncommitted changes found. Checking if remote is up to date..."
    
    # Check if local is behind remote
    git fetch origin
    LOCAL=$(git rev-parse main)
    REMOTE=$(git rev-parse origin/main)
    
    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "⚠️  Local branch is not in sync with remote"
        echo "📋 Pushing to GitHub..."
        git push origin main
        
        if [ $? -ne 0 ]; then
            echo "❌ Failed to push changes"
            exit 1
        fi
        echo "✅ Synced with GitHub"
    else
        echo "✅ Already up to date with GitHub"
    fi
    echo ""
fi

echo "🎉 Deployment Process Complete!"
echo "================================"
echo ""
echo "📝 Next Steps:"
echo ""
echo "For RENDER (automatic deployment):"
echo "  1. Go to https://dashboard.render.com/"
echo "  2. Your backend service should automatically detect the new commit"
echo "  3. Wait for the deployment to complete (usually 2-5 minutes)"
echo "  4. Check the logs to confirm it's running without errors"
echo ""
echo "For HOSTINGER (manual deployment):"
echo "  1. SSH into your Hostinger server"
echo "  2. Pull the latest changes:"
echo "     cd /path/to/your/app && git pull origin main"
echo "  3. Install dependencies (if needed):"
echo "     cd backend && npm install"
echo "  4. Restart the Node.js application:"
echo "     pm2 restart all"
echo "     # OR use Hostinger's control panel to restart"
echo ""
echo "✅ Once deployed, your emails will no longer have confirmation buttons!"
echo ""
