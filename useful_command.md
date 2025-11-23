echo -e "help\nhelp view\nhelp done\nhelp delete\nhelp update\nhelp add\nhelp list\nexit" | gtasks interactive
/Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli && echo "search tuku" | gtasks interactive | grep -A 20 "Search results"

gtasks interactive -- list "My Tasks" --filter this_month:created_at --search "apple|Tuku" --order-by title

gtasks interactive -- tags

gtasks interactive -- list --list-names

gtasks generate-report rp9 --email suresh.das@intglobal.com

gtasks generate-report rp9 --only-title --no-other-tasks
gtasks generate-report rp9 --only-title --no-other-tasks  --email suresh.das@intglobal.com

sqlite3 /Users/int/.gtasks/personal/tasks.db "SELECT COUNT(*) FROM tasks;"
sqlite3 /Users/int/.gtasks/personal/tasks.db "SELECT COUNT(DISTINCT id) FROM tasks;"
sqlite3 /Users/int/.gtasks/personal/tasks.db "SELECT title, COUNT(*) as count FROM tasks GROUP BY title HAVING COUNT(*) > 1 ORDER BY count DESC
 LIMIT 10;"



 ========================

# Tasks with Priority Tags sort it with resepct to date
4. Tasks with "*****" tag ---> Highest Priority or 7. Tasks with "p1" tag ---> Highest Priority
5. Tasks with "***" tag ---> Medium Priority or 8. Tasks with "p2" tag ---> Medium Priority
9. Tasks with "defects" or "bugs" tag
17. Tasks with "inTesting" tag

# Tasks with Functional Tags sort it with resepct to date
6. Tasks with "FE" tag ---> Frontend Tasks
6. Tasks with "BE" tag ---> Backend Tasks
2. Tasks with "DEP" tag ---> Dependency
18. Tasks with "in-uat" tag. ---> Tasks in UAT Phase

# Tasks with Pending Tags sort it with resepct to date
6. Tasks with "PET" tag ---> Pending Testing
6. Tasks with "PDEP" tag ---> Pending Development
6. Tasks with "PE" tag ---> Pending Estimation
10. Tasks with "pending" tag
11. Tasks with "pending-prod" tag

# Tasks with Time-Based Tags sort it with resepct to date
21. Tasks with "today" tag or has today's date as due date
26. Tasks with "daily" tag
22. Tasks with "todo" tag
13. Tasks with "this-week" tag
16. Tasks with "DEL-T" tag ---> Delivery Today Tasks
19. Tasks with "meeting" or "meetings" tag
24. Tasks with "vapt" or 'waf" tag --> Security Related Tasks

# PM related Tasks sort it with resepct to date
14. Tasks with "events" tag
27. Tasks with "go-live:" tag
15. Tasks with "pm" tag ---> Project Management Tasks
25. Tasks with "estimation" tag
23. Tasks with "upcoming-cr" tag
3. Tasks with "cr" tag ---> Change Request

# Other Tasks
20. Tasks with "long-term" tag
1. Tasks with "HOLD" tag
12. Tasks with "study" tag