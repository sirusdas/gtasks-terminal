#!/usr/bin/env python3
"""
Dashboard Generator for Google Tasks
Parses tasks, extracts tags (both style #/@ and []), and generates an HTML dashboard.
"""

import sys
import os
import json
import re
from datetime import datetime

# Configure Path to access gtasks_cli
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gtasks_cli', 'src'))

try:
    from gtasks_cli.storage.sqlite_storage import SQLiteStorage
    from gtasks_cli.utils.tag_extractor import extract_tags_from_text
except ImportError as e:
    print(f"Error importing gtasks_cli modules: {e}")
    sys.exit(1)

# Default DB Path (can be overridden)
DB_PATH = os.path.join(current_dir, 'gtasks_cli', 'tasks.db')

# Mapping Configuration
# Defines the Level 1 (Keys) and Level 2 (Value Lists) hierarchy.
# You can add both #/@ tags and [bracket] tags here.
CATEGORY_MAPPING = {
    'Team': ['@Alice', '@Bob', '@DevTeam', '@John', '@Sara', '@Mike'],
    'Status': ['#UAT', '#Defects', '#Bug', '#Regression', '#Live', '#Hotfix', '#In-Progress', 'pending'],
    'Workstream': ['#CR', '#Production', '#Enhancement', '[FE]', '[BE]', '[PDEP]', '[DEP]'],
    'Priority': ['#High', '#Urgent', '[p1]', '[p2]', '*****'],
    'Timeline': ['today', 'tomorrow', 'this-week', '[DEL-T]']
}

def get_mapping_category(tag):
    """Find which category a tag belongs to."""
    tag_lower = tag.lower()
    for category, tags in CATEGORY_MAPPING.items():
        # Check if tag matches any in the list (case insensitive)
        for map_tag in tags:
            if map_tag.lower() == tag_lower:
                return category
    return "Other"

def extract_all_tags(text):
    """Extracts #tags, @tags, and [tags] from text."""
    if not text:
        return []
    
    tags = []
    
    # 1. Extract # and @ tags (alphanumeric + hyphen/underscore)
    # Examples: #UAT, @John, #CR-2024
    social_tags = re.findall(r'([#@][\w-]+)', text)
    tags.extend(social_tags)
    
    # 2. Extract Bracket tags (FULL bracket string)
    # Examples: [FE], [DEL-T]
    bracket_tags = re.findall(r'(\[[^\]]+\])', text)
    tags.extend(bracket_tags)
    
    return list(set(tags))

