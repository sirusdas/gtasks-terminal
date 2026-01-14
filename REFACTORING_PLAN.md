# GTasks Automation - Refactoring Plan

## Current Issues (Based on context/rules.txt and context/architecture.md)

### 1. **Single Source of Truth Violations**
❌ **Problem**: Multiple dashboard implementations
- `gtasks_dashboard.html` (root level)
- `gtasks_dashboard/enhanced_dashboard.html`
- `gtasks_dashboard/super_enhanced_dashboard.html`
- `gtasks_dashboard/hierarchical_dashboard.py`

✅ **Solution**: Consolidate into ONE dashboard implementation
- Keep: `gtasks_dashboard/main_dashboard.py` (Flask app)
- Keep: `gtasks_dashboard/templates/dashboard.html` (single template)
- Delete: All "enhanced", "super", "hierarchical" variants

### 2. **Duplicate Data Managers**
❌ **Problem**: Multiple data manager files
- `gtasks_dashboard/data_manager.py`
- `gtasks_dashboard/enhanced_data_manager.py`

✅ **Solution**: Merge into single `gtasks_dashboard/services/data_manager.py`
- Use feature flags or configuration for "enhanced" features
- Follow: `services/` directory for business logic

### 3. **Root-Level Dashboard File**
❌ **Problem**: `gtasks_dashboard.html` at root level
- This is a standalone HTML file with embedded data
- Doesn't integrate with Flask dashboard architecture

✅ **Solution**: 
- Move to `gtasks_dashboard/templates/` if it's a template
- OR keep as a standalone static export option
- Document its purpose clearly

### 4. **Missing Modular Structure**
❌ **Problem**: `generate_dashboard.py` doesn't follow architecture
- Should be in `gtasks_dashboard/services/` or `gtasks_cli/commands/`
- Logic should be separated from HTML generation

✅ **Solution**: Refactor to:
```
gtasks_dashboard/
├── services/
│   ├── data_manager.py (single source)
│   └── dashboard_generator.py (HTML generation logic)
├── routes/
│   ├── api.py (API endpoints)
│   └── dashboard.py (page routes)
├── templates/
│   └── dashboard.html (single template)
└── main_dashboard.py (Flask app entry point)
```

## Implementation Steps

### Phase 1: Audit & Document
1. ✅ Review all dashboard files and their purposes
2. ✅ Identify unique features in each variant
3. ✅ Document which features to keep

### Phase 2: Consolidation
1. Merge all data manager logic into `services/data_manager.py`
2. Merge all dashboard features into single template
3. Use configuration flags for optional features

### Phase 3: Cleanup
1. Delete duplicate files:
   - `enhanced_dashboard.html`
   - `super_enhanced_dashboard.html`
   - `enhanced_data_manager.py`
   - `super_enhanced_main_dashboard.py`
2. Move `generate_dashboard.py` to proper location
3. Update imports across the project

### Phase 4: Documentation Update
1. Update `context/architecture.md` with new structure
2. Update README files
3. Add migration guide for users

## File Actions Required

### Files to DELETE:
```
gtasks_dashboard/enhanced_dashboard.html
gtasks_dashboard/super_enhanced_dashboard.html
gtasks_dashboard/enhanced_data_manager.py
gtasks_dashboard/super_enhanced_main_dashboard.py
gtasks_dashboard/hierarchical_dashboard.py
gtasks_dashboard/*.log (all log files)
```

### Files to CONSOLIDATE:
```
gtasks_dashboard/data_manager.py + enhanced_data_manager.py
  → gtasks_dashboard/services/data_manager.py

gtasks_dashboard/main_dashboard.py + super_enhanced_main_dashboard.py
  → gtasks_dashboard/main_dashboard.py (with feature flags)
```

### Files to MOVE:
```
generate_dashboard.py (root)
  → gtasks_dashboard/services/dashboard_generator.py

gtasks_dashboard.html (root)
  → gtasks_dashboard/templates/static_dashboard.html
  OR keep as standalone export option
```

## Configuration-Based Features

Instead of multiple files, use configuration:

```python
# gtasks_dashboard/config.py
class DashboardConfig:
    # Feature flags
    ENABLE_HIERARCHICAL_VIEW = True
    ENABLE_PRIORITY_SYSTEM = True
    ENABLE_ADVANCED_FILTERING = True
    
    # UI Options
    THEME = "modern"  # or "classic"
    GRAPH_LIBRARY = "force-graph"  # or "d3"
```

## Benefits of This Refactoring

1. ✅ **Single Source of Truth**: One dashboard implementation
2. ✅ **Maintainability**: Easier to update and debug
3. ✅ **Modularity**: Clear separation of concerns
4. ✅ **Extensibility**: Add features via configuration, not duplication
5. ✅ **Follows Rules**: Adheres to context/rules.txt principles

## Next Steps

1. **Review this plan** with the user
2. **Get approval** for file deletions
3. **Execute consolidation** in phases
4. **Update context/architecture.md** to reflect new structure
5. **Run `ctx save`** to version-control the changes
