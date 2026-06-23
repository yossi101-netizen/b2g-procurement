# DEPLOYMENT SCRIPT - Windows PowerShell
# Run this to deploy your changes to remove email confirmation

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "DEPLOYING BACKEND WITHOUT CONFIRMATION" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to project root
Set-Location "c:\Users\Swathi priya\kritikaal"

# Stage all changes
Write-Host "📦 Staging all changes..." -ForegroundColor Yellow
git add .

# Commit changes
Write-Host "💾 Committing changes..." -ForegroundColor Yellow
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
Write-Host "🚀 Pushing to repository..." -ForegroundColor Yellow
git push origin main

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "✅ CODE PUSHED TO GITHUB" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host ""
Write-Host "FOR RENDER:" -ForegroundColor Cyan
Write-Host "1. Go to https://dashboard.render.com"
Write-Host "2. Select your backend service"
Write-Host "3. Click 'Manual Deploy' → 'Deploy latest commit'"
Write-Host "4. Wait 2-3 minutes for deployment"
Write-Host ""
Write-Host "FOR HOSTINGER:" -ForegroundColor Cyan
Write-Host "1. Upload backend folder via FTP/File Manager"
Write-Host "2. Restart Node.js application in control panel"
Write-Host ""
Write-Host "=========================================" -ForegroundColor Yellow
Write-Host "After deployment, test by submitting a booking" -ForegroundColor Yellow
Write-Host "You should receive an email with:" -ForegroundColor Yellow
Write-Host "- 'THANK YOU FOR BOOKING A CALL WITH US'" -ForegroundColor Green
Write-Host "- NO confirmation button" -ForegroundColor Green
Write-Host "- NO confirmation link" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Yellow
