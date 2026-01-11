# Google Tasks Dashboard Implementation Plan

## 1. Analysis of Current Tagging System
The current `gtasks_cli` project uses a bracket-based tagging system:
- **Format**: `[TAG_NAME]` (e.g., `[FE]`, `[urgent]`, `[PDEP]`).
- **Extraction**: The `gtasks_cli.utils.tag_extractor` module extracts these tags from:
  - Task Title
  - Task Description
  - Task Notes
- **Storage**: Tags are aggregated into a list in the `Task` model.
- **Reporting**: The `OrganizedTasksReport` uses a `category_groups` configuration to map specific tags (like "FE", "p1") to Categories (like "Functional Tags", "Priority").

## 2. Dashboard Requirement Analysis
The new dashboard requirement introduces a hierarchical visualization:
- **Structure**: Category -> Tag -> Tasks.
- **Visuals**: D3.js Force Graph (Category/Tag nodes) + DataTables (Task List).
- **New Tagging Style**: The requirement specifically mentions `#` (e.g., `#UAT`) and `@` (e.g., `@John`) style tags, distinct from the current `[]` style.
- **Mapping**: A explicit mapping dictionary is requested: `CATEGORIES = {'Team': ['@John'], ...}`.

## 3. Bridge Strategy
To implement the dashboard while respecting the existing system, the "Bridge Script" will:
1.  **Leverage Existing Data**: Use `gtasks_cli` models to fetch and represent tasks.
2.  **Hybrid Tag Parsing**: Support **both** the existing `[]` tags and the requested `#/@` tags.
    - We will extend the extraction logic to find `#word` and `@word` in the task text.
    - This allows users to start using the new dashboard features without rewriting all their existing `[Bracket]` tags if they simply map `[FE]` syntax in the configuration.
3.  **Data Transformation**: Convert the linear list of tasks into the hierarchical JSON format required by D3.js.

## 4. Implementation Steps

### Step 1: Create `generate_dashboard.py`
We will create a script in `gtasks_cli/scripts/` (or root) that handles data fetching and HTML generation.

### Step 2: Define Configuration
The script will include the user-defined mapping:
```python
TAG_MAPPING = {
    "Team": ["@Alice", "@Bob", "[FE]", "[BE]"],  # Mixed style support
    "Status": ["#UAT", "#Defects", "[BUG]"],
    "Priority": ["#High", "[p1]"]
}
```

### Step 3: Implement Hybrid Tag Parser
Logic to scan `task.title` and `task.notes` for regex patterns:
- `r'\[([^\]]+)\]'` (Existing)
- `r'([#@]\w+)'` (New)

### Step 4: Generate HTML
The script will embed the JSON data into a template HTML file containing:
- FORCE-GRAPH library (via CDN).
- DATATABLES library (via CDN).
- Custom JS to render the graph and table.

## 5. Refined Master Prompt
*Use this prompt to generate the code, tailored to the project structure:*

```markdown
Create a Python script `generate_dashboard_html.py` for the `gtasks_cli` project.

**Context:**
- The project is at `/Users/int/Documents/workspace/projects/gtasks_automation/`.
- Core models are in `gtasks_cli.models.task`.
- Use `gtasks_cli.utils.tag_extractor` as a reference but extend it.
- **Goal:** Generate a `gtasks_dashboard.html` file.

**Requirements:**

1.  **Data Source:**
    - Load tasks using a method compatible with `gtasks_cli` (e.g., connect to the SQLite DB `tasks.db` or parse the local JSON backup).
    - If `tasks.db` is available using SQLAlchemy/SQLite, query it. Otherwise, load from `google_tasks_backup_*.json`.

2.  **Tag Parsing (Hybrid):**
    - Iterate through all tasks.
    - Extract tags looking for BOTH:
      - Bracket style: `[Tag]`
      - Hash/At style: `#Tag`, `@Tag`
    - Normalize tags (lowercase, remove symbols for matching).

3.  **Category Mapping:**
    - Implement a dictionary:
      ```python
      CATEGORY_MAPPING = {
          'Team': ['alice', 'bob', 'devteam'],
          'Production': ['live', 'hotfix'],
          'UAT': ['uat', 'bug', 'regression'],
          'Priorities': ['p1', 'urgent']
      }
      ```
    - Map extracted tags to these Categories. If a tag isn't in the mapping, put it in "Uncategorized" or ignore it based on a flag.

4.  **Graph & Table JSON:**
    - Construct a JSON object with:
      - `nodes`: Categories (Level 1) and Tags (Level 2).
      - `links`: Category <-> Tag.
      - `tasks`: Flat list of tasks with their assigned tags.
    - Calculate node sizes based on task counts.

5.  **HTML Output:**
    - Generate a single HTML file.
    - Embed the JSON data into a `<script id="data-json">` tag.
    - **Frontend:**
      - Use `force-graph` (from unpkg/dstdn) or D3.js v7.
      - Use `DataTables` (jQuery).
      - **Interaction:** Click node -> Filter DataTable (using `table.search(tag).draw()`).

**Output:**
- The Python script code.
- A brief instruction on how to run it.
```
