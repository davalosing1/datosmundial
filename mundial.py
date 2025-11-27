import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Análisis Mundial", layout="wide", page_icon="⚽")
st.title("⚽ Dashboard de Estadísticas del Mundial (Completo)")
st.markdown("Este proyecto analiza el rendimiento de jugadores utilizando datos de defensa, disparo, tiempo de juego, **porteros, posesión y disciplina**.")

# --- 2. CARGAR TODOS LOS ARCHIVOS ---
# Archivos Iniciales
df_stats = pd.read_csv('player_stats.csv')
df_defense = pd.read_csv('player_defense.csv')
df_shooting = pd.read_csv('player_shooting.csv')
df_time = pd.read_csv('player_playingtime.csv')

# Nuevos Archivos
df_keepers = pd.read_csv('player_keepers.csv')
df_misc = pd.read_csv('player_misc.csv')
df_possession = pd.read_csv('player_possession.csv')

# --- 3. UNIR LAS TABLAS (MERGE) ---
# Usamos df_stats como base y le agregamos columnas de los otros archivos.

# 1. Unir con Defensa, Disparo y Tiempo
df_temp1 = pd.merge(df_stats, df_defense[['player', 'tackles', 'interceptions', 'blocks']], on='player', how='left')
df_temp2 = pd.merge(df_temp1, df_shooting[['player', 'shots', 'average_shot_distance']], on='player', how='left')
df_temp3 = pd.merge(df_temp2, df_time[['player', 'minutes_pct']], on='player', how='left')
df_temp3 = df_temp3.drop(columns=['cards_yellow', 'cards_red'], errors='ignore')
df_misc_cols = df_misc[['player', 'cards_red', 'cards_yellow', 'fouls', 'fouled']]
df_temp4 = pd.merge(df_temp3, df_misc_cols, on='player', how='left')
df_temp5 = pd.merge(df_temp4, df_possession[['player', 'touches']], on='player', how='left')
df = pd.merge(df_temp5, df_keepers[['player', 'gk_saves']], on='player', how='left')

# Limpieza básica: Rellenar vacíos con 0
df = df.fillna(0)

# --- CORRECCIÓN DE ERROR DE FORMATO DE EDAD ---
def limpiar_edad(age_str):
    try:
        if isinstance(age_str, str) and '-' in age_str:
            return int(age_str.split('-')[0])
        else:
            # Si no es una cadena o ya es un número, intenta convertirlo a int
            return int(age_str)
    except:
        return 0

df['age'] = df['age'].apply(limpiar_edad)
# -----------------------------------------------

# --- 4. BARRA LATERAL (FILTROS) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/53/53283.png", width=80)
st.sidebar.header("Filtros Globales")

# Componente 1: Selectbox (Selección de País)
paises = sorted(df['team'].unique())
paises.insert(0, "Todos") # Agregamos la opción "Todos" al inicio
pais_seleccionado = st.sidebar.selectbox("Selecciona un País:", paises)

# Componente 2: Multiselect (Selección de Posición)
posiciones = sorted(df['position'].unique())
posiciones_seleccionadas = st.sidebar.multiselect(
    "Filtrar por Posición:",
    posiciones,
    default=posiciones
)

# Componente 3: Slider (Rango de Edad)
edad_min, edad_max = int(df['age'].min()), int(df['age'].max())
rango_edad = st.sidebar.slider("Selecciona Rango de Edad:", edad_min, edad_max, (20, 35))

# --- APLICAR FILTROS ---

# 1. Definir la condición de país
if pais_seleccionado == "Todos":
    # Si es "Todos", la condición es True para todos los jugadores
    filtro_pais = pd.Series([True] * len(df))
else:
    # Si se selecciona un país, aplicar el filtro normal
    filtro_pais = (df['team'] == pais_seleccionado)

# 2. Aplicar el filtro completo
df_filtrado = df[
    (filtro_pais) & # Usamos la condición dinámica del país
    (df['position'].isin(posiciones_seleccionadas)) &
    (df['age'] >= rango_edad[0]) &
    (df['age'] <= rango_edad[1])
]

st.sidebar.markdown("---")
st.sidebar.write(f"📊 Jugadores mostrados: **{len(df_filtrado)}**")

# --- 5. ESTRUCTURA DE PESTAÑAS (TABS) ---
tab1, tab2 = st.tabs(["📈 Dashboard Gráfico", "📄 Datos Detallados"])

