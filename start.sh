#!/usr/bin/env bash
# Autocomply starten (Linux/macOS) — Gegenstück zu start.bat
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
API_PORT=8010

echo ""
echo "  AUTOCOMPLY START"
echo "  ================"
echo ""

echo "[1/5] Alte Prozesse beenden (Port 3000, $API_PORT)..."
fuser -k 3000/tcp "$API_PORT"/tcp 2>/dev/null
sleep 1

# venv anlegen/aktualisieren, falls nötig
PY="$ROOT/api/.venv/bin/python"
if [ ! -x "$PY" ]; then
    echo "[1b]  Python-venv anlegen und Abhängigkeiten installieren..."
    python3 -m venv "$ROOT/api/.venv"
    "$ROOT/api/.venv/bin/pip" install -q -r "$ROOT/api/requirements.txt"
fi

echo "[2/5] API starten (Port $API_PORT)..."
(cd "$ROOT/api" && exec "$PY" -m uvicorn main:app --host 127.0.0.1 --port "$API_PORT" --reload) &
API_PID=$!

echo "[3/5] Warte auf kalibrierte Checkliste-API..."
API_READY=0
for i in $(seq 1 25); do
    sleep 1
    HEALTH=$(curl -s --max-time 2 "http://127.0.0.1:$API_PORT/api/health" || true)
    case "$HEALTH" in
        *checklist*)
            echo "  API bereit: $HEALTH"
            API_READY=1
            break
            ;;
        "") echo "  ... ${i}s" ;;
        *)  echo "  ... falsche API-Version: $HEALTH" ;;
    esac
done
[ "$API_READY" = 1 ] || echo "  WARNUNG: API antwortet nicht korrekt auf Port $API_PORT"

echo "[4/5] Frontend starten (Port 3000, API-Proxy -> $API_PORT)..."
# NEXT_PUBLIC_API_URL absichtlich NICHT setzen — der Next-Rewrite
# (next.config.js) leitet /api standardmäßig auf 127.0.0.1:$API_PORT um.
(cd "$ROOT/frontend" && [ -d node_modules ] || npm install; cd "$ROOT/frontend" && exec npm run dev) &
FRONT_PID=$!

trap 'echo ""; echo "Beende..."; kill "$API_PID" "$FRONT_PID" 2>/dev/null; exit 0' INT TERM

echo "[5/5] Warte auf Frontend..."
for i in $(seq 1 30); do
    sleep 1
    if curl -s -o /dev/null --max-time 2 "http://127.0.0.1:3000"; then
        echo ""
        echo "  FERTIG! Öffne http://localhost:3000"
        break
    fi
    echo "  ... ${i}s"
done

echo ""
echo "  Terminal offen lassen — Beenden mit Ctrl+C."
echo ""
wait
