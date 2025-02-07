import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import calendar

# Configuração do Streamlit
st.set_page_config(page_title='Dashboard - Grag Apostador (broker)', layout='wide')
st.title('Dashboard - Grag Apostador (broker)')


# Obter o nome do mês em português
def get_month_name(month_number):
    months_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    return months_pt.get(month_number, "Mês Inválido")

# Função para converter strings numéricas para float
def convert_to_float(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.replace('R$', '').replace(' ', '').replace(',', '.')
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


# Função para carregar dados do Google Sheets
def load_google_sheets(sheet_url):
    sheet_id = sheet_url.split("/d/")[1].split("/")[0]
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"

    try:
        df = pd.read_csv(csv_url)
        df.drop(columns=['A', 'M/F', 'Referência', 'Stake*', 'Unnamed: 16', 'Dia', 'Saldo.1'], inplace=True)

        df['Stake'] = df['Stake'].astype(str).str.replace(',', '.').astype(float)
        df['L/P'] = df['L/P'].astype(str).str.replace(',', '.').astype(float)
        df['Saldo'] = df['Saldo'].astype(str).str.replace(',', '.').astype(float)


        # Converter colunas numéricas
        numeric_columns = ['L/P', 'Odd', 'Stake']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(convert_to_float)

        # Converter a coluna Day para datetime
        if 'Data' in df.columns:
            try:
                df['Data'] = pd.to_datetime(df['Data'], format='%d/%m', errors='coerce')
                df['Data'] = df['Data'].apply(lambda x: x.replace(year=2025) if pd.notnull(x) else x)


            except Exception as e:
                st.warning(f"Aviso: Erro ao converter datas: {e}")

        return df
    except Exception as e:
        st.error(f"Erro ao carregar a planilha: {e}")
        return None


# URL da planilha do Google Sheets
google_sheets_url = "https://docs.google.com/spreadsheets/d/1HhrDjcCB6nIfnbJxh7vRCOkfZ372Ln3heHIA1p6w6aI/edit?usp=sharing"

# Carregar os dados
df = load_google_sheets(google_sheets_url)
df = df.dropna(axis=1, how='all')

month_translation = {
    "January": "Janeiro", "February": "Fevereiro", "March": "Março", "April": "Abril",
    "May": "Maio", "June": "Junho", "July": "Julho", "August": "Agosto",
    "September": "Setembro", "October": "Outubro", "November": "Novembro", "December": "Dezembro"
}

if df is not None:
    # Sidebar com filtros
    st.sidebar.header("📊 Filtros")

    # Filtro de data
    if 'Data' in df.columns and pd.api.types.is_datetime64_any_dtype(df['Data']):
        valid_dates = df['Data'].dropna().dt.date.unique()
        if len(valid_dates) > 0:
            start_date, end_date = st.sidebar.date_input(
                "Selecione o período:",
                value=(min(valid_dates), max(valid_dates)),
                min_value=min(valid_dates),
                max_value=max(valid_dates)
            )

            # Filtrar o dataframe com base nas datas selecionadas
            df_filtered = df[(df['Data'].dt.date >= start_date) & (df['Data'].dt.date <= end_date)]
        else:
            df_filtered = df.copy()
    else:
        df_filtered = df.copy()

    # Layout principal com quatro colunas
    col1, col2, col3, col4 = st.columns(4)

    # 💰 Saldo Total
    with col1:
        if 'Saldo' in df_filtered.columns and not df_filtered['Saldo'].isna().all():
            last_balance = df_filtered['Saldo'].dropna().iloc[-1]  # Último valor do Balance
            st.metric(label="💰 Saldo Total", value=f"{last_balance:.2f} unidades")
        else:
            st.metric(label="💰 Saldo Total", value="N/A")

    # 📊 ROI
    with col2:
        if 'Saldo' in df_filtered.columns and 'Stake' in df_filtered.columns and not df_filtered[
            'Saldo'].isna().all():
            last_balance = df_filtered['Saldo'].dropna().iloc[-1]  # Último valor do Balance
            total_stakes = df_filtered['Stake'].dropna().sum()

            # Calcular ROI
            if total_stakes > 0:
                roi = ((last_balance) / total_stakes) * 100
                st.metric(
                    label="📊 ROI",
                    value=f"{roi:.1f}%"
                )
            else:
                st.metric(label="📊 ROI", value="N/A")
        else:
            st.metric(label="📊 ROI", value="N/A")

    # 📈 Taxa de Acerto
    with col3:
        if 'Resultado' in df_filtered.columns:
            # [Rest of the existing win rate calculation remains the same]
            total_wins = len(df_filtered[df_filtered['Resultado'] == 'Ganha'])
            total_losses = len(df_filtered[df_filtered['Resultado'] == 'Perdida'])
            total_half_win = len(df_filtered[df_filtered['Resultado'] == 'Ganha/devolvida']) * 0.5
            total_half_loss = len(df_filtered[df_filtered['Resultado'] == 'Perdida/devolvida']) * 0.5

            total_valid_bets = total_wins + total_losses + total_half_win + total_half_loss

            if total_valid_bets > 0:
                win_rate = ((total_wins + total_half_win) / total_valid_bets) * 100
            else:
                win_rate = 0

            st.metric(
                label="📈 Taxa de Acerto",
                value=f"{win_rate:.1f}%",

            )
        else:
            st.metric(label="📈 Taxa de Acerto", value="N/A")

    # Convert the 'Odd' column to float, replacing ',' with '.'
    if 'Odd' in df_filtered.columns:
        df_filtered['Odd'] = df_filtered['Odd'].astype(str).str.replace(',', '.').astype(float)

    # 🎯 Odds Média
    with col4:
        if 'Odd' in df_filtered.columns and not df_filtered['Odd'].isna().all():
            avg_odds = df_filtered['Odd'].dropna().mean()
            st.metric(label="🎯 Odds Média", value=f"{avg_odds:.2f}")
        else:
            st.metric(label="🎯 Odds Média", value="N/A")

    # 📈 Evolução do Saldo
    if 'Saldo' in df_filtered.columns and not df_filtered['Saldo'].isna().all():
        st.subheader("📈 Evolução do Saldo Diário")

        # Criar uma cópia do dataframe
        df_graph = df_filtered.dropna(subset=['Data', 'Saldo']).copy()

        # Criar uma coluna com o nome do mês
        df_graph['Mês'] = df_graph['Data'].dt.strftime('%B')

        # Obter o nome do mês único para o título
        unique_months = df_graph['Mês'].unique()
        if len(unique_months) == 1:
            month_title = month_translation.get(unique_months[0], "Mês Inválido")
        else:
            month_title = "Múltiplos Meses"

        # Agrupar por Data e pegar o saldo final do dia
        df_daily_balance = df_graph.groupby('Data', as_index=False)['Saldo'].last()

        # Criar a coluna formatada de data para rótulos do eixo X
        df_daily_balance['Data_Formatada'] = df_daily_balance['Data'].dt.strftime('%d/%m')

        # Criar o gráfico com X sendo os dias e Y o saldo final do dia
        fig_balance = px.line(
            df_daily_balance,
            x='Data_Formatada',  # Agora o eixo X será por dia
            y='Saldo',
            title=f'Evolução do Saldo - {month_title}',
            markers=True  # Adiciona pontos nos dias
        )

        # Ajustar o eixo X para mostrar todas as datas corretamente
        fig_balance.update_xaxes(
            title="Data",
            tickmode="linear"  # Garante espaçamento uniforme entre os dias
        )

        # Mostrar o gráfico no Streamlit
        st.plotly_chart(fig_balance, use_container_width=True)

    # 📊 Gráficos de Resultados e Categorias
    col_left, col_right = st.columns(2)

    with col_left:
        if 'Resultado' in df_filtered.columns:
            results_count = df_filtered['Resultado'].value_counts()
            fig_results = px.pie(
                values=results_count.values,
                names=results_count.index,
                title='Distribuição de Resultados'
            )
            st.plotly_chart(fig_results)

    with col_right:
        if 'Category' in df_filtered.columns:
            category_count = df_filtered['Category'].value_counts()
            fig_category = px.bar(
                x=category_count.index,
                y=category_count.values,
                title='Apostas por Categoria'
            )
            st.plotly_chart(fig_category)

    # 📋 Tabela de Detalhamento de Apostas
    st.subheader("📋 Detalhamento das Apostas")

    # Ensure 'Nº' is numeric and sort in descending order
    df["Nº"] = pd.to_numeric(df["Nº"], errors="coerce")
    df = df.dropna(subset=["Entrada"])  # Remove rows where 'Nº' is NaN

    # Select columns B to M (indices 1 to 12) and sort in descending order by 'Nº'
    df_sorted = df.sort_values(by="Nº", ascending=False).reset_index(drop=True)
    df_detailed = df_sorted.iloc[:, 1:13]
    df_detailed = df_detailed.reset_index(drop=True)
    df_detailed.drop(columns=['Em aberto'], inplace=True)
    df_detailed["Data"] = df_detailed["Data"].dt.strftime("%d/%m/%y")
    # Ensure numeric columns are properly formatted to 3 decimal places
    df_detailed["Stake"] = df_detailed["Stake"].apply(lambda x: f"{x:.3f}")
    df_detailed["Odd"] = df_detailed["Odd"].apply(lambda x: f"{x:.3f}")
    df_detailed["L/P"] = df_detailed["L/P"].apply(lambda x: f"{x:.3f}")
    df_detailed["Saldo"] = df_detailed["Saldo"].apply(lambda x: f"{x:.3f}")

    # Define the color function for the 'Resultado' column
    def color_resultado(value):
        colors = {
            "Ganha": "#27AE60",  # Strong green
            "Ganha/devolvida": "#2ECC71",  # Light green
            "Devolvida": "#BFBFBF",  # Neutral gray
            "Aguardando": "#BFBFBF",  # Neutral gray
            "Perdida/devolvida": "#E74C3C",  # Light red
            "Perdida": "#C0392B",  # Strong red
        }
        return f"color: {colors.get(value, 'black')}"  # Default to black if not in dictionary

    # Apply styles only to 'Resultado' and 'L/P'
    styled_df = df_detailed.style.map(color_resultado, subset=["Resultado"])

    # Display in Streamlit
    st.subheader("📋 Detalhamento das Apostas")
    st.dataframe(styled_df, use_container_width=True)

    # 📥 Download dos dados filtrados
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download dos dados",
        data=csv,
        file_name="betting_data.csv",
        mime="text/csv"
    )
else:
    st.error("⚠️ Não foi possível carregar os dados.")

st.write("Desenvolvido por Grag Apostador ⚽")