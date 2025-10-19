import streamlit as st
import pandas as pd
import io
import plotly.express as px

st.set_page_config(page_title="Calculadora de Cashback e Relatórios", page_icon="📊", layout="wide")
st.title("📊 Calculadora de Cashback e Relatórios")

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
# Criação das abas
# -----------------------------
abas = st.tabs(["💸 Aba 1: Cashback", "📊 Aba 2: Resumo Detalhado"])

# =====================================
# ABA 1 – CALCULADORA DE CASHBACK
# =====================================
with abas[0]:
    st.markdown("### 📥 Envie o CSV para calcular cashback (rodadas reais apenas)")
    uploaded_file = st.file_uploader("Envie o arquivo CSV", type=["csv"], key="aba1")

    if uploaded_file:
        try:
            raw = uploaded_file.read().decode("utf-8")
            sep = ',' if raw.count(',') > raw.count(';') else ';'
            df = pd.read_csv(io.StringIO(raw), sep=sep)

            if len(df.columns) < 3:
                st.error("O CSV precisa ter pelo menos 3 colunas.")
                st.stop()

            # Identificação automática das colunas
            coluna_a = df.columns[0]  # rodadas (primeira coluna)
            coluna_b = next((c for c in df.columns if 'bet' in c.lower() or 'entrada' in c.lower()), None)
            coluna_c = next((c for c in df.columns if 'payout' in c.lower() or 'saida' in c.lower()), None)
            if not coluna_b or not coluna_c:
                st.error("❌ Não foi possível identificar as colunas de 'bet' e 'payout'.")
                st.stop()

            df = df.rename(columns={coluna_a: 'A', coluna_b: 'B', coluna_c: 'C'})
            df['B'] = df['B'].apply(converter_numero)
            df['C'] = df['C'].apply(converter_numero)

            # Considera apenas rodadas reais (Free Spin = False)
            if 'Free Spin' in df.columns:
                df['Free Spin'] = df['Free Spin'].astype(str).str.lower()
                df = df[df['Free Spin'] == 'false']

            # Cálculos principais
            df['Diferença'] = df['B'] - df['C']
            soma_b = df['B'].sum()
            soma_c = df['C'].sum()
            diferenca = df['Diferença'].sum()
            qtd_rodadas = df['A'].count()
            percentual = calcular_percentual(qtd_rodadas)
            resultado_final = diferenca * percentual

            # Exibe resultados gerais
            st.subheader("📈 Resultados do Cashback")
            st.write(f"💰 Total apostado: {formatar_brl(soma_b)}")
            st.write(f"🏆 Payout: {formatar_brl(soma_c)}")
            st.write(f"💵 Perdas (BET - Payout): {formatar_brl(diferenca)}")
            st.write(f"📊 Número de rodadas: {qtd_rodadas}")
            st.write(f"📌 Percentual aplicado: {percentual*100:.0f}%")
            st.write(f"💸 Valor a ser creditado: {formatar_brl(resultado_final)}")

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

            st.divider()

            # -----------------------------
            # Resumo visual por jogo
            # -----------------------------
            st.subheader("🎮 Resumo por Jogo (Rodadas Reais)")

            df_reais = df.copy()
            jogos = df_reais['Game Name'].unique()
            resumo_jogos = []

            for jogo in jogos:
                df_jogo = df[df["Game Name"] == jogo]
                total_rodadas = len(df_jogo)
                total_apostado = df_jogo['B'].sum()
                total_payout = df_jogo['C'].sum()
                lucro = total_apostado - total_payout
                emoji_lucro = "💵" if lucro >= 0 else "❌💸"

                st.markdown(f"### 🎰 {jogo}")
                col1, col2, col3 = st.columns(3)
                col1.metric("📊 Total de rodadas", total_rodadas)
                col2.metric("💰 Total apostado", formatar_brl(total_apostado))
                col3.metric(f"{emoji_lucro} Lucro", formatar_brl(lucro))
                st.write(f"🏆 Valor ganho (Payout): {formatar_brl(total_payout)}")
                st.divider()

                resumo_jogos.append({
                    "Game Name": jogo,
                    "Rodadas": total_rodadas,
                    "Total Apostado": total_apostado,
                    "Valor Ganho": total_payout,
                    "Lucro": lucro
                })

            # Gráfico comparativo por jogo
            df_plot = pd.DataFrame(resumo_jogos)
            fig = px.bar(
                df_plot,
                x="Game Name",
                y=["Total Apostado", "Valor Ganho", "Lucro"],
                barmode="group",
                title="💹 Comparativo por jogo",
                labels={"value": "Valor (R$)", "variable": "Categoria"},
                text_auto=True
            )
            st.plotly_chart(fig, use_container_width=True)

            # Download do resumo
            df_resumo_jogos = pd.DataFrame(resumo_jogos)
            df_resumo_jogos["Total Apostado"] = df_resumo_jogos["Total Apostado"].apply(formatar_brl)
            df_resumo_jogos["Valor Ganho"] = df_resumo_jogos["Valor Ganho"].apply(formatar_brl)
            df_resumo_jogos["Lucro"] = df_resumo_jogos["Lucro"].apply(formatar_brl)
            st.download_button(
                label="📥 Baixar resumo por jogo",
                data=df_resumo_jogos.to_csv(index=False).encode("utf-8"),
                file_name="resumo_cashback_jogos.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

# =====================================
# ABA 2 – RESUMO DETALHADO POR JOGO COM GRÁFICOS
# =====================================
with abas[1]:
    st.subheader("🎮 Resumo Detalhado por Jogo com Gráficos")

    uploaded_file2 = st.file_uploader("Envie o CSV para análise detalhada", type=["csv"], key="aba2")

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

            df["Bet"] = df["Bet"].apply(converter_numero)
            df["Payout"] = df["Payout"].apply(converter_numero)
            df["Creation Date"] = pd.to_datetime(df["Creation Date"], errors="coerce")

            st.markdown("### 📅 Filtrar a partir de uma data e hora")
            data_padrao = df["Creation Date"].min().date()
            hora_padrao = df["Creation Date"].min().time()
            data_inicial = st.date_input("Data inicial (dd/mm/aaaa):", value=data_padrao, format="DD/MM/YYYY")
            hora_inicial = st.time_input("⏰ Horário inicial (hh:mm):", value=hora_padrao)
            filtro_inicial = pd.to_datetime(f"{data_inicial} {hora_inicial}")
            df = df[df["Creation Date"] >= filtro_inicial]

            if df.empty:
                st.warning("⚠️ Nenhuma aposta encontrada após a data/hora selecionada.")
                st.stop()

            jogos = df["Game Name"].unique()
            resumo_geral = []

            for jogo in jogos:
                st.markdown(f"### 🎰 {jogo}")
                df_jogo = df[df["Game Name"] == jogo]
                reais = df_jogo[df_jogo["Free Spin"].astype(str).str.lower() == "false"]
                gratis = df_jogo[df_jogo["Free Spin"].astype(str).str.lower() == "true"]

                def calcular_resumo(df_tipo, tipo_nome, emoji):
                    if df_tipo.empty:
                        st.info(f"{emoji} Sem rodadas {tipo_nome.lower()}.")
                        return pd.DataFrame()
                    total_apostado = df_tipo['Bet'].sum()
                    total_payout = df_tipo['Payout'].sum()
                    lucro = total_apostado - total_payout
                    st.markdown(f"**{emoji} {tipo_nome}:**")
                    st.write(f"📊 Total de rodadas: {len(df_tipo)}")
                    st.write(f"💰 Total apostado: {formatar_brl(total_apostado)}")
                    st.write(f"🏆 Total payout: {formatar_brl(total_payout)}")
                    st.write(f"💵 Lucro: {formatar_brl(lucro)}")
                    st.write(f"🕒 Primeira rodada: {df_tipo['Creation Date'].min().strftime('%d/%m/%Y %H:%M')}")
                    st.write(f"🕒 Última rodada: {df_tipo['Creation Date'].max().strftime('%d/%m/%Y %H:%M')}")
                    st.divider()
                    return pd.DataFrame({
                        "Game Name": [jogo],
                        "Tipo": [tipo_nome],
                        "Rodadas": [len(df_tipo)],
                        "Total Apostado": [total_apostado],
                        "Total Payout": [total_payout],
                        "Lucro": [lucro],
                        "Primeira Rodada": [df_tipo['Creation Date'].min()],
                        "Última Rodada": [df_tipo['Creation Date'].max()]
                    })

                resumo_geral.append(calcular_resumo(reais, "Rodadas reais", "🎯"))
                resumo_geral.append(calcular_resumo(gratis, "Rodadas gratuitas", "🎁"))

            # Gráficos
            df_relatorio = pd.concat(resumo_geral, ignore_index=True)
            if not df_relatorio.empty:
                fig = px.bar(
                    df_relatorio,
                    x="Game Name",
                    y=["Total Apostado", "Total Payout", "Lucro"],
                    color="Tipo",
                    barmode="group",
                    title="💹 Comparativo por Jogo (Rodadas Reais vs Gratuitas)",
                    text_auto=True,
                    labels={"value": "Valor (R$)", "variable": "Categoria"}
                )
                st.plotly_chart(fig, use_container_width=True)

                df_consolidado = df_relatorio.groupby("Game Name").agg({
                    "Total Apostado": "sum",
                    "Total Payout": "sum",
                    "Lucro": "sum"
                }).reset_index()

                fig2 = px.bar(
                    df_consolidado,
                    x="Game Name",
                    y=["Total Apostado", "Total Payout", "Lucro"],
                    barmode="group",
                    title="📊 Resumo Consolidado Geral por Jogo",
                    text_auto=True,
                    labels={"value": "Valor (R$)", "variable": "Categoria"}
                )
                st.plotly_chart(fig2, use_container_width=True)

                # Preparar CSV para download
                df_relatorio["Total Apostado"] = df_relatorio["Total Apostado"].apply(formatar_brl)
                df_relatorio["Total Payout"] = df_relatorio["Total Payout"].apply(formatar_brl)
                df_relatorio["Lucro"] = df_relatorio["Lucro"].apply(formatar_brl)
                df_relatorio["Primeira Rodada"] = df_relatorio["Primeira Rodada"].dt.strftime("%d/%m/%Y %H:%M")
                df_relatorio["Última Rodada"] = df_relatorio["Última Rodada"].dt.strftime("%d/%m/%Y %H:%M")

                st.download_button(
                    label="📥 Baixar relatório completo",
                    data=df_relatorio.to_csv(index=False).encode("utf-8"),
                    file_name="resumo_apostas_completo.csv",
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

