import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Gestor d'Ofertes", layout="wide")
st.title("📊 Planificador d'Ofertes i Ocupació")

# 1. DEFINICIÓ D'EQUIPS I DEPARTAMENTS (Pots canviar els noms aquí)
equips = {
    "Ofertes França": ["Brendan", "Olivier", "Damien", "Agustín", "JordiVila", "Adria"],
    "Ofertes Recycling": ["JordiVila", "RicardJoan","Brendan", "Adria", "Samuel", "David" ],
    "Ofertes Internacionals": ["JordiVila", "RicardJoan","Brendan", "Adria", "Samuel", "David", "IagoParga"]
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
    # Busquem de quin departament és la persona seleccionada
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
    default=list(equips.keys()) # Per defecte es mostren tots
)

# Filtrem les dades segons els botons seleccionats
df_filtrat = st.session_state.ofertes[st.session_state.ofertes["Departament"].isin(departaments_seleccionats)]
personal_filtrat = [persona for dept in departaments_seleccionats for persona in equips[dept]]

st.divider()

# 5. BARRA D'OCUPACIÓ (Només del personal filtrat)
st.subheader("🔥 Ocupació del Personal")
if personal_filtrat:
    columnes = st.columns(len(personal_filtrat))
    # Simulació d'ocupació (es pot canviar per càlcul real més endavant)
    ocupacio_simulada = np.random.randint(40, 95, size=len(personal_filtrat)) 
    
    for i, persona in enumerate(personal_filtrat):
        with columnes[i]:
            st.metric(label=persona, value=f"{ocupacio_simulada[i]}%")
            st.progress(ocupacio_simulada[i] / 100.0)
else:
    st.info("Selecciona com a mínim un departament per veure l'ocupació.")

st.divider()

# 6. CALENDARI VISUAL (GANTT) DE DILLUNS A DIVENDRES
st.subheader("📅 Calendari d'Ofertes (Dilluns - Divendres)")

if not df_filtrat.empty:
    # Convertim les dates per assegurar-nos que Plotly les llegeix bé
    df_filtrat["Inici"] = pd.to_datetime(df_filtrat["Inici"])
    df_filtrat["Final"] = pd.to_datetime(df_filtrat["Final"])

    # Creem el gràfic de Gantt
    fig = px.timeline(
        df_filtrat, 
        x_start="Inici", 
        x_end="Final", 
        y="Projecte", 
        color="Responsable",
        hover_data=["Departament", "Documents"],
        title="Planificació de projectes"
    )
    
    # Ordenem perquè la primera oferta surti a dalt
    fig.update_yaxes(autorange="reversed")
    
    # AMAGUEM ELS CAPS DE SETMANA (Dissabte i Diumenge)
    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]) 
        ]
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrem la taula de dades a sota per si es volen veure els detalls
    with st.expander("Veure la taula de dades d'aquestes ofertes"):
        st.dataframe(df_filtrat, use_container_width=True)
else:
    st.warning("No hi ha cap oferta registrada en els departaments seleccionats. Afegeix-ne una al menú lateral.")
