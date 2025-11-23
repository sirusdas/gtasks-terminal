echo -e "help\nhelp view\nhelp done\nhelp delete\nhelp update\nhelp add\nhelp list\nexit" | gtasks interactive
/Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli && echo "search tuku" | gtasks interactive | grep -A 20 "Search results"

gtasks interactive -- list "My Tasks" --filter this_month:created_at --search "apple|Tuku" --order-by title

gtasks interactive -- tags


sqlite3 /Users/int/.gtasks/personal/tasks.db "SELECT COUNT(*) FROM tasks;"
sqlite3 /Users/int/.gtasks/personal/tasks.db "SELECT COUNT(DISTINCT id) FROM tasks;"
sqlite3 /Users/int/.gtasks/personal/tasks.db "SELECT title, COUNT(*) as count FROM tasks GROUP BY title HAVING COUNT(*) > 1 ORDER BY count DESC
 LIMIT 10;"