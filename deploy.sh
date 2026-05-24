#!/bin/bash
# Auto-deploy script for GUS dashboards

echo "🔄 Generating fresh dashboard data from GUS..."
python3 generate_dashboard.py

if [ $? -ne 0 ]; then
    echo "❌ Dashboard generation failed"
    exit 1
fi

echo "📝 Committing changes to Git..."
git add *.html *.md *.py
git commit -m "Update dashboard: $(date '+%Y-%m-%d %H:%M:%S')"

echo "🚀 Pushing to Salesforce Git..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Dashboard deployed successfully!"
    echo ""
    echo "📊 Your dashboards will be available at:"
    echo "   https://git.soma.salesforce.com/pages/YOUR_USERNAME/gus-industries-dashboard/"
    echo ""
    echo "⏱️  Pages typically update within 1-2 minutes"
else
    echo "❌ Push failed. Check your Git configuration."
    exit 1
fi
