# WTTJ Bot/Captcha Bypass Guide

## Overview

The system now includes an automated bot/captcha bypass handler that uses Firefox with stealth techniques to bypass Cloudflare, reCAPTCHA, and other bot detection challenges before account creation.

## How It Works

### Bot Bypass Handler Components

1. **Stealth Firefox Browser**
   - Uses Playwright with Firefox
   - Anti-automation detection headers
   - Realistic user-agent strings
   - Proper viewport and timezone settings

2. **Challenge Detection**
   - Detects Cloudflare challenges
   - Detects reCAPTCHA challenges
   - Waits for JavaScript execution
   - Monitors page loading state

3. **Automatic Bypass**
   - Handles Cloudflare with proper headers and waiting
   - Attempts reCAPTCHA checkbox clicking
   - Waits for network idle state
   - Redirects handling

## API Endpoints

### 1. Bypass Bot Challenge

**Endpoint:** `POST /api/v1/tls/bypass-bot-challenge`

**Purpose:** Open Firefox, navigate to WTTJ signup URL, and bypass any bot/captcha challenges

**Parameters:**
```json
{
  "signup_url": "https://www.welcometothe.jungle/users/sign_up",
  "headless": false,
  "proxy": "http://user:pass@proxy:8080"
}
```

**Response:**
```json
{
  "status": "bypassed",
  "url": "https://www.welcometothe.jungle/users/sign_up",
  "message": "Successfully bypassed bot/captcha challenge",
  "page_ready": true
}
```

**Options:**
- `signup_url`: WTTJ signup page URL (default: official signup page)
- `headless`: Run Firefox in headless mode or visible (default: false - shows browser)
- `proxy`: Optional proxy for requests (recommended for anonymity)

### 2. Create Account (After Bypass)

**Endpoint:** `POST /api/v1/tls/create-account`

**Purpose:** Create account after successful bot bypass

**Parameters:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!@",
  "first_name": "John",
  "last_name": "Doe",
  "ip_address": "203.0.113.1",
  "use_hybrid": true
}
```

**Workflow:**
1. Call `bypass-bot-challenge` first
2. Wait for success response
3. Call `create-account` with user details
4. Account is created with TLS protection

## Usage Workflow

### Step 1: Bypass Bot Challenge

```bash
curl -X POST http://69.62.110.23:8012/api/v1/tls/bypass-bot-challenge \
  -H "Content-Type: application/json" \
  -d '{
    "signup_url": "https://www.welcometothe.jungle/users/sign_up",
    "headless": false,
    "proxy": "http://user:pass@proxy:8080"
  }'
```

**Response:**
```json
{
  "status": "bypassed",
  "page_ready": true,
  "message": "Successfully bypassed bot/captcha challenge"
}
```

### Step 2: Create Account

Once bot challenge is bypassed:

```bash
curl -X POST http://69.62.110.23:8012/api/v1/tls/create-account \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePass123!@",
    "first_name": "John",
    "last_name": "Doe",
    "use_hybrid": true
  }'
```

**Response:**
```json
{
  "status": "created",
  "data": {
    "success": true,
    "email": "newuser@example.com",
    "message": "Account created successfully"
  }
}
```

## Features

### Stealth Techniques

- ✅ **Anti-Automation Detection**
  - Disables `AutomationControlled` blink features
  - Sets realistic user-agent
  - Proper timezone and locale settings

- ✅ **Browser Context Spoofing**
  - Realistic viewport (1920x1080)
  - Proper Accept-Language headers
  - Accept-Encoding with compression support
  - Cache-Control headers

- ✅ **Challenge Handling**
  - Cloudflare bypass with waiting
  - reCAPTCHA checkbox interaction
  - Network idle monitoring
  - JavaScript execution wait

### Rate Limiting & Safety

- **Adaptive rate limiting** between account creations
- **IP rotation** for multiple accounts
- **User-agent rotation** to avoid pattern detection
- **Proxy support** for anonymity
- **Jitter/random delays** for human-like behavior

## Configuration

### Rate Limits

```bash
curl -X POST http://69.62.110.23:8012/api/v1/tls/configure-limits \
  -H "Content-Type: application/json" \
  -d '{
    "min_delay_between_requests": 3.0,
    "max_delay_between_requests": 10.0,
    "max_requests_per_ip_per_hour": 5,
    "max_requests_per_ip_per_day": 20,
    "max_requests_per_email_per_day": 1,
    "enable_jitter": true,
    "enable_proxy_rotation": true,
    "enable_ua_rotation": true
  }'
```

### Proxies

```bash
curl -X POST http://69.62.110.23:8012/api/v1/tls/configure-proxies \
  -H "Content-Type: application/json" \
  -d '{
    "proxies": [
      "http://user:pass@proxy1:8080",
      "http://user:pass@proxy2:8080",
      "http://user:pass@proxy3:8080"
    ]
  }'
```

## Health Check

```bash
curl http://69.62.110.23:8012/api/v1/tls/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "tls-account-creation",
  "requests_processed": 0,
  "rate_limiter_active": true,
  "bot_bypass_available": true
}
```

## Troubleshooting

### Bot Bypass Fails

1. **Check browser visibility**: Set `headless: false` to see what's happening
2. **Verify proxy**: Test proxy connection separately
3. **Check WTTJ URL**: Make sure signup URL is correct
4. **Wait longer**: Some challenges take 30-60 seconds

### Account Creation Fails After Bypass

1. **Check email format**: Must be valid email
2. **Check password**: Must meet requirements (8+ chars, mix of types)
3. **Check rate limits**: May be throttled - wait before retry
4. **Check proxy rotation**: Some proxies may be blocked

### Page Still Shows Challenge

1. Increase timeout (currently 60 seconds)
2. Try different proxy
3. Check browser logs: `docker-compose logs wttj`
4. Verify JavaScript is enabled

## Technical Details

### Browser Settings

- **Engine**: Firefox (better stealth than Chromium)
- **Viewport**: 1920x1080 (realistic)
- **User-Agent**: Mozilla/5.0 Firefox/120.0
- **Timezone**: America/New_York
- **Locale**: en-US

### Challenge Handling

**Cloudflare:**
- Waits for `networkidle` state
- Monitors for challenge frames
- Clicks challenge button if present
- Handles JavaScript-based challenges

**reCAPTCHA:**
- Detects reCAPTCHA iframe
- Attempts checkbox click
- Waits 3 seconds for processing
- Falls back gracefully

## Performance

- **Bot Bypass Time**: 15-60 seconds (depends on challenge complexity)
- **Account Creation Time**: 3-10 seconds (after bypass)
- **Rate Limit**: 1-5 accounts per hour per IP (configurable)
- **Concurrent**: Up to 10 simultaneous bypasses

## Security Notes

1. **Proxy Recommended**: Use proxy for production account creation
2. **Rate Limiting**: Enable to avoid detection
3. **User-Agent Rotation**: Automatically enabled
4. **Jitter**: Adds random delays for human-like behavior

## Next Steps

1. Start bot bypass: Call `/bypass-bot-challenge` endpoint
2. Wait for success confirmation
3. Create account: Call `/create-account` endpoint
4. Monitor: Check statistics with `/statistics` endpoint
5. Export: Get full report with `/export-report` endpoint

---

**System Ready**: The bot bypass handler is active and ready to bypass anti-bot challenges automatically!
