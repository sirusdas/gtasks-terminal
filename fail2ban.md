To set up Fail2Ban as a Senior Engineer, you’ll want a configuration that is clean, modular, and won't accidentally lock you out of your own server.

Since you are running **Nginx** on what looks like a Linux environment (likely Ubuntu/Debian based on the paths), here is the professional way to set it up.



---

## 1. Installation
First, install the package and ensure it's running.

```bash
sudo apt update
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## 2. Global Configuration (The "Safety Net")
Never edit `jail.conf` directly, as updates will overwrite it. Always create a `.local` file.

**Create/Edit:** `/etc/fail2ban/jail.local`
Add your own IP to the `ignoreip` line so you never get locked out.

```ini
[DEFAULT]
# Whitelist your own IP(s) here
ignoreip = 127.0.0.1/8 ::1 1.2.3.4  

# How long they are banned (1 hour)
bantime  = 3600

# Window of time to count retries (10 minutes)
findtime = 600

# Number of "hits" before they are banned
maxretry = 5

# Use nftables or iptables for the ban
banaction = iptables-multiport
```

---

## 3. Create a Custom Filter for your Logs
Your logs show specific probes for `.env` and `.php` files. We need a regex "filter" to catch these patterns.

**Create:** `/etc/fail2ban/filter.d/nginx-probing.conf`

```ini
[Definition]
failregex = ^<HOST> -.*"(GET|POST|HEAD) .*\.(env|php|bak|sql|config).* HTTP.*" (404|403|400)
            ^<HOST> -.*"(GET|POST|HEAD) /wp-.* HTTP.*" (404|403|400)
ignoreregex = 
```

---

## 4. Activate the Nginx Jail
Now, tell Fail2Ban to use that filter on your actual Nginx logs.

**Add to the end of:** `/etc/fail2ban/jail.local`

```ini
[nginx-probing]
enabled  = true
port     = http,https
filter   = nginx-probing
logpath  = /var/log/nginx/access.log
maxretry = 3
bantime  = 86400 
# Note: I set this to 24 hours because these specific probes are 100% malicious.
```

---

## 5. Verify and Restart
After saving the files, test your configuration and restart the service.

```bash
# Test the regex against your log file to see if it catches anything
fail2ban-regex /var/log/nginx/access.log /etc/fail2ban/filter.d/nginx-probing.conf

# Restart the service
sudo systemctl restart fail2ban

# Check the status of your new jail
sudo fail2ban-client status nginx-probing
```

---

### Key Commands for Management
* **Unban an IP:** `sudo fail2ban-client set nginx-probing unbanip <IP_ADDRESS>`
* **Check current bans:** `sudo fail2ban-client status nginx-probing`
* **View Fail2Ban logs:** `tail -f /var/log/fail2ban.log`

### Pro-Tip: The "Recidive" Jail
Since you've seen these attacks multiple times, you might want a **Recidive Jail**. This looks at the Fail2Ban log itself; if an IP gets banned 3 times in one day, it bans them for **one month**. It's the ultimate "go away" for bots.

Would you like the configuration for that long-term "Recidive" ban as well?


---

### 1. Start the Jail
Since the regex is verified, restart Fail2Ban to apply the configuration from your `jail.local` file:

```bash
sudo systemctl restart fail2ban
```

### 2. Verify the Active Jail
Check that `nginx-probing` is now officially running:

```bash
sudo fail2ban-client status nginx-probing
```

### 3. Check for Banned IPs
As soon as those bots hit your server again, they will be moved to the "Banned IP list." You can see the live count by running:

```bash
# This shows you the current 'Jail' stats and banned IPs
sudo fail2ban-client status nginx-probing
```

---

### How to Monitor the Action
Since you are likely curious to see it in real-time, you can tail the Fail2Ban log. This is where you'll see lines saying **[nginx-probing] Ban 40.85.246.124**:

```bash
sudo tail -f /var/log/fail2ban.log
```



### What happens next?
If an IP is banned, Fail2Ban has added a rule to your server's firewall (iptables). That IP can no longer even establish a connection to your Nginx port for the duration of the `bantime` you set (which we set to 24 hours).

**Would you like me to show you how to set up a "Slack" or "Email" notification so you get alerted whenever a new attacker is banned?**