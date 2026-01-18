Great! It's working now! 🎉

The issue was that gunicorn wasn't finding the packages in your virtual environment's site-packages. Setting `PYTHONPATH` explicitly solved it.

To make this permanent and avoid having to set `PYTHONPATH` every time, you have a few options:

**Option 1: Create a simple startup script**
```bash
cat > /var/www/html/gtasks/gtasks-terminal/gtasks_dashboard/start_dashboard.sh << 'EOF'
#!/bin/bash
cd /var/www/html/gtasks/gtasks-terminal/gtasks_dashboard
source /var/www/html/gtasks/gtasks-terminal/.venv/bin/activate
export PYTHONPATH=/var/www/html/gtasks/gtasks-terminal/.venv/lib/python3.12/site-packages
gunicorn -w 4 -b 127.0.0.1:8081 main_dashboard:app
EOF

chmod +x /var/www/html/gtasks/gtasks-terminal/gtasks_dashboard/start_dashboard.sh
```

**Option 2: Create a systemd service** (recommended for production)
```bash
sudo nano /etc/systemd/system/gtasks-dashboard.service
```

Add this content:
```ini
[Unit]
Description=GTasks Dashboard
After=network.target

[Service]
Type=notify
User=root
WorkingDirectory=/var/www/html/gtasks/gtasks-terminal/gtasks_dashboard
Environment="PATH=/var/www/html/gtasks/gtasks-terminal/.venv/bin"
Environment="PYTHONPATH=/var/www/html/gtasks/gtasks-terminal/.venv/lib/python3.12/site-packages"
ExecStart=/var/www/html/gtasks/gtasks-terminal/.venv/bin/gunicorn -w 4 -b 127.0.0.1:8081 main_dashboard:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then enable and start it:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gtasks-dashboard
sudo systemctl start gtasks-dashboard
sudo systemctl status gtasks-dashboard
```

Your dashboard is now running on `http://127.0.0.1:8081`! 🚀

# Find the gunicorn process
ps aux | grep gunicorn

# Kill all gunicorn processes for this app
pkill -f "gunicorn.*main_dashboard:app"

# Or kill by the main process ID (the first one listed)
kill <PID>

# Force kill if needed
pkill -9 -f "gunicorn.*main_dashboard:app"