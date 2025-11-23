# Organized Tasks Report (rp9)

## Overview

The Organized Tasks Report (rp9) is a new report type that organizes tasks according to the specific priority and functional categories as requested. This report is specifically designed for clean email delivery with all tags removed from task titles, descriptions, and notes.

## Features

1. **Categorized Task Organization**:
   - Tasks are automatically categorized based on the exact numbered categories specified
   - Categories are grouped by functional areas as specified in the requirements
   - Within each category, tasks are sorted by due date

2. **Tag Removal for Clean Email Delivery**:
   - All tags (text within square brackets) are removed from task titles, descriptions, and notes
   - This ensures clean presentation when sending reports via email

3. **Enhanced Visual Formatting**:
   - Professional report header and footer for clear document boundaries
   - Well-structured sections with clear visual separators
   - Improved indentation and task relationship visualization
   - Descriptive task details with clear hierarchy indicators (└─ for descriptions)

4. **Colorful Terminal Output**:
   - When viewed in the terminal with Rich library support, the report uses colors for better readability
   - Different elements are color-coded for quick visual scanning
   - Group headers are displayed in blue
   - Category headers are displayed in yellow
   - Task numbers are displayed in green
   - Due dates are displayed in cyan
   - Notes are displayed in magenta
   - Descriptions are dimmed for visual hierarchy

5. **Professional Category Titles**:
   - Category titles have been improved to be more professional and clear
   - Instead of "Tasks with "cr" tag ", it now shows "Change Request Tasks"
   - All category titles have been simplified and made more descriptive
   - Group headers are clearly marked and separated for easy navigation

6. **Multiple Export Formats**:
   - Text format for terminal viewing (with color support when available)
   - CSV format for spreadsheet import
   - Ready for PDF export integration

7. **Timezone Handling**:
   - Properly handles both timezone-aware and timezone-naive datetime objects
   - Avoids datetime comparison errors that can occur with mixed timezone formats

8. **Filtering Options**:
   - `--only-title`: Shows only task titles, without descriptions or notes
   - `--no-other-tasks`: Hides the "Other Tasks (not matching any category)" section

## Categories

The report organizes tasks into the following exact categories grouped by functional areas:

### Priority Tasks
4. Highest Priority Tasks (***** tag)
7. Highest Priority Tasks (p1 tag)
5. Medium Priority Tasks (*** tag)
8. Medium Priority Tasks (p2 tag)
9. Defect/Bug Tasks
17. In Testing Tasks

### Functional Tasks
6. Frontend Tasks (FE tag)
6. Backend Tasks (BE tag)
2. Dependency Tasks (DEP tag)
18. UAT Phase Tasks (in-uat tag)

### Pending Tasks
6. Pending Testing Tasks (PET tag)
6. Pending Development Tasks (PDEP tag)
6. Pending Estimation Tasks (PE tag)
10. Pending Tasks
11. Pending Production Tasks (pending-prod tag)

### Time-Based Tasks
21. Today's Tasks (today tag)
26. Daily Tasks (daily tag)
22. To-Do Tasks (todo tag)
13. This Week Tasks (this-week tag)
16. Delivery Today Tasks (DEL-T tag)
19. Meeting Tasks (meeting/meetings tag)
24. Security Tasks (vapt/waf tag)

### Project Management Tasks
14. Event Tasks (events tag)
27. Go-Live Tasks (go-live: tag)
15. Project Management Tasks (pm tag)
25. Estimation Tasks (estimation tag)
23. Upcoming Change Request Tasks (upcoming-cr tag)
3. Change Request Tasks (cr tag)

### Other Tasks
20. Long-term Tasks (long-term tag)
1. Hold Tasks (HOLD tag)
12. Study Tasks (study tag)

## Usage

To generate the organized tasks report:

```bash
gtasks generate-report rp9
```

To send the report via email (as specified in the requirements):

```bash
gtasks generate-report rp9 --email suresh.das@intglobal.com
```

To export in CSV format:

```bash
gtasks generate-report rp9 --export csv --output organized_tasks.csv
```

To show only task titles without descriptions or notes:

```bash
gtasks generate-report rp9 --only-title
```

To hide the "Other Tasks (not matching any category)" section:

```bash
gtasks generate-report rp9 --no-other-tasks
```

To use both options together:

```bash
gtasks generate-report rp9 --only-title --no-other-tasks
```

## Implementation Details

The report is implemented as a separate class [OrganizedTasksReport](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src/gtasks_cli/reports/organized_tasks_report.py#L12-L493) that extends the base [BaseReport](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src/gtasks_cli/reports/base_report.py#L11-L148) class. It uses the existing tag extraction utilities to identify and categorize tasks, and implements the tag removal functionality for clean presentation.

### Key Components

1. **Tag-based Categorization**: Tasks are categorized based on the presence of specific tags according to the exact numbering scheme and grouping
2. **Date-based Sorting**: Within each category, tasks are sorted by due date
3. **Tag Removal**: All square bracket tags are removed from task content for clean display
4. **Enhanced Formatting**: Professional report structure with clear headers, footers, and visual separators
5. **Color Support**: Uses the Rich library for colorful terminal output when available
6. **Multiple Export Formats**: Supports both text and CSV export formats
7. **Timezone Handling**: Properly handles timezone-aware and timezone-naive datetime objects
8. **Filtering Options**: Supports `--only-title` and `--no-other-tasks` options for customized output

### Technical Implementation

- The report is registered with ID `rp9` in the [generate_report.py](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src/gtasks_cli/commands/generate_report.py) command
- It follows the same pattern as other reports in the system
- It uses the existing [tag_extractor.py](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src/gtasks_cli/utils/tag_extractor.py) utilities for tag processing
- The tag removal functionality is implemented in the [_remove_tags_from_task_fields](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src/gtasks_cli/reports/organized_tasks_report.py#L169-L189) method
- Timezone handling is implemented in the [_normalize_datetime](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src/gtasks_cli/reports/organized_tasks_report.py#L143-L151) method to prevent comparison errors
- Enhanced formatting is implemented in the [_export_txt](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src/gtasks_cli/reports/organized_tasks_report.py#L255-L391) method
- Filtering options are implemented in both [_export_txt](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src/gtasks_cli/reports/organized_tasks_report.py#L255-L391) and [_export_csv](file:///Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli/src/gtasks_cli/reports/organized_tasks_report.py#L393-L492) methods

## Error Handling

The report includes robust error handling for common issues:

1. **Timezone Handling**: Properly normalizes datetime objects to prevent comparison errors between timezone-aware and timezone-naive objects
2. **None Data Handling**: Gracefully handles cases where no data is available for report generation
3. **Data Structure Validation**: Validates data structures before attempting to access their properties
4. **Color Library Fallback**: Gracefully degrades to plain text output when the Rich library is not available

## Testing

A comprehensive test suite is included in [test_rp9_report.py](file:///Users/int/Documents/workspace/projects/gtasks_automation/test_rp9_report.py) that verifies:
- Report generation functionality
- Task categorization accuracy according to the exact numbering scheme and grouping
- Tag removal effectiveness
- Export format support
- Date-based sorting within categories
- Timezone-aware datetime handling
- Error handling for None data
- Color output support
- Filtering options (`--only-title` and `--no-other-tasks`)

## Future Enhancements

Possible future enhancements include:
- PDF export support
- Custom category definitions
- Additional sorting options
- Integration with email sending functionality
- Custom filtering options