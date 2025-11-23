#!/usr/bin/env python3
"""
Demo script showing plain text output of the report
"""

plain_text_output = """
============================================================
                    ORGANIZED TASKS REPORT
============================================================
Generated on: 2025-11-23 21:54:57
Total tasks: 4


# PRIORITY TASKS
============================================================

4. Highest Priority Tasks (***** tag)
--------------------------------------------------
 1. Fix critical bug ***** (Due: 2025-11-23)
     └─ Fix critical production bug with highest priority

7. Highest Priority Tasks (p1 tag)
--------------------------------------------------
 1. Priority task p1 (Due: 2025-11-24)
     └─ High priority task for project

5. Medium Priority Tasks (*** tag)
--------------------------------------------------
 1. Medium priority task ***
     └─ Medium priority task

9. Defect/Bug Tasks
--------------------------------------------------
 1. Bug fixes and defects (Due: 2025-11-23)
     └─ Fix reported defects in the system

============================================================
              END OF ORGANIZED TASKS REPORT
============================================================
"""

print("Plain Text Output Example:")
print(plain_text_output)