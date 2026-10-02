# GTasks System Memory & Operational Guide

## Web Dashboard (Browser Interface)

- **URL**: [http://gtasks.com:48275](http://gtasks.com:48275) *(or [http://localhost:48275](http://localhost:48275) / [http://gtasks.local:48275](http://gtasks.local:48275))*
- **Port**: `48275` (mnemonic: spells `GTASK` on keypad: 4-8-2-7-5, avoiding standard web ports)
- **Hosts Entry**: `127.0.0.1 gtasks.com gtasks.local` in `/etc/hosts`
- **Shell Aliases**:
  - `gtasks-web` → opens `http://gtasks.com:48275` in default browser
  - `gtasks-ui` → alias to `gtasks-web`
- **Systemd User Service**: `gtasks-dashboard.service`
  - Location: `~/.config/systemd/user/gtasks-dashboard.service`
  - Dotfiles source: `~/.dotfiles/systemd/gtasks-dashboard.service`
  - Status check: `systemctl --user status gtasks-dashboard.service`
  - Restart: `systemctl --user restart gtasks-dashboard.service`
  - Logs: `journalctl --user -u gtasks-dashboard.service -f`
- **Boot Auto-Start**:
  - Enabled via `systemctl --user enable gtasks-dashboard.service`.
  - User lingering is active (`loginctl enable-linger sirus`), ensuring the service starts immediately upon system boot without requiring interactive login.
- **Service Configuration**:
  - Working Directory: `/run/media/sirus/workspace/projects/gtasks-terminal/gtasks_dashboard`
  - Executable: `/run/media/sirus/workspace/projects/gtasks-terminal/venv/bin/gunicorn -w 2 -b 0.0.0.0:48275 main_dashboard:app`
  - Config directory: `GTASKS_CONFIG_DIR=/home/sirus/.gtasks`
  - Data store: `/home/sirus/.gtasks/tasks.db`

## GTasks CLI & Google Authentication

- **Binary**: `/home/sirus/.local/bin/gtasks` (pipx venv at `/home/sirus/.local/share/pipx/venvs/gtasks-cli`)
- **Config Directory**: `/home/sirus/.gtasks`
- **OAuth Credentials**: `/home/sirus/.gtasks/credentials.json`
- **OAuth Token**: `/home/sirus/.gtasks/token.pickle`
- **OAuth Command**: `BROWSER=xdg-open gtasks auth` (or `gtasks auth` with terminal console URL fallback)

## Multi-Tier Architecture

1. **Local CLI & DB**: `gtasks-cli` operating on SQLite database (`~/.gtasks/tasks.db`).
2. **Web Dashboard**: Flask / Gunicorn REST & UI server at `http://gtasks.com:48275` with interactive D3.js visualization, multi-account filters, and priority metrics.
3. **Cloud Remote Sync (Turso)**: Ready for multi-device sync via Turso libSQL (`gtasks remote add <url> <token>`).
4. **Google Tasks API**: Upstream sync target via `gtasks advanced-sync`.
