#!/usr/bin/env python3
"""
RCM (Revenue Cloud Management) Dashboard Generator
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
    """Fetch all RCM-related work items."""
    # Build keyword search condition
    keyword_conditions = " OR ".join([f"Subject__c LIKE '%{keyword}%'" for keyword in RCM_KEYWORDS])

    query = f"""
        SELECT Id, Name, Subject__c, Status__c, Type__c, Story_Points__c,
               Assignee__r.Name, Assignee__r.Email,
               Product_Tag__r.Name, Scheduled_Build_Name__c,
               Theme__r.Name, Priority__c, QA_Engineer__r.Name,
               Details__c, CreatedDate, LastModifiedDate, Found_in_Build__c
        FROM ADM_Work__c
        WHERE ({keyword_conditions})
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

    # Calculate statistics
    all_stats = calculate_statistics(work_items)
    epic_stats = calculate_statistics(epics)
    bug_stats = calculate_statistics(bugs)
    td_stats = calculate_statistics(tds)

    # Calculate completion percentage
    completion_pct = 0
    if all_stats['total_points'] > 0:
        completion_pct = (all_stats['completed_points'] / all_stats['total_points']) * 100

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

    # Priority colors
    priority_colors = {
        "P0": "#dc3545",
        "P1": "#fd7e14",
        "P2": "#ffc107",
        "P3": "#28a745",
        "P4": "#6c757d"
    }

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RCM Project Dashboard - Revenue Cloud Management</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%);
            padding: 20px;
            color: #333;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        .header .subtitle {{
            font-size: 1.3em;
            opacity: 0.95;
            margin-bottom: 5px;
        }}

        .header .timestamp {{
            margin-top: 15px;
            font-size: 0.95em;
            opacity: 0.85;
        }}

        .progress-section {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 40px;
            border-bottom: 3px solid #1e3c72;
        }}

        .progress-container {{
            max-width: 800px;
            margin: 0 auto;
        }}

        .progress-label {{
            font-size: 1.5em;
            font-weight: bold;
            color: #1e3c72;
            margin-bottom: 15px;
            text-align: center;
        }}

        .progress-bar-container {{
            background: white;
            border-radius: 50px;
            height: 60px;
            box-shadow: inset 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
            position: relative;
        }}

        .progress-bar {{
            height: 100%;
            background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
            border-radius: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 1.3em;
            transition: width 1s ease-in-out;
            box-shadow: 0 2px 8px rgba(40, 167, 69, 0.4);
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}

        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            text-align: center;
            transition: all 0.3s;
            border-top: 4px solid #1e3c72;
        }}

        .stat-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        }}

        .stat-card.epic {{
            border-top-color: #7e22ce;
        }}

        .stat-card.bug {{
            border-top-color: #dc3545;
        }}

        .stat-card.td {{
            border-top-color: #ffc107;
        }}

        .stat-card .number {{
            font-size: 3.5em;
            font-weight: bold;
            color: #1e3c72;
            margin-bottom: 10px;
        }}

        .stat-card.epic .number {{
            color: #7e22ce;
        }}

        .stat-card.bug .number {{
            color: #dc3545;
        }}

        .stat-card.td .number {{
            color: #ffc107;
        }}

        .stat-card .label {{
            font-size: 1.05em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }}

        .stat-card .sublabel {{
            font-size: 0.85em;
            color: #999;
            margin-top: 5px;
        }}

        .section {{
            padding: 40px;
            border-top: 1px solid #e9ecef;
        }}

        .section h2 {{
            font-size: 2em;
            margin-bottom: 25px;
            color: #1e3c72;
            border-left: 5px solid #1e3c72;
            padding-left: 20px;
        }}

        .section h2.epic-header {{
            border-left-color: #7e22ce;
            color: #7e22ce;
        }}

        .section h2.bug-header {{
            border-left-color: #dc3545;
            color: #dc3545;
        }}

        .section h2.td-header {{
            border-left-color: #ffc107;
            color: #ffc107;
        }}

        .chart-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }}

        .chart-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        .chart-card h3 {{
            font-size: 1.3em;
            margin-bottom: 20px;
            color: #495057;
            text-align: center;
            font-weight: 600;
        }}

        .chart-canvas {{
            max-height: 350px;
            margin: 0 auto;
        }}

        .work-item-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .work-item-table th {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 0.5px;
        }}

        .work-item-table td {{
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
        }}

        .work-item-table tr:hover {{
            background: #f8f9fa;
        }}

        .work-item-id {{
            font-weight: bold;
            color: #1e3c72;
        }}

        .work-item-id a {{
            color: #1e3c72;
            text-decoration: none;
        }}

        .work-item-id a:hover {{
            text-decoration: underline;
        }}

        .badge {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            display: inline-block;
        }}

        .badge-status {{
            color: white;
        }}

        .badge-priority {{
            color: white;
        }}

        .badge-type {{
            background: #e9ecef;
            color: #495057;
        }}

        .footer {{
            padding: 25px;
            text-align: center;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            color: #666;
            font-size: 0.95em;
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
            <div class="subtitle">Revenue Cloud Management - Project Overview</div>
            <div class="timestamp">Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</div>
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
            <div class="stat-card">
                <div class="number">{all_stats['total']}</div>
                <div class="label">Total Items</div>
            </div>
            <div class="stat-card epic">
                <div class="number">{len(epics)}</div>
                <div class="label">Epics</div>
                <div class="sublabel">{epic_stats['total_points']:.0f} points</div>
            </div>
            <div class="stat-card bug">
                <div class="number">{len(bugs)}</div>
                <div class="label">Bugs</div>
                <div class="sublabel">{all_stats['by_status'].get('Closed', 0)} closed</div>
            </div>
            <div class="stat-card td">
                <div class="number">{len(tds)}</div>
                <div class="label">Tech Debt</div>
                <div class="sublabel">{td_stats['total_points']:.0f} points</div>
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

        <div class="section">
            <h2>📊 Analytics Overview</h2>
            <div class="chart-container">
                <div class="chart-card">
                    <h3>Status Distribution</h3>
                    <canvas id="statusPieChart" class="chart-canvas"></canvas>
                </div>
                <div class="chart-card">
                    <h3>Work Item Types</h3>
                    <canvas id="typeDoughnutChart" class="chart-canvas"></canvas>
                </div>
                <div class="chart-card">
                    <h3>Priority Breakdown</h3>
                    <canvas id="priorityBarChart" class="chart-canvas"></canvas>
                </div>
                <div class="chart-card">
                    <h3>Team Workload (Top 10)</h3>
                    <canvas id="assigneeBarChart" class="chart-canvas"></canvas>
                </div>
            </div>
        </div>
"""

    # Epic section
    if epics:
        html += """
        <div class="section">
            <h2 class="epic-header">🎯 Epics Progress</h2>
            <table class="work-item-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Subject</th>
                        <th>Status</th>
                        <th>Priority</th>
                        <th>Assignee</th>
                        <th>Points</th>
                    </tr>
                </thead>
                <tbody>
"""
        for epic in epics[:50]:  # Limit to 50 items
            work_id = epic.get("Name", "")
            subject = epic.get("Subject__c", "No subject")
            status = epic.get("Status__c", "Unknown")
            priority = epic.get("Priority__c", "Unknown")
            assignee = epic.get("Assignee__r", {}).get("Name", "Unassigned") if epic.get("Assignee__r") else "Unassigned"
            points = epic.get("Story_Points__c", 0) or 0
            gus_url = f"https://gus.lightning.force.com/lightning/r/ADM_Work__c/{epic['Id']}/view"
            status_color = status_colors.get(status, "#6c757d")
            priority_color = priority_colors.get(priority, "#6c757d")

            html += f"""
                    <tr>
                        <td class="work-item-id"><a href="{gus_url}" target="_blank">{work_id}</a></td>
                        <td>{subject[:80]}...</td>
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

    # Bug section
    if bugs:
        html += """
        <div class="section">
            <h2 class="bug-header">🐛 Bug Tracking</h2>
            <table class="work-item-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Subject</th>
                        <th>Status</th>
                        <th>Priority</th>
                        <th>Assignee</th>
                        <th>Found In</th>
                    </tr>
                </thead>
                <tbody>
"""
        for bug in bugs[:50]:  # Limit to 50 items
            work_id = bug.get("Name", "")
            subject = bug.get("Subject__c", "No subject")
            status = bug.get("Status__c", "Unknown")
            priority = bug.get("Priority__c", "Unknown")
            assignee = bug.get("Assignee__r", {}).get("Name", "Unassigned") if bug.get("Assignee__r") else "Unassigned"
            found_in = bug.get("Found_in_Build__c", "N/A") or "N/A"
            gus_url = f"https://gus.lightning.force.com/lightning/r/ADM_Work__c/{bug['Id']}/view"
            status_color = status_colors.get(status, "#6c757d")
            priority_color = priority_colors.get(priority, "#6c757d")

            html += f"""
                    <tr>
                        <td class="work-item-id"><a href="{gus_url}" target="_blank">{work_id}</a></td>
                        <td>{subject[:80]}...</td>
                        <td><span class="badge badge-status" style="background: {status_color};">{status}</span></td>
                        <td><span class="badge badge-priority" style="background: {priority_color};">{priority}</span></td>
                        <td>{assignee}</td>
                        <td>{found_in}</td>
                    </tr>
"""
        html += """
                </tbody>
            </table>
        </div>
"""

    # Tech Debt section
    if tds:
        html += """
        <div class="section">
            <h2 class="td-header">⚙️ Technical Debt</h2>
            <table class="work-item-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Subject</th>
                        <th>Status</th>
                        <th>Priority</th>
                        <th>Assignee</th>
                        <th>Points</th>
                    </tr>
                </thead>
                <tbody>
"""
        for td in tds[:50]:  # Limit to 50 items
            work_id = td.get("Name", "")
            subject = td.get("Subject__c", "No subject")
            status = td.get("Status__c", "Unknown")
            priority = td.get("Priority__c", "Unknown")
            assignee = td.get("Assignee__r", {}).get("Name", "Unassigned") if td.get("Assignee__r") else "Unassigned"
            points = td.get("Story_Points__c", 0) or 0
            gus_url = f"https://gus.lightning.force.com/lightning/r/ADM_Work__c/{td['Id']}/view"
            status_color = status_colors.get(status, "#6c757d")
            priority_color = priority_colors.get(priority, "#6c757d")

            html += f"""
                    <tr>
                        <td class="work-item-id"><a href="{gus_url}" target="_blank">{work_id}</a></td>
                        <td>{subject[:80]}...</td>
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
        Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        Chart.defaults.color = '#495057';

        const pieColors = [
            '#1e3c72', '#2a5298', '#7e22ce', '#28a745', '#dc3545',
            '#ffc107', '#17a2b8', '#6c757d', '#20c997', '#fd7e14',
            '#e83e8c', '#6f42c1', '#007bff', '#343a40', '#f8f9fa'
        ];
"""

    # Prepare chart data
    status_labels = list(all_stats['by_status'].keys())
    status_data = list(all_stats['by_status'].values())
    status_bg_colors = [status_colors.get(s, '#6c757d') for s in status_labels]

    type_labels = list(all_stats['by_type'].keys())
    type_data = list(all_stats['by_type'].values())

    priority_labels = list(all_stats['by_priority'].keys())
    priority_data = list(all_stats['by_priority'].values())
    priority_bg_colors = [priority_colors.get(p, '#6c757d') for p in priority_labels]

    assignee_items = sorted(all_stats['by_assignee'].items(), key=lambda x: -x[1])[:10]
    assignee_labels = [a[0] for a in assignee_items]
    assignee_data = [a[1] for a in assignee_items]

    # Add chart scripts
    html += f"""
        // Status Pie Chart
        const statusCtx = document.getElementById('statusPieChart').getContext('2d');
        new Chart(statusCtx, {{
            type: 'pie',
            data: {{
                labels: {json.dumps(status_labels)},
                datasets: [{{
                    data: {json.dumps(status_data)},
                    backgroundColor: {json.dumps(status_bg_colors)},
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            padding: 12,
                            font: {{ size: 11 }}
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return label + ': ' + value + ' (' + percentage + '%)';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Type Doughnut Chart
        const typeCtx = document.getElementById('typeDoughnutChart').getContext('2d');
        new Chart(typeCtx, {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(type_labels)},
                datasets: [{{
                    data: {json.dumps(type_data)},
                    backgroundColor: pieColors,
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            padding: 12,
                            font: {{ size: 11 }}
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return label + ': ' + value + ' (' + percentage + '%)';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Priority Bar Chart
        const priorityCtx = document.getElementById('priorityBarChart').getContext('2d');
        new Chart(priorityCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(priority_labels)},
                datasets: [{{
                    label: 'Count',
                    data: {json.dumps(priority_data)},
                    backgroundColor: {json.dumps(priority_bg_colors)},
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{ stepSize: 1 }}
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});

        // Assignee Bar Chart
        const assigneeCtx = document.getElementById('assigneeBarChart').getContext('2d');
        new Chart(assigneeCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(assignee_labels)},
                datasets: [{{
                    label: 'Work Items',
                    data: {json.dumps(assignee_data)},
                    backgroundColor: 'rgba(30, 60, 114, 0.8)',
                    borderColor: 'rgba(30, 60, 114, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    x: {{
                        beginAtZero: true,
                        ticks: {{ stepSize: 1 }}
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
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
