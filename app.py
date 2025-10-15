import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Calculadora de Rodadas", page_icon="📊", layout="centered")

st.title("📊 Calculadora de Rodadas — CSV Financeiro")

st.markdown("""
Procedimento:   
1️⃣  Filtre a data correta  
2️⃣ Filtre a coluna freespins como FALSE   
3️⃣ Exporte o as jogadas no formato .CSV
""")

# -----------------------------
# Funções auxiliares
# -----------------------------

def calcular_percentual(qtd_rodadas):
    regras = [
        (25, 59, 0.05),
        (60, 94, 0.06),
        (95, 129, 0.07),
        (130, 164, 0.08),
        (165, 199, 0.09),
        (200, 234, 0.10
