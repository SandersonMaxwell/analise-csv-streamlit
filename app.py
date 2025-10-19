import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Conversor de Datas (Excel)", page_icon="🎰", layout="centered")

st.title("🎰 Conversor de Datas e Filtro de FREESPINS")
st.write("""
Envie um arquivo Excel contendo uma coluna de datas (coluna **B**) e uma coluna **FREESPINS**.  
O app irá:
- Filtrar apenas as linhas onde **FREESPINS = False** (rodadas pagas);  
- Converter a data da coluna B para o formato **YYYY-MM-DD**;  
- Gerar um novo arquivo Excel com os dados filtrados e convertidos.
""")

# Upload do arquivo Excel
uploaded_file = st.file_uploader("📤 Envie seu arquivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Lê o Excel
        df = pd.read_excel(uploaded_file)

        st.subheader("📊 Pré-visualização dos dados originais:")
        st.dataframe(df.head())

        # Verifica se existe a coluna FREESPINS
        if "FREESPINS" not in df.columns:
            st.error("❌ A coluna 'FREESPINS' não foi encontrada no arquivo. Verifique o nome exato no cabeçalho.")
        else:
            # Filtra apenas onde FREESPINS é False
            df_filtrado = df[df["FREESPINS"] == False]

            # Verifica se ainda há linhas após o filtro
            if df_filtrado.empty:
                st.warning("⚠️ Nenhuma linha com FREESPINS = False foi encontrada.")
            else:
                # Define a coluna de data como a segunda (coluna B)
                coluna_data = df_filtrado.columns[1]

                if st.button("🚀 Converter Datas e Gerar Arquivo"):
                    # Converte as datas
                    df_filtrado[coluna_data] = pd.to_datetime(df_filtrado[coluna_data], errors='coerce')
                    df_filtrado[coluna_data] = df_filtrado[coluna_data].dt.strftime('%Y-%m-%d')

                    st.success("✅ Conversão concluída com sucesso!")
                    st.dataframe(df_filtrado.head())

                    # Cria buffer para download do Excel convertido
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df_filtrado.to_excel(writer, index=False, sheet_name='Dados Convertidos')
                    buffer.seek(0)

                    # Botão para baixar o novo Excel
                    st.download_button(
                        label="⬇️ Baixar Excel Convertido",
                        data=buffer,
                        file_name="datas_convertidas_filtradas.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    except Exception as e:
        st.error(f"❌ Ocorreu um erro ao processar o arquivo: {e}")
