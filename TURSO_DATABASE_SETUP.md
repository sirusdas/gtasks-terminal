# Turso Database Setup for Dashboard

## Problem
Dashboard shows only 6 tasks instead of 600+ tasks from Turso database.

## Root Cause
The dashboard's `data_manager.py` was not checking the `GTASKS_CONFIG_DIR` environment variable. It defaulted to `~/.gtasks` which is a DIFFERENT location than where `gtasks remote sync` saves data.

## Solution
**FIX APPLIED:** The dashboard now respects `GTASKS_CONFIG_DIR` environment variable.

---

## Step 1: Update Systemd Service (CRITICAL)

Edit the systemd service file:
```bash
sudo nano /etc/systemd/system/gtasks-dashboard.service
```

Add the `Environment` line under `[Service]`:
```ini
[Service]
Environment="GTASKS_CONFIG_DIR=/var/www/html/gtasks/gtasks-terminal/gtasks_cli/config"
User=www-data
Group=www-data
```

## Step 2: Reload and Restart

```bash
sudo systemctl daemon-reload
sudo systemctl restart gtasks-dashboard
sudo systemctl status gtasks-dashboard
```

## Step 3: Verify Dashboard is Reading Correct Database

Check the logs for the path being used:
```bash
sudo journalctl -u gtasks-dashboard -f | grep "GTASKS_CONFIG_DIR"
```

You should see:
```
[DataManager] Using GTASKS_CONFIG_DIR: /var/www/html/gtasks/gtasks-terminal/gtasks_cli/config
```

## Step 4: Test API

```bash
curl http://127.0.0.1:8081/gtasks/gtasks-terminal/gtasks_dashboard/api/data | jq '.stats.total'
```

Should now show 681 tasks instead of 6!
