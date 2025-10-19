import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Painel de Cashback e Apostas", page_icon="🎰", layout="centered")

st.title("🎰 Calculadora")

# -----------------------------
# Funções auxiliares
# -----------------------------
def calcular_percentual(qtd_rodadas):
    regras = [
        (25, 59, 0.05), (60, 94, 0.06), (95, 129, 0.07), (130, 164, 0.08),
        (165, 199, 0.09), (200, 234, 0.10), (235, 269, 0.11), (270, 304, 0.12),
        (305, 339, 0.13), (340, 374, 0.14), (375, 409, 0.15), (410, 444, 0.16)
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
# Tabs
# -----------------------------
aba1, aba2 = st.tabs(["💰 Calculadora de Cashback", "🎮 Resumo por Jogo"])

# -----------------------------
# ABA 1 - CÁLCULO DE CASHBACK
# -----------------------------
with aba1:
    st.subheader("💰 Calculadora de Cashback")

    st.markdown("""
    **Procedimento:**  
    1️⃣ Filtre a data de ocorrencia de cashback  
    2️⃣ Exporte o resultado como .CSV  
    
    """)

    uploaded_file = st.file_uploader("Envie o arquivo CSV", type=["csv"], key="cashback")

    if uploaded_file:
        try:
            raw = uploaded_file.read().decode("utf-8")
            sep = ',' if raw.count(',') > raw.count(';') else ';'
            df = pd.read_csv(io.StringIO(raw), sep=sep)

            if len(df.columns) < 3:
                st.error("O CSV precisa ter pelo menos 3 colunas.")
                st.stop()

            # Identificação das colunas principais
            colunas_lower = [c.lower() for c in df.columns]

            coluna_a = df.columns[0]
            coluna_b = next((c for c in df.columns if 'bet' in c.lower() or 'entrada' in c.lower()), None)
            coluna_c = next((c for c in df.columns if 'payout' in c.lower() or 'saida' in c.lower()), None)
            coluna_free = next((c for c in df.columns if c.strip().lower() == 'free spin'), None)

            if not coluna_b or not coluna_c:
                st.error("❌ Não foi possível identificar as colunas de 'bet' e 'payout'.")
                st.stop()

            # Filtro Free Spin
            if coluna_free:
                df = df[df[coluna_free].astype(str).str.lower() == 'false']
                st.info(f"✅ Considerando apenas {len(df)} rodadas com Free Spin = false")
            else:
                st.warning("⚠️ Coluna 'Free Spin' não encontrada. Nenhum filtro aplicado.")

            # Renomeia
            df = df.rename(columns={coluna_a: 'A', coluna_b: 'B', coluna_c: 'C'})

            df['B'] = df['B'].apply(converter_numero)
            df['C'] = df['C'].apply(converter_numero)

            df['Diferença'] = df['B'] - df['C']
            soma_b = df['B'].sum()
            soma_c = df['C'].sum()
            diferenca = df['Diferença'].sum()
            qtd_rodadas = df['A'].count()
            percentual = calcular_percentual(qtd_rodadas)
            resultado_final = diferenca * percentual

            # Resultados
            st.subheader("📈 Resultados:")
            st.write(f"**Total apostado:** {formatar_brl(soma_b)}")
            st.write(f"**Payout:** {formatar_brl(soma_c)}")
            st.write(f"**Perdas (BET - Payout):** {formatar_brl(diferenca)}")
            st.write(f"**Número de rodadas válidas:** {qtd_rodadas}")
            st.write(f"**Percentual aplicado:** {percentual * 100:.0f}%")
            st.write(f"**Valor a ser creditado:** {formatar_brl(resultado_final)}")

            # Lógica de cashback
            if qtd_rodadas < 25 or percentual < 0.05 or resultado_final < 10:
                st.warning("❌ O jogador **não tem direito a receber cashback**.")
                motivos = []
                if qtd_rodadas < 25:
                    motivos.append(f"rodadas insuficientes ({qtd_rodadas})")
                if percentual < 0.05:
                    motivos.append(f"percentual menor que 5% ({percentual*100:.0f}%)")
                if resultado_final < 10:
                    motivos.append(f"valor final menor que 10 ({formatar_brl(resultado_final)})")
                st.info("Motivo(s): " + ", ".join(motivos))
            else:
                st.success(f"✅ O jogador deve receber **{formatar_brl(resultado_final)}** em cashback!")

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

# -----------------------------
# ABA 2 - RESUMO POR JOGO
# -----------------------------
with abas[1]:
    st.header("🎯 Análise de Apostas por Jogo")

    uploaded_file = st.file_uploader("Envie o arquivo CSV do jogador", type=["csv"], key="file_apostas")

    if uploaded_file:
        try:
            raw = uploaded_file.read().decode("utf-8")
            sep = ',' if raw.count(',') > raw.count(';') else ';'
            df = pd.read_csv(io.StringIO(raw), sep=sep)

            # Garante que as colunas necessárias existem
            colunas_necessarias = ["Game Name", "Bet", "Creation Date", "Free Spin"]
            for col in colunas_necessarias:
                if col not in df.columns:
                    st.error(f"❌ A coluna '{col}' não foi encontrada no CSV.")
                    st.stop()

            # Filtra Free Spin = false
            df = df[df["Free Spin"].astype(str).str.lower() == "false"]

            # Converte coluna de data
            df["Creation Date"] = pd.to_datetime(df["Creation Date"], errors="coerce")

            if df["Creation Date"].isna().all():
                st.error("❌ Nenhuma data válida encontrada na coluna 'Creation Date'.")
                st.stop()

            # Filtro por data e hora inicial
            st.markdown("### 📅 Filtro por data e hora inicial")
            data_padrao = df["Creation Date"].min().date()
            hora_padrao = df["Creation Date"].min().time()

            data_inicial = st.date_input(
                "Selecione a data inicial (formato: dia/mês/ano):",
                value=data_padrao,
                format="DD/MM/YYYY"
            )
            hora_inicial = st.time_input("Selecione o horário inicial:", value=hora_padrao)

            filtro_inicial = pd.to_datetime(f"{data_inicial} {hora_inicial}")

            # Aplica filtro
            df = df[df["Creation Date"] >= filtro_inicial]

            if df.empty:
                st.warning("⚠️ Nenhuma aposta encontrada após a data/hora selecionada.")
                st.stop()

            # Agrupa por jogo
            resumo = (
                df.groupby("Game Name")
                .agg(
                    Rodadas=("Game Name", "count"),
                    TotalApostado=("Bet", "sum"),
                    PrimeiraRodada=("Creation Date", "min"),
                    UltimaRodada=("Creation Date", "max"),
                )
                .reset_index()
            )

            # Exibe resultados
            st.markdown(f"#### 🎯 Resultados a partir de {filtro_inicial.strftime('%d/%m/%Y %H:%M')}")
            for _, row in resumo.iterrows():
                st.markdown(f"### 🎰 {row['Game Name']}")
                st.write(f"**Total de rodadas:** {int(row['Rodadas'])}")
                st.write(f"**Total apostado:** {formatar_brl(row['TotalApostado'])}")
                st.write(f"**Primeira rodada:** {row['PrimeiraRodada'].strftime('%d/%m/%Y %H:%M')}")
                st.write(f"**Última rodada:** {row['UltimaRodada'].strftime('%d/%m/%Y %H:%M')}")
                st.divider()

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")



