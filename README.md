# GUS Dashboard Generator for Industries Monthly Release

This Python script generates a beautiful HTML dashboard for tracking Industries Monthly Release work items in GUS.

## Features

- **Real-time data** from GUS via Salesforce CLI
- **Visual statistics** - Total items, closed count, in-progress count, story points
- **Interactive charts** - Status distribution and product tag breakdown
- **Organized work items** - Grouped by status with color coding
- **Clickable work items** - Direct links to GUS
- **Responsive design** - Works on desktop and mobile

## Prerequisites

- Python 3.6+
- Salesforce CLI (`sf`) installed
- Authenticated GUS org (alias: `anawal-gus`)

## Usage

### Quick Start

```bash
cd ~/gus-dashboard-262
python3 generate_dashboard.py
```

The script will:
1. Query GUS for all work items in patch 262.6 with "Industries Monthly Release" theme
2. Generate an HTML dashboard
3. Save it as `industries_monthly_release_262.6_dashboard.html`
4. Automatically open it in your default browser

### Manual Open

If the dashboard doesn't open automatically:

```bash
open industries_monthly_release_262.6_dashboard.html
```

Or just double-click the HTML file in Finder.

## Customization

You can modify the script to track different releases or themes by editing these variables at the top of `generate_dashboard.py`:

```python
TARGET_ORG = "anawal-gus"          # Your GUS org alias
BUILD_VERSION = "262.6"            # Build/patch version
THEME_KEYWORD = "Industries Monthly Release"  # Theme filter
```

## Output

The dashboard includes:

### Summary Statistics
- Total work items
- Closed items
- In-progress items
- Total story points

### Visual Charts
- Status distribution (bar chart)
- Product tag distribution (bar chart)

### Detailed Work Items
Each work item displays:
- Work item ID (clickable link to GUS)
- Subject/description
- Status (color-coded)
- Type (Bug, User Story, etc.)
- Assignee
- QA Engineer
- Product Tag
- Story Points

### Status Color Coding
- **New** - Gray
- **Triaged** - Teal
- **In Progress** - Yellow
- **Ready for Review** - Blue
- **Fixed** - Green
- **QA In Progress** - Aqua
- **Closed** - Green
- **Waiting** - Orange
- **Integrate** - Purple
- **Pending Release** - Pink
- **Never** - Red

## Refreshing the Dashboard

Run the script anytime to get the latest data from GUS:

```bash
python3 generate_dashboard.py
```

The HTML file will be regenerated with current data.

## Scheduling Automatic Updates

You can set up automatic dashboard generation using cron:

```bash
# Edit crontab
crontab -e

# Add this line to generate dashboard every hour at minute 0
0 * * * * cd ~/gus-dashboard-262 && /usr/bin/python3 generate_dashboard.py
```

## Troubleshooting

### "No authorization information found for gus"

Re-authenticate with GUS:
```bash
sf org login web --instance-url https://gus.my.salesforce.com --alias anawal-gus
```

### "No work items found"

Check that:
- The build version is correct
- Work items have "Industries Monthly Release" in the subject
- The scheduled build name is exactly "262.6"

### Script won't run

Make sure it's executable:
```bash
chmod +x generate_dashboard.py
```

## Support

For issues or questions, contact the Industries team or modify the script to fit your needs.
