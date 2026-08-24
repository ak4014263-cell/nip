#!/usr/bin/env python3
"""
WTTJ Service Launcher with proper Windows event loop configuration
"""
import sys
import asyncio

# CRITICAL: Set event loop policy BEFORE any other imports that might create an event loop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("✓ Windows ProactorEventLoop policy set before uvicorn starts")

# Now import and run uvicorn
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8012,
        reload=True,
        log_level="info"
    )
