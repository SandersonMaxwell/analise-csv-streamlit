import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.set_page_config(page_title="Calculadora", page_icon="🧮", layout="wide")
st.title("💸 Calculadora de Cashback e Análise de Jogadas de Cassino")

abas = st.tabs(["📊 Cashback", "🎯 Analise Cassino"])

# =============================
# FUNÇÕES AUXILIARES
# =============================
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

def mostrar_lucro(lucro):
    if lucro > 0:
        return f"💰 <span style='color:green;'>Lucro do jogador: {formatar_brl(lucro)}</span>"
    elif lucro < 0:
        return f"💸 <span style='color:red;'>Prejuízo do jogador: {formatar_brl(lucro)}</span>"
    else:
        return f"⚖️ <span style='color:gray;'>Sem lucro ou prejuízo</span>"

# =============================
# ABA 1 - CASHBACK
# =============================
with abas[0]:
    st.header("📊 Cálculo de Cashback")

    uploaded_file = st.file_uploader("Envie o arquivo CSV do jogador", type=["csv"], key="aba1")

    if uploaded_file:
        try:
            raw = uploaded_file.read().decode("utf-8")
            sep = ',' if raw.count(',') > raw.count(';') else ';'
            df = pd.read_csv(io.StringIO(raw), sep=sep)

            
            # -----------------------------
            # ID do jogador
            # -----------------------------
            if "Client" in df.columns:
                player_id = df["Client"].iloc[0]
                st.markdown(f"### 🆔 ID do Jogador: {player_id}")


            coluna_bet = next((c for c in df.columns if 'bet' in c.lower()), None)
            coluna_payout = next((c for c in df.columns if 'payout' in c.lower()), None)
            coluna_free = next((c for c in df.columns if 'free' in c.lower()), None)
            coluna_jogo = next((c for c in df.columns if 'game' in c.lower() or 'nome' in c.lower()), None)

            if not coluna_bet or not coluna_payout:
                st.error("❌ Não foi possível identificar as colunas 'Bet' e 'Payout'. Verifique o CSV.")
                st.stop()

            df[coluna_bet] = df[coluna_bet].apply(converter_numero)
            df[coluna_payout] = df[coluna_payout].apply(converter_numero)

            if coluna_free:
                df['Free Spin'] = df[coluna_free].astype(str).str.lower()
                df_reais = df[df['Free Spin'] == 'false']
            else:
                df_reais = df.copy()

            # ⚠️ CÁLCULO DO CASHBACK (visão da casa)
            soma_b = df_reais[coluna_bet].sum()
            soma_c = df_reais[coluna_payout].sum()
            diferenca = soma_b - soma_c  # apostado - payout
            qtd_rodadas = len(df_reais)
            percentual = calcular_percentual(qtd_rodadas)
            resultado_final = diferenca * percentual

            # EXIBIÇÃO
            st.subheader("📈 Resultados Gerais")
            st.write(f"**Total apostado:** {formatar_brl(soma_b)}")
            st.write(f"**Total ganho (payout):** {formatar_brl(soma_c)}")

            # mostra lucro para a casa (sem inverter aqui)
            if diferenca > 0:
                st.markdown(f"🏦 <span style='color:green;'>Lucro da casa: {formatar_brl(diferenca)}</span>", unsafe_allow_html=True)
            elif diferenca < 0:
                st.markdown(f"💸 <span style='color:red;'>Prejuízo da casa: {formatar_brl(diferenca)}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"⚖️ <span style='color:gray;'>Sem lucro ou prejuízo</span>", unsafe_allow_html=True)

            st.write(f"**Número de rodadas:** {qtd_rodadas}")
            st.write(f"**Percentual aplicado:** {percentual * 100:.0f}%")
            st.write(f"**Valor de cashback:** {formatar_brl(resultado_final)}")

            # REGRAS DE ELEGIBILIDADE
            if qtd_rodadas < 25 or percentual < 0.05 or resultado_final < 10 or diferenca <= 0:
                st.warning("❌ O jogador **não tem direito a receber cashback**.")
                motivos = []
                if qtd_rodadas < 25:
                    motivos.append(f"rodadas insuficientes ({qtd_rodadas})")
                if percentual < 0.05:
                    motivos.append(f"percentual aplicado menor que 5% ({percentual*100:.0f}%)")
                if resultado_final < 10:
                    motivos.append(f"valor final menor que 10 ({formatar_brl(resultado_final)})")
                if diferenca <= 0:
                    motivos.append("jogador teve lucro (sem perdas para cashback)")
                st.info("Motivo(s): " + ", ".join(motivos))
            else:
                st.success(f"✅ O jogador deve receber **{formatar_brl(resultado_final)}** em cashback!")

            # RESUMO POR JOGO (aqui visão do jogador)
            if coluna_jogo:
                st.divider()
                st.subheader("🎮 Resumo por Jogo (Rodadas Reais)")
                resumo_jogos = df_reais.groupby(coluna_jogo).agg(
                    Total_Apostado=(coluna_bet, 'sum'),
                    Total_Payout=(coluna_payout, 'sum'),
                    Rodadas=(coluna_bet, 'count')
                ).reset_index()

                for _, linha in resumo_jogos.iterrows():
                    st.markdown(f"#### 🎯 {linha[coluna_jogo]}")
                    st.write(f"📊 Total de rodadas: {int(linha['Rodadas'])}")
                    st.write(f"💰 Total apostado: {formatar_brl(linha['Total_Apostado'])}")
                    st.write(f"🏆 Total ganho (payout): {formatar_brl(linha['Total_Payout'])}")
                    lucro = linha['Total_Payout'] - linha['Total_Apostado']  # visão do jogador
                    st.markdown(mostrar_lucro(lucro), unsafe_allow_html=True)
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
            df.columns = [c.strip() for c in df.columns]

            # -----------------------------
            # ID do jogador
            # -----------------------------
            if "Client ID" in df.columns:
                player_id = df["Client ID"].iloc[0]
                st.markdown(f"### 🆔 ID do Jogador: {player_id}")

            # Colunas
            data_col = df.columns[1]
            free_col = "Free Spin"
            bet_col = "Bet"
            payout_col = "Payout"
            game_col = "Game Name"

            # Conversões
            df[bet_col] = df[bet_col].apply(converter_numero)
            df[payout_col] = df[payout_col].apply(converter_numero)
            df[data_col] = pd.to_datetime(df[data_col], errors="coerce")

            # -----------------------------
            # Filtro data/hora
            # -----------------------------
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

            # Função para lucro colorido
            def lucro_colorido(valor):
                if valor >= 0:
                    return f"<span style='color:green;'>R${valor:,.2f}</span>"
                else:
                    return f"<span style='color:red;'>R${valor:,.2f}</span>"

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
                           f"- Total apostado: {formatar_brl(total_apostado)}\n" \
                           f"- Total payout: {formatar_brl(total_payout)}\n" \
                           f"- Lucro do jogador: {lucro_colorido(lucro_jogador)}\n" \
                           f"- Primeira rodada: {primeira.strftime('%d/%m/%Y %H:%M')}\n" \
                           f"- Última rodada: {ultima.strftime('%d/%m/%Y %H:%M')}\n"

                st.markdown(f"### 🎰 {jogo}")
                st.markdown(resumo_tipo(df_reais, "reais"), unsafe_allow_html=True)
                st.markdown(resumo_tipo(df_free, "gratuitas"), unsafe_allow_html=True)

                # Resumo geral por jogo
                total_jogo_apostado = df_jogo[bet_col].sum()
                total_jogo_payout = df_jogo[payout_col].sum()
                lucro_jogo = total_jogo_payout - total_jogo_apostado
                st.markdown(f"**📈 Lucro total (reais + gratuitas):** {lucro_colorido(lucro_jogo)}", unsafe_allow_html=True)
                st.markdown("---")

                linhas_relatorio.append({
                    "Jogo": jogo,
                    "Total Apostado": total_jogo_apostado,
                    "Total Pago": total_jogo_payout,
                    "Lucro do Jogador": lucro_jogo
                })

            # -----------------------------
            # DataFrame final para download
            # -----------------------------
            df_relatorio = pd.DataFrame(linhas_relatorio)
            if "Lucro do Jogador" not in df_relatorio.columns:
                df_relatorio["Lucro do Jogador"] = 0

            # Função para gerar CSV
            def gerar_relatorio_csv(df_rel):
                return df_rel.to_csv(index=False).encode("utf-8")

            relatorio_csv = gerar_relatorio_csv(df_relatorio)

            st.download_button(
                label="📥 Baixar Relatório Completo",
                data=relatorio_csv,
                file_name="relatorio_jogos.csv",
                mime="text/csv"
            )

            # -----------------------------
            # Análise com Net Deposit
            # -----------------------------
            st.subheader("💵 Análise de Banca com Net Deposit")
            net_deposit_input = st.text_input("Informe o Net Deposit do jogador (R$)", "0,00")

            def parse_brl(valor):
                try:
                    return float(str(valor).replace("R$", "").replace(".", "").replace(",", "."))
                except:
                    return 0

            net_deposit = parse_brl(net_deposit_input)
            banca_total = net_deposit + df_relatorio["Lucro do Jogador"].sum()
            st.markdown(f"**Banca estimada do jogador considerando Net Deposit e resultados:** {formatar_brl(banca_total)}")

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
