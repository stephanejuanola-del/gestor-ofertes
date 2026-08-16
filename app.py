import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Gestor d'Ofertes", layout="wide")
st.title("📊 Planificador d'Ofertes i Ocupació")

# 1. DEFINICIÓ D'EQUIPS I DEPARTAMENTS
equips = {
    "Ofertes França": ["Anna", "Marc"],
    "Ofertes Recycling": ["Laura", "Jordi"],
    "Ofertes Internacionals": ["Joan", "Carla", "Sara"]
}

# Creem una llista amb tots els noms per al formulari
personal_total = [persona for sublista in equips.values() for persona in sublista]

# 2. BASE DE DADES TEMPORAL
if "ofertes" not in st.session_state:
    st.session_state.ofertes = pd.DataFrame(columns=["Projecte", "Departament", "Responsable", "Inici", "Final", "Documents"])

# 3. FORMULARI LATERAL
with st.sidebar.form("nova_oferta"):
    st.header("➕ Nova Oferta")
    nom_projecte = st.text_input("Nom del Projecte/Oferta")
    responsable = st.selectbox("Personal assignat", personal_total)
    data_inici = st.date_input("Data d'inici")
    data_final = st.date_input("Data final")
    documents = st.text_area("Documents a preparar")
    guardar = st.form_submit_button("Guardar Oferta")

if guardar:
    dept_assignat = next(dept for dept, pers in equips.items() if responsable in pers)
    nova_fila = {
        "Projecte": nom_projecte, 
        "Departament": dept_assignat, 
        "Responsable": responsable, 
        "Inici": data_inici, 
        "Final": data_final, 
        "Documents": documents
    }
    st.session_state.ofertes = pd.concat([st.session_state.ofertes, pd.DataFrame([nova_fila])], ignore_index=True)
    st.success("Oferta afegida!")

# 4. FILTRES PER DEPARTAMENT
st.subheader("🔍 Filtra per departament")
departaments_seleccionats = st.multiselect(
    "Selecciona quins departaments vols visualitzar:", 
    options=list(equips.keys()), 
    default=list(equips.keys())
)

# Filtrem les dades segons els botons seleccionats
df_filtrat = st.session_state.ofertes[st.session_state.ofertes["Departament"].isin(departaments_seleccionats)]
personal_filtrat = [persona for dept in departaments_seleccionats for persona in equips[dept]]

st.divider()

# 5. BARRA D'OCUPACIÓ REAL
st.subheader("🔥 Ocupació del Personal (Basat en capacitat mensual)")
if personal_filtrat:
    columnes = st.columns(len(personal_filtrat))
    capacitat_mensual = 21 
    
    for i, persona in enumerate(personal_filtrat):
        ofertes_persona = df_filtrat[df_filtrat["Responsable"] == persona]
        
        total_dies_feina = 0
        for _, fila in ofertes_persona.iterrows():
            inici = pd.to_datetime(fila["Inici"]).date()
            final = pd.to_datetime(fila["Final"]).date()
            
            dies_oferta = np.busday_count(inici, final) + 1
            total_dies_feina += dies_oferta
            
        percentatge_real = int((total_dies_feina / capacitat_mensual) * 100)
        percentatge_barra = min(percentatge_real, 100)
        
        with columnes[i]:
            st.metric(
                label=persona, 
                value=f"{percentatge_real}%", 
                delta=f"{total_dies_feina} dies ocupats", 
                delta_color="off"
            )
            st.progress(percentatge_barra / 100.0)
else:
    st.info("Selecciona com a mínim un departament per veure l'ocupació.")

st.divider()

# 6. CALENDARI VISUAL (GANTT)
st.subheader("📅 Calendari d'Ofertes (Dilluns - Divendres)")

if not df_filtrat.empty:
    df_filtrat["Inici"] = pd.to_datetime(df_filtrat["Inici"])
    df_filtrat["Final"] = pd.to_datetime(df_filtrat["Final"])

    fig = px.timeline(
        df_filtrat, 
        x_start="Inici", 
        x_end="Final", 
        y="Projecte", 
        color="Responsable",
        hover_data=["Departament", "Documents"],
        title="Planificació de projectes"
    )
    
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("Veure la taula de dades d'aquestes ofertes"):
        st.dataframe(df_filtrat, use_container_width=True)
else:
    st.warning("No hi ha cap oferta registrada en els departaments seleccionats. Afegeix-ne una al menú lateral.")
