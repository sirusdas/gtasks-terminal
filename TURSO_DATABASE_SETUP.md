# Turso Database Setup for Dashboard

## Problem
Dashboard shows only 6 tasks instead of 600+ tasks from Turso database.

## Solution
Set `GTASKS_CONFIG_DIR` environment variable to point to the Turso database location.

---

## Step 1: Find Your Turso Database Location

Run on server:
```bash
# Check if Turso DB file exists
find /var/www/html -name "*.db" -o -name "*turso*" 2>/dev/null

# Check your config directory
ls -la /var/www/html/gtasks/gtasks-terminal/
```

## Step 2: Update Systemd Service

Edit the systemd service file:
```bash
sudo nano /etc/systemd/system/gtasks-dashboard.service
```

Add or update the `[Service]` section:
```ini
[Service]
Environment="GTASKS_CONFIG_DIR=/var/www/html/gtasks/gtasks-terminal/gtasks_cli/config"
User=www-data
Group=www-data
```

## Step 3: Reload and Restart

```bash
sudo systemctl daemon-reload
sudo systemctl restart gtasks-dashboard
sudo systemctl status gtasks-dashboard
```

## Step 4: Verify

```bash
# Test API endpoint
curl http://127.0.0.1:8081/gtasks/gtasks-terminal/gtasks_dashboard/api/data | jq '.stats.total'

# Check journalctl logs
sudo journalctl -u gtasks-dashboard -f
```

---

## Alternative: Check Current Configuration

If you need to find where the config is currently pointing:

```bash
# Check environment variable
echo $GTASKS_CONFIG_DIR

# Check local config
cat ~/.gtasks/config.yaml

# Check the dashboard's config.py
cat /var/www/html/gtasks/gtasks-terminal/gtasks_dashboard/config.py
```

---

## Sync Data to Turso (If Needed)

If the Turso database is empty, sync from Google Tasks:

```bash
export GTASKS_CONFIG_DIR=/var/www/html/gtasks/gtasks-terminal/gtasks_cli/config
cd /var/www/html/gtasks/gtasks-terminal
source venv/bin/activate
gtasks sync
```

---

## Troubleshooting

### "Database file not found"
- Verify the path to your Turso DB file
- Check file permissions: `chmod 644 /path/to/your.db`

### "permission denied"
- Ensure www-data can read the config directory:
  ```bash
  sudo chown -R www-data:www-data /var/www/html/gtasks/gtasks-terminal/gtasks_cli/config
  sudo chmod -R 755 /var/www/html/gtasks/gtasks-terminal/gtasks_cli/config
  ```

### Still showing wrong data
- Clear any cached data
- Check which account is active: `jq '.current_account' /path/to/data.json`
- Set the correct account: `gtasks account set work`