def generate_dashboard():
    print(f"Connecting to database at {DB_PATH}...")
    if not os.path.exists(DB_PATH):
        print("Warning: Database not found. Trying default location...")
        storage = SQLiteStorage() # uses default
    else:
        storage = SQLiteStorage(storage_path=DB_PATH)
        
    tasks = storage.load_tasks()
    print(f"Loaded {len(tasks)} tasks map DB.")
    
    if len(tasks) == 0:
        # Try to load from backup JSON
        json_files = [f for f in os.listdir(current_dir) if f.startswith('google_tasks_backup_') and f.endswith('.json')]
        if json_files:
            json_files.sort(reverse=True) # Get newest
            backup_file = os.path.join(current_dir, json_files[0])
            print(f"Database empty. Loading from backup file: {backup_file}")
            
            try:
                with open(backup_file, 'r') as f:
                    data = json.load(f)
                    
                for tasklist in data.get('tasklists', []):
                    list_name = tasklist.get('title', 'Unknown List')
                    for t in tasklist.get('tasks', []):
                        # Normalize task dict to match what we expect
                        t['list_name'] = list_name
                        # Ensure fields exist
                        if 'tags' not in t: t['tags'] = []
                        if 'description' not in t: t['description'] = ""
                        if 'notes' not in t: t['notes'] = ""
                        if 'status' not in t: t['status'] = "pending"
                        tasks.append(t)
                        
                print(f"Loaded {len(tasks)} tasks from JSON backup.")
            except Exception as e:
                print(f"Error loading backup JSON: {e}")

    
    # --- Data Processing ---
    
    # Structure for D3 Graph
    # Nodes: { id: "Category" or "Tag", group: 1 or 2, val: size }
    # Links: { source: "Category", target: "Tag" }
    
    nodes_map = {} # id -> node object
    links = []
    
    # Initialize Category Nodes (Level 1)
    for cat in CATEGORY_MAPPING.keys():
        nodes_map[cat] = {"id": cat, "group": 1, "val": 20} # Base size for categories
        
    nodes_map["Other"] = {"id": "Other", "group": 1, "val": 10}
    
    # Process Tasks
    processed_tasks = []
    
    tag_counts = {} # tag -> count
    
    for task in tasks:
        # Combine text fields for searching
        full_text = f"{task['title']} {task.get('description') or ''} {task.get('notes') or ''}"
        
        found_tags = extract_all_tags(full_text)
        
        # If no specific tags found, check for simple keyword matches from the mapping (fallback)
        # e.g. if mapping has 'today' (no hash), check for word 'today'
        for cat, map_tags in CATEGORY_MAPPING.items():
            for map_tag in map_tags:
                if not re.match(r'^[@#\[]', map_tag): # It's a plain word like 'today' or 'pending'
                    if re.search(r'\b' + re.escape(map_tag) + r'\b', full_text, re.IGNORECASE):
                        if map_tag not in found_tags:
                            found_tags.append(map_tag)

        # Assign task to tags
        task_tags_for_display = []
        
        for tag in found_tags:
            category = get_mapping_category(tag)
            
            # Ensure Tag Node exists (Level 2)
            if tag not in nodes_map:
                nodes_map[tag] = {"id": tag, "group": 2, "val": 0, "category": category}
                # Link Tag to Category
                links.append({"source": category, "target": tag})
            
            # Increment tag count (size)
            nodes_map[tag]["val"] += 1
            task_tags_for_display.append(tag)
            
        # Add to processed list
        due_date = task['due']
        if isinstance(due_date, datetime):
            due_date = due_date.strftime('%Y-%m-%d')
        elif due_date and 'T' in due_date:
             due_date = due_date.split('T')[0]
             
        processed_tasks.append({
            "id": task['id'],
            "title": task['title'],
            "list": task.get('list_name', 'Default'),
            "tags": task_tags_for_display,
            "due": due_date,
            "status": task['status']
        })

    # Convert nodes map to list
    nodes = list(nodes_map.values())
    
    graph_data = {
        "nodes": nodes,
        "links": links
    }
    
    full_data = {
        "graph": graph_data,
        "tasks": processed_tasks
    }
    
    # --- HTML Generation ---
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Tasks Dashboard</title>
    
    <script src="https://code.jquery.com/jquery-3.7.0.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <script src="https://unpkg.com/force-graph"></script>
    
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
    
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        #dashboard-container {{ display: flex; flex-direction: column; gap: 20px; max-width: 1200px; margin: 0 auto; }}
        
        .card {{ background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 20px; overflow: hidden; }}
        
        #graph-container {{ height: 500px; width: 100%; }}
        
        h1 {{ margin-top: 0; color: #333; }}
        .header-controls {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
        
        button#reset-filter {{ background-color: #4285f4; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }}
        button#reset-filter:hover {{ background-color: #3367d6; }}
        
        .tag-pill {{ display: inline-block; background: #e0e0e0; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-right: 4px; }}
    </style>
</head>
<body>

<div id="dashboard-container">
    <div class="card">
        <div class="header-controls">
            <h1>Project Executive View</h1>
            <button id="reset-filter">Reset Filter</button>
        </div>
        <div id="graph-container"></div>
        <p style="text-align: center; color: #666; font-size: 0.9em;">Click a node to filter the table below.</p>
    </div>

    <div class="card">
        <h2>Task Execution View</h2>
        <table id="tasks-table" class="display" style="width:100%">
            <thead>
                <tr>
                    <th>Title</th>
                    <th>List</th>
                    <th>Tags</th>
                    <th>Due Date</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
            </tbody>
        </table>
    </div>
</div>

<script>
    // Embedded Data
    const DATA = {json.dumps(full_data)};
    
    $(document).ready(function() {{
        // Initialize DataTable
        const table = $('#tasks-table').DataTable({{
            data: DATA.tasks,
            columns: [
                {{ data: 'title' }},
                {{ data: 'list' }},
                {{ 
                    data: 'tags',
                    render: function(data) {{
                        return data.map(t => `<span class="tag-pill">${{t}}</span>`).join('');
                    }}
                }},
                {{ data: 'due', defaultContent: "" }},
                {{ data: 'status' }}
            ],
            order: [[3, 'asc']] // Sort by Due Date by default
        }});
        
        // Initialize Force Graph
        const Graph = ForceGraph()
            (document.getElementById('graph-container'))
            .graphData(DATA.graph)
            .nodeLabel('id')
            .nodeColor(node => node.group === 1 ? '#4285f4' : '#ea4335') // Blue for Categories, Red for Tags
            .nodeVal('val')
            .linkWidth(1)
            .onNodeClick(node => {{
                // Filter Table on Click
                if (node.group === 2) {{ // Tag Node
                    // Search for the tag in the Tags column (index 2)
                    // We stick to simple text search
                    table.column(2).search(node.id).draw();
                    console.log("Filtering by tag:", node.id);
                }} else if (node.group === 1) {{ // Category Node
                    // Filter for any tag belonging to this category ?? 
                    // For now, let's just clear or maybe filter by implicit logic.
                    // Let's keep it simple: Click category -> Show all tasks involved in that category?
                    // Implementation: Find all child tags of this node and join them with OR
                    
                    // We need to find links where source.id === node.id
                    // Note: ForceGraph modifies links to be objects, so link.source is the node object.
                    
                    const childTags = DATA.graph.links
                        .filter(l => l.source.id === node.id || l.source === node)
                        .map(l => (l.target.id || l.target).replace(/[.*+?^${{}}()|[\]\\\\]/g, '\\\\$&')); // escape regex
                    
                    if (childTags.length > 0) {{
                       const searchStr = childTags.join('|');
                       table.column(2).search(searchStr, true, false).draw(); // Regex search
                    }}
                }}
                
                Graph.centerAt(node.x, node.y, 1000);
                Graph.zoom(2, 1000);
            }});
            
        // Reset Filter
        $('#reset-filter').click(function() {{
            table.search('').columns().search('').draw();
            Graph.zoomToFit(1000);
        }});
    }});
</script>

</body>
</html>
    """
    
    output_path = os.path.join(current_dir, 'gtasks_dashboard.html')
    with open(output_path, 'w') as f:
        f.write(html_content)
        
    print(f"Dashboard generated successfully at: {output_path}")

if __name__ == "__main__":
    generate_dashboard()
