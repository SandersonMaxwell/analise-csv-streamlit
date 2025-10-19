import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Painel de Cashback e Apostas", page_icon="🎰", layout="centered")
st.title("🎰 Painel de Cashback e Análise de Apostas")

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
# Cria abas
# -----------------------------
abas = st.tabs(["💰 Calculadora de Cashback", "🎮 Resumo por Jogo"])

# -----------------------------
# ABA 1 - CALCULADORA DE CASHBACK
# -----------------------------
with abas[0]:
    st.subheader("💰 Calculadora de Cashback")

    st.markdown("""
    **Procedimento:**  
    1️⃣ Filtre a data de ocorrencia do cashback no BKO  
    2️⃣ Exporte como .CSV 
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

            coluna_a = df.columns[0]
            coluna_b = next((c for c in df.columns if 'bet' in c.lower() or 'entrada' in c.lower()), None)
            coluna_c = next((c for c in df.columns if 'payout' in c.lower() or 'saida' in c.lower()), None)
            coluna_free = next((c for c in df.columns if c.strip().lower() == 'free spin'), None)

            if not coluna_b or not coluna_c:
                st.error("❌ Não foi possível identificar as colunas de 'bet' e 'payout'.")
                st.stop()

            if coluna_free:
                df = df[df[coluna_free].astype(str).str.lower() == 'false']
                st.info(f"✅ Considerando apenas {len(df)} rodadas com Free Spin = false")
            else:
                st.warning("⚠️ Coluna 'Free Spin' não encontrada. Nenhum filtro aplicado.")

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

            st.subheader("📈 Resultados:")
            st.write(f"**Total apostado:** {formatar_brl(soma_b)}")
            st.write(f"**Payout:** {formatar_brl(soma_c)}")
            st.write(f"**Perdas (BET - Payout):** {formatar_brl(diferenca)}")
            st.write(f"**Número de rodadas válidas:** {qtd_rodadas}")
            st.write(f"**Percentual aplicado:** {percentual * 100:.0f}%")
            st.write(f"**Valor a ser creditado:** {formatar_brl(resultado_final)}")

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
    st.subheader("🎮 Resumo por Jogo Detalhado com Lucros")

    uploaded_file2 = st.file_uploader("Envie o arquivo CSV para análise por jogo", type=["csv"], key="resumo")

    if uploaded_file2:
        try:
            raw = uploaded_file2.read().decode("utf-8")
            sep = ',' if raw.count(',') > raw.count(';') else ';'
            df = pd.read_csv(io.StringIO(raw), sep=sep)

            obrigatorias = ["Game Name", "Bet", "Payout", "Creation Date", "Free Spin"]
            for col in obrigatorias:
                if col not in df.columns:
                    st.error(f"❌ Coluna obrigatória '{col}' não encontrada.")
                    st.stop()

            # Converte valores
            df["Bet"] = df["Bet"].apply(converter_numero)
            df["Payout"] = df["Payout"].apply(converter_numero)
            df["Creation Date"] = pd.to_datetime(df["Creation Date"], errors="coerce")

            if df.empty or df["Creation Date"].isna().all():
                st.warning("⚠️ Nenhuma data válida encontrada.")
                st.stop()

            # -----------------------------
            # Filtro por data inicial
            # -----------------------------
            st.markdown("### 📅 Filtrar a partir de uma data e hora")
            data_padrao = df["Creation Date"].min().date()
            hora_padrao = df["Creation Date"].min().time()

            data_inicial = st.date_input(
                "Data inicial (dd/mm/aaaa):", value=data_padrao, format="DD/MM/YYYY"
            )
            hora_inicial = st.time_input("Horário inicial (hh:mm):", value=hora_padrao)

            filtro_inicial = pd.to_datetime(f"{data_inicial} {hora_inicial}")
            df = df[df["Creation Date"] >= filtro_inicial]

            if df.empty:
                st.warning("⚠️ Nenhuma aposta encontrada após a data/hora selecionada.")
                st.stop()

            # -----------------------------
            # Agrupa e exibe por jogo
            # -----------------------------
            jogos = df["Game Name"].unique()
            resumo_final = []

            for jogo in jogos:
                st.markdown(f"### 🎰 {jogo}")
                df_jogo = df[df["Game Name"] == jogo]

                # Rodadas reais (Free Spin = false)
                reais = df_jogo[df_jogo["Free Spin"].astype(str).str.lower() == "false"]
                if not reais.empty:
                    total_apostado_reais = reais['Bet'].sum()
                    total_payout_reais = reais['Payout'].sum()
                    lucro_reais = total_apostado_reais - total_payout_reais

                    st.markdown("**Rodadas reais:**")
                    st.write(f"Total de rodadas: {len(reais)}")
                    st.write(f"Total apostado: {formatar_brl(total_apostado_reais)}")
                    st.write(f"Total payout: {formatar_brl(total_payout_reais)}")
                    st.write(f"Lucro: {formatar_brl(lucro_reais)}")
                    st.write(f"Primeira rodada: {reais['Creation Date'].min().strftime('%d/%m/%Y %H:%M')}")
                    st.write(f"Última rodada: {reais['Creation Date'].max().strftime('%d/%m/%Y %H:%M')}")
                else:
                    st.info("Sem rodadas reais.")

                # Rodadas gratuitas (Free Spin = true)
                gratis = df_jogo[df_jogo["Free Spin"].astype(str).str.lower() == "true"]
                if not gratis.empty:
                    total_apostado_gratis = gratis['Bet'].sum()
                    total_payout_gratis = gratis['Payout'].sum()
                    lucro_gratis = total_apostado_gratis - total_payout_gratis

                    st.markdown("**Rodadas gratuitas:**")
                    st.write(f"Total de rodadas: {len(gratis)}")
                    st.write(f"Total apostado: {formatar_brl(total_apostado_gratis)}")
                    st.write(f"Total payout: {formatar_brl(total_payout_gratis)}")
                    st.write(f"Lucro: {formatar_brl(lucro_gratis)}")
                    st.write(f"Primeira rodada: {gratis['Creation Date'].min().strftime('%d/%m/%Y %H:%M')}")
                    st.write(f"Última rodada: {gratis['Creation Date'].max().strftime('%d/%m/%Y %H:%M')}")
                else:
                    st.info("Sem rodadas gratuitas.")

                # -----------------------------
                # Resumo final por jogo (reais + gratuitas)
                # -----------------------------
                total_apostado = (reais['Bet'].sum() if not reais.empty else 0) + (gratis['Bet'].sum() if not gratis.empty else 0)
                total_payout = (reais['Payout'].sum() if not reais.empty else 0) + (gratis['Payout'].sum() if not gratis.empty else 0)
                lucro_total = total_apostado - total_payout

                st.markdown(f"**Resumo total do jogo (rodadas reais + gratuitas):**")
                st.write(f"Lucro total: {formatar_brl(lucro_total)}")

                st.divider()

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")



