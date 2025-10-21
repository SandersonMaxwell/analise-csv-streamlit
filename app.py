import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Calculadora", page_icon="📊", layout="wide")
st.title("📊 Calculadora")

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

    uploaded_file = st.file_uploader("Envie o arquivo CSV do jogador", type=["csv"])

    if uploaded_file:
        try:
            raw = uploaded_file.read().decode("utf-8")
            sep = ',' if raw.count(',') > raw.count(';') else ';'
            df = pd.read_csv(io.StringIO(raw), sep=sep)

            colunas_lower = [c.lower() for c in df.columns]
            coluna_bet = next((c for c in df.columns if 'bet' in c.lower()), None)
            coluna_payout = next((c for c in df.columns if 'payout' in c.lower()), None)
            coluna_free = next((c for c in df.columns if 'free' in c.lower()), None)
            coluna_jogo = next((c for c in df.columns if 'game' in c.lower()), None)

            if not coluna_bet or not coluna_payout:
                st.error("❌ Não foi possível identificar as colunas 'Bet' e 'Payout'.")
                st.stop()

            df[coluna_bet] = df[coluna_bet].apply(converter_numero)
            df[coluna_payout] = df[coluna_payout].apply(converter_numero)

            if coluna_free:
                df['Free Spin'] = df[coluna_free].astype(str).str.lower()
                df_reais = df[df['Free Spin'] == 'false']
            else:
                df_reais = df.copy()

            soma_b = df_reais[coluna_bet].sum()
            soma_c = df_reais[coluna_payout].sum()
            diferenca = soma_c - soma_b
            qtd_rodadas = len(df_reais)
            percentual = calcular_percentual(qtd_rodadas)
            resultado_final = diferenca * percentual

            st.subheader("📈 Resultados Gerais")
            st.write(f"**Total apostado:** {formatar_brl(soma_b)}")
            st.write(f"**Total ganho (payout):** {formatar_brl(soma_c)}")
            st.markdown(mostrar_lucro(diferenca), unsafe_allow_html=True)
            st.write(f"**Número de rodadas:** {qtd_rodadas}")
            st.write(f"**Percentual aplicado:** {percentual * 100:.0f}%")
            st.write(f"**Valor de cashback:** {formatar_brl(resultado_final)}")

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

            if coluna_jogo:
                st.subheader("🎮 Resumo por Jogo (Rodadas Reais)")
                resumo_jogos = df_reais.groupby(coluna_jogo).agg(
                    Total_Apostado=(coluna_bet, 'sum'),
                    Total_Payout=(coluna_payout, 'sum'),
                    Rodadas=('Free Spin', 'count')
                ).reset_index()

                for _, linha in resumo_jogos.iterrows():
                    st.markdown(f"#### 🎯 {linha[coluna_jogo]}")
                    st.write(f"Total de rodadas: {int(linha['Rodadas'])}")
                    st.write(f"Total apostado: {formatar_brl(linha['Total_Apostado'])}")
                    st.write(f"Total ganho (payout): {formatar_brl(linha['Total_Payout'])}")
                    lucro = linha['Total_Payout'] - linha['Total_Apostado']
                    st.markdown(mostrar_lucro(lucro), unsafe_allow_html=True)
                    st.divider()

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

# =============================
# ABA 2 - RESUMO DETALHADO
# =============================
with abas[1]:
    st.header("🎯 Resumo Detalhado por Jogo")

    uploaded_file2 = st.file_uploader("Envie o arquivo CSV do jogador", type=["csv"], key="detalhado")

    if uploaded_file2:
        try:
            raw = uploaded_file2.read().decode("utf-8")
            sep = ',' if raw.count(',') > raw.count(';') else ';'
            df = pd.read_csv(io.StringIO(raw), sep=sep)

            coluna_jogo = next((c for c in df.columns if 'game' in c.lower()), None)
            coluna_bet = next((c for c in df.columns if 'bet' in c.lower()), None)
            coluna_payout = next((c for c in df.columns if 'payout' in c.lower()), None)
            coluna_data = next((c for c in df.columns if 'creation' in c.lower()), None)
            coluna_free = next((c for c in df.columns if 'free' in c.lower()), None)

            if not all([coluna_jogo, coluna_bet, coluna_payout, coluna_data]):
                st.error("❌ O CSV precisa conter as colunas 'Game Name', 'Bet', 'Payout' e 'Creation Date'.")
                st.stop()

            df[coluna_bet] = df[coluna_bet].apply(converter_numero)
            df[coluna_payout] = df[coluna_payout].apply(converter_numero)
            df[coluna_data] = pd.to_datetime(df[coluna_data], errors='coerce')

            if coluna_free:
                df['Free Spin'] = df[coluna_free].astype(str).str.lower()
            else:
                df['Free Spin'] = 'false'

            # =============================
            # FILTROS DE DATA E HORA
            # =============================
            st.markdown("### 📅 Filtro por Data e Hora")

            data_min = df[coluna_data].min()
            data_max = df[coluna_data].max()

            col1, col2 = st.columns(2)
            with col1:
                data_inicio = st.datetime_input(
                    "📆 Data e hora inicial",
                    value=data_min,
                    min_value=data_min,
                    max_value=data_max,
                    format="DD/MM/YYYY HH:mm"
                )
            with col2:
                data_fim = st.datetime_input(
                    "📆 Data e hora final",
                    value=data_max,
                    min_value=data_min,
                    max_value=data_max,
                    format="DD/MM/YYYY HH:mm"
                )

            df = df[(df[coluna_data] >= data_inicio) & (df[coluna_data] <= data_fim)]

            # =============================
            # EXIBIÇÃO DOS RESULTADOS
            # =============================
            jogos = df[coluna_jogo].unique()

            for jogo in jogos:
                st.markdown(f"### 🎮 {jogo}")

                for status in ['false', 'true']:
                    tipo = "Rodadas Reais" if status == 'false' else "Rodadas Gratuitas"
                    subset = df[(df[coluna_jogo] == jogo) & (df['Free Spin'] == status)]

                    if not subset.empty:
                        total_rodadas = len(subset)
                        total_apostado = subset[coluna_bet].sum()
                        total_payout = subset[coluna_payout].sum()
                        lucro = total_payout - total_apostado

                        primeira_data = subset[coluna_data].min().strftime("%d/%m/%Y %H:%M")
                        ultima_data = subset[coluna_data].max().strftime("%d/%m/%Y %H:%M")

                        st.markdown(f"#### 🎯 {tipo}")
                        st.write(f"**Total de rodadas:** {total_rodadas}")
                        st.write(f"**Total apostado:** {formatar_brl(total_apostado)}")
                        st.write(f"**Total ganho (payout):** {formatar_brl(total_payout)}")
                        st.markdown(mostrar_lucro(lucro), unsafe_allow_html=True)
                        st.write(f"**Primeira rodada:** {primeira_data}")
                        st.write(f"**Última rodada:** {ultima_data}")
                        st.divider()

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

