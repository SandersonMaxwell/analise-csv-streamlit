import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Calculadora de Rodadas", page_icon="📊", layout="centered")

st.title("📊 Calculadora de Rodadas — CSV Financeiro")

st.markdown("""
Envie um arquivo CSV **Analise de cashback**:
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
    v = str(valor).strip().replace(' ', '')
    if ',' in v and '.' in v:
        # ponto = milhar, vírgula = decimal
        v = v.replace('.', '').replace(',', '.')
    elif ',' in v:
        v = v.replace(',', '.')
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

        if len(df.columns) < 3:
            st.error("O CSV precisa ter pelo menos 3 colunas (A, B e C).")
            st.stop()

        df.columns = ['A', 'B', 'C'] + list(df.columns[3:])
        df['B'] = df['B'].apply(converter_numero)
        df['C'] = df['C'].apply(converter_numero)

        soma_b = df['B'].sum()
        soma_c = df['C'].sum()
        diferenca = soma_b - soma_c
        qtd_rodadas = df['A'].count()
        percentual = calcular_percentual(qtd_rodadas)
        resultado_final = diferenca * percentual

        # Exibe resultados
        st.subheader("📈 Resultados:")
        st.write(f"**Soma da coluna B:** {soma_b:,.2f}")
        st.write(f"**Soma da coluna C:** {soma_c:,.2f}")
        st.write(f"**Diferença (B - C):** {diferenca:,.2f}")
        st.write(f"**Número de rodadas (coluna A):** {qtd_rodadas}")
        st.write(f"**Percentual aplicado:** {percentual * 100:.0f}%")
        st.write(f"**Resultado final:** {resultado_final:,.2f}")

        # Lógica de cashback
        if qtd_rodadas < 25 or percentual < 0.05 or resultado_final < 10:
            st.warning("❌ O jogador **não tem direito a receber cashback**.")
            motivos = []
            if qtd_rodadas < 25:
                motivos.append(f"rodadas insuficientes ({qtd_rodadas})")
            if percentual < 0.05:
                motivos.append(f"percentual aplicado menor que 5% ({percentual*100:.0f}%)")
            if resultado_final < 10:
                motivos.append(f"valor final menor que 10 ({resultado_final:,.2f})")
            st.info("Motivo(s): " + ", ".join(motivos))
        else:
          valor_brl = f"R${resultado_final:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        st.success(f"✅ O jogador deve receber **{valor_brl}** em cashback!")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")


