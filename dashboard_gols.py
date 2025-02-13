import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import calendar
import urllib.parse
from PIL import Image
from pathlib import Path
import streamlit.components.v1 as components



# Configuração do Streamlit
st.set_page_config(page_title='Dashboard - Grag Apostador BetPro IA - Gols Asiáticos', layout='wide')
# Função para escolher a logo com base no tema
def setup_theme_logo():
    # Componente Javascript para detectar o tema
    theme_detector = components.html(
        """
        <script>
            // Detectar se o tema é escuro
            const isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

            // Enviar o tema para o Python
            window.parent.postMessage({
                type: 'theme',
                isDark: document.body.classList.contains('dark')
            }, '*');
        </script>
        """,
        height=0,
    )

    # Se não houver tema definido na sessão, assumir dark como padrão
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'

    # Definir os caminhos das imagens
    logo_dark = "assets/logo_vetor.png"
    logo_light = "assets/logo_vetor.png"

    # Usar o tema da sessão para selecionar a logo
    logo_path = logo_dark if st.session_state.theme == 'dark' else logo_light

    # Mostrar a imagem
    st.sidebar.image(logo_path, width=200)

st.title('Dashboard - Grag Apostador BetPro IA - Gols Asiáticos')

# Mapping of Portuguese month names to month numbers
month_map = {
    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4,
    "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8,
    "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
}

# Function to parse "Mês/Ano" strings into datetime objects
def parse_month_year(month_year_str):
    try:
        month_name, year = month_year_str.split('/')
        month = month_map[month_name]
        year = int(year) + 2000  # Convert "23" to 2023, "24" to 2024, etc.
        return datetime(year, month, 1)
    except (ValueError, KeyError):
        return None

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
def load_google_sheets(sheet_url, sheet_name):
    sheet_id = sheet_url.split("/d/")[1].split("/")[0]
    # URL-encode the sheet name to handle special characters like 'ç'
    encoded_sheet_name = urllib.parse.quote(sheet_name)
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}"

    try:
        df = pd.read_csv(csv_url, encoding='utf-8')
        df = df[['Nº', 'Data', 'Entrada', 'Liga', 'Mercado', 'Unidade', 'EV', 'Odd', 'Resultado', 'Lucro/prejuízo', 'Saldo']]
        df['Unidade'] = df['Unidade'].astype(str).str.replace(',', '.').astype(float)
        df['Lucro/prejuízo'] = df['Lucro/prejuízo'].astype(str).str.replace(',', '.').astype(float)
        df['Saldo'] = df['Saldo'].astype(str).str.replace(',', '.').astype(float)
        df['EV'] = df['EV'].astype(str).str.replace(',', '.').astype(float)


        # Converter colunas numéricas
        numeric_columns = ['Lucro/prejuízo', 'Odd', 'Unidade', 'Saldo', 'EV']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(convert_to_float)

        # Converter a coluna Data para datetime
        if 'Data' in df.columns:
            try:
                df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%y', errors='coerce')
                # Ajustar o ano com base no nome da aba (ex: "Maio/23" -> 2023)
                year = int(sheet_name.split('/')[1]) + 2000  # Converte "23" para 2023, "24" para 2024, etc.
                df['Data'] = df['Data'].apply(lambda x: x.replace(year=year) if pd.notnull(x) else x)
                # Remover linhas com datas inválidas
                df = df.dropna(subset=['Data'])
            except Exception as e:
                st.warning(f"Aviso: Erro ao converter datas na aba {sheet_name}: {e}")

        return df
    except Exception as e:
        st.error(f"Erro ao carregar a planilha {sheet_name}: {e}")
        return None

# URL da planilha do Google Sheets
google_sheets_url = "https://docs.google.com/spreadsheets/d/1eBsyCzVzA1lO44cJLQis7Wf5-H1kW4b7UTeax-oYO3s/edit?usp=sharing"

# Gerar a lista de abas desde "Maio/23" até o mês atual
def generate_sheet_names():
    start_month = 10  # Maio
    start_year = 2024
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year

    sheet_names = []
    for year in range(start_year, current_year + 1):
        start_m = start_month if year == start_year else 1
        end_m = current_month if year == current_year else 12
        for month in range(start_m, end_m + 1):
            month_name = get_month_name(month)
            sheet_name = f"{month_name}/{str(year)[-2:]}"
            sheet_names.append(sheet_name)
    return sheet_names

