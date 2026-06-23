# ============================================
# Kritikaal Deployment Script (Windows)
# ============================================
# This script deploys your updated backend to remove email confirmation flow

Write-Host "🚀 Kritikaal Deployment Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git is not installed. Please install Git first." -ForegroundColor Red
    exit 1
}

Write-Host "📋 Step 1: Checking for uncommitted changes..." -ForegroundColor Yellow

# Check git status
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "✅ Found changes to commit" -ForegroundColor Green
    Write-Host ""
    
    # Show changed files
    Write-Host "📝 Changed files:" -ForegroundColor Cyan
    git status --short
    Write-Host ""
    
    # Add all changes
    Write-Host "📋 Step 2: Adding all changes to git..." -ForegroundColor Yellow
    git add .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to add changes" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Changes added" -ForegroundColor Green
    Write-Host ""
    
    # Commit changes
    Write-Host "📋 Step 3: Committing changes..." -ForegroundColor Yellow
    $commitMessage = "Remove email confirmation flow - direct emails only"
    git commit -m $commitMessage
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to commit changes" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Changes committed" -ForegroundColor Green
    Write-Host ""
    
    # Push to GitHub
    Write-Host "📋 Step 4: Pushing to GitHub..." -ForegroundColor Yellow
    git push origin main
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to push changes" -ForegroundColor Red
        Write-Host "ℹ️  You may need to pull first: git pull origin main" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✅ Changes pushed to GitHub" -ForegroundColor Green
    Write-Host ""
    
} else {
    Write-Host "ℹ️  No uncommitted changes found. Checking if remote is up to date..." -ForegroundColor Yellow
    
    # Check if local is behind remote
    git fetch origin
    $localCommit = git rev-parse main
    $remoteCommit = git rev-parse origin/main
    
    if ($localCommit -ne $remoteCommit) {
        Write-Host "⚠️  Local branch is not in sync with remote" -ForegroundColor Yellow
        Write-Host "📋 Pushing to GitHub..." -ForegroundColor Yellow
        git push origin main
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Failed to push changes" -ForegroundColor Red
            exit 1
        }
        Write-Host "✅ Synced with GitHub" -ForegroundColor Green
    } else {
        Write-Host "✅ Already up to date with GitHub" -ForegroundColor Green
    }
    Write-Host ""
}

Write-Host "🎉 Deployment Process Complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "For RENDER (automatic deployment):" -ForegroundColor Cyan
Write-Host "  1. Go to https://dashboard.render.com/" -ForegroundColor White
Write-Host "  2. Your backend service should automatically detect the new commit" -ForegroundColor White
Write-Host "  3. Wait for the deployment to complete (usually 2-5 minutes)" -ForegroundColor White
Write-Host "  4. Check the logs to confirm it's running without errors" -ForegroundColor White
Write-Host ""
Write-Host "For HOSTINGER (manual deployment):" -ForegroundColor Cyan
Write-Host "  1. Pull the latest changes on your Hostinger server:" -ForegroundColor White
Write-Host "     cd /path/to/your/app && git pull origin main" -ForegroundColor Gray
Write-Host "  2. Install dependencies (if needed):" -ForegroundColor White
Write-Host "     cd backend && npm install" -ForegroundColor Gray
Write-Host "  3. Restart the Node.js application:" -ForegroundColor White
Write-Host "     pm2 restart all" -ForegroundColor Gray
Write-Host "     # OR use Hostinger's control panel to restart" -ForegroundColor Gray
Write-Host ""
Write-Host "✅ Once deployed, your emails will no longer have confirmation buttons!" -ForegroundColor Green
Write-Host ""
