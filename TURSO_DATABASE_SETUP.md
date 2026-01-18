# Dashboard Data Location Fix

## Problem
Dashboard shows only 6 demo tasks instead of 681 tasks from your database.

## Root Cause
The dashboard runs as a user whose home directory determines where `~/.gtasks` points:
- **root** home: `/root` → `~/.gtasks` = `/root/.gtasks` ✅ (has 681 tasks!)
- **www-data** home: `/var/www` → `~/.gtasks` = `/var/www/.gtasks` ❌ (EMPTY!)

## Solution: Run as root (or ensure User= matches your data location)

### Option 1: Run as root (SIMPLE - WORKS!)
```ini
[Service]
User=root
Group=root
```

### Option 2: Keep www-data but point to root's data (requires permissions)
```ini
[Service]
Environment="GTASKS_CONFIG_DIR=/root/.gtasks"
User=www-data
Group=www-data

# Also need to grant www-data read access to /root/.gtasks:
# sudo chmod -R 755 /root/.gtasks
```

### Recommended: Option 1 (run as root)

```bash
sudo nano /etc/systemd/system/gtasks-dashboard.service
```

```ini
[Unit]
Description=GTasks Dashboard
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/var/www/html/gtasks/gtasks-terminal/gtasks_dashboard
ExecStart=/var/www/html/gtasks/gtasks-terminal/gtasks_dashboard/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8081 \
    --chdir /var/www/html/gtasks/gtasks-terminal/gtasks_dashboard \
    main_dashboard:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart gtasks-dashboard
sudo systemctl status gtasks-dashboard
```

### Verify

```bash
# Test API
curl http://127.0.0.1:8081/gtasks/gtasks-terminal/gtasks_dashboard/api/data | jq '.stats.total'
```

Should show **681 tasks**!

### Check logs
```bash
sudo journalctl -u gtasks-dashboard -f
```

Should see:
```
[DataManager] Detected gtasks path: /root/.gtasks
```
