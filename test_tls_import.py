#!/usr/bin/env python3
"""Test TLS endpoints import"""
import sys
import os

# Add root to path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from services.wttj.app.tls_endpoints import router
    print("✅ SUCCESS: TLS endpoints imported successfully")
    print(f"Router: {router}")
    print(f"Router prefix: {router.prefix}")
    print(f"Router routes: {len(router.routes)}")
except Exception as e:
    print(f"❌ ERROR: Failed to import TLS endpoints")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    import traceback
    traceback.print_exc()
