# GTasks Dashboard Refactoring - Quick Start Checklist

## 📋 Pre-Flight Checklist

- [ ] Read `ANALYSIS_SUMMARY.md` for overview
- [ ] Read `STRUCTURE_COMPARISON.md` for visual understanding
- [ ] Read `DASHBOARD_REFACTORING_GUIDE.md` for detailed steps
- [ ] Backup current state (see below)

## 🚀 Quick Start Commands

### 1. Backup Current State
```bash
cd /Users/int/Documents/workspace/projects/gtasks_automation
git checkout -b backup-before-refactor
git add .
git commit -m "Backup before dashboard refactoring"
git checkout main
git checkout -b feature/dashboard-refactoring
```

### 2. Quick Audit
```bash
# List all duplicate files
find gtasks_dashboard -name "*enhanced*" -o -name "*super*"

# List all log files
find gtasks_dashboard -name "*.log"

# List test files in wrong location
find gtasks_dashboard -maxdepth 1 -name "test_*.py"
```

### 3. Create Required Directories
```bash
cd gtasks_dashboard

# Create missing directories
mkdir -p services
mkdir -p tests
mkdir -p templates

# Create __init__.py files
touch services/__init__.py
touch tests/__init__.py
touch routes/__init__.py
touch modules/__init__.py
touch models/__init__.py
```

### 4. Create Configuration File
```bash
cat > config.py << 'EOF'
"""Dashboard configuration with feature flags"""

class DashboardConfig:
    """Configuration class for dashboard features"""
    
    # Feature Flags
    ENABLE_HIERARCHICAL_VIEW = True
    ENABLE_PRIORITY_SYSTEM = True
    ENABLE_ADVANCED_FILTERING = True
    ENABLE_TAG_MANAGEMENT = True
    ENABLE_MULTI_ACCOUNT = True
    
    # UI Configuration
    THEME = "modern"
    GRAPH_LIBRARY = "force-graph"
    TABLE_LIBRARY = "datatables"
    
    # Category Mapping
    DEFAULT_CATEGORY_MAPPING = {
        'Team': ['@alice', '@bob', '@john'],
        'Status': ['#uat', '#bug', '#pending'],
        'Priority': ['[p1]', '[urgent]', '#high'],
        'Timeline': ['today', 'tomorrow', 'this-week']
    }
    
    # Performance
    CACHE_ENABLED = True
    CACHE_TTL = 300
EOF
```

### 5. Update .gitignore
```bash
cd /Users/int/Documents/workspace/projects/gtasks_automation

# Add to .gitignore
cat >> .gitignore << 'EOF'

# Dashboard generated files
gtasks_dashboard.html

# Log files
*.log
gtasks_dashboard/*.log

# Cache
__pycache__/
*.pyc
.pytest_cache/

# IDE
.vscode/
.idea/
EOF
```

## 📝 Phase-by-Phase Execution

### Phase 1: Low Risk Changes ✅

```bash
# 1. Move generate_dashboard.py
mv generate_dashboard.py gtasks_dashboard/services/dashboard_generator.py

# 2. Move test files
mv gtasks_dashboard/test_*.py gtasks_dashboard/tests/

# 3. Remove log files
rm gtasks_dashboard/*.log

# 4. Commit Phase 1
git add .
git commit -m "Phase 1: Move files to correct locations"
```

### Phase 2: Consolidate Data Managers 🔄

```bash
# This requires manual merging - see DASHBOARD_REFACTORING_GUIDE.md Step 2
# Key steps:
# 1. Copy unique features from enhanced_data_manager.py to data_manager.py
# 2. Add feature flag checks
# 3. Test thoroughly
# 4. Delete enhanced_data_manager.py

# After manual consolidation:
git add gtasks_dashboard/services/data_manager.py
git commit -m "Phase 2: Consolidate data managers"
```

### Phase 3: Consolidate Main Dashboard 🔄

```bash
# This requires manual merging - see DASHBOARD_REFACTORING_GUIDE.md Step 3
# Key steps:
# 1. Add feature flag loading to main_dashboard.py
# 2. Copy unique features from super_enhanced_main_dashboard.py
# 3. Test thoroughly
# 4. Delete super_enhanced_main_dashboard.py

# After manual consolidation:
git add gtasks_dashboard/main_dashboard.py
git commit -m "Phase 3: Consolidate main dashboard files"
```

### Phase 4: Consolidate Templates 🔄

```bash
# This requires manual merging - see DASHBOARD_REFACTORING_GUIDE.md Step 4
# Key steps:
# 1. Create templates/dashboard.html with Jinja2 conditionals
# 2. Copy unique features from all HTML variants
# 3. Test thoroughly
# 4. Delete duplicate HTML files

# After manual consolidation:
git add gtasks_dashboard/templates/
git commit -m "Phase 4: Consolidate dashboard templates"
```

