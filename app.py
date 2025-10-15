import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Calculadora de Rodadas", page_icon="📊", layout="centered")

st.title("📊 Calculadora de Rodadas — CSV Financeiro")

st.markdown("""
Envie um arquivo CSV contendo **3 colunas**:
1️⃣ Coluna 1 = Rodada (coluna A)  
2️⃣ Coluna 2 = Valor 1 (coluna B)  
3️⃣ Coluna 3 = Valor 2 (coluna C)  
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
    return 0  # caso não se encaixe em nenhuma regra

# Função segura para converter números do CSV
def converter_numero(valor):
    if pd.isna(valor):
        return 0
    v = str(valor).strip()
    # Remove espaços
    v = v.replace(' ', '')
    # Detecta vírgula decimal
    if ',' in v and '.' in v:
        # ponto = milhar, vírgula = decimal
        v = v.replace('.', '').replace(',', '.')
    elif ',' in v:
        v = v.replace(',', '.')
    else:
        # ponto decimal ou só número
        v = v
    try:
        return float(v)
    except:
        return 0

# Upload CSV
uploaded_file = st.file_uploader("Envie o arquivo CSV", type=["csv"])

if uploaded_file:
    try:
        raw = uploaded_file.read().decode("utf-8")
        sep = ',' if raw.count(',') > raw.count(';') else ';'
        df = pd.read_csv(io.StringIO(raw), sep=sep)

        # Verifica colunas
        if len(df.columns) < 3:
            st.error("O CSV precisa ter pelo menos 3 colunas (A, B e C).")
            st.stop()

        # Renomeia as 3 primeiras colunas
        df.columns = ['A', 'B', 'C'] + list(df.columns[3:])

        # Converte B e C com função segura
        df['B'] = df['B'].apply(converter_numero)
        df['C'] = df['C'].apply(converter_numero)

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
