#!/bin/sh
# init.sh — cria a entidade Crusher:001 no Orion e a subscription no QuantumLeap
# Aguarda os serviços ficarem disponíveis antes de agir.

ORION="http://orion:1026"
QL="http://quantumleap:8668"

wait_for() {
  URL=$1
  echo "Aguardando $URL ..."
  until curl -sf "$URL" > /dev/null 2>&1; do
    sleep 3
  done
  echo "$URL disponível."
}

wait_for "$ORION/version"
wait_for "$QL/v2/version"

# ── Cria entidade Crusher:001 ──────────────────────────────────────────────
echo "Criando entidade Crusher:001 ..."
curl -s -o /dev/null -w "Orion create entity: %{http_code}\n" \
  -X POST "$ORION/v2/entities" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "Crusher:001",
    "type": "Crusher",
    "temperature": { "value": 60, "type": "Number" },
    "vibration":   { "value": 3,  "type": "Number" },
    "current":     { "value": 100,"type": "Number" },
    "production":  { "value": 100,"type": "Number" },
    "status":      { "value": "NORMAL", "type": "Text" },
    "timestamp":   { "value": "2026-01-01T00:00:00Z", "type": "DateTime" }
  }'

# ── Cria subscription NGSI-v2 → QuantumLeap ───────────────────────────────
echo "Criando subscription no QuantumLeap ..."
curl -s -o /dev/null -w "Orion subscription: %{http_code}\n" \
  -X POST "$ORION/v2/subscriptions" \
  -H "Content-Type: application/json" \
  -d @/subscriptions/quantumleap_subscription.json

echo "Inicialização concluída."