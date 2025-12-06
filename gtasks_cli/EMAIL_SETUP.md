# Email Configuration Guide for GTasks CLI

This guide will help you configure email functionality in GTasks CLI to send reports via email using Gmail.

## Prerequisites

- A Gmail account
- GTasks CLI installed and configured

## Gmail Setup

### Step 1: Enable 2-Step Verification (if not already enabled)

1. Go to your Google Account: https://myaccount.google.com/
2. Navigate to **Security** → **2-Step Verification**
3. Follow the prompts to enable 2-Step Verification

### Step 2: Generate an App Password

Since Gmail requires App Passwords for third-party applications when 2-Step Verification is enabled:

1. Go to your Google Account: https://myaccount.google.com/
2. Navigate to **Security** → **2-Step Verification** → **App passwords**
   - Or directly visit: https://myaccount.google.com/apppasswords
3. Select **App**: Choose "Mail" or "Other (Custom name)"
4. If choosing "Other", enter a name like "GTasks CLI"
5. Click **Generate**
6. **Copy the 16-character password** (it will look like: `xxxx xxxx xxxx xxxx`)
   - **Important**: You won't be able to see this password again, so save it securely

### Step 3: Configure Environment Variables

You need to set two environment variables:
- `GTASKS_EMAIL_USER`: Your Gmail address
- `GTASKS_EMAIL_PASSWORD`: The App Password you just generated

#### Option A: Temporary Setup (Current Session Only)

```bash
export GTASKS_EMAIL_USER="your.email@gmail.com"
export GTASKS_EMAIL_PASSWORD="xxxx xxxx xxxx xxxx"
```

#### Option B: Permanent Setup (Recommended)

Add these lines to your shell configuration file:

**For Zsh (macOS default):**
```bash
echo 'export GTASKS_EMAIL_USER="your.email@gmail.com"' >> ~/.zshrc
echo 'export GTASKS_EMAIL_PASSWORD="xxxx xxxx xxxx xxxx"' >> ~/.zshrc
source ~/.zshrc
```

**For Bash:**
```bash
echo 'export GTASKS_EMAIL_USER="your.email@gmail.com"' >> ~/.bashrc
echo 'export GTASKS_EMAIL_PASSWORD="xxxx xxxx xxxx xxxx"' >> ~/.bashrc
source ~/.bashrc
```

**Important Security Notes:**
- Never commit these credentials to version control
- Keep your App Password secure
- You can revoke the App Password anytime from your Google Account settings

## Testing Email Configuration

### Test 1: Verify Environment Variables

```bash
echo $GTASKS_EMAIL_USER
echo $GTASKS_EMAIL_PASSWORD
```

Both should display your configured values.

### Test 2: Send a Test Report

Generate and email a simple report:

```bash
gtasks generate-report rp10 \
  --filter this_week:created_at \
  --email your.email@gmail.com
```

You should receive an email with the report content.

## Using Email with Reports

### Basic Usage

Send any report via email using the `--email` flag:

```bash
gtasks generate-report <report_id> --email recipient@example.com
```

### Examples

**Send weekly summary:**
```bash
gtasks generate-report rp10 \
  --filter this_week:created_at \
  --tags "***|--ex:cr" \
  --email your.email@gmail.com
```

**Send custom filtered report:**
```bash
gtasks generate-report rp10 \
  --filter past2weeks:created_at \
  --tags "prasen|--ex:cr" \
  --output-tags "--group:1[prasen,***,urgent],2[prod]" \
  --only-pending \
  --email manager@example.com
```

**Save to file AND send via email:**
```bash
gtasks generate-report rp10 \
  --filter this_week:created_at \
  --output report.txt \
  --email your.email@gmail.com
```

## Troubleshooting

### Error: "Email credentials not configured"

**Solution**: Ensure environment variables are set correctly:
```bash
echo $GTASKS_EMAIL_USER
echo $GTASKS_EMAIL_PASSWORD
```

If empty, follow Step 3 again.

### Error: "Authentication failed" or "Username and Password not accepted"

**Possible causes:**
1. **Using regular Gmail password instead of App Password**
   - Solution: Generate and use an App Password (see Step 2)
2. **2-Step Verification not enabled**
   - Solution: Enable 2-Step Verification (see Step 1)
3. **Incorrect App Password**
   - Solution: Generate a new App Password and update the environment variable

### Error: "SMTPAuthenticationError"

**Solution**: 
1. Verify your Gmail address is correct
2. Regenerate the App Password
3. Ensure there are no extra spaces in the password

### Email not received

**Check:**
1. Spam/Junk folder
2. Recipient email address is correct
3. Check Gmail's "Sent" folder to confirm the email was sent

## Security Best Practices

1. **Use App Passwords**: Never use your main Gmail password
2. **Limit Access**: Only set environment variables on trusted machines
3. **Revoke When Done**: If you stop using GTasks CLI, revoke the App Password from your Google Account
4. **Separate Account**: Consider using a dedicated Gmail account for automated emails
5. **Environment Files**: If using `.env` files, add them to `.gitignore`

## Alternative: Using a Configuration File

If you prefer not to use environment variables, you can modify the code to read from a config file:

```yaml
# ~/.gtasks/email_config.yaml
email:
  user: "your.email@gmail.com"
  password: "xxxx xxxx xxxx xxxx"
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
```

**Note**: This requires code modification and is less secure than environment variables.

## Additional Resources

- [Google App Passwords Help](https://support.google.com/accounts/answer/185833)
- [Gmail SMTP Settings](https://support.google.com/mail/answer/7126229)
- [2-Step Verification](https://support.google.com/accounts/answer/185839)

## Support

If you encounter issues not covered here, please check:
1. GTasks CLI logs for detailed error messages
2. Verify your Gmail account settings
3. Ensure no firewall is blocking SMTP connections (port 587)
