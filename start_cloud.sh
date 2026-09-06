#!/bin/bash
# Avvia Rose Creator Web + Cloudflare Tunnel pubblico con protocollo resiliente HTTP/2

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "🔄 Pulizia processi precedenti..."
pkill -f "cloudflared tunnel" 2>/dev/null
pkill -f "uvicorn app.main:app" 2>/dev/null
sleep 1

# Pulisce il log del tunnel per non leggere vecchi URL scaduti
> "$DIR/tunnel.log"

echo "⚽ Avvio server locale Rose Creator..."
./venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
sleep 2

echo "🌐 Avvio Cloudflare Tunnel (modalità HTTP/2)..."
./bin/cloudflared tunnel --protocol http2 --no-autoupdate --url http://127.0.0.1:8000 --logfile "$DIR/tunnel.log" > /dev/null 2>&1 &

echo -n "⏳ Connessione al Cloudflare Edge in corso"
URL=""
for i in {1..15}; do
    sleep 1
    echo -n "."
    URL=$(grep -o "https://[-a-zA-Z0-9]*\.trycloudflare\.com" "$DIR/tunnel.log" | tail -n 1)
    if [ -n "$URL" ]; then
        break
    fi
done
echo ""

if [ -z "$URL" ]; then
    echo "⚠️ Attenzione: Impossibile generare il link in tempo."
    echo "Controlla il file tunnel.log per maggiori dettagli."
else
    echo ""
    echo "================================================================="
    echo "  ⚽ ROSE CREATOR BY GIUSEPPE MAFFIA (ONLINE CLOUD)"
    echo "================================================================="
    echo ""
    echo "  🌐 Nuovo Link Cloud Pubblico (HTTPS per iPhone & Android):"
    echo "     👉 $URL"
    echo ""
    echo "  📱 Aprilo su Safari (iPhone) o Chrome (Android)."
    echo "  💡 Suggerimento: Salvalo nella schermata Home per averlo come app nativa!"
    echo "================================================================="
fi
