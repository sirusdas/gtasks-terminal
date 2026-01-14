# GTasks Automation - Coding Rules

## Modular Architecture

### Single Source of Truth
- Each feature should have ONE implementation
- NEVER create multiple versions: `main.py` → `advanced_main.py` → `complete_main.py` is PROHIBITED
- Instead: Extend the original file with new parameters, flags, or configuration options

### Example of Correct Approach
```
✅ GOOD: main.py with --enhanced flag
✅ GOOD: data_manager.py with optional features via parameters
❌ BAD: main.py, main_enhanced.py, main_advanced.py, main_complete.py
❌ BAD: data_manager.py, enhanced_data_manager.py, super_data_manager.py
```

### File Naming Conventions
- Use descriptive, singular names: `task_manager.py`, not `task_managers.py`
- Avoid prefixes like `super_`, `advanced_`, `enhanced_` in filenames
- Use suffixes for variants only when they represent fundamentally different types:
  - `base_report.py` (base class), `task_report.py` (specific report type)

---

## Code Organization

### Directory Structure
- Keep related functionality in the same module
- Routes → `routes/`
- Models → `models/`
- Services → `services/`
- Utils → `utils/`
- Tests → alongside source files or in `tests/`

### Import Order
1. Standard library imports
2. Third-party imports
3. Local application imports

### Module Responsibilities
- Each module should have ONE clear responsibility
- Services handle business logic
- Models handle data structures
- Routes/Commands handle I/O and routing
- Utils handle reusable helpers

---

## Code Quality

### Functions
- Keep functions small and focused (single responsibility)
- Maximum 50 lines per function (excluding docstrings)
- Use type hints for function signatures
- Document complex logic with docstrings

### Naming
- Use descriptive names: `get_completed_tasks()` not `get_tasks()`
- Avoid single-letter variables (except loop counters)
- Use verbs for functions: `validate_input()`, `fetch_data()`

### Error Handling
- Use custom exceptions in `utils/exceptions.py`
- Log errors with appropriate level (ERROR, WARNING, INFO)
- Provide meaningful error messages

---

## Git & Version Control

### Commit Messages
- Use imperative mood: "Add feature" not "Added feature"
- Keep first line under 72 characters
- Reference issues/tickets when applicable

### Branch Naming
- `feature/` for new features
- `bugfix/` for bug fixes
- `refactor/` for code improvements

---

## Testing

### Test Files
- Place tests alongside source or in `tests/` directory
- Name test files: `test_<module>.py`
- Use descriptive test method names

### Coverage
- Aim for meaningful test coverage on critical paths
- Test edge cases and error conditions

---

## Documentation

### Code Comments
- Explain WHY, not WHAT
- Keep comments up-to-date with code
- Remove commented-out code

### README
- Keep project README updated
- Include setup instructions
- Document main use cases

---

## Anti-Patterns to Avoid

```
❌ Duplicate files (dashboard.py, dashboard2.py, new_dashboard.py)
❌ God classes/modules that do everything
❌ Deep nesting (if/elif/else > 3 levels)
❌ Magic numbers (use constants/enums)
❌ Ignoring linter/formatter rules
❌ Large functions (>100 lines)
❌ Circular imports
```

---

## Best Practices Summary

1. **DRY**: Don't Repeat Yourself - abstract common code
2. **KISS**: Keep It Simple, Stupid
3. **YAGNI**: You Aren't Gonna Need It - don't over-engineer
4. **SOLID**: Follow SOLID principles for object-oriented code
5. **Single Responsibility**: Each module/class/function has one purpose
6. **Open/Closed**: Open for extension, closed for modification
7. **Dependency Injection**: Use interfaces, not concrete implementations
8. **Fail Fast**: Validate inputs early
9. **Logging**: Log important operations and errors
10. **Review**: Read your own code before submitting

## Context Management
- ALWAYS check `context/architecture.md` before suggesting file structural changes.
- If you implement a new feature (e.g., a new automation script), you MUST update the mapping in `architecture.md`.
- After significant changes, prompt the user to run `ctx save` to version-control the "memory".

## Kilo Code / Continue Specifics
- When asked to "refactor," prioritize modularity so logic is separate from the dashboard UI.
- Use verbose logging for automation scripts to help debug in headless remote environments.

## 🏗 Modular Architecture & Extension
### Single Source of Truth
- **Strict Requirement**: Each feature must have exactly ONE implementation.
- **Prohibited**: Creating duplicate "versioned" files (e.g., `main_v2.py`, `dashboard_new.py`).
- **Standard**: Extend existing files using parameters, flags, or configuration objects.

### File Naming Conventions
- **Case**: Use `snake_case` for filenames.
- **Singular**: Use descriptive singular names (`task_manager.py`).
- **Variants**: No `super_`, `advanced_`, or `enhanced_` prefixes. Use functional suffixes only if necessary (e.g., `base_report.py` vs `task_report.py`).

---

## 📂 Code Organization & Logic
### Directory Mapping
- **Routes**: `routes/` (API/Web endpoints)
- **Models**: `models/` (Data structures)
- **Services**: `services/` (Business logic/Data managers)
- **Utils**: `utils/` (Helpers/Exceptions)

### Module Responsibilities
- **Functions**: Single responsibility. Maximum **50 lines** per function.
- **Type Hints**: Mandatory for all function signatures.
- **Error Handling**: Use custom exceptions from `utils/exceptions.py`. Log meaningful messages before raising.

---

## 🤖 AI & Context Management
### IDE Behavior (Kilo Code / Continue)
- **Modularity**: Always separate business logic from UI/CLI code.
- **Logging**: Use verbose logging for automation scripts to aid remote debugging.
- **Self-Update**: If you (the AI) create a new module, you MUST update the mapping in `architecture.md` immediately.

### 🌍 Browser Debugging (Playwright MCP)
For browser-based debugging operations, use the **Playwright MCP** server. This provides direct access to browser automation capabilities including:

#### Playwright MCP Capabilities
- **Navigation**: `browser_navigate` - Navigate to URLs, go back/forward, reload
- **DOM Inspection**: `browser_snapshot` - Take accessibility snapshots of the page
- **Form Interactions**: `browser_fill_form`, `browser_click`, `browser_type` - Form filling and element interaction
- **Screenshots**: `browser_take_screenshot` - Capture page or element screenshots
- **Console Access**: `browser_console_messages` - Retrieve console messages and errors
- **Network Monitoring**: `browser_network_requests` - Monitor network requests

#### Usage Guidelines
- **For UI Bugs**: Use `browser_snapshot` to inspect DOM structure and element states
- **For Console Errors**: Use `browser_console_messages` to retrieve error logs
- **For Network Issues**: Use `browser_network_requests` to monitor API calls
- **For Automation**: Use `browser_fill_form`, `browser_click` for user interaction testing

### Memory Sync
- **Pre-flight Check**: ALWAYS read `context/architecture.md` before suggesting structural changes.
- **Checkpoint**: After significant changes, prompt the user: *"Would you like me to run 'ctx save' to sync this context?"*

---

## ⚠️ Anti-Patterns (The "Never" List)
- ❌ **Duplicate Files**: No `dashboard2.py` or `temp_sync.py`.
- ❌ **Deep Nesting**: Avoid `if/else` logic deeper than 3 levels.
- ❌ **Magic Numbers**: Use `constants.py` or Enums.
- ❌ **God Modules**: No single file should handle both API sync and UI rendering.