#!/usr/bin/env python3
"""
RCM (Regulated Content Management) Dashboard Generator
Queries GUS for RCM project work items and generates an interactive HTML dashboard
Tracks: Epics, Bugs, Technical Debt, and overall project progress
"""

import json
import subprocess
import sys
from datetime import datetime
from collections import defaultdict

# Configuration
TARGET_ORG = "anawal-gus"
RCM_KEYWORDS = [
    "RCM",
    "Revenue Cloud",
    "Revenue Management"
]
BUILD_FILTERS = ["262", "264"]  # Target builds to track

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

def get_rcm_work_items():
    """Fetch all RCM-related work items for LifeSciences teams."""
    # Build keyword search condition
    keyword_conditions = " OR ".join([f"Subject__c LIKE '%{keyword}%'" for keyword in RCM_KEYWORDS])

    # Build version filter condition
    build_conditions = " OR ".join([f"Scheduled_Build_Name__c LIKE '{build}%'" for build in BUILD_FILTERS])

    # Team filter
    team_filter = "(Scrum_Team__r.Name = 'LifeSciences-Ahsoka' OR Scrum_Team__r.Name = 'LifeSciences-Skywalker')"

    query = f"""
        SELECT Id, Name, Subject__c, Status__c, Type__c, Story_Points__c,
               Assignee__r.Name, Assignee__r.Email,
               Product_Tag__r.Name, Scheduled_Build_Name__c,
               Theme__r.Name, Priority__c, QA_Engineer__r.Name,
               Details__c, CreatedDate, LastModifiedDate, Found_in_Build__c,
               Scrum_Team__r.Name
        FROM ADM_Work__c
        WHERE ({keyword_conditions})
          AND ({build_conditions})
          AND {team_filter}
          AND (Type__c LIKE '%Epic%' OR Type__c LIKE '%Bug%')
          AND Status__c != 'Never'
          AND CreatedDate >= 2024-01-01T00:00:00Z
        ORDER BY Priority__c DESC, Status__c, Type__c, Name
        LIMIT 1000
    """
    return run_sf_query(query)

def categorize_items(work_items):
    """Categorize work items into Epics, Bugs, and TDs."""
    epics = []
    bugs = []
    tds = []
    others = []

    for item in work_items:
        item_type = (item.get("Type__c") or "").lower()
        subject = (item.get("Subject__c") or "").lower()

        if "epic" in item_type or "program" in item_type:
            epics.append(item)
        elif "bug" in item_type or "defect" in item_type:
            bugs.append(item)
        elif "tech debt" in subject or "technical debt" in subject or "td" in item_type or item_type == "technical debt":
            tds.append(item)
        else:
            others.append(item)

    return epics, bugs, tds, others

def categorize_by_build(work_items):
    """Categorize work items by build version."""
    by_build = defaultdict(list)

    for item in work_items:
        build = item.get("Scheduled_Build_Name__c", "Unknown")
        by_build[build].append(item)

    return by_build

def calculate_statistics(work_items):
    """Calculate comprehensive statistics."""
    stats = {
        'total': len(work_items),
        'by_status': defaultdict(int),
        'by_type': defaultdict(int),
        'by_priority': defaultdict(int),
        'by_assignee': defaultdict(int),
        'by_product_tag': defaultdict(int),
        'by_theme': defaultdict(int),
        'total_points': 0,
        'completed_points': 0,
        'in_progress_points': 0,
    }

    for item in work_items:
        status = item.get("Status__c", "Unknown")
        item_type = item.get("Type__c", "Unknown")
        priority = item.get("Priority__c", "Unknown")
        assignee = item.get("Assignee__r", {}).get("Name", "Unassigned") if item.get("Assignee__r") else "Unassigned"
        product_tag = item.get("Product_Tag__r", {}).get("Name", "No Tag") if item.get("Product_Tag__r") else "No Tag"
        theme = item.get("Theme__r", {}).get("Name", "No Theme") if item.get("Theme__r") else "No Theme"
        points = item.get("Story_Points__c", 0) or 0

        stats['by_status'][status] += 1
        stats['by_type'][item_type] += 1
        stats['by_priority'][priority] += 1
        stats['by_assignee'][assignee] += 1
        stats['by_product_tag'][product_tag] += 1
        stats['by_theme'][theme] += 1
        stats['total_points'] += points

        if status in ['Closed', 'Fixed']:
            stats['completed_points'] += points
        elif status in ['In Progress', 'Ready for Review', 'QA In Progress']:
            stats['in_progress_points'] += points

    return stats

