# Reports Feature

This document describes the reports feature for the Google Tasks CLI application. The reports feature allows users to generate various analytical reports based on their task data.

## Available Reports

1. **rp1: Task Completion Report** - Summary of completed tasks over a specified period
2. **rp2: Pending Tasks Report** - List of all pending tasks with their due dates
3. **rp3: Task Creation Report** - Overview of tasks created within a certain timeframe
4. **rp4: Overdue Tasks Report** - Detailed list of tasks that are past their due dates
5. **rp5: Task Distribution Report** - Analysis of tasks by category, priority, or tags
6. **rp6: Task Completion Rate Report** - Percentage of tasks completed over a given period
7. **rp7: Future Timeline Report** - Tasks scheduled for future dates
8. **rp8: Timeline Report** - A visual representation of tasks completed over a specified time period

## Usage

To generate reports, use the `generate-report` command:

```bash
gtasks generate-report [OPTIONS] [REPORT_IDS]...
```

### Options

- `--list`: List all available reports
- `--list-tags`: List all available tags extracted from tasks
- `--email`: Send report via email
- `--export [txt|csv|pdf]`: Export format (default: txt)
- `--output`, `-o`: Output file path
- `--days`: Number of days to analyze (default: 30)
- `--start-date`: Start date (YYYY-MM-DD)
- `--end-date`: End date (YYYY-MM-DD)
- `--days-ahead`: Number of days ahead for future reports (default: 30)
- `--tags`: Filter tasks by tags (comma-separated)
- `--with-all-tags`: Require all specified tags to be present (used with --tags)

### Examples

List all available reports:
```bash
gtasks generate-report --list
```

List all available tags:
```bash
gtasks generate-report --list-tags
```

Generate a task completion report for the last 7 days:
```bash
gtasks generate-report rp1 --days 7
```

Generate multiple reports at once:
```bash
gtasks generate-report rp1 rp2 rp4 --days 30
```

Export a report to a CSV file:
```bash
gtasks generate-report rp5 --export csv --output task_distribution.csv
```

Generate a report with a custom date range:
```bash
gtasks generate-report rp1 --start-date 2023-01-01 --end-date 2023-12-31
```

Generate a future timeline report with a custom lookahead period:
```bash
gtasks generate-report rp7 --days-ahead 60
```

### Tag Filtering

You can filter tasks by tags using the `--tags` option. Tags are extracted from task titles, descriptions, and notes by looking for text within square brackets `[tag]`.

Filter tasks that have any of the specified tags:
```bash
gtasks generate-report rp1 --tags "work,urgent"
```

Filter tasks that have all of the specified tags:
```bash
gtasks generate-report rp1 --tags "work,urgent" --with-all-tags
```

## Report Details

### Task Completion Report (rp1)
Provides a summary of completed tasks over a specified period, including:
- Total completed tasks
- Average completion rate per day
- Daily completion breakdown
- Overall completion rate

### Pending Tasks Report (rp2)
Lists all pending tasks with their due dates, organized into:
- Overdue tasks
- Tasks due soon (within 7 days)
- Future due dates
- Tasks with no due date

### Task Creation Report (rp3)
Analyzes tasks created within a certain timeframe, showing:
- Total tasks created
- Creation trends over time
- Daily creation counts

### Overdue Tasks Report (rp4)
Provides a detailed list of tasks that are past their due dates, categorized by:
- Very overdue (30+ days)
- Moderately overdue (7-29 days)
- Recently overdue (< 7 days)

### Task Distribution Report (rp5)
Analyzes tasks by category, priority, or tags, showing:
- Status distribution
- Priority distribution
- Tag distribution
- Project distribution (if applicable)

### Task Completion Rate Report (rp6)
Calculates the percentage of tasks completed over a given period, including:
- Total relevant tasks
- Completed tasks count
- Completion rate percentage
- Weekly completion breakdown

### Future Timeline Report (rp7)
Lists tasks scheduled for future dates, organized by:
- Tasks due within the next week
- Tasks due in the next 2 weeks
- Tasks due in the next month
- Tasks due beyond a month

### Timeline Report (rp8)
Provides a visual representation of tasks completed over a specified time period, showing:
- Daily task creation and completion visualization
- Max tasks created/completed in a day
- Visual timeline of task activity

## Export Formats

Reports can be exported in the following formats:
- **Text (txt)**: Default format, suitable for terminal viewing
- **CSV**: Comma-separated values, suitable for importing into spreadsheets
- **PDF**: (Planned for future implementation)

## Implementation Details

The reports feature is implemented with a modular architecture that allows for easy extension with new report types. Each report is implemented as a separate class that extends the base `BaseReport` class.