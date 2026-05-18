#!/usr/bin/env python3
"""
GUS Dashboard Generator for Industries Monthly Release 262.6
Queries GUS via Salesforce CLI and generates an HTML dashboard
"""

import json
import subprocess
import sys
from datetime import datetime
from collections import defaultdict

# Configuration
TARGET_ORG = "anawal-gus"
BUILD_VERSION = "262.6"
THEME_KEYWORD = "Industries Monthly Release"

def run_sf_query(query):
    """Execute a Salesforce SOQL query and return parsed JSON results."""
    try:
        result = subprocess.run(
            ["sf", "data", "query", "--target-org", TARGET_ORG, "--query", query, "--json"],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        return data.get("result", {}).get("records", [])
    except subprocess.CalledProcessError as e:
        print(f"Error executing query: {e}", file=sys.stderr)
        print(f"Output: {e.stdout}", file=sys.stderr)
        print(f"Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)

def get_work_items():
    """Fetch all work items for the specified build and theme."""
    query = f"""
        SELECT Id, Name, Subject__c, Status__c, Type__c, Story_Points__c,
               Assignee__r.Name, Assignee__r.Email,
               Product_Tag__r.Name, Scheduled_Build_Name__c,
               Theme__r.Name, Priority__c, QA_Engineer__r.Name,
               Details__c, CreatedDate, LastModifiedDate
        FROM ADM_Work__c
        WHERE Scheduled_Build_Name__c = '{BUILD_VERSION}'
          AND Subject__c LIKE '%{THEME_KEYWORD}%'
        ORDER BY Status__c, Name
    """
    return run_sf_query(query)

def generate_html(work_items):
    """Generate HTML dashboard from work items data."""

    # Calculate statistics
    total_items = len(work_items)
    status_counts = defaultdict(int)
    type_counts = defaultdict(int)
    assignee_counts = defaultdict(int)
    product_tag_counts = defaultdict(int)
    total_points = 0
    items_with_points = 0

    for item in work_items:
        status_counts[item.get("Status__c", "Unknown")] += 1
        type_counts[item.get("Type__c", "Unknown")] += 1

        assignee_name = item.get("Assignee__r", {}).get("Name", "Unassigned") if item.get("Assignee__r") else "Unassigned"
        assignee_counts[assignee_name] += 1

        product_tag = item.get("Product_Tag__r", {}).get("Name", "No Tag") if item.get("Product_Tag__r") else "No Tag"
        product_tag_counts[product_tag] += 1

        points = item.get("Story_Points__c")
        if points:
            total_points += points
            items_with_points += 1

    # Status colors
    status_colors = {
        "New": "#6c757d",
        "Triaged": "#17a2b8",
        "In Progress": "#ffc107",
        "Ready for Review": "#007bff",
        "Fixed": "#28a745",
        "QA In Progress": "#20c997",
        "Closed": "#28a745",
        "Waiting": "#fd7e14",
        "Integrate": "#6f42c1",
        "Pending Release": "#e83e8c",
        "Never": "#dc3545"
    }

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Industries Monthly Release {BUILD_VERSION} Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .header .timestamp {{
            margin-top: 15px;
            font-size: 0.9em;
            opacity: 0.8;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.2s;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}

        .stat-card .number {{
            font-size: 3em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}

        .stat-card .label {{
            font-size: 1em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .section {{
            padding: 30px;
            border-top: 1px solid #e9ecef;
        }}

        .section h2 {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #667eea;
            border-left: 4px solid #667eea;
            padding-left: 15px;
        }}

        .status-group {{
            margin-bottom: 30px;
            background: #f8f9fa;
            border-radius: 8px;
            overflow: hidden;
        }}

        .status-header {{
            padding: 15px 20px;
            color: white;
            font-weight: bold;
            font-size: 1.2em;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .status-badge {{
            background: rgba(255,255,255,0.3);
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }}

        .work-items {{
            padding: 0;
        }}

        .work-item {{
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
            background: white;
            transition: background 0.2s;
        }}

        .work-item:hover {{
            background: #f8f9fa;
        }}

        .work-item:last-child {{
            border-bottom: none;
        }}

        .work-item-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 10px;
        }}

        .work-item-id {{
            font-weight: bold;
            color: #667eea;
            font-size: 1.1em;
        }}

        .work-item-id a {{
            color: #667eea;
            text-decoration: none;
        }}

        .work-item-id a:hover {{
            text-decoration: underline;
        }}

        .work-item-type {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            background: #e9ecef;
            color: #495057;
        }}

        .work-item-subject {{
            font-size: 1.05em;
            margin-bottom: 12px;
            color: #2c3e50;
            line-height: 1.5;
        }}

        .work-item-details {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            font-size: 0.9em;
            color: #666;
        }}

        .detail-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        .detail-label {{
            font-weight: 600;
            color: #495057;
        }}

        .points-badge {{
            background: #667eea;
            color: white;
            padding: 3px 10px;
            border-radius: 12px;
            font-weight: bold;
        }}

        .chart-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-top: 20px;
        }}

        .chart-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .chart-card h3 {{
            font-size: 1.2em;
            margin-bottom: 15px;
            color: #495057;
        }}

        .chart-bar {{
            margin-bottom: 12px;
        }}

        .chart-bar-label {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-size: 0.9em;
        }}

        .chart-bar-fill {{
            height: 25px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            padding-left: 10px;
            color: white;
            font-weight: bold;
            font-size: 0.85em;
        }}

        .footer {{
            padding: 20px;
            text-align: center;
            background: #f8f9fa;
            color: #666;
            font-size: 0.9em;
        }}

        .no-items {{
            padding: 40px;
            text-align: center;
            color: #999;
            font-style: italic;
        }}

        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}

            .work-item-header {{
                flex-direction: column;
                gap: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Industries Monthly Release Dashboard</h1>
            <div class="subtitle">Patch {BUILD_VERSION}</div>
            <div class="timestamp">Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="number">{total_items}</div>
                <div class="label">Total Items</div>
            </div>
            <div class="stat-card">
                <div class="number">{status_counts.get('Closed', 0)}</div>
                <div class="label">Closed</div>
            </div>
            <div class="stat-card">
                <div class="number">{status_counts.get('In Progress', 0)}</div>
                <div class="label">In Progress</div>
            </div>
            <div class="stat-card">
                <div class="number">{total_points}</div>
                <div class="label">Story Points</div>
            </div>
        </div>
"""

    # Add charts section
    html += """
        <div class="section">
            <h2>Overview Charts</h2>
            <div class="chart-container">
"""

    # Status distribution chart
    if status_counts:
        html += """
                <div class="chart-card">
                    <h3>Status Distribution</h3>
"""
        max_count = max(status_counts.values())
        for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
            percentage = (count / total_items) * 100
            width = (count / max_count) * 100
            html += f"""
                    <div class="chart-bar">
                        <div class="chart-bar-label">
                            <span>{status}</span>
                            <span>{count} ({percentage:.1f}%)</span>
                        </div>
                        <div class="chart-bar-fill" style="width: {width}%; background: {status_colors.get(status, '#6c757d')};">
                            {count}
                        </div>
                    </div>
"""
        html += """
                </div>
"""

    # Product tag distribution chart
    if product_tag_counts:
        html += """
                <div class="chart-card">
                    <h3>Product Tags</h3>
"""
        max_count = max(product_tag_counts.values())
        for tag, count in sorted(product_tag_counts.items(), key=lambda x: -x[1]):
            percentage = (count / total_items) * 100
            width = (count / max_count) * 100
            html += f"""
                    <div class="chart-bar">
                        <div class="chart-bar-label">
                            <span>{tag}</span>
                            <span>{count}</span>
                        </div>
                        <div class="chart-bar-fill" style="width: {width}%;">
                            {count}
                        </div>
                    </div>
"""
        html += """
                </div>
"""

    html += """
            </div>
        </div>
"""

    # Work items grouped by status
    html += """
        <div class="section">
            <h2>Work Items by Status</h2>
"""

    # Group items by status
    items_by_status = defaultdict(list)
    for item in work_items:
        status = item.get("Status__c", "Unknown")
        items_by_status[status].append(item)

    # Sort statuses by logical progression
    status_order = ["New", "Triaged", "In Progress", "Ready for Review", "Fixed", "QA In Progress",
                   "Integrate", "Pending Release", "Closed", "Waiting", "Never"]

    for status in status_order:
        if status not in items_by_status:
            continue

        items = items_by_status[status]
        status_color = status_colors.get(status, "#6c757d")

        html += f"""
            <div class="status-group">
                <div class="status-header" style="background: {status_color};">
                    <span>{status}</span>
                    <span class="status-badge">{len(items)} item{'s' if len(items) != 1 else ''}</span>
                </div>
                <div class="work-items">
"""

        for item in items:
            work_id = item.get("Name", "")
            subject = item.get("Subject__c", "No subject")
            item_type = item.get("Type__c", "Unknown")
            assignee = item.get("Assignee__r", {}).get("Name", "Unassigned") if item.get("Assignee__r") else "Unassigned"
            assignee_email = item.get("Assignee__r", {}).get("Email", "") if item.get("Assignee__r") else ""
            qa_engineer = item.get("QA_Engineer__r", {}).get("Name", "") if item.get("QA_Engineer__r") else ""
            product_tag = item.get("Product_Tag__r", {}).get("Name", "") if item.get("Product_Tag__r") else ""
            points = item.get("Story_Points__c")

            # GUS work item URL
            gus_url = f"https://gus.lightning.force.com/lightning/r/ADM_Work__c/{item['Id']}/view"

            html += f"""
                    <div class="work-item">
                        <div class="work-item-header">
                            <div class="work-item-id">
                                <a href="{gus_url}" target="_blank">{work_id}</a>
                            </div>
                            <div class="work-item-type">{item_type}</div>
                        </div>
                        <div class="work-item-subject">{subject}</div>
                        <div class="work-item-details">
                            <div class="detail-item">
                                <span class="detail-label">Assignee:</span>
                                <span>{assignee}</span>
                            </div>
"""

            if qa_engineer:
                html += f"""
                            <div class="detail-item">
                                <span class="detail-label">QA:</span>
                                <span>{qa_engineer}</span>
                            </div>
"""

            if product_tag:
                html += f"""
                            <div class="detail-item">
                                <span class="detail-label">Product:</span>
                                <span>{product_tag}</span>
                            </div>
"""

            if points:
                html += f"""
                            <div class="detail-item">
                                <span class="points-badge">{int(points)} pts</span>
                            </div>
"""

            html += """
                        </div>
                    </div>
"""

        html += """
                </div>
            </div>
"""

    html += """
        </div>

        <div class="footer">
            Generated by GUS Dashboard Generator | Data from GUS via Salesforce CLI
        </div>
    </div>
</body>
</html>
"""

    return html

def main():
    """Main function to generate the dashboard."""
    print("Fetching work items from GUS...")
    work_items = get_work_items()

    if not work_items:
        print("No work items found matching the criteria.")
        print(f"Build: {BUILD_VERSION}, Theme: {THEME_KEYWORD}")
        sys.exit(0)

    print(f"Found {len(work_items)} work items. Generating dashboard...")

    html_content = generate_html(work_items)

    output_file = f"industries_monthly_release_{BUILD_VERSION}_dashboard.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✓ Dashboard generated successfully!")
    print(f"  Output file: {output_file}")
    print(f"  Open it in your browser to view the dashboard.")

    # Try to open in browser
    try:
        import webbrowser
        import os
        file_path = os.path.abspath(output_file)
        webbrowser.open(f"file://{file_path}")
        print(f"\n  Opening dashboard in browser...")
    except:
        pass

if __name__ == "__main__":
    main()