def generate_html(work_items, epics, bugs, tds, others):
    """Generate comprehensive HTML dashboard."""

    # Calculate statistics for all items (treating as epics)
    all_stats = calculate_statistics(work_items)

    # Calculate completion percentage
    completion_pct = 0
    if all_stats['total_points'] > 0:
        completion_pct = (all_stats['completed_points'] / all_stats['total_points']) * 100

    # Status colors - clean and subtle
    status_colors = {
        "New": "#718096",
        "Triaged": "#4299e1",
        "In Progress": "#f6ad55",
        "Ready for Review": "#4299e1",
        "Fixed": "#48bb78",
        "QA In Progress": "#38b2ac",
        "Closed": "#48bb78",
        "Waiting": "#ed8936",
        "Integrate": "#9f7aea",
        "Pending Release": "#d69e2e",
        "Never": "#f56565"
    }

    # Priority colors - clean and subtle
    priority_colors = {
        "P0": "#f56565",
        "P1": "#ed8936",
        "P2": "#ecc94b",
        "P3": "#48bb78",
        "P4": "#a0aec0"
    }

    # Categorize by build
    by_build = categorize_by_build(work_items)
    build_stats = {build: calculate_statistics(items) for build, items in by_build.items()}

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RCM Project Dashboard - Regulated Content Management</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f7fa;
            padding: 0;
            margin: 0;
            color: #2c3e50;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            min-height: 100vh;
        }}

        .header {{
            background: white;
            border-bottom: 1px solid #e1e8ed;
            padding: 30px 40px;
        }}

        .header h1 {{
            font-size: 2em;
            margin-bottom: 8px;
            color: #1a202c;
            font-weight: 600;
        }}

        .header .subtitle {{
            font-size: 1em;
            color: #718096;
            margin-bottom: 5px;
        }}

        .header .timestamp {{
            margin-top: 10px;
            font-size: 0.85em;
            color: #a0aec0;
        }}

        .filter-section {{
            background: #fafbfc;
            padding: 20px 40px;
            border-bottom: 1px solid #e1e8ed;
            display: flex;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
        }}

        .filter-label {{
            font-size: 0.9em;
            font-weight: 500;
            color: #718096;
        }}

        .filter-buttons {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .filter-btn {{
            padding: 8px 20px;
            border: 1px solid #cbd5e0;
            background: white;
            color: #4a5568;
            border-radius: 6px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.9em;
        }}

        .filter-btn:hover {{
            background: #f7fafc;
            border-color: #4299e1;
        }}

        .filter-btn.active {{
            background: #4299e1;
            color: white;
            border-color: #4299e1;
        }}

        .build-badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 0.75em;
            font-weight: 500;
        }}

        .build-262 {{
            background: #ebf8ff;
            color: #2c5282;
            border: 1px solid #bee3f8;
        }}

        .build-264 {{
            background: #faf5ff;
            color: #6b46c1;
            border: 1px solid #e9d8fd;
        }}

        .progress-section {{
            background: white;
            padding: 30px 40px;
            border-bottom: 1px solid #e1e8ed;
        }}

        .progress-container {{
            max-width: 800px;
            margin: 0 auto;
        }}

        .progress-label {{
            font-size: 1em;
            font-weight: 500;
            color: #4a5568;
            margin-bottom: 12px;
        }}

        .progress-bar-container {{
            background: #f7fafc;
            border-radius: 8px;
            height: 40px;
            border: 1px solid #e1e8ed;
            overflow: hidden;
            position: relative;
        }}

        .progress-bar {{
            height: 100%;
            background: #48bb78;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 0.95em;
            transition: width 1s ease-in-out;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 15px;
            padding: 30px 40px;
            background: #fafbfc;
            border-bottom: 1px solid #e1e8ed;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e1e8ed;
            text-align: center;
            transition: all 0.2s;
        }}

        .stat-card:hover {{
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            transform: translateY(-2px);
        }}

        .stat-card .number {{
            font-size: 2.5em;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 8px;
        }}

        .stat-card.epic .number {{
            color: #805ad5;
        }}

        .stat-card.bug .number {{
            color: #f56565;
        }}

        .stat-card.td .number {{
            color: #ed8936;
        }}

        .stat-card .label {{
            font-size: 0.85em;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 500;
        }}

        .stat-card .sublabel {{
            font-size: 0.8em;
            color: #a0aec0;
            margin-top: 4px;
        }}

        .section {{
            padding: 30px 40px;
            border-top: 1px solid #e1e8ed;
            background: white;
        }}

        .section h2 {{
            font-size: 1.3em;
            margin-bottom: 20px;
            color: #2d3748;
            font-weight: 600;
        }}

        .section h2.epic-header {{
            color: #805ad5;
        }}

        .section h2.bug-header {{
            color: #f56565;
        }}

        .section h2.td-header {{
            color: #ed8936;
        }}

        .chart-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .chart-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e1e8ed;
        }}

        .chart-card h3 {{
            font-size: 1em;
            margin-bottom: 15px;
            color: #4a5568;
            font-weight: 600;
        }}

        .chart-canvas {{
            max-height: 300px;
            margin: 0 auto;
        }}

        .work-item-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            background: white;
            border: 1px solid #e1e8ed;
            border-radius: 8px;
            overflow: hidden;
        }}

        .work-item-table th {{
            background: #f7fafc;
            color: #4a5568;
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.8em;
            letter-spacing: 0.3px;
            border-bottom: 2px solid #e1e8ed;
        }}

        .work-item-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #f7fafc;
            font-size: 0.9em;
        }}

        .work-item-table tr:hover {{
            background: #fafbfc;
        }}

        .work-item-id {{
            font-weight: 600;
            color: #4299e1;
        }}

        .work-item-id a {{
            color: #4299e1;
            text-decoration: none;
        }}

        .work-item-id a:hover {{
            text-decoration: underline;
        }}

        .badge {{
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.75em;
            font-weight: 500;
            display: inline-block;
        }}

        .badge-status {{
            color: white;
        }}

        .badge-priority {{
            color: white;
        }}

        .badge-type {{
            background: #edf2f7;
            color: #4a5568;
        }}

        .footer {{
            padding: 20px 40px;
            text-align: center;
            background: #fafbfc;
            color: #a0aec0;
            font-size: 0.85em;
            border-top: 1px solid #e1e8ed;
        }}

        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}

            .chart-container {{
                grid-template-columns: 1fr;
            }}

            .work-item-table {{
                font-size: 0.85em;
            }}

            .work-item-table th,
            .work-item-table td {{
                padding: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 RCM Project Dashboard</h1>
            <div class="subtitle">Regulated Content Management - Project Overview</div>
            <div class="timestamp">Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</div>
        </div>

        <div class="filter-section">
            <span class="filter-label">Filter by Build:</span>
            <div class="filter-buttons">"""

    # Add only 262 and 264 filter buttons
    for build_num in BUILD_FILTERS:
        matching_builds = [b for b in by_build.keys() if build_num in str(b)]
        if matching_builds:
            count = sum(len(by_build[b]) for b in matching_builds)
            active_class = "active" if build_num == "262" else ""
            html += f"""
                <button class="filter-btn {active_class}" data-build="{build_num}" onclick="filterByBuild('{build_num}')">
                    Build {build_num} ({count})
                </button>"""

    html += """
            </div>
        </div>

        <div class="progress-section">
            <div class="progress-container">
                <div class="progress-label">Overall Project Completion: {completion_pct:.1f}%</div>
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: {completion_pct}%;">
                        {all_stats['completed_points']:.0f} / {all_stats['total_points']:.0f} pts
                    </div>
                </div>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card epic">
                <div class="number">{all_stats['total']}</div>
                <div class="label">Total Items</div>
            </div>
            <div class="stat-card">
                <div class="number">{all_stats['total_points']:.0f}</div>
                <div class="label">Story Points</div>
            </div>
            <div class="stat-card">
                <div class="number">{all_stats['by_status'].get('In Progress', 0)}</div>
                <div class="label">In Progress</div>
            </div>
            <div class="stat-card">
                <div class="number">{all_stats['by_status'].get('Closed', 0)}</div>
                <div class="label">Completed</div>
            </div>
        </div>
"""

    # Epic section - Show all epics (not just categorized ones)
    html += """
        <div class="section">
            <h2 class="epic-header">🎯 Epics</h2>
            <table class="work-item-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Subject</th>
                        <th>Build</th>
                        <th>Status</th>
                        <th>Priority</th>
                        <th>Assignee</th>
                        <th>Points</th>
                    </tr>
                </thead>
                <tbody>
"""
    # Show all work items as epics since we're focusing on epic-level
    for epic in work_items[:200]:  # Show up to 200 items
            work_id = epic.get("Name", "")
            subject = epic.get("Subject__c", "No subject")
            status = epic.get("Status__c", "Unknown")
            priority = epic.get("Priority__c", "Unknown")
            assignee = epic.get("Assignee__r", {}).get("Name", "Unassigned") if epic.get("Assignee__r") else "Unassigned"
            points = epic.get("Story_Points__c", 0) or 0
            build = epic.get("Scheduled_Build_Name__c", "Unknown") or "Unknown"
            gus_url = f"https://gus.lightning.force.com/lightning/r/ADM_Work__c/{epic['Id']}/view"
            status_color = status_colors.get(status, "#6c757d")
            priority_color = priority_colors.get(priority, "#6c757d")

            build_class = ""
            if "262" in build:
                build_class = "build-262"
            elif "264" in build:
                build_class = "build-264"

            html += f"""
                    <tr class="work-item-row" data-build="{build}">
                        <td class="work-item-id"><a href="{gus_url}" target="_blank">{work_id}</a></td>
                        <td>{subject[:100] if len(subject) <= 100 else subject[:100] + '...'}</td>
                        <td><span class="build-badge {build_class}">{build}</span></td>
                        <td><span class="badge badge-status" style="background: {status_color};">{status}</span></td>
                        <td><span class="badge badge-priority" style="background: {priority_color};">{priority}</span></td>
                        <td>{assignee}</td>
                        <td><strong>{int(points)}</strong></td>
                    </tr>
"""
    html += """
                </tbody>
            </table>
        </div>
"""

    html += """
        <div class="footer">
            Generated by RCM Dashboard Generator | Data from GUS via Salesforce CLI
        </div>
    </div>

    <script>
        function filterByBuild(build) {{
            document.querySelectorAll('.filter-btn').forEach(btn => {{
                btn.classList.remove('active');
                if (btn.dataset.build === build) {{
                    btn.classList.add('active');
                }}
            }});

            const rows = document.querySelectorAll('.work-item-row');
            rows.forEach(row => {{
                const rowBuild = row.dataset.build;
                if (rowBuild.includes(build)) {{
                    row.style.display = '';
                }} else {{
                    row.style.display = 'none';
                }}
            }});
        }}

        // Apply default filter on page load
        window.addEventListener('DOMContentLoaded', function() {{
            filterByBuild('262');
        }});
    </script>
</body>
</html>
"""

    return html

def main():
    """Main function to generate the RCM dashboard."""
    print("Fetching RCM work items from GUS...")
    work_items = get_rcm_work_items()

    if not work_items:
        print("No RCM work items found.")
        sys.exit(0)

    print(f"Found {len(work_items)} RCM work items. Categorizing...")

    epics, bugs, tds, others = categorize_items(work_items)

    print(f"  Epics: {len(epics)}")
    print(f"  Bugs: {len(bugs)}")
    print(f"  Technical Debt: {len(tds)}")
    print(f"  Others: {len(others)}")
    print("\nGenerating dashboard...")

    html_content = generate_html(work_items, epics, bugs, tds, others)

    output_file = "rcm_dashboard.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✓ RCM Dashboard generated successfully!")
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
