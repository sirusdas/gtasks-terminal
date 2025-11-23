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
9. **rp9: Organized Tasks Report** - Tasks organized by priority and functional categories with tags removed for email

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
- `--only-title`: Show only task titles, no descriptions or notes (rp9 only)
- `--no-other-tasks`: Do not show Other Tasks (not matching any category) in the output (rp9 only)

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

Generate an organized tasks report for email delivery:
```bash
gtasks generate-report rp9 --email suresh.das@intglobal.com
```

Generate an organized tasks report with only titles and no uncategorized tasks:
```bash
gtasks generate-report rp9 --only-title --no-other-tasks
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

### Organized Tasks Report (rp9)
Organizes tasks according to the exact sequence of categories grouped by functional areas:

#### Priority Tasks
4. Highest Priority Tasks (***** tag)
7. Highest Priority Tasks (p1 tag)
5. Medium Priority Tasks (*** tag)
8. Medium Priority Tasks (p2 tag)
9. Defect/Bug Tasks
17. In Testing Tasks

#### Functional Tasks
6. Frontend Tasks (FE tag)
6. Backend Tasks (BE tag)
2. Dependency Tasks (DEP tag)
18. UAT Phase Tasks (in-uat tag)

#### Pending Tasks
6. Pending Testing Tasks (PET tag)
6. Pending Development Tasks (PDEP tag)
6. Pending Estimation Tasks (PE tag)
10. Pending Tasks
11. Pending Production Tasks (pending-prod tag)

#### Time-Based Tasks
21. Today's Tasks (today tag)
26. Daily Tasks (daily tag)
22. To-Do Tasks (todo tag)
13. This Week Tasks (this-week tag)
16. Delivery Today Tasks (DEL-T tag)
19. Meeting Tasks (meeting/meetings tag)
24. Security Tasks (vapt/waf tag)

#### Project Management Tasks
14. Event Tasks (events tag)
27. Go-Live Tasks (go-live: tag)
15. Project Management Tasks (pm tag)
25. Estimation Tasks (estimation tag)
23. Upcoming Change Request Tasks (upcoming-cr tag)
3. Change Request Tasks (cr tag)

#### Other Tasks
20. Long-term Tasks (long-term tag)
1. Hold Tasks (HOLD tag)
12. Study Tasks (study tag)

All tags are removed from task titles, descriptions, and notes in the report output, making it suitable for clean email delivery to stakeholders. Tasks are organized in the exact sequence specified above, grouped by functional areas, and within each category, tasks are sorted by due date.

The report features colorful terminal output when the Rich library is available, with:
- Group headers in blue
- Category headers in yellow
- Task numbers in green
- Due dates in cyan
- Notes in magenta
- Descriptions dimmed for visual hierarchy

Additional options for the rp9 report:
- `--only-title`: Shows only task titles, without descriptions or notes
- `--no-other-tasks`: Hides the "Other Tasks (not matching any category)" section

## Export Formats

Reports can be exported in the following formats:
- **Text (txt)**: Default format, suitable for terminal viewing with color support when available
- **CSV**: Comma-separated values, suitable for importing into spreadsheets
- **PDF**: (Planned for future implementation)

## Implementation Details

The reports feature is implemented with a modular architecture that allows for easy extension with new report types. Each report is implemented as a separate class that extends the base `BaseReport` class.