# --- PESTAÑA 1: VISUALIZACIONES ---
with tab1:
    st.subheader(f"Análisis visual de: {pais_seleccionado}")

    # KPIs / Métricas principales
    col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)
    col_kpi1.metric("Goles Totales", df_filtrado['goals'].sum())
    col_kpi2.metric("Asistencias", df_filtrado['assists'].sum())
    col_kpi3.metric("Entradas (Tackles)", df_filtrado['tackles'].sum())
    col_kpi4.metric("Tarjetas Amarillas", df_filtrado['cards_yellow'].sum())
    col_kpi5.metric("Tarjetas Rojas", df_filtrado['cards_red'].sum())

    st.markdown("---")

    # FILA 1 DE GRÁFICOS (Ofensivo y Defensivo)
    col1, col2 = st.columns(2)

    with col1:
        # --- Lógica de Título Dinámico ---
        if pais_seleccionado == "Todos":
            st.info("Top 10 Goleadores del Mundial")
        else:
            st.info(f"Top Goleadores {pais_seleccionado}")
        # --- Fin de Lógica de Título Dinámico ---
        
        # GRÁFICO 1: BARRAS (Goals)
        # Agrupamos por jugador para el filtrado, si es "Todos", muestra los top goleadores de todos los países.
        if pais_seleccionado == "Todos":
            df_goles = df_filtrado.groupby('player')['goals'].sum().reset_index()
            df_goles = df_goles[df_goles['goals'] > 0].sort_values('goals', ascending=False).head(10)
        else:
            df_goles = df_filtrado[df_filtrado['goals'] > 0].sort_values('goals', ascending=False)


        if not df_goles.empty:
            fig1, ax1 = plt.subplots(figsize=(6, 4))
            ax1.bar(df_goles['player'], df_goles['goals'], color='teal')
            ax1.set_ylabel("Cantidad de Goles")
            ax1.set_title("Goles por Jugador")
            plt.xticks(rotation=45, ha='right')
            st.pyplot(fig1)
        else:
            st.warning("No hay goles registrados con estos filtros.")

    with col2:
        st.info("Relación: Minutos vs Tiros/Intercepciones")
        # GRÁFICO 2: SCATTER PLOT (Minutes vs Shots)
        opcion_y = st.radio("Elige variable Y:", ["shots", "interceptions"], horizontal=True, key="radio_scatter")

        if not df_filtrado.empty:
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            sns.scatterplot(data=df_filtrado, x='minutes', y=opcion_y, hue='position', s=100, ax=ax2)
            ax2.set_xlabel("Minutos Jugados")
            ax2.set_ylabel(opcion_y.capitalize())
            ax2.set_title(f"Minutos vs {opcion_y.capitalize()}")
            st.pyplot(fig2)
        else:
            st.warning("No hay datos para esta combinación de filtros.")

    st.markdown("---")

    # FILA 2 DE GRÁFICOS (Edad y Distribución Defensiva)
    col3, col4 = st.columns(2)

    with col3:
        # --- GRÁFICO 3: EDAD VS TOTAL DE GOLES ---
        st.info("Rendimiento Ofensivo: Edad vs. Total de Goles")
        
        # Agrupar por 'age' y sumar 'goals' (total de goles, no promedio/90min)
        df_rendimiento = df_filtrado.groupby('age')['goals'].sum().reset_index()
        df_rendimiento = df_rendimiento[df_rendimiento['goals'] > 0] # Mostrar solo edades con goles

        if not df_rendimiento.empty:
            fig3, ax3 = plt.subplots(figsize=(6, 4))
            # Usamos un gráfico de dispersión con línea para ver la tendencia por edad
            sns.lineplot(data=df_rendimiento, x='age', y='goals', marker='o', color='crimson', ax=ax3)
            # También podemos añadir las etiquetas de goles sobre los puntos si hay pocos datos
            for index, row in df_rendimiento.iterrows():
                ax3.text(row['age'], row['goals'], int(row['goals']), ha='center', va='bottom', fontsize=9)
                
            ax3.set_xlabel("Edad del Jugador")
            ax3.set_ylabel("Total de Goles")
            ax3.set_title("Total de Goles por Edad")
            st.pyplot(fig3)
        else:
            st.warning("No hay goles registrados con estos filtros para el análisis de edad.")


    with col4:
        # --- GRÁFICO 4: TOTAL DE INTERCEPCIONES POR POSICIÓN ---
        df_plot_interceptions = df if pais_seleccionado == "Todos" else df_filtrado
        
        st.info(f"Total de Intercepciones por Posición ({pais_seleccionado})")
        
        # 1. Agrupar por posición y sumar las intercepciones
        df_interceptions_total = df_plot_interceptions.groupby('position')['interceptions'].sum().reset_index()
        df_interceptions_total = df_interceptions_total.sort_values(by='interceptions', ascending=False)
        
        if not df_interceptions_total.empty:
            fig4, ax4 = plt.subplots(figsize=(6, 4))
            bars = sns.barplot(data=df_interceptions_total, x='position', y='interceptions', palette="Pastel1", ax=ax4)
            
            # 2. Ajustar el límite del eje Y y añadir etiquetas de datos
            max_interceptions = df_interceptions_total['interceptions'].max()
            ax4.set_ylim(0, max_interceptions * 1.1) 
            
            for bar in bars.patches:
                height = bar.get_height()
                ax4.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height + (max_interceptions * 0.01),
                    f'{int(height)}',
                    ha='center',
                    va='bottom',
                    fontsize=10 
                )

            ax4.set_title("Defensa: Total de Intercepciones por Posición")
            ax4.set_ylabel("Total de Intercepciones")
            ax4.set_xlabel("Posición")
            st.pyplot(fig4)
        else:
            st.warning("No hay datos de intercepciones para esta selección.")

    st.markdown("---")

    # FILA 3 DE GRÁFICOS (Nuevas Métricas: Disciplina y Porteros)
    col5, col6 = st.columns(2)

    with col5:
        # --- GRÁFICO 5: DISCIPLINA DINÁMICA ---
        df_plot_cards = df if pais_seleccionado == "Todos" else df_filtrado
        
        # Radio Button para seleccionar la métrica
        opcion_card = st.radio(
            "Métrica de Disciplina:", 
            ["cards_yellow", "cards_red"], 
            format_func=lambda x: "Tarjetas Amarillas" if x == "cards_yellow" else "Tarjetas Rojas",
            horizontal=True, 
            key="radio_cards"
        )

        # Lógica de Título Dinámico para el Gráfico 5
        titulo_card_map = {"cards_yellow": "Tarjetas Amarillas", "cards_red": "Tarjetas Rojas"}
        st.info(f"Total de {titulo_card_map[opcion_card]} por Posición ({pais_seleccionado})")
        
        # 1. Agrupar por posición y sumar la métrica seleccionada
        df_cards_total = df_plot_cards.groupby('position')[opcion_card].sum().reset_index()
        df_cards_total = df_cards_total[df_cards_total[opcion_card] > 0] # Solo mostrar posiciones con al menos una tarjeta
        df_cards_total = df_cards_total.sort_values(by=opcion_card, ascending=False)
        
        # Definir color y título según la selección
        color_map = {"cards_yellow": "gold", "cards_red": "darkred"}
        
        if not df_cards_total.empty:
            fig5, ax5 = plt.subplots(figsize=(6, 4))
            # Gráfico de barras con color dinámico
            bars = sns.barplot(
                data=df_cards_total, 
                x='position', 
                y=opcion_card, 
                palette=[color_map[opcion_card]], # Usamos una paleta de un solo color
                ax=ax5
            )
            
            # 2. Ajustar el límite del eje Y para incluir el valor más alto con un margen
            max_cards = df_cards_total[opcion_card].max()
            ax5.set_ylim(0, max_cards * 1.1) 
            
            # 3. Añadir etiquetas de datos sobre cada barra
            for bar in bars.patches:
                height = bar.get_height()
                ax5.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height + (max_cards * 0.01), 
                    f'{int(height)}', 
                    ha='center',
                    va='bottom',
                    fontsize=10 
                )

            ax5.set_title(f"Disciplina: Total de {titulo_card_map[opcion_card]} por Posición")
            ax5.set_ylabel(f"Total de {titulo_card_map[opcion_card]}")
            ax5.set_xlabel("Posición")
            st.pyplot(fig5)
        else:
            st.warning(f"No hay datos de {titulo_card_map[opcion_card]} para esta selección.")


    with col6:
        st.info(f"Top Atajadas (Saves) por Portero ({pais_seleccionado})")
        # GRÁFICO 6: BARRAS (Atajadas)
        # Filtramos a jugadores que son porteros (GK) Y tienen atajadas
        df_porteros = df_filtrado[
            (df_filtrado['position'] == 'GK') &
            (df_filtrado['gk_saves'] > 0)
        ].sort_values('gk_saves', ascending=False).head(10) # Añadido .head(10) para mejor visualización

        if not df_porteros.empty:
            fig6, ax6 = plt.subplots(figsize=(6, 4))
            # Si es "Todos", mostramos también el país en la etiqueta para contexto
            if pais_seleccionado == "Todos":
                player_labels = df_porteros['player'] + " (" + df_porteros['team'] + ")"
                ax6.bar(player_labels, df_porteros['gk_saves'], color='goldenrod')
            else:
                ax6.bar(df_porteros['player'], df_porteros['gk_saves'], color='goldenrod')

            ax6.set_ylabel("Total de Atajadas")
            ax6.set_title("Rendimiento de Porteros (Top 10)")
            plt.xticks(rotation=45, ha='right')
            st.pyplot(fig6)
        else:
            st.warning("No hay porteros con atajadas en esta selección.")

# --- PESTAÑA 2: DATOS ---
with tab2:
    st.header("Explorador de Datos")
    st.dataframe(df_filtrado)
    st.sidebar.text("Trabajo realizado por: ")
    st.sidebar.text("- Daniel Avalos")
    st.sidebar.text("- Ricardo Perez")
