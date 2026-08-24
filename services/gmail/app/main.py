"""
Gmail OAuth Service (Web Application Flow)
Handles Gmail authentication and email fetching using OAuth 2.0
Works with Web Application type OAuth credentials from Google Cloud
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import os
import json
import httpx
from datetime import datetime
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Swiply Gmail Service",
    description="Gmail OAuth and email management",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Try to load Gmail OAuth Configuration from web-type client secret file
OAUTH_CONFIG = None
GOOGLE_CLIENT_ID = None
GOOGLE_CLIENT_SECRET = None
REDIRECT_URI = "http://localhost:8008/oauth2callback"

# Look for web-type client secret in the app directory
app_dir = Path("services/gmail/app")
for file in app_dir.glob("client_secret_*.json"):
    try:
        with open(file, 'r') as f:
            config = json.load(f)
            if 'web' in config:  # Web application type
                oauth_config = config.get('web', {})
                GOOGLE_CLIENT_ID = oauth_config.get('client_id')
                GOOGLE_CLIENT_SECRET = oauth_config.get('client_secret')
                OAUTH_CONFIG = config
                logger.info(f"✅ Gmail OAuth config loaded from {file.name}")
                logger.info(f"   Client ID: {GOOGLE_CLIENT_ID[:30]}...")
                break
    except Exception as e:
        logger.warning(f"Could not load config from {file.name}: {e}")

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    logger.warning("⚠️  No valid OAuth web credentials found!")
    logger.warning("To set up Gmail OAuth:")
    logger.warning("1. Go to Google Cloud Console")
    logger.warning("2. Create OAuth 2.0 credentials (Web Application type)")
    logger.warning("3. Add authorized redirect URI: http://localhost:8008/oauth2callback")
    logger.warning("4. Download the JSON and place in: services/gmail/app/")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# Create tokens directory if it doesn't exist
TOKENS_DIR = Path("gmail_tokens")
TOKENS_DIR.mkdir(exist_ok=True)

# Store for user tokens (in production, use database)
user_tokens = {}

@app.get("/")
async def root():
    return {
        "service": "Gmail Service",
        "status": "operational",
        "port": 8008,
        "auth_type": "OAuth 2.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "gmail",
        "oauth_configured": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/start-gmail-auth/{user_id}")
async def start_gmail_auth(user_id: str):
    """Start Gmail OAuth flow - returns authorization URL"""
    try:
        logger.info(f"Starting Gmail auth for user: {user_id}")
        
        # Check if user already has valid Gmail token
        token_file = TOKENS_DIR / f"{user_id}_token.json"
        if token_file.exists():
            try:
                with open(token_file, 'r') as f:
                    token_data = json.load(f)
                    if token_data.get('access_token'):
                        logger.info(f"User {user_id} already has Gmail token")
                        return {
                            "success": True,
                            "already_connected": True,
                            "message": "Gmail already connected"
                        }
            except:
                pass
        
        # Generate OAuth authorization URL
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?" \
                  f"client_id={GOOGLE_CLIENT_ID}&" \
                  f"redirect_uri={REDIRECT_URI}&" \
                  f"response_type=code&" \
                  f"scope=https://www.googleapis.com/auth/gmail.readonly%20https://www.googleapis.com/auth/gmail.send&" \
                  f"access_type=offline&" \
                  f"prompt=consent&" \
                  f"state={user_id}"
        
        logger.info(f"Authorization URL generated for {user_id}")
        return {
            "success": True,
            "authorization_url": auth_url,
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Error starting Gmail auth: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/oauth2callback")
async def gmail_callback(code: str = Query(...), state: str = Query(...)):
    """Handle Gmail OAuth callback"""
    try:
        user_id = state
        logger.info(f"Gmail callback received for user: {user_id}, code length: {len(code)}")
        
        # Exchange code for token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": REDIRECT_URI,
                    "grant_type": "authorization_code"
                }
            )
        
        if token_response.status_code == 200:
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            # Save token to file
            token_file = TOKENS_DIR / f"{user_id}_token.json"
            with open(token_file, 'w') as f:
                json.dump(token_data, f)
            
            # Store in memory too
            user_tokens[user_id] = access_token
            logger.info(f"✅ Gmail connected for user: {user_id}")
            
            # Redirect back to frontend with success
            return RedirectResponse(
                url=f"http://localhost:5173/auth/gmail/success?user_id={user_id}"
            )
        else:
            logger.error(f"❌ Token exchange failed: {token_response.text}")
            error_detail = token_response.json().get("error", "token_exchange_failed")
            return RedirectResponse(
                url=f"http://localhost:5173/auth/gmail/error?reason={error_detail}"
            )
            
    except Exception as e:
        logger.error(f"Error in Gmail callback: {e}")
        return RedirectResponse(
            url=f"http://localhost:5173/auth/gmail/error?reason={str(e)}"
        )

@app.get("/inbox/{user_id}")
async def get_inbox(user_id: str, max_results: int = 50):
    """Get Gmail inbox with formatted WTTJ emails for user"""
    try:
        # Try to load token from file first
        token_file = TOKENS_DIR / f"{user_id}_token.json"
        access_token = None
        
        if token_file.exists():
            with open(token_file, 'r') as f:
                token_data = json.load(f)
                access_token = token_data.get('access_token')
        
        if not access_token and user_id in user_tokens:
            access_token = user_tokens[user_id]
        
        if not access_token:
            return {
                "success": False,
                "emails": [],
                "gmail_address": None,
                "total": 0,
                "unread": 0,
                "message": "Gmail not connected"
            }
        
        # Get Gmail profile to get the email address
        async with httpx.AsyncClient() as client:
            profile_response = await client.get(
                "https://www.googleapis.com/gmail/v1/users/me/profile",
                headers={"Authorization": f"Bearer {access_token}"}
            )
        
        if profile_response.status_code != 200:
            return {
                "success": False,
                "emails": [],
                "gmail_address": None,
                "total": 0,
                "unread": 0,
                "message": "Failed to fetch profile"
            }
        
        profile_data = profile_response.json()
        gmail_address = profile_data.get("emailAddress")
        messages_total = profile_data.get("messagesTotal", 0)
        messages_unread = profile_data.get("messagesUnread", 0)
        
        # Fetch WTTJ emails with multiple search queries
        wttj_emails = []
        search_queries = [
            'from:welcometothejungle.com',
            'subject:"Welcome to the Jungle"',
            'subject:WTTJ'
        ]
        
        async with httpx.AsyncClient() as client:
            for query in search_queries:
                try:
                    list_response = await client.get(
                        f"https://www.googleapis.com/gmail/v1/users/me/messages?q={query}&maxResults={max_results}",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    
                    if list_response.status_code == 200:
                        messages = list_response.json().get("messages", [])
                        
                        # Fetch full message details
                        for msg in messages:
                            try:
                                msg_response = await client.get(
                                    f"https://www.googleapis.com/gmail/v1/users/me/messages/{msg['id']}?format=full",
                                    headers={"Authorization": f"Bearer {access_token}"}
                                )
                                if msg_response.status_code == 200:
                                    msg_data = msg_response.json()
                                    headers = msg_data.get("payload", {}).get("headers", [])
                                    
                                    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
                                    from_addr = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
                                    date = next((h["value"] for h in headers if h["name"] == "Date"), "")
                                    
                                    # Get body
                                    body = ""
                                    if "parts" in msg_data.get("payload", {}):
                                        for part in msg_data["payload"]["parts"]:
                                            if part.get("mimeType") == "text/plain":
                                                if "data" in part.get("body", {}):
                                                    import base64
                                                    try:
                                                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode('utf-8')
                                                    except:
                                                        pass
                                    elif "body" in msg_data.get("payload", {}):
                                        if "data" in msg_data["payload"]["body"]:
                                            import base64
                                            try:
                                                body = base64.urlsafe_b64decode(msg_data["payload"]["body"]["data"]).decode('utf-8')
                                            except:
                                                pass
                                    
                                    # Check if already added
                                    email_id = msg['id']
                                    if not any(e['id'] == email_id for e in wttj_emails):
                                        wttj_emails.append({
                                            "id": msg['id'],
                                            "subject": subject,
                                            "from": from_addr,
                                            "sender": from_addr,
                                            "recipient": gmail_address,
                                            "date": date,
                                            "received_at": int(msg_data.get("internalDate", 0)) // 1000,
                                            "preview": body[:150] if body else "",
                                            "content": body,
                                            "body": body,
                                            "snippet": msg_data.get("snippet", ""),
                                            "category": "general",
                                            "read": False
                                        })
                            except Exception as e:
                                logger.error(f"Error processing message {msg['id']}: {e}")
                except Exception as e:
                    logger.warning(f"Search query '{query}' failed: {e}")
                    continue
        
        logger.info(f"Gmail inbox fetched for {user_id}: {len(wttj_emails)} emails")
        return {
            "success": True,
            "emails": wttj_emails,
            "gmail_address": gmail_address,
            "total": len(wttj_emails),
            "unread": len([e for e in wttj_emails if not e.get('read', False)]),
            "messages_total": messages_total,
            "messages_unread": messages_unread,
            "message": f"Found {len(wttj_emails)} WTTJ emails" if wttj_emails else "No WTTJ Emails Yet. Your WTTJ emails will appear here once you receive them."
        }
            
    except Exception as e:
        logger.error(f"Error fetching inbox: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fetch-wttj-emails/{user_id}")
async def fetch_wttj_emails(user_id: str, max_results: int = 50):
    """Fetch WTTJ emails from Gmail - triggers email refresh"""
    try:
        logger.info(f"Fetching WTTJ emails for user {user_id}")
        
        # Try to load token from file first
        token_file = TOKENS_DIR / f"{user_id}_token.json"
        access_token = None
        
        if token_file.exists():
            with open(token_file, 'r') as f:
                token_data = json.load(f)
                access_token = token_data.get('access_token')
        
        if not access_token and user_id in user_tokens:
            access_token = user_tokens[user_id]
        
        if not access_token:
            return {
                "success": False,
                "emails": [],
                "message": "Gmail not connected"
            }
        
        # Fetch emails from WTTJ - try multiple search queries
        wttj_emails = []
        search_queries = [
            'from:noreply@welcometothejungle.com',
            'from:welcome@welcometothejungle.com',
            'from:jobs@welcometothejungle.com',
            'from:recruiter@welcometothejungle.com',
            'subject:"Welcome to the Jungle"',
            'subject:WTTJ',
            'from:welcometothejungle.com'
        ]
        
        async with httpx.AsyncClient() as client:
            for query in search_queries:
                try:
                    list_response = await client.get(
                        f"https://www.googleapis.com/gmail/v1/users/me/messages?q={query}&maxResults={max_results}",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    
                    if list_response.status_code == 200:
                        messages = list_response.json().get("messages", [])
                        if messages:
                            logger.info(f"Found {len(messages)} emails with query: {query}")
                            
                            # Fetch full details for each email
                            for msg in messages:
                                try:
                                    msg_response = await client.get(
                                        f"https://www.googleapis.com/gmail/v1/users/me/messages/{msg['id']}?format=full",
                                        headers={"Authorization": f"Bearer {access_token}"}
                                    )
                                    if msg_response.status_code == 200:
                                        msg_data = msg_response.json()
                                        headers = msg_data.get("payload", {}).get("headers", [])
                                        
                                        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
                                        from_addr = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
                                        date = next((h["value"] for h in headers if h["name"] == "Date"), "")
                                        
                                        # Get body
                                        body = ""
                                        if "parts" in msg_data.get("payload", {}):
                                            for part in msg_data["payload"]["parts"]:
                                                if part.get("mimeType") == "text/plain":
                                                    if "data" in part.get("body", {}):
                                                        import base64
                                                        try:
                                                            body = base64.urlsafe_b64decode(part["body"]["data"]).decode('utf-8')
                                                        except:
                                                            pass
                                        elif "body" in msg_data.get("payload", {}):
                                            if "data" in msg_data["payload"]["body"]:
                                                import base64
                                                try:
                                                    body = base64.urlsafe_b64decode(msg_data["payload"]["body"]["data"]).decode('utf-8')
                                                except:
                                                    pass
                                        
                                        # Check if already added
                                        email_id = msg['id']
                                        if not any(e['id'] == email_id for e in wttj_emails):
                                            wttj_emails.append({
                                                "id": msg['id'],
                                                "subject": subject,
                                                "from": from_addr,
                                                "date": date,
                                                "preview": body[:150] if body else "",
                                                "body": body,
                                                "snippet": msg_data.get("snippet", "")
                                            })
                                except Exception as e:
                                    logger.error(f"Error processing message {msg['id']}: {e}")
                except Exception as e:
                    logger.warning(f"Search query '{query}' failed: {e}")
                    continue
        
        if not wttj_emails:
            logger.info(f"No WTTJ emails found for user {user_id}")
            return {
                "success": True,
                "emails": [],
                "message": "No WTTJ Emails Yet. Your WTTJ emails will appear here once you receive them."
            }
        
        logger.info(f"Fetched {len(wttj_emails)} WTTJ emails for user {user_id}")
        return {
            "success": True,
            "emails": wttj_emails,
            "total": len(wttj_emails),
            "message": f"Found {len(wttj_emails)} WTTJ emails"
        }
        
    except Exception as e:
        logger.error(f"Error fetching WTTJ emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/emails/{user_id}")
async def get_emails(user_id: str, max_results: int = 10):
    """Get Gmail emails for user - formatted for display"""
    try:
        # Try to load token from file first
        token_file = TOKENS_DIR / f"{user_id}_token.json"
        access_token = None
        
        if token_file.exists():
            with open(token_file, 'r') as f:
                token_data = json.load(f)
                access_token = token_data.get('access_token')
        
        if not access_token and user_id in user_tokens:
            access_token = user_tokens[user_id]
        
        if not access_token:
            return {
                "success": False,
                "emails": [],
                "wttj_emails": [],
                "total": 0,
                "message": "Gmail not connected"
            }
        
        # Fetch Gmail messages with multiple search queries to find WTTJ emails
        wttj_emails = []
        search_queries = [
            'from:welcometothejungle.com',
            'subject:"Welcome to the Jungle"',
            'subject:WTTJ'
        ]
        
        async with httpx.AsyncClient() as client:
            for query in search_queries:
                try:
                    list_response = await client.get(
                        f"https://www.googleapis.com/gmail/v1/users/me/messages?q={query}&maxResults={max_results}",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    
                    if list_response.status_code == 200:
                        messages = list_response.json().get("messages", [])
                        
                        # Fetch full message details for each email
                        for msg in messages:
                            try:
                                msg_response = await client.get(
                                    f"https://www.googleapis.com/gmail/v1/users/me/messages/{msg['id']}?format=full",
                                    headers={"Authorization": f"Bearer {access_token}"}
                                )
                                if msg_response.status_code == 200:
                                    msg_data = msg_response.json()
                                    headers = msg_data.get("payload", {}).get("headers", [])
                                    
                                    # Extract email details
                                    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
                                    from_addr = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
                                    date = next((h["value"] for h in headers if h["name"] == "Date"), "")
                                    
                                    # Get email body
                                    body = ""
                                    if "parts" in msg_data.get("payload", {}):
                                        for part in msg_data["payload"]["parts"]:
                                            if part.get("mimeType") == "text/plain":
                                                if "data" in part.get("body", {}):
                                                    import base64
                                                    try:
                                                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode('utf-8')
                                                    except:
                                                        pass
                                    elif "body" in msg_data.get("payload", {}):
                                        if "data" in msg_data["payload"]["body"]:
                                            import base64
                                            try:
                                                body = base64.urlsafe_b64decode(msg_data["payload"]["body"]["data"]).decode('utf-8')
                                            except:
                                                pass
                                    
                                    # Check if already added (avoid duplicates)
                                    email_id = msg['id']
                                    if not any(e['id'] == email_id for e in wttj_emails):
                                        wttj_emails.append({
                                            "id": msg['id'],
                                            "subject": subject,
                                            "from": from_addr,
                                            "date": date,
                                            "preview": body[:200] if body else "",
                                            "body": body,
                                            "snippet": msg_data.get("snippet", "")
                                        })
                            except Exception as e:
                                logger.error(f"Error processing message {msg['id']}: {e}")
                                continue
                except Exception as e:
                    logger.warning(f"Search query '{query}' failed: {e}")
                    continue
        
        if not wttj_emails:
            logger.info(f"No WTTJ emails found for user {user_id}")
            return {
                "success": True,
                "emails": [],
                "wttj_emails": [],
                "total": 0,
                "message": "No WTTJ Emails Yet. Your WTTJ emails will appear here once you receive them."
            }
        
        logger.info(f"Gmail emails fetched for {user_id}: {len(wttj_emails)} emails")
        return {
            "success": True,
            "emails": wttj_emails,
            "wttj_emails": wttj_emails,
            "total": len(wttj_emails),
            "message": f"Found {len(wttj_emails)} WTTJ emails"
        }
            
    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/disconnect/{user_id}")
async def disconnect_gmail(user_id: str):
    """Disconnect Gmail for user"""
    try:
        # Remove from memory
        if user_id in user_tokens:
            del user_tokens[user_id]
        
        # Remove token file
        token_file = TOKENS_DIR / f"{user_id}_token.json"
        if token_file.exists():
            token_file.unlink()
        
        logger.info(f"Gmail disconnected for user: {user_id}")
        
        return {
            "success": True,
            "message": "Gmail disconnected",
            "user_id": user_id
        }
    except Exception as e:
        logger.error(f"Error disconnecting Gmail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)

