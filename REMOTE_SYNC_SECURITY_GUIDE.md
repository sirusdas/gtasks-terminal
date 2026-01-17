# Remote Sync Security Guide

This guide explains how to securely use the remote sync feature while protecting your credentials and tokens.

## Overview

The remote sync feature allows bidirectional synchronization between:
- **Local SQLite database** (on your machine)
- **Remote Turso database** (in the cloud)
- **Google Tasks API** (source of truth)

Your requirement is:
- **Configs stay local** (tokens never leave your machine)
- **Dashboard can be remote** (accessible from all devices)
- **Secure token handling** (no tokens in Git or shared configs)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LOCAL MACHINE                            │
│  ┌─────────────────┐    ┌─────────────────────────────┐   │
│  │  Local SQLite   │◄──►│  gtasks CLI (with tokens)   │   │
│  │  Database       │    │  - Configs stay local       │   │
│  └─────────────────┘    │  - Tokens in env vars only  │   │
│                         └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Sync via CLI or Dashboard API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     REMOTE SERVER                           │
│  ┌─────────────────┐    ┌─────────────────────────────┐   │
│  │  Dashboard UI   │◄──►│  Dashboard API (no tokens)  │   │
│  │  - Access from  │    │  - Pulls from remote DB     │   │
│  │    all devices  │    │  - Falls back to local if   │   │
│  └─────────────────┘    │    needed                    │   │
│                         └─────────────────────────────┘   │
│                              │                             │
│                              ▼                             │
│  ┌─────────────────┐                                      │
│  │  Remote Turso   │  ← Cloud database (shared state)    │
│  │  Database       │    No tokens stored here             │
│  └─────────────────┘                                      │
└─────────────────────────────────────────────────────────────┘
```

## Token Security

### ✅ DO: Secure Token Handling

1. **Use Environment Variables**
   ```bash
   # Set token in your shell profile (.bashrc, .zshrc, etc.)
   export GTASKS_TURSO_TOKEN="your-jwt-token-here"
   
   # Or use a .env file (add to .gitignore!)
   echo "GTASKS_TURSO_TOKEN=your-jwt-token-here" > .env
   ```

2. **Use .gitignore**
   The project `.gitignore` includes:
   ```
   .env
   .env.local
   *.token
   *.auth
   *turso*
   sync_config_*.yaml
   ```

3. **Rotate Tokens Regularly**
   - Generate new tokens in Turso dashboard
   - Update your local environment variables
   - No need to change shared configs

4. **Use Different Tokens for Different Environments**
   ```bash
   # Development
   export GTASKS_TURSO_TOKEN_DEV="dev-token"
   
   # Production
   export GTASKS_TURSO_TOKEN_PROD="prod-token"
   ```

### ❌ DON'T: Insecure Token Handling

1. **Never commit tokens to Git**
   ```bash
   ❌ Bad: git commit -am "Added my token"
   ❌ Bad: echo "token=xxx" >> config.yaml
   ❌ Bad: Store in shared config file
   ```

2. **Never share tokens**
   ```bash
   ❌ Bad: Send token in Slack/email
   ❌ Bad: Hardcode in source code
   ❌ Bad: Put in public Gist
   ```

3. **Never use same token in multiple places**
   ```bash
   ❌ Bad: Use production token on public server
   ❌ Bad: Share token with team members
   ```

## Dashboard Deployment

### Option 1: Local Dashboard with Remote DB (Recommended for you)

This matches your requirement: **configs stay local, dashboard accessible remotely**

**Setup:**
1. Keep tokens in local `.env` file
2. Run dashboard locally with port forwarding or VPN
3. Remote Turso DB syncs with local SQLite

**Access from other devices:**
```bash
# SSH port forwarding (secure)
ssh -L 8081:localhost:8081 your-local-machine

