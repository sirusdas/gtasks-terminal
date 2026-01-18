Here's how to set up a systemd service for your gunicorn app:

**Step 1: Create the service file**

```bash
sudo nano /etc/systemd/system/gtasks-dashboard.service
```

**Step 2: Add this configuration**

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

**Step 3: Save and exit** (Ctrl+X, then Y, then Enter)

**Step 4: Enable and start the service**

```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable gtasks-dashboard

# Start the service now
sudo systemctl start gtasks-dashboard

# Check the status
sudo systemctl status gtasks-dashboard
```

**Step 5: Useful commands for managing the service**

```bash
# Restart the service
sudo systemctl restart gtasks-dashboard

# Stop the service
sudo systemctl stop gtasks-dashboard

# View live logs
sudo journalctl -u gtasks-dashboard -f

# View recent logs
sudo journalctl -u gtasks-dashboard -n 50

# Reload without downtime
sudo systemctl reload gtasks-dashboard
```

That's it! Your app will now run as a proper system service and automatically restart on boot or if it crashes.

Your dashboard is now running on `http://127.0.0.1:8081`! 🚀

# Find the gunicorn process
ps aux | grep gunicorn

# Kill all gunicorn processes for this app
pkill -f "gunicorn.*main_dashboard:app"

# Or kill by the main process ID (the first one listed)
kill <PID>

# Force kill if needed
pkill -9 -f "gunicorn.*main_dashboard:app"