#!/bin/bash
echo "🛑 Arresto Rose Creator e Cloudflare Tunnel..."
pkill -f "cloudflared tunnel" 2>/dev/null
pkill -f "uvicorn app.main:app" 2>/dev/null
echo "✅ Processi arrestati con successo."
