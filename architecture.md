# Gêmeo Digital — Britador de Minério
## Documentação de Arquitetura

---

## Visão Geral

```
Python Publisher
    │  publica JSON a cada 5s
    ▼
MQTT (Mosquitto :1883)
    │  tópico: mining/crusher/telemetry
    ▼
Node-RED (:1880)
    │  valida payload
    │  aplica regra de negócio (temperatura > 80 AND vibração > 10 → ALERTA)
    │  monta payload NGSI-v2
    ▼
Orion Context Broker (:1026)
    │  mantém estado atual de Crusher:001
    │  dispara notificação via subscription
    ▼
QuantumLeap (:8668)
    │  recebe notificação NGSI-v2
    │  persiste série temporal
    ▼
CrateDB (:4200)
    │  armazena tabela etcrushercrusher001
    ▼
Streamlit (:8501)
    consulta Orion (tempo real)
    consulta QuantumLeap (histórico)
    exibe dashboard
```

---

## Serviços e Portas

| Serviço       | Porta | Uso                          |
|---------------|-------|------------------------------|
| Mosquitto     | 1883  | MQTT TCP                     |
| Mosquitto     | 9001  | MQTT WebSocket               |
| MongoDB       | 27017 | Backend do Orion             |
| Orion         | 1026  | NGSI-v2 API                  |
| CrateDB       | 4200  | Admin UI + HTTP SQL          |
| CrateDB       | 5432  | PostgreSQL wire              |
| QuantumLeap   | 8668  | Time-series API              |
| Node-RED      | 1880  | Editor de fluxo              |
| Streamlit     | 8501  | Dashboard                    |

---

## Como Iniciar

```bash
# Clone / entre no diretório do projeto
cd project/

# Suba toda a stack
docker compose up -d --build

# Verifique os logs
docker compose logs -f publisher nodered
```

---

## Comandos curl — Orion Context Broker

### Verificar versão do Orion
```bash
curl -s http://localhost:1026/version | python3 -m json.tool
```

### Criar entidade (executado pelo init automaticamente)
```bash
curl -s -X POST http://localhost:1026/v2/entities \
  -H "Content-Type: application/json" \
  -d '{
    "id": "Crusher:001",
    "type": "Crusher",
    "temperature": { "value": 60,      "type": "Number"   },
    "vibration":   { "value": 3,       "type": "Number"   },
    "current":     { "value": 100,     "type": "Number"   },
    "production":  { "value": 100,     "type": "Number"   },
    "status":      { "value": "NORMAL","type": "Text"     },
    "timestamp":   { "value": "2026-01-01T00:00:00Z", "type": "DateTime" }
  }'
```

### Consultar entidade atual
```bash
curl -s http://localhost:1026/v2/entities/Crusher:001 | python3 -m json.tool
```

### Atualizar atributos manualmente (exemplo ALERTA)
```bash
curl -s -X PATCH http://localhost:1026/v2/entities/Crusher:001/attrs \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": { "value": 92, "type": "Number" },
    "vibration":   { "value": 13, "type": "Number" },
    "status":      { "value": "ALERTA", "type": "Text" }
  }'
```

### Listar subscriptions ativas
```bash
curl -s http://localhost:1026/v2/subscriptions | python3 -m json.tool
```

---

## Comandos curl — QuantumLeap

### Verificar versão
```bash
curl -s http://localhost:8668/v2/version
```

### Criar subscription (executado pelo init automaticamente)
```bash
curl -s -X POST http://localhost:1026/v2/subscriptions \
  -H "Content-Type: application/json" \
  -d @subscriptions/quantumleap_subscription.json
```

### Consultar últimas 10 leituras
```bash
curl -s "http://localhost:8668/v2/entities/Crusher:001/attrs?limit=10&lastN=10"
```

### Consultar as últimas 24h
```bash
curl -s "http://localhost:8668/v2/entities/Crusher:001/attrs?fromDate=$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)&limit=10000"
```

---

## CrateDB — Estrutura e Consultas

O QuantumLeap cria automaticamente a tabela `etcrushercrusher001`
no schema `mtopeniot` (ou `doc` dependendo da versão).

### Acessar via Admin UI
Abra: http://localhost:4200

### Consultas SQL úteis

```sql
-- Últimas 20 leituras
SELECT time_index, temperature, vibration, current, production, status
FROM doc.etcrushercrusher001
ORDER BY time_index DESC
LIMIT 20;

-- Média por hora
SELECT
  date_trunc('hour', time_index) AS hora,
  AVG(temperature)  AS temp_media,
  AVG(vibration)    AS vib_media,
  AVG(production)   AS prod_media,
  COUNT(*) AS leituras
FROM doc.etcrushercrusher001
GROUP BY hora
ORDER BY hora DESC;

-- Contagem de alertas por hora
SELECT
  date_trunc('hour', time_index) AS hora,
  COUNT(*) AS total_alertas
FROM doc.etcrushercrusher001
WHERE status = 'ALERTA'
GROUP BY hora
ORDER BY hora DESC;

-- Produção perdida total (em R$)
SELECT
  SUM(GREATEST(0, (100 - production)) * 200.0 * 5.0 / 3600.0) AS perda_acumulada_reais
FROM doc.etcrushercrusher001;

-- Percentual de tempo em alerta
SELECT
  CAST(SUM(CASE WHEN status = 'ALERTA' THEN 1 ELSE 0 END) AS DOUBLE)
    / COUNT(*) * 100.0 AS pct_alerta
FROM doc.etcrushercrusher001;
```

---

## Modelo NGSI-v2 — Crusher:001

```json
{
  "id": "Crusher:001",
  "type": "Crusher",
  "temperature": { "type": "Number",   "value": 65.3  },
  "vibration":   { "type": "Number",   "value": 4.1   },
  "current":     { "type": "Number",   "value": 102.5 },
  "production":  { "type": "Number",   "value": 98.7  },
  "status":      { "type": "Text",     "value": "NORMAL" },
  "timestamp":   { "type": "DateTime", "value": "2026-06-24T10:00:00Z" }
}
```

---

## Cálculo Econômico

```
Produção ideal  = 100 t/h
Valor do minério = R$ 200 / tonelada

perda_hora (R$/h) = MAX(0, (100 - producao_media) × 200)

perda_por_ponto (R$) = MAX(0, (100 - producao) × 200 × 5s / 3600s)

perda_acumulada = Σ perda_por_ponto

perda_diaria = perda_hora × 24

perda_por_alerta = perda_acumulada / qtd_alertas
```

---

## Regra de Negócio (Node-RED)

```
IF  temperature > 80
AND vibration   > 10
THEN status = "ALERTA"
ELSE status = "NORMAL"
```

---

## Reiniciar apenas o Publisher

```bash
docker compose restart publisher
```

## Ver logs em tempo real

```bash
docker compose logs -f --tail=50 publisher nodered orion quantumleap
```

## Parar tudo e limpar volumes

```bash
docker compose down -v
```