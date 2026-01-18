cat > /var/www/html/gtasks/gtasks-terminal/gtasks_dashboard/start_dashboard.sh << 'EOF'
#!/bin/bash
cd /var/www/html/gtasks/gtasks-terminal/gtasks_dashboard
source /var/www/html/gtasks/gtasks-terminal/.venv/bin/activate
export PYTHONPATH=/var/www/html/gtasks/gtasks-terminal/.venv/lib/python3.12/site-packages
gunicorn -w 4 -b 127.0.0.1:8081 main_dashboard:app
EOF