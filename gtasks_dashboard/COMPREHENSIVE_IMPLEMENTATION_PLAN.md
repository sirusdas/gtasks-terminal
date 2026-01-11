# GTasks Dashboard - Comprehensive Implementation Plan

## Executive Summary

This document outlines a complete overhaul of the GTasks Dashboard to fix critical multi-account implementation issues and implement all terminal features in the browser with enhanced UI/UX and the new hierarchical visualization system.

## Current State Analysis

### Issues Identified

1. **Multi-Account Implementation is Incorrect**
   - Current dashboard treats task lists as "accounts" instead of using actual account directories
   - Should leverage `~/.gtasks/ACCOUNT_NAME/` structure like the CLI
   - Missing proper account switching functionality

2. **Missing Terminal Features**
   - Terminal has 20+ commands (add, list, search, view, done, delete, update, interactive, etc.)
   - Dashboard only shows basic statistics and task lists
   - No advanced filtering, searching, or task management capabilities

3. **Tagging System Needs Enhancement**
   - Current system uses `[tag]` brackets
   - Need to support new `#tag` and `@user` style tags
   - Required hierarchical mapping: `CATEGORIES = {'Team': ['@John'], ...}`

4. **Missing Hierarchical Visualization**
   - No Category -> Tag -> Tasks structure
   - Missing D3.js Force Graph implementation
   - No DataTables for advanced task listing

## Detailed Implementation Plan

### Phase 1: Fix Multi-Account Implementation

**Objective**: Implement proper multi-account support that matches the CLI behavior

**Implementation Steps**:
1. **Account Detection System**
   ```python
   def detect_accounts():
       """Detect all configured accounts from ~/.gtasks/ directory structure"""
       gtasks_dir = Path.home() / '.gtasks'
       account_dirs = [d.name for d in gtasks_dir.iterdir() 
                      if d.is_dir() and d.name != 'default']
       return account_dirs
   ```

2. **Account-Aware Data Loading**
   - Load tasks from each account's separate database
   - Implement account switching mechanism
   - Support session and global default accounts

3. **Account Management UI**
   - Account selector dropdown
   - Account statistics per account
   - Switch between accounts seamlessly

### Phase 2: Implement Hierarchical Visualization

**Objective**: Create Category -> Tag -> Tasks structure with D3.js Force Graph

**Implementation Steps**:

1. **Enhanced Tag Parser**
   ```python
   def extract_tags_hybrid(task_text):
       """Extract both [] and #/@ style tags"""
       # Existing bracket tags: [tag]
       bracket_tags = re.findall(r'\[([^\]]+)\]', task_text)
       
       # New hash/user tags: #tag, @user
       hash_tags = re.findall(r'#(\w+)', task_text)
       user_tags = re.findall(r'@(\w+)', task_text)
       
       return {
           'bracket': bracket_tags,
           'hash': hash_tags,
           'user': user_tags
       }
   ```

2. **Category Mapping System**
   ```python
   CATEGORIES = {
       'Team': ['@John', '@Alice', '@Bob'],
       'UAT': ['#UAT', '#Testing'],
       'Production': ['#Live', '#Hotfix'],
       'Priority': ['#High', '#Critical', '[p1]'],
       'Project': ['#API', '#Frontend', '#Backend']
   }
   ```

3. **D3.js Force Graph Implementation**
   - Category nodes (Level 1)
   - Tag nodes (Level 2) 
   - Task nodes (Level 3)
   - Interactive filtering on node click

4. **DataTables Integration**
   - Advanced sorting and filtering
   - Real-time search
   - Pagination
   - Export capabilities

### Phase 3: Port All Terminal Features

**Terminal Commands to Implement**:

1. **Task Management**
   - `add` - Create new tasks with full form
   - `list` - Advanced listing with filters
   - `search` - Powerful search interface
   - `view` - Detailed task view modal
   - `done` - Mark tasks complete
   - `delete` - Remove tasks
   - `update` - Edit task properties

