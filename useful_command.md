echo -e "help\nhelp view\nhelp done\nhelp delete\nhelp update\nhelp add\nhelp list\nexit" | gtasks interactive
/Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli && echo "search tuku" | gtasks interactive | grep -A 20 "Search results"

gtasks interactive -- list "My Tasks" --filter this_month:created_at --search "apple|Tuku" --order-by title

gtasks interactive -- tags

gtasks interactive -- list --list-names

gtasks generate-report rp9 --email test@test.com

gtasks generate-report rp9 --only-title --no-other-tasks
gtasks generate-report rp9 --only-title --no-other-tasks  --email test@test.com

gtasks interactive -- list --filter this_week:created_at --search "--em:[***]|--ex:[cr]"

gtasks interactive -- list --filter this_week:created_at --tags "--em:[***]|--ex:[cr]"

gtasks interactive -- list "My Tasks" --filter this_month:created_at --search "apple|Tuku" --order-by title | view

gtasks config set sync.auto_save true

gtasks list --filter 25122023:due_date
gtasks list --filter 01122023-31122023:created_at
gtasks interactive -- list --filter 25122023:modified_at

sqlite3 /Users/int/.gtasks/personal/tasks.db "SELECT COUNT(*) FROM tasks;"
sqlite3 /Users/int/.gtasks/personal/tasks.db "SELECT COUNT(DISTINCT id) FROM tasks;"
sqlite3 /Users/int/.gtasks/personal/tasks.db "SELECT title, COUNT(*) as count FROM tasks GROUP BY title HAVING COUNT(*) > 1 ORDER BY count DESC
 LIMIT 10;"