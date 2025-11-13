# Google Tasks CLI SQLite Migration Plan

## Objective
Migrate from JSON file-based storage to SQLite database while enhancing functionality and ensuring seamless Google Tasks synchronization.

## Phase 1: Database Schema Design & Implementation

### 1.1 Finalize Database Schema
```sql
-- Tasks Table
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    due DATETIME,
    priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'critical')),
    status TEXT CHECK(status IN ('pending', 'completed', 'deleted')) DEFAULT 'pending',
    project TEXT,
    created_at DATETIME NOT NULL,
    modified_at DATETIME NOT NULL,
    completed_at DATETIME,
    tasklist_id TEXT,
    google_task_id TEXT,
    is_local BOOLEAN DEFAULT 1,
    is_synced BOOLEAN DEFAULT 0,
    last_synced DATETIME
);

-- Task Tags (Many-to-Many)
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE task_tags (
    task_id TEXT NOT NULL,
    tag_id INTEGER NOT NULL,
    FOREIGN KEY(task_id) REFERENCES tasks(id),
    FOREIGN KEY(tag_id) REFERENCES tags(id),
    PRIMARY KEY(task_id, tag_id)
);

-- Task Notes
CREATE TABLE task_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    modified_at DATETIME NOT NULL,
    FOREIGN KEY(task_id) REFERENCES tasks(id)
);

-- Task Dependencies
CREATE TABLE task_dependencies (
    task_id TEXT NOT NULL,
    depends_on TEXT NOT NULL,
    FOREIGN KEY(task_id) REFERENCES tasks(id),
    FOREIGN KEY(depends_on) REFERENCES tasks(id),
    PRIMARY KEY(task_id, depends_on)
);

-- Task History (Audit Log)
CREATE TABLE task_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    action TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    details TEXT,
    user_id TEXT,
    FOREIGN KEY(task_id) REFERENCES tasks(id)
);

-- Users (For future multi-user support)
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at DATETIME NOT NULL,
    last_login DATETIME
);

-- Task Assignments
CREATE TABLE task_assignments (
    task_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    assigned_at DATETIME NOT NULL,
    status TEXT CHECK(status IN ('pending', 'accepted', 'completed')) DEFAULT 'pending',
    FOREIGN KEY(task_id) REFERENCES tasks(id),
    FOREIGN KEY(user_id) REFERENCES users(id),
    PRIMARY KEY(task_id, user_id)
);

-- Notification Settings
CREATE TABLE notification_settings (
    user_id TEXT PRIMARY KEY,
    email_enabled BOOLEAN DEFAULT 1,
    push_enabled BOOLEAN DEFAULT 1,
    due_date_reminder_hours INTEGER DEFAULT 24,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Create necessary indexes
CREATE INDEX idx_tasks_due ON tasks(due);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_project ON tasks(project);
CREATE INDEX idx_tasks_google_id ON tasks(google_task_id);
CREATE INDEX idx_tasks_list ON tasks(tasklist_id);
CREATE INDEX idx_task_history_task ON task_history(task_id);
```

### 1.2 Implement SQLite Storage Layer
- [x] Create `sqlite_storage.py` with complete implementation (already done)
- [ ] Update `storage/__init__.py` to register SQLiteStorage as an option
- [ ] Add database migration capabilities for schema changes
- [ ] Implement data validation for SQLite operations

### 1.3 Create Data Migration Path
- [ ] Develop migration script from JSON to SQLite
- [ ] Ensure data integrity during migration
- [ ] Add rollback capability in case of migration failure

## Phase 2: Core System Integration

### 2.1 Update Task Manager
- [ ] Modify `TaskManager` to support pluggable storage
- [ ] Add configuration option for storage backend (json/sqlite)
- [ ] Update all task operations to work with SQLite
- [ ] Implement transaction handling for critical operations

### 2.2 Enhance Synchronization Logic
- [ ] Update sync manager to handle SQLite-specific queries
- [ ] Optimize sync performance with database indexing
- [ ] Implement conflict resolution strategies
- [ ] Add sync history tracking

### 2.3 Add Advanced Task Features
- [ ] Implement tag management (add/remove/list)
- [ ] Add note-taking capabilities for tasks
- [ ] Implement task dependencies
- [ ] Add task history/audit logging

## Phase 3: User Management & Collaboration

### 3.1 Multi-User Support
- [ ] Implement user authentication (local or Google)
- [ ] Add user profile management
- [ ] Create permission system for shared tasks

### 3.2 Task Assignment & Collaboration
- [ ] Implement task assignment workflow
- [ ] Add status tracking for assigned tasks
- [ ] Create notification system for task updates

### 3.3 Notification System
- [ ] Implement email notification backend
- [ ] Add configurable notification rules
- [ ] Create notification history

## Phase 4: Testing & Validation

### 4.1 Unit Testing
- [ ] Update existing tests for SQLite storage
- [ ] Add tests for new features
- [ ] Create migration path tests

### 4.2 Integration Testing
- [ ] Test sync functionality with SQLite
- [ ] Validate multi-user scenarios
- [ ] Test edge cases and error handling

### 4.3 Performance Testing
- [ ] Benchmark SQLite vs JSON performance
- [ ] Optimize slow queries
- [ ] Test with large datasets

## Implementation Timeline

| Phase | Estimated Duration | Priority |
|-------|-------------------|----------|
| 1.1-1.3 | 3 days | Critical |
| 2.1-2.3 | 5 days | Critical |
| 3.1-3.3 | 7 days | High |
| 4.1-4.3 | 3 days | Medium |

## Risk Assessment

| Risk | Mitigation Strategy |
|------|---------------------|
| Data loss during migration | Implement robust backup & rollback system |
| Sync conflicts | Enhance conflict detection & resolution logic |
| Performance issues | Add proper indexing & query optimization |
| Schema evolution challenges | Implement database migration framework |

## Next Steps

1. Finalize this plan with team
2. Begin Phase 1 implementation
3. Create detailed technical specifications for each component