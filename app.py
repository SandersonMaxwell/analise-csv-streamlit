import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Calculadora de Cashback", page_icon="📊", layout="centered")

st.title("📊 Calculadora de Cashback")


st.markdown("""
Procedimento:  
1️⃣ Filtre a data da semana de cashback  
2️⃣ Filtre a coluna FREE SPINS como FALSE  
3️⃣ Exporte como .CSV 
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
    return 0

def converter_numero(valor):
    if pd.isna(valor):
        return 0
    v = str(valor).strip().replace(' ', '')
    if ',' in v and '.' in v:
        v = v.replace('.', '').replace(',', '.')
    elif ',' in v:
        v = v.replace(',', '.')
    try:
        return float(v)
    except:
        return 0

def formatar_brl(valor):
    return f"R${valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# -----------------------------
# Upload do CSV
# -----------------------------
uploaded_file = st.file_uploader("Envie o arquivo CSV", type=["csv"])

if uploaded_file:
    try:
        raw = uploaded_file.read().decode("utf-8")
        sep = ',' if raw.count(',') > raw.count(';') else ';'
        df = pd.read_csv(io.StringIO(raw), sep=sep)

        if len(df.columns) < 3:
            st.error("O CSV precisa ter pelo menos 3 colunas.")
            st.stop()

        # -----------------------------
        # Identificação automática das colunas
        # -----------------------------
        colunas_lower = [c.lower() for c in df.columns]

        coluna_a = df.columns[0]  # rodadas (primeira coluna)
        coluna_b = next((c for c in df.columns if 'bet' in c.lower() or 'entrada' in c.lower()), None)
        coluna_c = next((c for c in df.columns if 'payout' in c.lower() or 'saida' in c.lower()), None)

        if not coluna_b or not coluna_c:
            st.error("❌ Não foi possível identificar as colunas de 'bet' e 'payout'. Verifique o cabeçalho do CSV.")
            st.write("Dica: use nomes de colunas contendo 'bet' e 'payout' (qualquer variação de maiúsculas/minúsculas).")
            st.stop()

        # Renomeia colunas principais
        df = df.rename(columns={coluna_a: 'A', coluna_b: 'B', coluna_c: 'C'})

        # Converte valores numéricos
        df['B'] = df['B'].apply(converter_numero)
        df['C'] = df['C'].apply(converter_numero)

        # -----------------------------
        # Cálculos principais
        # -----------------------------
        df['Diferença'] = df['B'] - df['C']
        soma_b = df['B'].sum()
        soma_c = df['C'].sum()
        diferenca = df['Diferença'].sum()
        qtd_rodadas = df['A'].count()
        percentual = calcular_percentual(qtd_rodadas)
        resultado_final = diferenca * percentual

        # -----------------------------
        # Exibe resultados
        # -----------------------------
        st.subheader("📈 Resultados:")
        st.write(f"**Total apostado:** {formatar_brl(soma_b)}")
        st.write(f"**Payout:** {formatar_brl(soma_c)}")
        st.write(f"**Perdas (BET - Payout):** {formatar_brl(diferenca)}")
        st.write(f"**Número de rodadas:** {qtd_rodadas}")
        st.write(f"**Percentual aplicado:** {percentual * 100:.0f}%")
        st.write(f"**Valor a ser creditado:** {formatar_brl(resultado_final)}")


        # -----------------------------
        # Lógica de cashback
        # -----------------------------
        if qtd_rodadas < 25 or percentual < 0.05 or resultado_final < 10:
            st.warning("❌ O jogador **não tem direito a receber cashback**.")
            motivos = []
            if qtd_rodadas < 25:
                motivos.append(f"rodadas insuficientes ({qtd_rodadas})")
            if percentual < 0.05:
                motivos.append(f"percentual aplicado menor que 5% ({percentual*100:.0f}%)")
            if resultado_final < 10:
                motivos.append(f"valor final menor que 10 ({formatar_brl(resultado_final)})")
            st.info("Motivo(s): " + ", ".join(motivos))
        else:
            st.success(f"✅ O jogador deve receber **{formatar_brl(resultado_final)}** em cashback!")

        # -----------------------------
        # Conclusão
        # -----------------------------
        st.markdown("""
        ---
        ### 🏁 Conclusão  
        Com esta ferramenta, o processo de cálculo de cashback fica **simples, rápido e confiável**.  
        Em poucos cliques, é possível analisar rodadas, aplicar as regras de porcentagem e obter o valor exato que cada jogador deve receber — tudo automaticamente e sem erro.  
        """)

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

