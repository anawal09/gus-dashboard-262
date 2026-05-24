# Setup Guide: Deploy GUS Dashboard to Salesforce Git Pages

## Overview
This guide helps you publish your GUS dashboard to Salesforce Git Pages, similar to:
https://git.soma.salesforce.com/pages/npant/Industries-Monthly-release-Dashboard/

## Prerequisites
- Salesforce Git account (git.soma.salesforce.com)
- Git CLI configured with Salesforce credentials

## Step 1: Create Repository on Salesforce Git

1. Go to https://git.soma.salesforce.com
2. Click "New Repository" (or use an existing one)
3. Repository name: `gus-industries-dashboard` (or your choice)
4. Make it Public or Internal (so others can view the pages)
5. Initialize with README: No (we already have files)

## Step 2: Connect Local Repository to Salesforce Git

```bash
cd ~/gus-dashboard-262

# Add Salesforce Git as remote (replace YOUR_USERNAME with your Salesforce Git username)
git remote add origin https://git.soma.salesforce.com/YOUR_USERNAME/gus-industries-dashboard.git

# Check your remote
git remote -v
```

## Step 3: Prepare for Pages

Salesforce Git Pages looks for an `index.html` file in the root or in a `docs/` folder.

Option A: Rename your dashboard to index.html (simplest):
```bash
cp industries_monthly_release_262.6_dashboard.html index.html
```

Option B: Create an index.html that links to multiple dashboards:
```bash
# We'll create this for you
```

## Step 4: Initial Commit and Push

```bash
# Stage all files
git add .

# Commit
git commit -m "Initial commit: Industries Monthly Release Dashboard"

# Push to main branch
git push -u origin main
```

## Step 5: Enable Pages

1. Go to your repository on git.soma.salesforce.com
2. Click "Settings" > "Pages"
3. Source: Select "main" branch
4. Folder: Select "/" (root) or "/docs"
5. Click "Save"

After a few minutes, your dashboard will be available at:
`https://git.soma.salesforce.com/pages/YOUR_USERNAME/gus-industries-dashboard/`

## Step 6: Share the Link

Your shareable URL will be:
```
https://git.soma.salesforce.com/pages/YOUR_USERNAME/gus-industries-dashboard/index.html
```

Or if you keep the original filename:
```
https://git.soma.salesforce.com/pages/YOUR_USERNAME/gus-industries-dashboard/industries_monthly_release_262.6_dashboard.html
```

## Updating the Dashboard

Use the deploy script:
```bash
cd ~/gus-dashboard-262
./deploy.sh
```

This will:
1. Query GUS for latest data
2. Regenerate the HTML dashboard
3. Commit changes
4. Push to Salesforce Git
5. Pages will auto-update within 1-2 minutes

## Creating Multiple Dashboards

You can create multiple dashboards for different releases:
```bash
# Modify the script for different builds
# BUILD_VERSION = "262.6" -> "264.0"
python3 generate_dashboard.py

# Or create a new script
cp generate_dashboard.py generate_dashboard_264.py
# Edit BUILD_VERSION in the new file
```

Then create an index page that lists all dashboards.

## Troubleshooting

**Pages not showing?**
- Wait 2-3 minutes after enabling Pages
- Check repository is Public or Internal (not Private)
- Verify index.html or target HTML file exists in root

**Authentication issues?**
```bash
# Configure Git credentials
git config --global user.name "Your Name"
git config --global user.email "your.email@salesforce.com"

# Use SSH instead of HTTPS (recommended)
git remote set-url origin git@git.soma.salesforce.com:YOUR_USERNAME/gus-industries-dashboard.git
```

**Dashboard not updating?**
- Check if commit was successful: `git log`
- Check if push was successful: `git status`
- Clear browser cache
- Wait 1-2 minutes for Pages to rebuild

## Best Practices

1. **Schedule automatic updates**: Use cron to run deploy.sh daily
2. **Create index page**: List all your dashboards in one place
3. **Add timestamps**: Dashboard shows generation time
4. **Version control**: Keep old versions in Git history
5. **Document**: Add README explaining what each dashboard tracks

