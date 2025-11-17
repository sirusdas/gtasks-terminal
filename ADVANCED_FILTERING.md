# Advanced Filtering in GTasks CLI

GTasks CLI provides powerful filtering capabilities to help you find exactly the tasks you need. This document explains the advanced filtering features, including time-based filtering with specific date fields.

## Time-Based Filtering

The `--filter` option allows you to filter tasks based on time periods. You can filter by general time periods or specify which date field to use for filtering.

### Basic Time Filters

The following time periods are supported:

- `today` - Tasks for today
- `this_week` - Tasks for this week
- `this_month` - Tasks for this month
- `last_month` - Tasks from last month
- `last_3m` - Tasks from the last 3 months
- `last_6m` - Tasks from the last 6 months
- `last_year` - Tasks from the last year

### Advanced Time Filtering with Specific Date Fields

You can specify which date field to use for time-based filtering by using the format `PERIOD:DATE_FIELD`. This allows you to be more precise about which tasks to include in your results.

Available date fields:
- `due_date` - The task's due date
- `created_at` - When the task was created
- `modified_at` - When the task was last modified

#### Examples:

1. Filter tasks due this week:
   ```
   gtasks list --filter this_week:due_date
   ```

2. Filter tasks created this month:
   ```
   gtasks list --filter this_month:created_at
   ```

3. Filter tasks modified in the last 3 months:
   ```
   gtasks list --filter last_3m:modified_at
   ```

### How It Works

When you use a basic time filter (e.g., `this_month`), the system checks all three date fields:
1. Due date
2. Creation date
3. Modification date

If any of these dates fall within the specified time period, the task is included in the results.

When you specify a date field (e.g., `this_month:due_date`), only that specific date field is checked.

### Combining Filters

You can combine time filters with other filters for more precise results:

```
# Find high priority tasks created this month containing "report"
gtasks list --priority high --filter this_month:created_at --search report

# Find completed tasks modified in the last 3 months in the "Work" project
gtasks list --status completed --filter last_3m:modified_at --project Work
```

### Interactive Mode

All these filtering options work in interactive mode as well:

```
# Start interactive mode with pre-filtered tasks
gtasks interactive -- list --filter this_month:created_at --project Personal
```

## Best Practices

1. Use `due_date` filters when you want to focus on upcoming deadlines
2. Use `created_at` filters when you want to find recently added tasks
3. Use `modified_at` filters when you want to find recently updated tasks
4. Use basic time filters when you want a broader view that includes tasks based on any date field

## Examples

Here are some practical examples of advanced filtering:

1. Find all tasks due today:
   ```
   gtasks list --filter today:due_date
   ```

2. Find tasks you've been working on recently (modified this week):
   ```
   gtasks list --filter this_week:modified_at
   ```

3. Find tasks you added this month that are still pending:
   ```
   gtasks list --status pending --filter this_month:created_at
   ```

4. Find important tasks (high priority) that are due soon (this week):
   ```
   gtasks list --priority high --filter this_week:due_date
   ```

5. In interactive mode, start with tasks you created this month:
   ```
   gtasks interactive -- list "My Tasks" --filter this_month:created_at
   ```

These advanced filtering capabilities make it easier to focus on exactly the tasks you need to see, whether you're planning your day, reviewing recent work, or catching up on overdue items.