### Phase 5: Final Cleanup 🧹

```bash
# Delete remaining duplicate files
cd gtasks_dashboard
rm -f enhanced_dashboard.html
rm -f super_enhanced_dashboard.html
rm -f hierarchical_dashboard.py
rm -f enhanced_data_manager.py
rm -f super_enhanced_main_dashboard.py

# Commit cleanup
git add .
git commit -m "Phase 5: Remove duplicate files"
```

### Phase 6: Update Documentation 📚

```bash
# Update context
cd /Users/int/Documents/workspace/projects/gtasks_automation

# Context already updated in context/architecture.md ✅

# Commit documentation
git add context/architecture.md
git commit -m "Phase 6: Update architecture documentation"
```

### Phase 7: Testing 🧪

```bash
# Run dashboard
cd gtasks_dashboard
python main_dashboard.py

# In another terminal, test API
curl http://localhost:5000/api/tasks

# Test static export
python -m services.dashboard_generator

# Run tests
pytest tests/
```

### Phase 8: Finalize 🎉

```bash
# Merge to main
git checkout main
git merge feature/dashboard-refactoring

# Save context (if using context-llemur)
# ctx save

# Push to remote
git push origin main
```

## ⚡ Quick Reference

### Files to Delete
```bash
gtasks_dashboard/enhanced_dashboard.html
gtasks_dashboard/super_enhanced_dashboard.html
gtasks_dashboard/hierarchical_dashboard.py
gtasks_dashboard/enhanced_data_manager.py
gtasks_dashboard/super_enhanced_main_dashboard.py
gtasks_dashboard/*.log
```

### Files to Move
```bash
generate_dashboard.py → gtasks_dashboard/services/dashboard_generator.py
gtasks_dashboard/test_*.py → gtasks_dashboard/tests/test_*.py
```

### Files to Create
```bash
gtasks_dashboard/config.py
gtasks_dashboard/services/__init__.py
gtasks_dashboard/routes/__init__.py
gtasks_dashboard/modules/__init__.py
gtasks_dashboard/models/__init__.py
gtasks_dashboard/tests/__init__.py
```

## 🔍 Verification Checklist

After each phase, verify:

- [ ] No import errors
- [ ] Dashboard loads without errors
- [ ] All features work as expected
- [ ] Tests pass
- [ ] No duplicate files remain
- [ ] Code follows rules.txt principles

## 🆘 Rollback Plan

If something goes wrong:

```bash
# Rollback to backup
git checkout backup-before-refactor

# Or rollback specific phase
git log --oneline  # Find commit hash
git revert <commit-hash>
```

## 📞 Need Help?

Refer to detailed documentation:
1. `ANALYSIS_SUMMARY.md` - What and why
2. `STRUCTURE_COMPARISON.md` - Visual comparison
3. `DASHBOARD_REFACTORING_GUIDE.md` - Detailed steps
4. `REFACTORING_PLAN.md` - High-level plan

## ✅ Success Criteria

You'll know the refactoring is complete when:

1. ✅ Only ONE main_dashboard.py exists
2. ✅ Only ONE data_manager.py exists (in services/)
3. ✅ Only ONE dashboard.html exists (in templates/)
4. ✅ No files with "enhanced" or "super" in the name
5. ✅ All features work via feature flags
6. ✅ Tests pass
7. ✅ Documentation is updated
8. ✅ context/architecture.md matches reality

## 🎯 Estimated Time

- **Phase 1**: 15 minutes (automated)
- **Phase 2**: 30-45 minutes (manual merge)
- **Phase 3**: 30-45 minutes (manual merge)
- **Phase 4**: 45-60 minutes (manual merge)
- **Phase 5**: 10 minutes (cleanup)
- **Phase 6**: 15 minutes (documentation)
- **Phase 7**: 30 minutes (testing)
- **Phase 8**: 10 minutes (finalize)

**Total**: 2.5 - 4 hours

## 💡 Pro Tips

1. **Work in phases** - Don't try to do everything at once
2. **Test after each phase** - Catch issues early
3. **Commit frequently** - Easy to rollback if needed
4. **Keep backup branch** - Safety net
5. **Use feature flags** - Gradual rollout of features

## 🚦 Status Tracking

Mark your progress:

- [ ] Phase 1: Low Risk Changes
- [ ] Phase 2: Consolidate Data Managers
- [ ] Phase 3: Consolidate Main Dashboard
- [ ] Phase 4: Consolidate Templates
- [ ] Phase 5: Final Cleanup
- [ ] Phase 6: Update Documentation
- [ ] Phase 7: Testing
- [ ] Phase 8: Finalize

---

**Ready to start? Begin with Phase 1!**
