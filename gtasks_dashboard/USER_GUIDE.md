# GTasks Unified Dashboard - User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Feature Guide](#feature-guide)
4. [Navigation](#navigation)
5. [Filtering and Search](#filtering-and-search)
6. [Task Management](#task-management)
7. [Reports and Analytics](#reports-and-analytics)
8. [Settings](#settings)
9. [Tips and Best Practices](#tips-and-best-practices)
10. [Keyboard Shortcuts](#keyboard-shortcuts)
11. [FAQ](#faq)

## Getting Started

### Accessing the Dashboard
1. **Start the Dashboard**: Run `python3 unified_dashboard_with_api.py`
2. **Open Browser**: Navigate to `http://localhost:8087`
3. **Welcome Screen**: The dashboard will display an overview with all features

### First Time Setup
- The dashboard automatically detects your GTasks accounts
- Real-time data sync happens every 60 seconds
- Settings are automatically saved

### Navigation Basics
- **Left Menu**: Navigate between different views
- **Header**: Account selector, filters, and settings
- **Main Content**: The active feature's interface

## Dashboard Overview

### Main Dashboard
The home page provides:
- **Statistics Cards**: Total, completed, pending, in-progress, deleted, overdue, high priority, critical, and recurring tasks
- **Quick Charts**: Task status and priority distribution
- **Recent Tasks**: Latest tasks with priority indicators
- **Feature Status**: All 9 features are integrated and functional

### Status Cards Explained
- **Total Tasks**: All tasks across all accounts
- **Completed Tasks**: Tasks marked as done
- **Pending Tasks**: Tasks waiting to be started
- **In Progress Tasks**: Currently active tasks
- **Deleted Tasks**: Soft-deleted tasks (if enabled)
- **Overdue Tasks**: Past due date tasks
- **High+ Priority**: Critical and high priority tasks
- **Critical Tasks**: Only critical priority tasks
- **Recurring Tasks**: Tasks with recurrence rules

### Quick Charts
- **Status Distribution**: Pie chart of task statuses
- **Priority Distribution**: Pie chart of calculated priorities

## Feature Guide

### 1. Account Type Filtering
**What it does**: Filter tasks by account categories (Work, Personal, Learning, etc.)

**How to use**:
1. Click the filter button in the header (📋 icon)
2. Select one or more account types
3. Tasks will be filtered to show only those from selected account types
4. Use "Clear All" to reset filters

**Examples**:
- Select "Work" to see only work-related tasks
- Select "Work" + "Learning" to see work and learning tasks
- Select "All" to see tasks from all account types

### 2. Advanced Tag Filtering
**What it does**: Sophisticated tag filtering with logical operations

**Syntax**:
- **OR**: `tag1|tag2` - Tasks with tag1 OR tag2
- **AND**: `tag1&tag2` - Tasks with tag1 AND tag2  
- **NOT**: `tag1 -tag2` - Tasks with tag1 but NOT tag2

**Examples**:
- `work|urgent` - Tasks tagged with "work" OR "urgent"
- `api&frontend` - Tasks tagged with both "api" AND "frontend"
- `work -urgent` - Tasks tagged with "work" but NOT "urgent"
- `backend api -production` - Tasks with "backend" AND "api" but NOT "production"

**Tag Formats Supported**:
- `[bracket tags]`: `[urgent]`, `[P1]`, `[***]`
- `#hashtag tags`: `#work`, `#api`, `#frontend`
- `@user tags`: `@john`, `@alice`, `@team`

### 3. Deleted Tasks Management
**What it does**: Safely delete and restore tasks

**Features**:
- **Soft Delete**: Tasks are marked as deleted but can be restored
- **Settings Toggle**: Show/hide deleted tasks in views
- **Restore**: Bring back deleted tasks
- **Permanent Delete**: Completely remove tasks

**How to use**:
1. Enable "Show Deleted Tasks" in Settings
2. Deleted tasks appear with strikethrough styling
3. Use the delete/restore buttons in task actions
4. Permanently delete from the Deleted Tasks page

### 4. Enhanced Task Management
**What it does**: Comprehensive task operations

**Features**:
- **Create**: Add new tasks with priority and tags
- **Edit**: Modify task details, priorities, and tags
- **Status Management**: Change between pending, in-progress, completed
- **Bulk Operations**: Select multiple tasks for batch operations
- **Project Assignment**: Organize tasks by projects

**How to use**:
1. Click "Add Task" to create new tasks
2. Use dropdown menus to change status
3. Select multiple tasks for bulk actions
4. Use the project filter to organize tasks

### 5. Reports Integration
**What it does**: Generate comprehensive reports

**Report Types**:
- **Summary Report**: Overall statistics and completion rates
- **Priority Analysis**: Breakdown of tasks by priority level
- **Account Performance**: Performance metrics by account
- **Export**: Download data in JSON format

**How to use**:
1. Navigate to the Reports page
2. Select report type from dropdown
3. Apply filters as needed
4. View results or export data

### 6. Hierarchical Visualization
**What it does**: Interactive visualization of task relationships

**Structure**: Priority → Category → Tag → Tasks

**How to use**:
1. Navigate to Hierarchy page
2. Interactive graph with zoom and pan
3. Click nodes to see details
4. Use "Reset Zoom" to return to full view

**Node Types**:
- **Priority Nodes**: Fire/Alert icons with priority levels
- **Category Nodes**: Category names with task counts
- **Tag Nodes**: Individual tags with usage counts
- **Task Nodes**: Individual tasks with status indicators

### 7. Left Menu Show/Hide
**What it does**: Toggle sidebar visibility

**Features**:
- **Click**: Menu button in header to show/hide
- **Keyboard**: Ctrl+M or Cmd+M shortcut
- **Animation**: Smooth sliding transition
- **Persistence**: Remember preference across sessions

### 8. Tasks Due Today Dashboard
**What it does**: Focus on tasks due today with time grouping

**Features**:
- **Time Groups**: Morning (6-12), Afternoon (12-18), Evening (18-24)
- **Priority Indicators**: Visual priority badges
- **Cross-Feature Integration**: Works with all filters

**How to use**:
1. Navigate to "Tasks Due Today" page
2. View tasks grouped by time slots
3. Use filters to narrow down tasks
4. Complete tasks directly from this view

### 9. Priority System Enhancement
**What it does**: Automatic priority calculation from asterisk patterns

**Priority Levels**:
- **🔥 Critical**: 6+ asterisks (`[******]`, `[*******urgent]`)
- **⚠️ High**: 4-5 asterisks (`[****]`, `[*****important]`)
- **📋 Medium**: 3 asterisks (`[***]`, `[***review]`)
- **📝 Low**: 1-2 asterisks (`[**]`, `[*optional]`)

**How it works**:
1. System scans task titles, descriptions, and tags
2. Counts asterisk patterns (`*`, `**`, `***`, etc.)
3. Calculates priority based on pattern length
4. Displays priority throughout the dashboard

**Priority Indicators**:
- **Visual Badges**: Color-coded priority badges on tasks
- **Status Integration**: Priority shown in all views
- **Filter Integration**: Filter tasks by priority level
- **Statistics**: Priority distribution in dashboard

## Navigation

### Left Menu Items
- **📊 Dashboard**: Main overview and statistics
- **📅 Tasks Due Today**: Today's tasks with time grouping
- **📋 Task Management**: Complete task operations
- **🌳 Hierarchy**: Interactive task visualization
- **🔥 Priority System**: Priority calculation and monitoring
- **📈 Reports**: Analytics and reporting
- **🗑️ Deleted Tasks**: Deleted task management
- **👥 Accounts**: Account management and switching

### Header Elements
- **Menu Button**: Toggle left sidebar
- **Account Filter**: Multi-select account type filtering
- **Settings**: Dashboard preferences
- **Account Selector**: Switch between accounts
- **Feature Status**: Shows all 9 features are integrated

### Keyboard Navigation
- **Ctrl/Cmd + M**: Toggle menu
- **Ctrl/Cmd + /**: Search tasks
- **Ctrl/Cmd + S**: Save changes
- **Escape**: Close modals and dropdowns
- **Tab**: Navigate between elements

## Filtering and Search

### Quick Search
- **Global Search**: Type in the search box to find tasks
- **Real-time**: Results update as you type
- **Scope**: Searches title and description fields

### Advanced Filtering
- **Status Filter**: All Status, Pending, Completed, In Progress
- **Priority Filter**: Critical, High, Medium, Low
- **Account Filter**: Filter by specific accounts
- **Project Filter**: Filter by project assignments
- **Deleted Filter**: Active Only, Include Deleted, Deleted Only
- **Tag Filter**: Advanced tag filtering with OR/AND/NOT

### Filter Combinations
- **Multi-Filter**: Use multiple filters together
- **Filter Persistence**: Filters are remembered during session
- **Filter Reset**: Clear filters to show all tasks
- **Filter Indicators**: Visual indicators show active filters

### Search Tips
- **Use Quotes**: "exact phrase" for exact matches
- **Wildcards**: Use * for partial matches
- **Case Insensitive**: Search is case-insensitive
- **Special Characters**: Search works with special characters and emojis

## Task Management

### Creating Tasks
**Method 1: Add Task Button**
1. Click "Add Task" in any task view
2. Fill in title (required)
3. Add description, priority, due date
4. Add tags using #hashtag, @user, [bracket] formats
5. Click "Add Task" to save

**Method 2: Quick Add**
- Type task directly in search bar and press Enter
- System creates basic task with your input

### Task Properties
- **Title**: Task name (required)
- **Description**: Detailed task information
- **Priority**: Manual priority setting
- **Due Date**: Task deadline
- **Tags**: Multiple tag formats supported
- **Project**: Project assignment
- **Status**: Current task state
- **Created Date**: Auto-generated timestamp
- **Account**: Which account the task belongs to

### Task Status Workflow
1. **Pending**: Task is created and waiting to be started
2. **In Progress**: Task is currently being worked on
3. **Completed**: Task is finished
4. **Deleted**: Task is soft-deleted (if enabled)

### Priority Integration
- **Manual Override**: You can set priority manually
- **Automatic Calculation**: System calculates from asterisk patterns
- **Priority Source**: Shows whether priority is manual or calculated
- **Priority Indicators**: Visual badges throughout interface

### Tag Management
**Supported Formats**:
- **Bracket Tags**: `[urgent]`, `[P1]`, `[***]`
- **Hashtag Tags**: `#work`, `#api`, `#frontend`
- **User Tags**: `@john`, `@alice`, `@team`
- **Mixed Formats**: You can use all formats together

**Examples**:
- `Implement #API endpoint for @john #UAT [***important]`
- `Fix critical #Bug in #Frontend @alice [****P0]`
- `#Feature: Dark mode [***review] @bob`

### Project Organization
- **Project Assignment**: Assign tasks to projects
- **Project Filtering**: Filter tasks by project
- **Project Statistics**: View project completion rates
- **Cross-Project**: Tasks can have multiple projects

## Reports and Analytics

### Summary Report
**Provides**:
- Total tasks across all accounts
- Completion rates and statistics
- Priority distribution breakdown
- Account performance metrics

**How to use**:
1. Navigate to Reports page
2. Select "Summary Report"
3. View comprehensive statistics
4. Export data if needed

### Priority Analysis
**Provides**:
- Breakdown of tasks by priority level
- Priority source analysis (manual vs calculated)
- Asterisk pattern statistics
- Priority trends over time

**Use Cases**:
- Understanding task urgency distribution
- Identifying tasks that need priority review
- Analyzing priority calculation effectiveness

### Account Performance
**Provides**:
- Performance metrics by account
- Completion rates per account
- Task distribution analysis
- Account-specific statistics

**Use Cases**:
- Comparing productivity across accounts
- Identifying accounts needing attention
- Account planning and resource allocation

### Export Functionality
**Export Formats**:
- **JSON**: Complete data export for analysis
- **Filtered Data**: Export only filtered results

**Export Contents**:
- All task data with metadata
- Account information
- Priority calculations
- Tag relationships
- Settings and preferences

## Settings

### Dashboard Settings
**Show Deleted Tasks**:
- **On**: Deleted tasks visible throughout dashboard
- **Off**: Deleted tasks hidden (default)
- **Impact**: Affects all views and statistics

**Priority System**:
- **On**: Automatic priority calculation enabled
- **Off**: Manual priority only
- **Impact**: Affects priority badges and statistics

**Auto Refresh**:
- **On**: Dashboard updates every 60 seconds
- **Off**: Manual refresh only
- **Impact**: Affects real-time data updates

**Theme**:
- **Light**: Light theme (default)
- **Dark**: Dark theme (coming soon)

**Notifications**:
- **On**: Enable browser notifications
- **Off**: Disable notifications

**Default View**:
- **Dashboard**: Start on main dashboard
- **Tasks**: Start on task management
- **Hierarchy**: Start on hierarchy view

**Compact View**:
- **On**: Dense task list display
- **Off**: Comfortable spacing

**Menu Settings**:
- **Menu Visible**: Show sidebar by default
- **Menu Animation**: Enable menu slide animations
- **Keyboard Shortcuts**: Enable keyboard shortcuts

**Advanced Features**:
- **Advanced Filters**: Enable advanced filtering
- **Reports**: Enable reporting features

### Settings Persistence
- **Auto-Save**: Settings save automatically
- **JSON File**: Settings stored in `unified_dashboard_settings.json`
- **Session Memory**: Settings apply immediately
- **Backup**: Settings backup with application

## Tips and Best Practices

### Task Creation Best Practices
1. **Use Descriptive Titles**: Make titles clear and actionable
2. **Add Priority Patterns**: Use `[***]`, `[****]`, etc. for priority
3. **Use Multiple Tags**: Combine #hashtag, @user, [bracket] formats
4. **Set Due Dates**: Add deadlines to stay organized
5. **Assign Projects**: Organize related tasks together

### Priority System Tips
1. **Asterisk Patterns**: Use consistent asterisk patterns
   - `[***]`: Medium priority
   - `[****]`: High priority  
   - `[*****]`: Critical priority
   - `[******]`: Emergency priority

2. **Context-Aware**: Include context in brackets
   - `[***review]`: Medium priority, needs review
   - `[****urgent]`: High priority, urgent
   - `[*****production]`: Critical priority, production issue

3. **Priority Source**: Monitor priority calculations
   - Manual priorities override calculated ones
   - Calculated priorities update automatically
   - Source indicator shows how priority was set

### Tagging Best Practices
1. **Consistent Naming**: Use consistent tag names
   - `#work` not `Work`
   - `@john` not `John`

2. **Hierarchical Tags**: Organize tags logically
   - `#frontend/api`: Specific work area
   - `#backend/database`: Backend database work

3. **Context Tags**: Add context with tags
   - `#urgent` vs `#routine`
   - `#high-impact` vs `#low-impact`

4. **Team Coordination**: Use @mentions for team tasks
   - `@alice`: Task for Alice
   - `@team`: Team-wide task

### Filtering Efficiency
1. **Combine Filters**: Use multiple filters together
2. **Save Filtered Views**: Bookmark frequently used filters
3. **Use Tag Filters**: Leverage advanced tag filtering
4. **Account Organization**: Use account types for organization

### Organization Strategies
1. **Project Organization**: Group related tasks by project
2. **Priority Workflow**: Use priority levels for work planning
3. **Account Segmentation**: Separate work types with account types
4. **Regular Review**: Use reports for regular task review

### Performance Tips
1. **Filter Efficiently**: Use specific filters to reduce data load
2. **Limit Date Ranges**: Use reasonable date ranges
3. **Regular Cleanup**: Delete completed or obsolete tasks
4. **Use Hierarchy**: Navigate complex relationships visually

## Keyboard Shortcuts

### Global Shortcuts
- **Ctrl/Cmd + M**: Toggle left menu
- **Ctrl/Cmd + /**: Focus search box
- **Ctrl/Cmd + S**: Save current changes
- **Escape**: Close modals, dropdowns
- **Ctrl/Cmd + R**: Refresh dashboard
- **Ctrl/Cmd + ,**: Open settings

### Navigation Shortcuts
- **Ctrl/Cmd + 1**: Dashboard
- **Ctrl/Cmd + 2**: Tasks Due Today
- **Ctrl/Cmd + 3**: Task Management
- **Ctrl/Cmd + 4**: Hierarchy
- **Ctrl/Cmd + 5**: Priority System
- **Ctrl/Cmd + 6**: Reports
- **Ctrl/Cmd + 7**: Deleted Tasks
- **Ctrl/Cmd + 8**: Accounts

### Task Management Shortcuts
- **Ctrl/Cmd + N**: New task
- **Ctrl/Cmd + E**: Edit selected task
- **Ctrl/Cmd + D**: Delete selected task
- **Ctrl/Cmd + C**: Complete selected task
- **Space**: Toggle task completion
- **Enter**: Edit selected task

### Filter Shortcuts
- **Ctrl/Cmd + F**: Focus tag filter
- **Ctrl/Cmd + B**: Toggle account filter
- **Ctrl/Cmd + P**: Focus priority filter
- **Ctrl/Cmd + S**: Focus status filter
- **Ctrl/Cmd + A**: Select all tasks

### View Shortcuts
- **Ctrl/Cmd + +**: Zoom in hierarchy
- **Ctrl/Cmd + -**: Zoom out hierarchy
- **Ctrl/Cmd + 0**: Reset hierarchy zoom
- **Ctrl/Cmd + H**: Toggle hierarchy visibility

## FAQ

### General Questions

**Q: How do I start using the dashboard?**
A: Simply run `python3 unified_dashboard_with_api.py` and open `http://localhost:8087` in your browser. The system automatically detects your GTasks accounts and loads data.

**Q: Do I need to install anything else?**
A: Only the GTasks CLI if you want real data. The dashboard works with demo data if GTasks CLI isn't available.

**Q: How often does the data update?**
A: Data updates automatically every 60 seconds, or you can refresh manually.

### Task Management

**Q: How do I create a task with priority?**
A: Add asterisk patterns in brackets like `[***]`, `[****]`, `[*****]` in the task title, description, or tags.

**Q: Can I bulk edit tasks?**
A: Yes, select multiple tasks and use the bulk action menu to change status, priority, or tags.

**Q: How do I restore a deleted task?**
A: Enable "Show Deleted Tasks" in Settings, then use the restore button on deleted tasks.

### Filtering and Search

**Q: What does "work|urgent" filter do?**
A: It shows tasks tagged with either "work" OR "urgent" (OR operation).

**Q: How do I exclude tasks with a certain tag?**
A: Use the NOT operation: `tag1 -tag2` shows tasks with tag1 but not tag2.

**Q: Can I save my filter settings?**
A: Filters are remembered during your session. For permanent saving, use the advanced filtering and bookmark the URL.

### Priority System

**Q: How does the priority calculation work?**
A: The system counts asterisks in brackets: `[***]` = 3 asterisks = Medium priority, `[****]` = 4 asterisks = High priority, etc.

**Q: Can I override calculated priorities?**
A: Yes, manually set priorities override calculated ones. The priority source indicator shows how each priority was set.

**Q: What if my asterisk pattern isn't recognized?**
A: Ensure asterisks are in brackets: `[***]`, not just `***`. The system looks for asterisk patterns within square brackets.

### Performance

**Q: The dashboard is slow with many tasks. What can I do?**
A: Use specific filters to reduce visible tasks, enable compact view, or consider archiving old completed tasks.

**Q: How many tasks can the dashboard handle?**
A: The dashboard is optimized for hundreds to thousands of tasks. For very large datasets, use filtering to improve performance.

### Technical

**Q: Can I run this on a different port?**
A: Yes, modify the port in the Python script or use command line arguments.

**Q: How do I backup my settings?**
A: Settings are automatically saved to `unified_dashboard_settings.json`. Copy this file to backup your preferences.

**Q: Can I access this from another computer?**
A: By default, it's localhost only. Configure network access in the settings or run on a server for remote access.

### Troubleshooting

**Q: My tasks aren't showing up. What's wrong?**
A: Check that GTasks CLI is installed and configured. The dashboard will fall back to demo data if no real data is found.

**Q: Priority calculations seem wrong. How do I fix this?**
A: Verify asterisk patterns are in brackets `[***]`, not loose asterisks `***`. Check the priority source indicator.

**Q: Tag filtering isn't working as expected. What should I check?**
A: Ensure you're using the correct syntax: `tag1|tag2` (OR), `tag1&tag2` (AND), `tag1 -tag2` (NOT).

**Q: The hierarchy view isn't loading. What should I do?**
A: Check that JavaScript is enabled in your browser and that you're not blocking scripts. The hierarchy requires D3.js to function.

---

## Support

For additional help:
1. Check the [COMPREHENSIVE_DEPLOYMENT_GUIDE.md](./COMPREHENSIVE_DEPLOYMENT_GUIDE.md) for technical details
2. Run `python3 integration_tests.py` to verify functionality
3. Check browser console for JavaScript errors
4. Review server logs for backend issues

**Happy task managing with GTasks Unified Dashboard! 🎉**