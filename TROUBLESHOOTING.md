# WTTJ Bot Bypass Troubleshooting Guide

## Quick Diagnosis

### Step 1: Test Locally First

Before testing on the server, run the local test to see what's happening:

```bash
cd C:\Users\hp\Downloads\IOP\WTJ
python test_bot_bypass_local.py
```

This will:
- Open Firefox (visible)
- Show you exactly what's happening
- Help identify where it's failing

### Step 2: Check Service Status

```bash
ssh root@69.62.110.23 "cd ~/nip && docker-compose ps wttj"
```

Should show: `Up`

### Step 3: Check Service Logs

```bash
ssh root@69.62.110.23 "cd ~/nip && docker-compose logs wttj --tail=50"
```

Look for:
- ✅ "TLS endpoints loaded" 
- ✅ "Bot bypass available: true"
- ❌ Any error messages

### Step 4: Test the API Endpoint

```bash
curl -X POST http://69.62.110.23:8012/api/v1/tls/health
```

Should return:
```json
{
  "status": "healthy",
  "bot_bypass_available": true
}
```

## Common Issues & Solutions

### Issue 1: "Bot bypass not available"

**Cause:** `wttj_bot_bypass.py` not in Docker image

**Solution:**
```bash
ssh root@69.62.110.23 "cd ~/nip && git pull && docker-compose build --no-cache wttj && docker-compose up -d wttj"
```

### Issue 2: "Could not click Agree button"

**Cause:** Button selector changed or page structure different

**Solution:** Run local test to see actual button text:
```bash
python test_bot_bypass_local.py
```

Check browser console output for button list.

### Issue 3: "Captcha not solved"

**Cause:** Captcha requires manual intervention

**Solution:** 
- Set `headless: false` to see the captcha
- Wait 30 seconds for manual solve
- Or use captcha solving service

### Issue 4: "Form not filled"

**Cause:** Field selectors don't match

**Solution:** Check logs for which fields failed:
```bash
docker-compose logs wttj | grep "Filling"
```

### Issue 5: "Cookies not accepted"

**Cause:** Cookie banner selector changed

**Solution:** Run with `headless: false` and observe cookie banner.

## Testing Commands

### 1. Test Complete Flow (Local)

```bash
python test_bot_bypass_local.py
```

### 2. Test Complete Flow (Server)

```bash
curl -X POST http://69.62.110.23:8012/api/v1/tls/bypass-and-create-account \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!@",
    "first_name": "John",
    "headless": false
  }'
```

### 3. Test Individual Steps

**Test Bot Bypass Only:**
```bash
curl -X POST http://69.62.110.23:8012/api/v1/tls/bypass-bot-challenge \
  -H "Content-Type: application/json" \
  -d '{
    "signup_url": "https://www.welcometothe.jungle/users/sign_up",
    "headless": false
  }'
```

**Test Account Creation (After Bypass):**
```bash
curl -X POST http://69.62.110.23:8012/api/v1/tls/create-account \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!@",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

## Debug Mode

To see detailed logs, check the container logs in real-time:

```bash
ssh root@69.62.110.23 "cd ~/nip && docker-compose logs -f wttj"
```

Press Ctrl+C to stop following.

## Manual Testing Steps

If automation isn't working, try manually:

1. Open Firefox
2. Go to: https://www.welcometothe.jungle/users/sign_up
3. Note what you see:
   - Cookie banner? (What's the button text?)
   - Captcha? (What type?)
   - Signup form? (What fields?)
   - What's the exact text on the yellow button?

4. Share this info to update selectors

## Current Known Button Text

Based on the screenshot, the button says:
**"Agree and create profile"**

Form fields:
- First name (placeholder: "Hope")
- Email (placeholder: shows gmail)
- Password (type: password)

## Need More Help?

Run the local test and share:
1. Screenshot of the browser at each step
2. Console output from the test
3. Any error messages

This will help identify exactly what's not working.
