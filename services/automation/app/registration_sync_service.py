#!/usr/bin/env python3
"""
Registration Sync Service - Backend Integration
Jab Swipply par user register kare, ye service automatically WTTJ form fill karegi
"""
from fastapi import FastAPI, BackgroundTasks, WebSocket
from pydantic import BaseModel
from playwright.async_api import async_playwright
import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Registration Sync Service")


class UserRegistrationData(BaseModel):
    """User ka registration data"""
    email: str
    password: str
    first_name: Optional[str] = "User"
    last_name: Optional[str] = "Swipply"
    role: str = "candidate"  # candidate or recruiter


class WTTJFormFiller:
    """WTTJ form automatically fill karta hai"""
    
    def __init__(self):
        self.active_sessions = {}
    
    async def fill_wttj_form(self, user_data: UserRegistrationData, session_id: str):
        """
        Background mein WTTJ form fill karo
        """
        try:
            logger.info(f"🚀 Starting WTTJ form filling for {user_data.email}")
            
            async with async_playwright() as p:
                # Headless browser (background mein chale)
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Load WTTJ signup page
                await page.goto("https://www.welcometothejungle.com/en/authenticate/signup")
                await asyncio.sleep(2)
                
                # Fill first name
                try:
                    first_name_field = page.locator('input[placeholder*="Anita"], input[name*="first"]').first
                    await first_name_field.fill(user_data.first_name)
                    logger.info(f"   ✓ First name: {user_data.first_name}")
                except Exception as e:
                    logger.error(f"   ✗ First name error: {e}")
                
                # Fill email
                try:
                    email_field = page.locator('input[type="email"]')
                    await email_field.fill(user_data.email)
                    logger.info(f"   ✓ Email: {user_data.email}")
                except Exception as e:
                    logger.error(f"   ✗ Email error: {e}")
                
                # Fill password (make it strong for WTTJ)
                try:
                    strong_password = user_data.password + "Wttj2026!@"
                    password_field = page.locator('input[type="password"]').first
                    await password_field.fill(strong_password)
                    logger.info(f"   ✓ Password: {strong_password}")
                except Exception as e:
                    logger.error(f"   ✗ Password error: {e}")
                
                # Check terms checkbox
                try:
                    checkbox = page.locator('input[type="checkbox"]').first
                    await checkbox.click(force=True)
                    logger.info("   ✓ Checkbox checked")
                except:
                    pass
                
                # Check if button is enabled
                button = page.locator('button[type="submit"]').first
                is_enabled = await button.is_enabled()
                
                if is_enabled:
                    logger.info("✅ WTTJ form is ready!")
                    
                    # Store session info
                    self.active_sessions[session_id] = {
                        "status": "ready",
                        "email": user_data.email,
                        "page": page,
                        "browser": browser
                    }
                    
                    # Keep browser open for 5 minutes for user to click
                    await asyncio.sleep(300)
                    
                else:
                    logger.warning("⚠️  Button is disabled - validation issue")
                    self.active_sessions[session_id] = {
                        "status": "error",
                        "error": "Button disabled"
                    }
                
                await browser.close()
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            self.active_sessions[session_id] = {
                "status": "error",
                "error": str(e)
            }


# Global instance
form_filler = WTTJFormFiller()


@app.post("/api/sync-registration")
async def sync_registration(user_data: UserRegistrationData, background_tasks: BackgroundTasks):
    """
    Jab user Swipply par register kare, ye API call hoga
    
    Example frontend code:
    ```javascript
    // Swipply registration submit handler
    const handleRegister = async (formData) => {
        // 1. Register on Swipply
        await fetch('/api/register', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        // 2. Trigger WTTJ form filling in background
        await fetch('http://localhost:8000/api/sync-registration', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    };
    ```
    """
    session_id = f"session_{user_data.email}_{asyncio.get_event_loop().time()}"
    
    # Background task start karo
    background_tasks.add_task(form_filler.fill_wttj_form, user_data, session_id)
    
    return {
        "success": True,
        "message": "WTTJ form filling started in background",
        "session_id": session_id
    }


@app.get("/api/sync-status/{session_id}")
async def get_sync_status(session_id: str):
    """
    Check karo ki WTTJ form filling ka status kya hai
    """
    if session_id in form_filler.active_sessions:
        return {
            "success": True,
            "status": form_filler.active_sessions[session_id]
        }
    else:
        return {
            "success": False,
            "error": "Session not found"
        }


@app.websocket("/ws/registration-sync")
async def websocket_sync(websocket: WebSocket):
    """
    Real-time updates via WebSocket
    Frontend ko real-time updates bhejo
    
    Frontend code:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/registration-sync');
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('WTTJ form status:', data);
        
        if (data.status === 'ready') {
            // Show notification: "WTTJ form is ready!"
        }
    };
    
    // Send user data when they register
    ws.send(JSON.stringify({
        action: 'register',
        data: formData
    }));
    ```
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive user data from frontend
            data = await websocket.receive_json()
            
            if data.get('action') == 'register':
                user_data = UserRegistrationData(**data['data'])
                session_id = f"ws_{user_data.email}"
                
                # Start background filling
                asyncio.create_task(form_filler.fill_wttj_form(user_data, session_id))
                
                # Send updates
                await websocket.send_json({
                    "status": "started",
                    "message": "WTTJ form filling started"
                })
                
                # Monitor progress
                for i in range(30):  # 30 seconds monitoring
                    await asyncio.sleep(1)
                    
                    if session_id in form_filler.active_sessions:
                        status = form_filler.active_sessions[session_id]['status']
                        await websocket.send_json({
                            "status": status,
                            "progress": (i + 1) * 3  # percentage
                        })
                        
                        if status == "ready":
                            await websocket.send_json({
                                "status": "complete",
                                "message": "WTTJ form is ready to submit!"
                            })
                            break
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@app.get("/")
async def root():
    """API info"""
    return {
        "service": "Registration Sync Service",
        "description": "Automatically fills WTTJ form when user registers on Swipply",
        "endpoints": {
            "POST /api/sync-registration": "Start background WTTJ form filling",
            "GET /api/sync-status/{session_id}": "Check filling status",
            "WS /ws/registration-sync": "Real-time updates via WebSocket"
        },
        "usage": {
            "1": "User registers on Swipply",
            "2": "Swipply calls this API",
            "3": "WTTJ form fills automatically in background",
            "4": "User can submit WTTJ form when ready"
        }
    }


if __name__ == '__main__':
    import uvicorn
    
    print("\n" + "="*80)
    print("REGISTRATION SYNC SERVICE")
    print("="*80)
    print("\nStarting service on http://localhost:8012")
    print("\nIntegration with Swipply:")
    print("  1. Add this to Swipply registration handler:")
    print("     fetch('http://localhost:8012/api/sync-registration', ...)")
    print("  2. Service will auto-fill WTTJ form in background")
    print("  3. User can check WTTJ and submit when ready")
    print("="*80 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8012, log_level="info")