# Carregar todas as abas e concatenar
sheet_names = generate_sheet_names()
dfs = []
for sheet_name in sheet_names:
    df = load_google_sheets(google_sheets_url, sheet_name)
    if df is not None:
        dfs.append(df)

# Concatenar os DataFrames
if dfs:
    df = pd.concat(dfs, ignore_index=True)
else:
    df = None

# Restante do código (processamento, filtros, gráficos, etc.) permanece o mesmo
if df is not None:
    df = df.dropna(axis=1, how='all')

    # Substituir as palavras na coluna 'Mercado'
    df['Mercado'] = df['Mercado'].str.replace('Under', 'Under gols', case=False)
    df['Mercado'] = df['Mercado'].str.replace('Over', 'Over gols', case=False)

    # Adicionar coluna de mês/ano para filtro
    df['Mês/Ano'] = df['Data'].dt.month.map(get_month_name) + '/' + df['Data'].dt.year.astype(str).str[-2:]

    # Identificar o último mês/ano disponível
    last_date = df['Data'].max()
    last_month_year = f"{get_month_name(last_date.month)}/{str(last_date.year)[-2:]}"
    # Adicionar o logo da empresa
    setup_theme_logo()

    st.sidebar.header("📊 Filtros")

    # Get unique month/year values, excluding invalid ones
    # Get unique month/year values, excluding invalid ones
    available_months_years = [m for m in df['Mês/Ano'].unique() if "Mês Inválido" not in m]

    # Sort the months chronologically (most recent to oldest)
    sorted_months_years = sorted(
        available_months_years,
        key=parse_month_year,
        reverse=True  # Most recent first
    )

    # Add "Acumulado" as the first option
    filter_options = ["Acumulado"] + sorted_months_years

    # Get the last month/year as default if no selection is stored in session state
    if 'selected_period' not in st.session_state:
        st.session_state.selected_period = last_month_year

    # Single select radio button for period selection
    selected_period = st.sidebar.radio(
        "Selecione o período:",
        filter_options,
        index=filter_options.index(
            st.session_state.selected_period) if st.session_state.selected_period in filter_options else 1
    )

    # Update session state
    st.session_state.selected_period = selected_period

    # Filter the dataframe based on selection
    # Filter and process the dataframe based on selection
    if selected_period == "Acumulado":
        df_filtered = df.copy()  # Create a copy to avoid modifying the original dataframe
        # Recalculate the running balance
        df_filtered['Saldo'] = df_filtered['Lucro/prejuízo'].cumsum()
    else:
        df_filtered = df[df['Mês/Ano'] == selected_period].copy()
        # For single month view, also ensure proper date sorting and balance calculation

    # # Filtro de data
    # if 'Data' in df_filtered.columns and pd.api.types.is_datetime64_any_dtype(df_filtered['Data']):
    #     valid_dates = df_filtered['Data'].dropna().dt.date.unique()
    #     if len(valid_dates) > 0:
    #         start_date, end_date = st.sidebar.date_input(
    #             "Selecione o período:",
    #             value=(min(valid_dates), max(valid_dates)),
    #             min_value=min(valid_dates),
    #             max_value=max(valid_dates)
    #         )
    #
    #         # Filtrar o dataframe com base nas datas selecionadas
    #         df_filtered = df_filtered[
    #             (df_filtered['Data'].dt.date >= start_date) & (df_filtered['Data'].dt.date <= end_date)]
    # else:
    #     df_filtered = df.copy()

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
        if 'Saldo' in df_filtered.columns and 'Unidade' in df_filtered.columns and not df_filtered[
            'Saldo'].isna().all():
            df_filtered['Unidade'] = pd.to_numeric(df['Unidade'].astype(str).str.replace(',', '.'), errors='coerce')

            last_balance = df_filtered['Saldo'].dropna().iloc[-1]  # Último valor do Balance
            total_stakes = df_filtered['Unidade'].dropna().sum()

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
                label="📈 Win-rate",
                value=f"{win_rate:.1f}%",

            )
        else:
            st.metric(label="📈 Win-rate", value="N/A")

        # 🎯 Odds Média
    with col4:
        if 'Odd' in df_filtered.columns and not df_filtered['Odd'].isna().all():
            avg_odds = df_filtered['Odd'].dropna().mean()
            st.metric(label="🎯 Odd Média", value=f"{avg_odds:.2f}")
        else:
            st.metric(label="🎯 Odd Média", value="N/A")
        # 📈 Evolução do Saldo
    if 'Saldo' in df_filtered.columns and not df_filtered['Saldo'].isna().all():
        st.subheader("📈 Evolução do Saldo Diário")

        # Criar uma cópia do dataframe
        df_graph = df_filtered.dropna(subset=['Data', 'Saldo']).copy()

        # Criar uma coluna com o nome do mês/ano
        df_graph['Mês/Ano'] = df_graph['Data'].dt.month.map(get_month_name) + '/' + df_graph['Data'].dt.year.astype(
            str).str[-2:]

        # Obter o nome do mês/ano único para o título
        # Agrupar por Data e pegar o saldo final do dia
        df_daily_balance = df_graph.groupby('Data', as_index=False)['Saldo'].last()

        unique_months_years = df_graph['Mês/Ano'].unique()
        if len(unique_months_years) == 1:
            month_title = unique_months_years[0]  # Usa o formato "Mês/Ano"
        else:
            month_title = "Acumulado"
        # Agrupar por Data e pegar o saldo final do dia
        df_daily_balance = df_graph.groupby('Data', as_index=False)['Saldo'].last()

        # Criar as colunas formatadas de data
        df_daily_balance['Data_Formatada'] = df_daily_balance['Data'].dt.strftime('%d/%m')  # Para os pontos do gráfico
        df_daily_balance['Mes_Formatado'] = df_daily_balance['Data'].dt.strftime('%m/%y')  # Para os ticks do eixo

        # Criar o gráfico com todos os pontos
        fig_balance = px.line(
            df_daily_balance,
            x='Data_Formatada',
            y='Saldo',
            title=f'Evolução do Saldo - {month_title}',
            markers=True
        )

        # Ajustar o eixo X com base no período selecionado
        if len(unique_months_years) == 1:
            # Para um único mês, mostra todos os dias
            fig_balance.update_xaxes(
                title="Data",
                tickmode="linear"
            )
        else:
            # Para o acumulado, mostra apenas um tick por mês
            # Encontrar a primeira data de cada mês
            first_days = []
            tick_positions = []

            for i, row in enumerate(df_daily_balance.itertuples()):
                # Se é o primeiro registro do mês ou o último registro do DataFrame
                if i == 0 or df_daily_balance['Mes_Formatado'].iloc[i] != df_daily_balance['Mes_Formatado'].iloc[i - 1]:
                    first_days.append(row.Mes_Formatado)
                    tick_positions.append(i)

            fig_balance.update_xaxes(
                title="Data",
                tickmode="array",
                ticktext=first_days,  # Texto dos ticks (mês/ano)
                tickvals=tick_positions,  # Posição dos ticks
                tickangle=0  # Rotacionar labels para melhor legibilidade
            )

        # Ajustes adicionais no layout
        fig_balance.update_layout(
            xaxis_title="Data",
            yaxis_title="Saldo (unidades)",
            hovermode='x unified'
        )

        # Mostrar o gráfico no Streamlit
        st.plotly_chart(fig_balance, use_container_width=True)

    # 📊 Gráficos de Resultados e Categorias
    col_left, col_right = st.columns(2)

    with col_left:
        if 'Mercado' in df_filtered.columns and 'Lucro/prejuízo' in df_filtered.columns:
            mercado_pl = df_filtered.groupby('Mercado')['Lucro/prejuízo'].sum().reset_index()
            mercado_pl = mercado_pl.sort_values('Lucro/prejuízo', ascending=True)
            fig_mercado = px.bar(
                mercado_pl,
                x='Lucro/prejuízo',
                y='Mercado',
                title='Lucro por Mercado',
                color='Lucro/prejuízo',
                color_continuous_scale='RdYlGn',
                color_continuous_midpoint=0,  # Define o zero como ponto neutro
                orientation='h',  # Define a orientação horizontal
                labels={'Lucro/prejuízo': 'Lucro em unidades'}  # Adiciona esta linha para mudar o título do eixo
            )

            st.plotly_chart(fig_mercado)

    with col_right:
        if 'Mercado' in df_filtered.columns and 'Lucro/prejuízo' in df_filtered.columns and 'Unidade' in df_filtered.columns:
            # Calcular lucro total e investimento total por mercado
            roi_df = df_filtered.groupby('Mercado').agg({'Lucro/prejuízo': 'sum', 'Unidade': 'sum'}).reset_index()

            # Calcular ROI
            roi_df['ROI'] = roi_df['Lucro/prejuízo'] / roi_df['Unidade']*100
            roi_df = roi_df.sort_values('ROI', ascending=True)

            # Criar gráfico de barras horizontais para ROI
            fig_roi = px.bar(
                roi_df,
                x='ROI',  # ROI no eixo X
                y='Mercado',  # Mercado no eixo Y
                title='ROI por Mercado',
                color='ROI',
                color_continuous_scale='RdYlGn',
                color_continuous_midpoint=0,  # Define o zero como ponto neutro
                orientation='h'  # Barras na horizontal

            )
            # Atualizar o formato dos rótulos do eixo X para exibir como porcentagem
            fig_roi.update_layout(
                xaxis_tickformat=".1f",  # Mantém uma casa decimal
                xaxis_ticksuffix="%"  # Adiciona o símbolo de porcentagem
            )

            st.plotly_chart(fig_roi)

    # 📋 Tabela de Detalhamento de Apostas
    st.subheader("📋 Detalhamento das Apostas")

    # Ensure 'Nº' is numeric and sort in descending order
    df_filtered["Nº"] = pd.to_numeric(df_filtered["Nº"], errors="coerce")
    df_filtered = df_filtered.dropna(subset=["Entrada"])  # Remove rows where 'Nº' is NaN

    # Select columns B to M (indices 1 to 12) and sort in descending order by 'Nº'
    df_filtered = df_filtered.sort_values(by="Nº", ascending=False).reset_index(drop=True)
    df_filtered = df_filtered.reset_index(drop=True)
    df_filtered["Data"] = df_filtered["Data"].dt.strftime("%d/%m/%y")
    # Ensure numeric columns are properly formatted to 3 decimal places
    df_filtered["Unidade"] = df_filtered["Unidade"].apply(lambda x: f"{x:.3f}")
    df_filtered["Odd"] = df_filtered["Odd"].apply(lambda x: f"{x:.3f}")
    df_filtered["Lucro/prejuízo"] = df_filtered["Lucro/prejuízo"].apply(lambda x: f"{x:.3f}")
    df_filtered["Saldo"] = df_filtered["Saldo"].apply(lambda x: f"{x:.3f} u")
    df_filtered = df_filtered.drop(['Nº', 'Mês/Ano'], axis=1)

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
        return f"color: {colors.get(value, 'black')}"  # Default to black if not found


    def color_saldo(value):
        try:
            # Remover o 'u' (ou qualquer outro caractere não numérico) antes da conversão
            value = float(value.replace('u', '').replace(',', ''))  # Garantir que o valor seja numérico
        except (ValueError, AttributeError):
            return "color: black"  # Caso não seja um número, usar preto

        if value > 0:
            return "color: #27AE60"  # Verde para valores positivos
        elif value < 0:
            return "color: #C0392B"  # Vermelho para valores negativos
        else:
            return "color: #BFBFBF"  # Cinza para zero


    def apply_colors(df):
        # Cria um DataFrame vazio para armazenar os estilos
        styles = pd.DataFrame("", index=df.index, columns=df.columns)

        # Aplica as cores para a coluna "Resultado"
        styles["Resultado"] = df_filtered["Resultado"].map(color_resultado)

        # Copia as cores de "Resultado" para "L/P"
        styles["Lucro/prejuízo"] = styles["Resultado"]

        # Aplica as cores para a coluna "Saldo"
        styles["Saldo"] = df["Saldo"].map(color_saldo)

        return styles


    # Aplicar estilos
    styled_df = df_filtered.style.apply(apply_colors, axis=None, subset=["Resultado", "Lucro/prejuízo", "Saldo"])

    # Display in Streamlit
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