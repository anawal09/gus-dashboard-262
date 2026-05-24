#!/bin/bash
# Quick start script to set up Salesforce Git Pages

echo "🚀 Industries Dashboard Quick Setup"
echo "===================================="
echo ""

# Get username
read -p "Enter your Salesforce Git username (e.g., anawal): " USERNAME

if [ -z "$USERNAME" ]; then
    echo "❌ Username required!"
    exit 1
fi

REPO_NAME="gus-industries-dashboard"
REPO_URL="https://git.soma.salesforce.com/$USERNAME/$REPO_NAME.git"

echo ""
echo "📋 Setup Summary:"
echo "   Repository: $REPO_NAME"
echo "   URL: $REPO_URL"
echo "   Pages URL: https://git.soma.salesforce.com/pages/$USERNAME/$REPO_NAME/"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Check if remote already exists
if git remote get-url origin &> /dev/null; then
    echo "⚠️  Remote 'origin' already exists. Updating..."
    git remote set-url origin $REPO_URL
else
    echo "🔗 Adding remote..."
    git remote add origin $REPO_URL
fi

# Update deploy script with username
echo "📝 Updating deploy script..."
sed -i.bak "s/YOUR_USERNAME/$USERNAME/g" deploy.sh
rm -f deploy.sh.bak

echo ""
echo "✅ Local setup complete!"
echo ""
echo "📌 Next Steps:"
echo ""
echo "1. Create repository on Salesforce Git:"
echo "   → Go to https://git.soma.salesforce.com"
echo "   → Click 'New Repository'"
echo "   → Name: $REPO_NAME"
echo "   → Visibility: Internal or Public"
echo "   → Don't initialize with README"
echo ""
echo "2. Push your dashboards:"
echo "   cd ~/gus-dashboard-262"
echo "   git add ."
echo "   git commit -m 'Initial commit: Industries dashboards'"
echo "   git push -u origin main"
echo ""
echo "3. Enable Pages in repository settings:"
echo "   → Go to your repo → Settings → Pages"
echo "   → Source: main branch"
echo "   → Folder: / (root)"
echo "   → Save"
echo ""
echo "4. Access your dashboard:"
echo "   https://git.soma.salesforce.com/pages/$USERNAME/$REPO_NAME/"
echo ""
echo "To update later, just run: ./deploy.sh"
echo ""

