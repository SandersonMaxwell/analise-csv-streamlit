import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Calculadora de Rodadas", page_icon="📊", layout="centered")

st.title("📊 Analisador de CSV — Cálculo de Rodadas")

st.markdown("""
Envie um arquivo CSV contendo:
- **Coluna A:** número da rodada  
- **Coluna B:** valor 1  
- **Coluna C:** valor 2  
""")

# Função para definir a porcentagem conforme o número de rodadas
def calcular_percentual(qtd_rodadas):
    regras = [
        (25, 59, 0.05),
        (60, 94, 0.06),
        (95, 129, 0.07),
        (130, 164, 0.08),
        (165, 199, 0.09),
        (200, 234, 0.10),
        (235, 269, 0.11),
        (270, 304, 0.12),
        (305, 339, 0.13),
        (340, 374, 0.14),
        (375, 409, 0.15),
        (410, 444, 0.16),
    ]
    if qtd_rodadas >= 445:
        return 0.17
    for (min_r, max_r, perc) in regras:
        if min_r <= qtd_rodadas <= max_r:
            return perc
    return 0  # Caso não se encaixe em nenhuma regra

# Upload do CSV
uploaded_file = st.file_uploader("Envie o arquivo CSV", type=["csv"])

if uploaded_file:
    try:
        # Leitura do arquivo
        raw = uploaded_file.read().decode("utf-8")

        # Detecta separador automático
        sep = ',' if raw.count(',') > raw.count(';') else ';'
        df = pd.read_csv(io.StringIO(raw), sep=sep)

        # Mostra preview
        st.subheader("Pré-visualização dos dados:")
        st.dataframe(df.head())

        # Substituir ponto por vírgula (mas converter pra número depois)
        for col in ['B', 'C']:
            df[col] = df[col].astype(str).str.replace('.', '').str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Soma das colunas
        soma_b = df['B'].sum()
        soma_c = df['C'].sum()
        diferenca = soma_b - soma_c

        # Contagem de rodadas
        qtd_rodadas = df['A'].count()

        # Calcula percentual
        percentual = calcular_percentual(qtd_rodadas)
        resultado_final = diferenca * percentual

        # Exibe resultados
        st.subheader("📈 Resultados:")
        st.write(f"**Soma da coluna B:** {soma_b:,.2f}")
        st.write(f"**Soma da coluna C:** {soma_c:,.2f}")
        st.write(f"**Diferença (B - C):** {diferenca:,.2f}")
        st.write(f"**Número de rodadas (coluna A):** {qtd_rodadas}")
        st.write(f"**Percentual aplicado:** {percentual * 100:.0f}%")
        st.success(f"💰 **Resultado final:** {resultado_final:,.2f}")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
