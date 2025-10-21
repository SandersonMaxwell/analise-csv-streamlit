import streamlit as st
import pandas as pd
from io import StringIO
from datetime import datetime

st.set_page_config(page_title="Calculadora 🧮", layout="wide")
st.title("🎰Calculadroa de Cashback e analise de apostas em cassino")

# -----------------------------
# Funções auxiliares
# -----------------------------
def format_brl(value):
    return f"R${value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def lucro_colorido(lucro):
    color = "green" if lucro >= 0 else "red"
    return f"<span style='color:{color}; font-weight:bold'>{format_brl(lucro)}</span>"

def gerar_relatorio_csv(df):
    output = StringIO()
    df.to_csv(output, index=False, sep=';')
    return output.getvalue()

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

# =============================
# ABAS
# =============================
abas = st.tabs(["💰Cashback", "📊 Apostas Cassino"])

# =============================
# ABA 1 - CASHBACK
# =============================
with abas[0]:
    st.header("💰 Cálculo de Cashback")
    arquivo = st.file_uploader("Envie o arquivo .csv", type=["csv"], key="aba1")

    if arquivo:
        try:
            df = pd.read_csv(arquivo)
            df.columns = [col.strip() for col in df.columns]

            # -----------------------------
            # ID do jogador
            # -----------------------------
            if "Client ID" in df.columns:
                player_id = df["Client ID"].iloc[0]
                st.markdown(f"### 🆔 ID do Jogador: {player_id}")

            # Colunas principais
            data_col = df.columns[1]
            free_col = "Free Spin"
            bet_col = "Bet"
            payout_col = "Payout"
            game_col = "Game Name"

            # Converte valores
            df[bet_col] = df[bet_col].apply(converter_numero)
            df[payout_col] = df[payout_col].apply(converter_numero)

            # Filtra apenas rodadas reais
            df_reais = df[df[free_col].astype(str).str.lower() == "false"]
            df_reais[data_col] = pd.to_datetime(df_reais[data_col], errors="coerce")

            # Cálculo cashback (visão da casa)
            total_bet = df_reais[bet_col].sum()
            total_payout = df_reais[payout_col].sum()
            diferenca = total_bet - total_payout
            qtd_rodadas = len(df_reais)
            percentual = calcular_percentual(qtd_rodadas)
            resultado_final = diferenca * percentual

            st.subheader("📈 Resultados Gerais")
            st.markdown(f"**Total Apostado:** {format_brl(total_bet)}")
            st.markdown(f"**Total Pago:** {format_brl(total_payout)}")
            st.markdown(f"**Cashback (visão da casa):** {lucro_colorido(diferenca)}")
            st.markdown(f"**Número de rodadas:** {qtd_rodadas}")
            st.markdown(f"**Percentual aplicado:** {percentual*100:.0f}%")
            st.markdown(f"**Valor de cashback:** {format_brl(resultado_final)}")

            # Elegibilidade cashback
            if qtd_rodadas < 25 or percentual < 0.05 or resultado_final < 10 or diferenca <= 0:
                st.warning("❌ O jogador não tem direito a receber cashback.")
                motivos = []
                if qtd_rodadas < 25:
                    motivos.append(f"rodadas insuficientes ({qtd_rodadas})")
                if percentual < 0.05:
                    motivos.append(f"percentual menor que 5% ({percentual*100:.0f}%)")
                if resultado_final < 10:
                    motivos.append(f"valor final menor que 10 ({format_brl(resultado_final)})")
                if diferenca <= 0:
                    motivos.append("jogador teve lucro")
                st.info("Motivo(s): " + ", ".join(motivos))
            else:
                st.success(f"✅ O jogador deve receber **{format_brl(resultado_final)}** em cashback!")

            # Resumo por jogo (visão do jogador)
            st.divider()
            st.subheader("🎮 Resumo por Jogo (Rodadas Reais)")
            resumo_jogos = df_reais.groupby(game_col).agg(
                Total_Apostado=(bet_col, "sum"),
                Total_Payout=(payout_col, "sum"),
                Rodadas=(bet_col, "count")
            ).reset_index()

            for _, row in resumo_jogos.iterrows():
                lucro_jogador = row["Total_Payout"] - row["Total_Apostado"]
                st.markdown(f"#### 🎯 {row[game_col]}")
                st.markdown(f"- Rodadas: {int(row['Rodadas'])}")
                st.markdown(f"- Total Apostado: {format_brl(row['Total_Apostado'])}")
                st.markdown(f"- Total Pago: {format_brl(row['Total_Payout'])}")
                st.markdown(f"- Lucro do jogador: {lucro_colorido(lucro_jogador)}")
                st.divider()

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

