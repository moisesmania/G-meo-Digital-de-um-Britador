import os
import time
import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# ─────────────────────────────────────────────
# CONFIG (SEM config.py)
# ─────────────────────────────────────────────

ORION_URL = os.getenv("ORION_URL", "http://orion:1026")
QL_URL = os.getenv("QUANTUMLEAP_URL", "http://quantumleap:8668")

ENTITY_ID = "Crusher:001"
REFRESH_SECONDS = 5

PRODUCAO_IDEAL = 100.0
VALOR_MINERIO = 200.0

COR_OK = "#00c853"
COR_BAD = "#d50000"

st.set_page_config(page_title="Gêmeo Digital", layout="wide")
def get_current_entity():
    try:
        url = f"{ORION_URL}/v2/entities/Crusher:001"
        headers = {
            "fiware-service": "default",
            "fiware-servicepath": "/"
        }

        r = requests.get(url, headers=headers, timeout=5)

        if r.status_code != 200:
            return None

        return r.json()

    except Exception:
        return None


# ─────────────────────────────────────────────
# HELPERS ROBUSTOS
# ─────────────────────────────────────────────
def safe_get(url, timeout=3, retries=3):
    for _ in range(retries):
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200:
                return r.json()
        except:
            time.sleep(1)
    return None


def get_entity():
    return safe_get(f"{ORION_URL}/v2/entities/{ENTITY_ID}")


def empty_state():
    return {
        "temperature": {"value": 0},
        "vibration": {"value": 0},
        "current": {"value": 0},
        "production": {"value": 0},
        "status": {"value": "OFFLINE"},
    }


def val(entity, key):
    return entity.get(key, {}).get("value", 0)


# ─────────────────────────────────────────────
# UI HEADER
# ─────────────────────────────────────────────
st.title("⛏️ Gêmeo Digital — Produção Blindada")

entity = get_entity()

if entity is None:
    st.warning("Orion offline ou sem dados. Exibindo fallback simulado.")
    entity = empty_state()

status = str(val(entity, "status")).upper()


# ─────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

col1.metric("Temperatura", f"{val(entity,'temperature')} °C")
col2.metric("Vibração", f"{val(entity,'vibration')} mm/s")
col3.metric("Corrente", f"{val(entity,'current')} A")

prod = val(entity, "production")
col4.metric(
    "Produção",
    f"{prod} t/h",
    f"{prod - PRODUCAO_IDEAL:.1f} vs ideal"
)

st.markdown(f"### Status: `{status}`")


# ─────────────────────────────────────────────
# ALERTA VISUAL
# ─────────────────────────────────────────────
if status == "ALERTA":
    st.error("Máquina em condição crítica")
elif status == "OFFLINE":
    st.warning("Sistema sem dados do Orion")


# ─────────────────────────────────────────────
# GRÁFICO SIMPLES (ROBUSTO)
# ─────────────────────────────────────────────
df = pd.DataFrame({
    "tempo": list(range(10)),
    "produção": [prod] * 10
})

fig = px.line(df, x="tempo", y="produção", title="Produção (fallback ou real)")
st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# AUTO REFRESH CONTROLADO
# ─────────────────────────────────────────────
time.sleep(REFRESH_SECONDS)
st.rerun()