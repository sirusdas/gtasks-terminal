echo -e "help\nhelp view\nhelp done\nhelp delete\nhelp update\nhelp add\nhelp list\nexit" | gtasks interactive
/Users/int/Documents/workspace/projects/gtasks_automation/gtasks_cli && echo "search tuku" | gtasks interactive | grep -A 20 "Search results"

gtasks interactive -- list "My Tasks" --filter this_month:created_at --search "apple|Tuku" --order-by title

gtasks interactive -- tags

gtasks interactive -- list --list-names

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

 --------------- USEFUL REPORTS COMMANDS ---------------

 gtasks generate-report rp10 --filter this_week:created_at --tags "--em:[***]|--ex:[cr]" --output-tags "em:***|ex:my" --output-lists "ex:My Tasks" --output-tasks "ex:Tracker"


gtasks generate-report rp10 --filter past3weeks:created_at --tags "--em:[***]|--ex:[cr]" --output-tags "em:***|ex:my" --output-lists "ex:My Tasks,Raju Da" --output-tasks "ex:Tracker"

gtasks generate-report rp10 --filter past3weeks:created_at --tags "prasen|--ex:cr" --output-tags "--ex:my,upscaling,tp1,todo,R,PH" --output-lists "--ex:My Tasks,Raju Da" --output-tasks "--ex:Tracker" --only-pending

gtasks generate-report rp10 --filter past2weeks:created_at --tags "prasen|--ex:cr" --output-tags "--ex:my,upscaling,tp1,todo,R,PH|--group:1[prasen,***,urgent],2[prod]" --output-lists "--ex:My Tasks,Raju Da" --output-tasks "--ex:Tracker" --only-pending --order-by "modified_at:desc"

gtasks generate-report rp10 --filter this_week:created_at --tags "prasen|--ex:cr" --output-tags "--ex:my,upscaling,tp1,todo,R,PH|--group:1[prasen,***,urgent],2[prod]" --output-lists "--ex:My Tasks,Raju Da" --output-tasks "--ex:Tracker" --only-pending --order-by "modified_at:desc"

gtasks generate-report rp10 --filter past2weeks:created_at --tags "prasen" --output-tags "--ex:my,upscaling,tp1,todo,R,PH|--group:1[prasen,***,urgent],2[prod], 3[discuss,meet]" --output-lists "--ex:My Tasks,Raju Da" --output-tasks "--ex:Tracker" --only-pending --order-by "modified_at:desc" --email prasenjitk.deb@example.com --cc suresh.das@example.com

------------ Suresh Commands --------------
gtasks generate-report rp10 --filter past2weeks:created_at --tags "my,vapt,waf,***|--ex:cr" --output-tags "--ex:tp1,R,PH|--group:1[my,***,urgent],2[prod,defect,uat,live,anal,resear,bugs],3[discuss,meet,plan],4[cr],5[DEL]" --output-tasks "--ex:Tracker" --only-pending --order-by "modified_at:desc"

gtasks generate-report rp10 --filter past2weeks:created_at --tags "prasen|--ex:cr" --output-tags "--ex:my,upscaling,tp1,todo,R,PH|--group:1[prasen,***,urgent],2[prod]" --output-lists "--ex:My Tasks,Raju Da" --output-tasks "--ex:Tracker" --only-pending --order-by "modified_at:desc" --email suresh.das@example.com

gtasks generate-report rp10 --filter this_week:created_at --output-tags "--ex:tp1,R,PH|--group:1[my,***,urgent],2[prod],3[discuss]" --output-tasks "--ex:Tracker" --only-pending --order-by "modified_at:desc"

gtasks generate-report rp10 --filter this_week:created_at  --tags "my|--ex:cr" --output-tags "--ex:tp1,R,PH|--group:1[my,***,urgent],2[prod],3[discuss]" --output-tasks "--ex:Tracker" --only-pending --order-by "modified_at:desc"

gtasks generate-report rp10 --filter this_week:created_at --tags "my" --output-tags "--ex:tp1,R,PH,P,m|--group:1[my,***,urgent],2[prod],3[discuss,meet]" --output-lists "--ex:Raju Da" --output-tasks "--ex:Tracker" --only-pending --order-by "modified_at:desc"


gtasks interactive -- list --filter today:created_at --search "[prasen" --order-by "due_date:desc"
gtasks interactive -- list --filter 08122025:due_date --search "[prasen" --order-by "due_date:desc"

gtasks interactive -- list --filter 08122025:due_date

# Kill all Python processes listening on ports
lsof -i -P -n | grep LISTEN | grep Python | awk '{print $2}' | xargs kill -9
lsof -i -P -n | grep LISTEN | grep python | awk '{print $2}' | xargs kill -9

# python kill

# Find the gunicorn process
ps aux | grep gunicorn

# Kill all gunicorn processes for this app
pkill -f "gunicorn.*main_dashboard:app"

# Or kill by the main process ID (the first one listed)
kill <PID>

# Force kill if needed
pkill -9 -f "gunicorn.*main_dashboard:app"