2. **Advanced Features**
   - `interactive` mode simulation
   - Time-based filtering (today, this_week, etc.)
   - Priority and status management
   - Project organization
   - Recurring tasks support
   - Dependencies visualization

3. **Reporting & Analytics**
   - Custom report generation
   - Statistics dashboard
   - Progress tracking
   - Export capabilities

### Phase 4: Multi-Page Architecture

**Proposed Page Structure**:

1. **Dashboard Home** (`/`)
   - Overview statistics
   - Recent tasks
   - Quick actions

2. **Tasks** (`/tasks`)
   - Advanced task list with DataTables
   - Filtering and search
   - Bulk operations

3. **Hierarchy** (`/hierarchy`)
   - D3.js Force Graph
   - Category/Tag/Task visualization
   - Interactive exploration

4. **Accounts** (`/accounts`)
   - Account management
   - Account switching
   - Per-account statistics

5. **Reports** (`/reports`)
   - Custom report builder
   - Analytics dashboard
   - Export tools

6. **Settings** (`/settings`)
   - Configuration
   - Category mapping
   - Preferences

### Phase 5: Enhanced UI/UX

**Design Improvements**:

1. **Modern Interface**
   - Responsive design
   - Dark/light theme toggle
   - Accessibility compliance
   - Mobile optimization

2. **Interactive Elements**
   - Drag & drop task management
   - Keyboard shortcuts
   - Context menus
   - Real-time updates

3. **Performance Optimization**
   - Lazy loading
   - Caching strategies
   - Efficient data structures
   - WebSocket real-time updates

## Technical Architecture

### Frontend Architecture
```
src/
├── components/
│   ├── common/         # Reusable UI components
│   ├── tasks/          # Task-related components
│   ├── accounts/       # Account management
│   ├── hierarchy/      # Graph visualization
│   └── reports/        # Reporting components
├── pages/              # Main application pages
├── hooks/              # Custom React hooks
├── store/              # State management (Zustand)
├── api/                # API client layer
├── utils/              # Utility functions
└── types/              # TypeScript definitions
```

### Backend Architecture
```
server/
├── routes/
│   ├── accounts.js     # Account management
│   ├── tasks.js        # Task operations
│   ├── hierarchy.js    # Graph data
│   └── reports.js      # Reporting APIs
├── services/
│   ├── gtasks-cli.js   # CLI integration
│   ├── accounts.js     # Account handling
│   └── data-processor.js # Data transformation
└── websocket/          # Real-time updates
```

### Data Flow

1. **Account Detection**: Scan `~/.gtasks/` directories
2. **Data Loading**: Load tasks from each account's database
3. **Tag Processing**: Extract and categorize tags
4. **Graph Generation**: Create hierarchical data structure
5. **UI Rendering**: Display using D3.js and DataTables

## Implementation Timeline

### Week 1: Foundation
- [x] Analysis and planning
- [ ] Fix multi-account detection
- [ ] Implement account switching

### Week 2: Core Features
- [ ] Port basic task operations
- [ ] Implement tag parsing enhancement
- [ ] Create category mapping system

### Week 3: Visualization
- [ ] Build D3.js Force Graph
- [ ] Implement DataTables
- [ ] Create interactive filtering

### Week 4: Advanced Features
- [ ] Complete terminal feature parity
- [ ] Multi-page architecture
- [ ] Enhanced UI/UX polish

### Week 5: Testing & Polish
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Documentation and deployment

## Success Metrics

1. **Account Management**: Correctly detect and switch between all accounts
2. **Feature Parity**: All terminal commands available in browser
3. **Visualization**: Working Category->Tag->Tasks hierarchy
4. **Performance**: < 3 second load times
5. **User Experience**: Intuitive interface with good UX

## Risk Mitigation

1. **Data Loss Prevention**: Robust backup and recovery
2. **Performance**: Progressive loading and caching
3. **Compatibility**: Graceful degradation for missing features
4. **Testing**: Comprehensive testing at each phase

## Conclusion

This comprehensive plan addresses all identified issues and provides a roadmap for creating a world-class GTasks Dashboard that matches the CLI's capabilities while adding powerful visualization and modern web interface features.