# =============================
# ABA 2 - RESUMO DETALHADO
# =============================
with abas[1]:
    st.header("📊 Resumo Detalhado por Jogo")
    arquivo2 = st.file_uploader("Envie o arquivo .csv", type=["csv"], key="file2")

    if arquivo2:
        try:
            df = pd.read_csv(arquivo2)
            df.columns = [col.strip() for col in df.columns]

            # -----------------------------
            # ID do jogador
            # -----------------------------
            if "Client ID" in df.columns:
                player_id = df["Client ID"].iloc[0]
                st.markdown(f"### 🆔 ID do Jogador: {player_id}")

            data_col = df.columns[1]
            free_col = "Free Spin"
            bet_col = "Bet"
            payout_col = "Payout"
            game_col = "Game Name"

            df[bet_col] = df[bet_col].apply(converter_numero)
            df[payout_col] = df[payout_col].apply(converter_numero)
            df[data_col] = pd.to_datetime(df[data_col], errors="coerce")

            # Filtro data/hora inicial e final
            st.subheader("⏰ Filtro por Data e Hora")
            data_inicio = st.date_input("Data inicial")
            hora_inicio_txt = st.text_input("Hora inicial (HH:MM)", "00:00")
            data_fim = st.date_input("Data final")
            hora_fim_txt = st.text_input("Hora final (HH:MM)", "23:59")

            try:
                hora_inicio = datetime.strptime(hora_inicio_txt, "%H:%M").time()
                hora_fim = datetime.strptime(hora_fim_txt, "%H:%M").time()
                data_hora_inicio = datetime.combine(data_inicio, hora_inicio)
                data_hora_fim = datetime.combine(data_fim, hora_fim)
            except ValueError:
                st.error("❌ Formato de hora inválido! Use HH:MM (ex: 14:30).")
                st.stop()

            df = df[(df[data_col] >= data_hora_inicio) & (df[data_col] <= data_hora_fim)]

            st.markdown("---")
            st.subheader("🎯 Resultado por Jogo")

            linhas_relatorio = []
            jogos = df[game_col].unique()

            for jogo in jogos:
                df_jogo = df[df[game_col] == jogo]
                df_reais = df_jogo[df_jogo[free_col].astype(str).str.lower() == "false"]
                df_free = df_jogo[df_jogo[free_col].astype(str).str.lower() == "true"]

                def resumo_tipo(df_tipo, tipo):
                    if df_tipo.empty:
                        return f"**Rodadas {tipo}:** Nenhuma rodada\n"
                    total_rodadas = len(df_tipo)
                    total_apostado = df_tipo[bet_col].sum()
                    total_payout = df_tipo[payout_col].sum()
                    lucro_jogador = total_payout - total_apostado
                    primeira = df_tipo[data_col].min()
                    ultima = df_tipo[data_col].max()
                    return f"**Rodadas {tipo}:**\n" \
                           f"- Total de rodadas: {total_rodadas}\n" \
                           f"- Total apostado: {format_brl(total_apostado)}\n" \
                           f"- Total payout: {format_brl(total_payout)}\n" \
                           f"- Lucro do jogador: {lucro_colorido(lucro_jogador)}\n" \
                           f"- Primeira rodada: {primeira.strftime('%d/%m/%Y %H:%M')}\n" \
                           f"- Última rodada: {ultima.strftime('%d/%m/%Y %H:%M')}\n"

                st.markdown(f"### 🎰 {jogo}")
                st.markdown(resumo_tipo(df_reais, "reais"))
                st.markdown(resumo_tipo(df_free, "gratuitas"))

                # Resumo geral por jogo
                total_jogo_apostado = df_jogo[bet_col].sum()
                total_jogo_payout = df_jogo[payout_col].sum()
                lucro_jogo = total_jogo_payout - total_jogo_apostado
                st.markdown(f"**📈 Lucro total (reais + gratuitas):** {lucro_colorido(lucro_jogo)}")
                st.markdown("---")

                linhas_relatorio.append({
                    "Jogo": jogo,
                    "Total Apostado": total_jogo_apostado,
                    "Total Pago": total_jogo_payout,
                    "Lucro do Jogador": lucro_jogo
                })

            df_relatorio = pd.DataFrame(linhas_relatorio)
            relatorio_csv = gerar_relatorio_csv(df_relatorio)

            st.download_button(
                label="📥 Baixar Relatório Completo",
                data=relatorio_csv,
                file_name="relatorio_jogos.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
