# GTasks Dashboard - Implementation Guide

## Overview
This guide provides step-by-step instructions to refactor the gtasks_dashboard to follow the Single Source of Truth principle and modular architecture defined in `context/rules.txt` and `context/architecture.md`.

## Current State Analysis

### Existing Files (Violating Rules)
```
❌ gtasks_dashboard.html (root) - Standalone HTML with embedded data
❌ gtasks_dashboard/enhanced_dashboard.html - Duplicate dashboard
❌ gtasks_dashboard/super_enhanced_dashboard.html - Another duplicate
❌ gtasks_dashboard/enhanced_data_manager.py - Duplicate data manager
❌ gtasks_dashboard/super_enhanced_main_dashboard.py - Duplicate main file
❌ gtasks_dashboard/hierarchical_dashboard.py - Yet another variant
```

### Target Structure (Following Rules)
```
✅ gtasks_dashboard/
   ├── main_dashboard.py (Single Flask app entry point)
   ├── config.py (Feature flags and configuration)
   ├── services/
   │   ├── data_manager.py (Single data manager)
   │   └── dashboard_generator.py (Static export generator)
   ├── routes/
   │   ├── api.py (REST API endpoints)
   │   └── dashboard.py (Page routes)
   ├── templates/
   │   ├── dashboard.html (Main template)
   │   └── static_export.html (Optional standalone export)
   ├── modules/
   │   ├── priority_system.py
   │   ├── tag_manager.py
   │   ├── account_manager.py
   │   └── settings_manager.py
   └── ui_components.py
```

## Implementation Steps

### Step 1: Backup Current State
```bash
# Create a backup branch
cd /Users/int/Documents/workspace/projects/gtasks_automation
git checkout -b backup-before-refactor
git add .
git commit -m "Backup before dashboard refactoring"
git checkout main
```

### Step 2: Consolidate Data Managers

**Action**: Merge `data_manager.py` and `enhanced_data_manager.py`

**File**: `gtasks_dashboard/services/data_manager.py`