# Then access http://localhost:8081 from other devices
```

**Or use a reverse proxy:**
```nginx
# On your server (not hosting dashboard)
location /gtasks/ {
    proxy_pass http://your-local-machine:8081/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### Option 2: Remote Dashboard with Read-Only Access

**Setup:**
1. Configure dashboard to use remote Turso DB (no tokens!)
2. Dashboard only reads from DB, doesn't sync
3. Local CLI handles all sync operations

**Security:**
```python
# Dashboard configuration (no tokens!)
REMOTE_DB_URL = "libsql://gtasks-remote-db-sirusdas.aws-ap-south-1.turso.io"
# No token needed for read-only access in some configurations
```

### Option 3: Hybrid Approach

**For maximum security and accessibility:**

1. **Local Machine** (with tokens):
   - Runs `gtasks_cli remote sync` periodically
   - Syncs local SQLite ↔ remote Turso
   - Dashboard can run locally or be accessed via VPN

2. **Remote Dashboard** (no tokens):
   - Connects directly to remote Turso DB
   - Shows data from last sync
   - Indicates "last sync time" to user

3. **Shared Remote DB**:
   - Contains only task data (no tokens)
   - Accessible by both local and remote systems
   - Single source of truth for synced data

## Environment Variable Configuration

### Local Machine (with tokens)

Create `~/.gtasks/remote_config.yaml`:
```yaml
# This file should NOT be in .gitignore if it's in your home directory
# But never commit it to version control!

remote_databases:
  - id: "turso_main"
    url: "libsql://gtasks-remote-db-sirusdas.aws-ap-south-1.turso.io"
    name: "Main Turso DB"
    active: true
    # Token loaded from GTASKS_TURSO_TOKEN env var (not stored here!)
    
sync_settings:
  push_on_change: true
  pull_interval: 300  # 5 minutes
  conflict_resolution: "newest_wins"
```

### Remote Dashboard (no tokens)

Create `gtasks_dashboard/config/production.yaml`:
```yaml
# This file CAN be committed to version control
# It contains no secrets!

database:
  # Use local SQLite if available, fallback to remote
  local_path: "./tasks.db"
  remote_url: "libsql://gtasks-remote-db-sirusdas.aws-ap-south-1.turso.io"
  # No token - dashboard uses read-only access
  
sync:
  enabled: false  # Dashboard doesn't sync directly
  show_last_sync: true
  show_connection_status: true
  
features:
  remote_sync_ui: true
  auto_refresh: true
  refresh_interval: 60000  # 1 minute
```

## Security Checklist

- [ ] **Environment Variables**: All tokens in env vars, not files
- [ ] **.gitignore**: Updated to exclude tokens and configs
- [ ] **No Commits**: Verify no tokens in git history
- [ ] **Token Rotation**: Regular token rotation schedule
- [ ] **Access Control**: Limit who has access to local machine
- [ ] **Network Security**: Use VPN or SSH for remote access
- [ ] **Monitoring**: Log sync operations for audit trail
- [ ] **Backup**: Regular backups of local SQLite database

## Monitoring and Logging

### Enable Verbose Logging

```bash
# CLI with debug output
export GTASKS_LOG_LEVEL=DEBUG
python -m gtasks_cli remote sync
```

### Dashboard Logging

```python
# In dashboard config
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/dashboard.log"
```

### Sync Audit Trail

The sync manager tracks:
- Last sync timestamp
- Number of tasks synced
- Conflicts resolved
- Errors encountered

Access via CLI:
```bash
python -m gtasks_cli remote status
```

## Troubleshooting

### Token Issues

```bash
# Check if token is set
echo $GTASKS_TURSO_TOKEN

# Test token validity
python -m gtasks_cli remote status

# Common errors:
# - "No auth token provided" → Set GTASKS_TURSO_TOKEN
# - "Invalid token" → Regenerate token in Turso dashboard
# - "Token expired" → Rotate token
```

### Connection Issues

```bash
# Test connection to Turso
python REMOTE_SYNC_TEST_SCRIPT.py --token $GTASKS_TURSO_TOKEN

# Check network connectivity
curl -I "https://gtasks-remote-db-sirusdas.aws-ap-south-1.turso.io"

# Verify URL format
# Should be: libsql://<database>.<region>.turso.io
```

### Sync Conflicts

```bash
# View sync conflicts
python -m gtasks_cli remote status

# Force push (overwrites remote with local)
python -m gtasks_cli remote push --force

# Force pull (overwrites local with remote)
python -m gtasks_cli remote pull --force

# Reset sync state
python -m gtasks_cli remote deactivate
python -m gtasks_cli remote activate
```

## Best Practices for Your Use Case

Since you want **configs local, dashboard remote**:

1. **Keep tokens only on your local machine**
   - Never set tokens on the remote dashboard server
   - Use SSH tunnel or VPN for access

2. **Use the remote Turso DB as intermediary**
   - Your local CLI syncs with Turso
   - Remote dashboard reads from Turso
   - Both systems stay in sync via the cloud DB

3. **Set up automated sync**
   ```bash
   # Cron job on local machine
   */5 * * * * export GTASKS_TURSO_TOKEN="..." && python -m gtasks_cli remote sync
   ```

4. **Dashboard fallback**
   - If local machine is offline, dashboard still shows last synced data
   - Dashboard can indicate when data was last updated

5. **Regular sync verification**
   ```bash
   # Weekly verification script
   python -m gtasks_cli remote status
   python -m gtasks_cli remote sync --dry-run
   ```

## Emergency Procedures

### Token Compromised

1. **Immediately rotate token** in Turso dashboard
2. **Update local environment variable**
3. **Check git history** for any accidental commits
4. **Review access logs** if available

### Data Sync Issues

1. **Check sync status**: `python -m gtasks_cli remote status`
2. **View recent logs**: Check dashboard logs
3. **Force full sync**: `python -m gtasks_cli remote sync --force`
4. **Manual intervention**: May need to restore from backup

### Dashboard Unavailable

1. **Access via alternative method** (VPN, SSH tunnel)
2. **Check local machine** is running
3. **Verify network connectivity**
4. **Fallback to CLI** for urgent task management

## Support and Resources

- **Turso Documentation**: https://docs.turso.co/
- **Project Issues**: Report bugs on GitHub
- **CLI Help**: `python -m gtasks_cli remote --help`
- **Dashboard Help**: Access via `/help` endpoint when running

---

**Remember**: Security is your responsibility. Never share tokens, always use environment variables, and regularly audit your configuration for potential exposure.
