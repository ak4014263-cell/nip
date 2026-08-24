#!/usr/bin/env python3
"""
Script to run all Python microservices in development mode
"""
import subprocess
import sys
import time
import os
from pathlib import Path

SERVICES = [
    {"name": "auth", "port": 8001},
    {"name": "profile", "port": 8004},
    {"name": "job", "port": 8003},
    {"name": "credential", "port": 8009},
    {"name": "email", "port": 8007},
    {"name": "automation", "port": 8006},
    {"name": "ai", "port": 8010},
    {"name": "wttj", "port": 8012},
    {"name": "wttj_scraper", "port": 8013}
]

def run_service(service_name, port):
    """Run a single service"""
    service_path = Path(__file__).parent / service_name
    
    if not service_path.exists():
        print(f"❌ Service directory not found: {service_path}")
        return None
    
    print(f"🚀 Starting {service_name} service on port {port}...")
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        "PORT": str(port),
        "DATABASE_URL": "postgresql://swiply:swiply123@localhost:5432/swiply",
        "REDIS_URL": "redis://localhost:6379/0",
        "ENCRYPTION_KEY": "your-32-byte-encryption-key-here",
        "HEADLESS": "true"
    })
    
    try:
        root_path = Path(__file__).parent.parent
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", f"services.{service_name}.app.main:app", "--host", "0.0.0.0", "--port", str(port)],
            cwd=root_path,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        return process
    except Exception as e:
        print(f"❌ Failed to start {service_name}: {e}")
        return None

def main():
    """Run all services"""
    print("🔥 Swiply Microservices Launcher")
    print("=" * 40)
    
    # Check if infrastructure is running
    print("🔍 Checking infrastructure...")
    
    processes = []
    
    try:
        for service in SERVICES:
            process = run_service(service["name"], service["port"])
            if process:
                processes.append((service["name"], process))
                time.sleep(2)  # Stagger startup
        
        print("\n✅ All services started!")
        print("\n📊 Service Status:")
        for name, process in processes:
            status = "🟢 Running" if process.poll() is None else "🔴 Stopped"
            print(f"  {name}: {status}")
        
        print("\n🌐 API Endpoints:")
        for service in SERVICES:
            print(f"  {service['name']}: http://localhost:{service['port']}/docs")
        
        print("\n📝 Logs will appear below. Press Ctrl+C to stop all services.\n")
        
        # Monitor processes and show logs
        while True:
            for name, process in processes:
                if process.poll() is not None:
                    print(f"❌ {name} service stopped unexpectedly")
                    return
                
                # Read and display logs
                try:
                    line = process.stdout.readline()
                    if line:
                        print(f"[{name}] {line.strip()}")
                except:
                    pass
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        for name, process in processes:
            print(f"  Stopping {name}...")
            process.terminate()
            process.wait()
        print("✅ All services stopped.")

if __name__ == "__main__":
    main()