**Key Features to Include**:
1. Task CRUD operations
2. Tag extraction (hybrid: @user, #tag, [bracket])
3. Category mapping
4. Hierarchical data generation for D3.js
5. DataTable data formatting
6. Multi-account support
7. Priority calculation
8. Statistics generation

**Configuration Flags** (in `config.py`):
```python
ENABLE_ADVANCED_FILTERING = True
ENABLE_PRIORITY_SYSTEM = True
ENABLE_HIERARCHICAL_VIEW = True
```

### Step 3: Consolidate Main Dashboard

**Action**: Merge all dashboard variants into single `main_dashboard.py`

**File**: `gtasks_dashboard/main_dashboard.py`

**Features**:
- Flask app initialization
- Blueprint registration
- Feature flag loading from config
- Conditional route registration based on flags
- Error handling
- Logging setup

### Step 4: Create Single Dashboard Template

**Action**: Consolidate all HTML templates

**File**: `gtasks_dashboard/templates/dashboard.html`

**Features**:
- Responsive layout
- Force-Graph visualization
- DataTables integration
- Tag filtering
- Priority highlighting
- Account switching
- Settings panel

**Conditional Rendering**:
```html
{% if config.ENABLE_HIERARCHICAL_VIEW %}
    <!-- Hierarchical graph view -->
{% endif %}

{% if config.ENABLE_PRIORITY_SYSTEM %}
    <!-- Priority indicators -->
{% endif %}
```

### Step 5: Move Static Export Generator

**Action**: Move `generate_dashboard.py` to proper location

**From**: `/Users/int/Documents/workspace/projects/gtasks_automation/generate_dashboard.py`
**To**: `gtasks_dashboard/services/dashboard_generator.py`

**Purpose**: Generate standalone HTML file for offline viewing

**Usage**:
```bash
# From CLI
gtasks dashboard export --output gtasks_dashboard.html

# Or directly
python -m gtasks_dashboard.services.dashboard_generator
```

### Step 6: Handle Root-Level Dashboard File

**Decision Required**: What to do with `gtasks_dashboard.html` at root?

**Option A**: Keep as static export output
```
gtasks_dashboard.html (root) - Generated output from dashboard_generator.py
```

**Option B**: Move to templates
```
gtasks_dashboard/templates/static_export.html - Template for static export
```

**Recommendation**: Option A - Keep as generated output, add to `.gitignore`

### Step 7: Update Configuration

**File**: `gtasks_dashboard/config.py`

```python
class DashboardConfig:
    """Dashboard configuration with feature flags"""
    
    # Feature Flags
    ENABLE_HIERARCHICAL_VIEW = True
    ENABLE_PRIORITY_SYSTEM = True
    ENABLE_ADVANCED_FILTERING = True
    ENABLE_TAG_MANAGEMENT = True
    ENABLE_MULTI_ACCOUNT = True
    
    # UI Configuration
    THEME = "modern"  # "modern" or "classic"
    GRAPH_LIBRARY = "force-graph"  # "force-graph" or "d3"
    TABLE_LIBRARY = "datatables"  # "datatables" or "ag-grid"
    
    # Data Configuration
    DEFAULT_CATEGORY_MAPPING = {
        'Team': ['@alice', '@bob', '@john'],
        'Status': ['#uat', '#bug', '#pending'],
        'Priority': ['[p1]', '[urgent]', '#high'],
        'Timeline': ['today', 'tomorrow', 'this-week']
    }
    
    # Performance
    CACHE_ENABLED = True
    CACHE_TTL = 300  # seconds
```

### Step 8: Update Tag Manager

**File**: `gtasks_dashboard/modules/tag_manager.py`

**Features**:
- Hybrid tag extraction: `@user`, `#tag`, `[bracket]`
- Tag normalization
- Category mapping
- Tag statistics

**Example**:
```python
class HybridTagManager:
    """Manages hybrid tag extraction and categorization"""
    
    TAG_PATTERNS = {
        'user': r'@(\w+)',
        'hash': r'#(\w+)',
        'bracket': r'\[([^\]]+)\]'
    }
    
    def extract_tags(self, text: str) -> List[str]:
        """Extract all tag types from text"""
        tags = []
        for pattern in self.TAG_PATTERNS.values():
            tags.extend(re.findall(pattern, text))
        return tags
    
    def categorize_tag(self, tag: str) -> str:
        """Map tag to category using config"""
        for category, tag_list in config.DEFAULT_CATEGORY_MAPPING.items():
            if tag.lower() in [t.lower() for t in tag_list]:
                return category
        return 'Other'
```

### Step 9: Delete Duplicate Files

**Files to Delete**:
```bash
# Dashboard duplicates
rm gtasks_dashboard/enhanced_dashboard.html
rm gtasks_dashboard/super_enhanced_dashboard.html
rm gtasks_dashboard/hierarchical_dashboard.py

# Data manager duplicates
rm gtasks_dashboard/enhanced_data_manager.py

# Main file duplicates
rm gtasks_dashboard/super_enhanced_main_dashboard.py

# Log files (should be in .gitignore)
rm gtasks_dashboard/*.log

# Test files (move to tests/ directory)
mv gtasks_dashboard/test_*.py gtasks_dashboard/tests/
```

### Step 10: Update Imports

**Search and Replace**:
```bash
# Find all imports of old modules
grep -r "from enhanced_data_manager" gtasks_dashboard/
grep -r "import enhanced_data_manager" gtasks_dashboard/

# Replace with new imports
# from enhanced_data_manager import X
# → from gtasks_dashboard.services.data_manager import X
```

### Step 11: Update Documentation

**Files to Update**:
1. `gtasks_dashboard/README.md` - Update architecture section
2. `context/architecture.md` - Already updated ✅
3. `DASHBOARD_IMPLEMENTATION_PLAN.md` - Mark as completed
4. Create `gtasks_dashboard/MIGRATION_GUIDE.md` - For users upgrading

### Step 12: Testing

**Test Checklist**:
- [ ] Dashboard loads without errors
- [ ] All features work with flags enabled
- [ ] All features disabled when flags are off
- [ ] Static export generates correctly
- [ ] Tag extraction works for all formats
- [ ] Category mapping works correctly
- [ ] Multi-account switching works
- [ ] Priority system calculates correctly

**Test Commands**:
```bash
# Run dashboard
python gtasks_dashboard/main_dashboard.py

# Generate static export
python -m gtasks_dashboard.services.dashboard_generator

# Run tests
pytest gtasks_dashboard/tests/
```

### Step 13: Update Context and Commit

```bash
# Update context
# (Manual step: Review and update context/architecture.md if needed)

# Stage changes
git add .

# Commit with descriptive message
git commit -m "Refactor: Consolidate dashboard to single source of truth

- Merged all dashboard variants into main_dashboard.py
- Consolidated data managers into services/data_manager.py
- Moved generate_dashboard.py to services/dashboard_generator.py
- Added feature flags in config.py
- Updated tag manager for hybrid tag support
- Deleted duplicate files (enhanced_*, super_enhanced_*)
- Updated architecture.md to reflect new structure

Follows principles from context/rules.txt:
- Single Source of Truth
- Modular Architecture
- Configuration-Driven Features"

# Save context
# ctx save (if using context-llemur)
```

## Migration Guide for Users

### If You Were Using `enhanced_dashboard.html`:
All features are now in the main dashboard with feature flags. Enable them in `config.py`:
```python
ENABLE_ADVANCED_FILTERING = True
ENABLE_PRIORITY_SYSTEM = True
```

### If You Were Using `super_enhanced_main_dashboard.py`:
Use the main dashboard with all flags enabled:
```python
# In config.py
ENABLE_HIERARCHICAL_VIEW = True
ENABLE_PRIORITY_SYSTEM = True
ENABLE_ADVANCED_FILTERING = True
```

### If You Were Using `generate_dashboard.py`:
Now located at `gtasks_dashboard/services/dashboard_generator.py`
```bash
# Old way
python generate_dashboard.py

# New way
python -m gtasks_dashboard.services.dashboard_generator
```

## Benefits of This Refactoring

1. ✅ **Single Source of Truth**: One dashboard, one data manager
2. ✅ **Easier Maintenance**: Update once, works everywhere
3. ✅ **Better Testing**: Test one implementation thoroughly
4. ✅ **Cleaner Codebase**: No duplicate logic
5. ✅ **Flexible Configuration**: Enable/disable features as needed
6. ✅ **Follows Best Practices**: Adheres to project coding rules

## Troubleshooting

### Issue: Import errors after refactoring
**Solution**: Update all imports to use new module paths

### Issue: Missing features
**Solution**: Check feature flags in `config.py`

### Issue: Static export not working
**Solution**: Ensure `dashboard_generator.py` is in `services/` directory

## Next Steps

1. Review this implementation guide
2. Execute steps 1-13 in order
3. Test thoroughly
4. Update documentation
5. Commit changes
6. Run `ctx save` to version-control the context

## Questions to Resolve

1. Should `gtasks_dashboard.html` (root) be kept as generated output or moved?
2. Are there any unique features in the duplicate files that need special handling?
3. Should we create a migration script to help users transition?
