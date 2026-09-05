#!/usr/bin/env python3
"""
Rose Creator Web & Mobile - Local Launcher
Esegui questo script per avviare il server e provarlo subito sia sul Mac sia su iPhone/iPad (stesso Wi-Fi).
"""

import socket
import sys
import os

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    local_ip = get_local_ip()
    port = 8000
    
    print("\n" + "═" * 65)
    print("  ⚽ ROSE CREATOR BY GIUSEPPE MAFFIA (WEB & MOBILE)")
    print("═" * 65)
    print(f"\n  🚀 Server locale attivo!")
    print(f"  💻 Dal tuo Mac apri nel browser:")
    print(f"     👉 http://localhost:{port}")
    print(f"\n  📱 Dal tuo iPhone / iPad / Android (stessa rete Wi-Fi):")
    print(f"     👉 http://{local_ip}:{port}")
    print(f"\n  ℹ️  Premi CTRL + C nel terminale per fermare il server.")
    print("═" * 65 + "\n")
    
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
