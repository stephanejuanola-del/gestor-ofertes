import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Gestor d'Ofertes", layout="wide")
st.title("📊 Planificador d'Ofertes i Ocupació")

# 1. DEFINICIÓ D'EQUIPS I DEPARTAMENTS
equips = {
    "Ofertes França": ["Brendan", "Olivier", "Damien", "Agustín", "JordiVila", "Adria"],
    "Ofertes Recycling": ["JordiVila", "RicardJoan", "Brendan", "Adria", "Samuel", "David"],
    "Ofertes Internacionals": ["JordiVila", "RicardJoan", "Brendan", "Adria", "Samuel", "David", "IagoParga"]
}

# 2. BASE DE DADES TEMPORAL
if "ofertes" not in st.session_state:
    st.session_state.ofertes = pd.DataFrame(columns=["Projecte", "Departament", "Responsable", "Inici", "Final", "Documents"])

# 3. MENÚ LATERAL (DINÀMIC)
st.sidebar.header("➕ Nova Oferta")
nom_projecte = st.sidebar.text_input("Nom del Projecte/Oferta")

# En triar el departament, el menú de sota s'actualitza sol
departament = st.sidebar.selectbox("Departament de l'oferta", list(equips.keys()))
responsable = st.sidebar.selectbox("Personal assignat", equips[departament])

data_inici = st.sidebar.date_input("Data d'inici")
data_final = st.sidebar.date_input("Data final")
documents = st.sidebar.text_area("Documents a preparar")

# Botó per guardar
if st.sidebar.button("Guardar Oferta", type="primary"):
    nova_fila = {
        "Projecte": nom_projecte, 
        "Departament": departament, 
        "Responsable": responsable, 
        "Inici": data_inici, 
        "Final": data_final, 
        "Documents": documents
    }
    st.session_state.ofertes = pd.concat([st.session_state.ofertes, pd.DataFrame([nova_fila])], ignore_index=True)
    st.sidebar.success("✅ Oferta afegida correctament!")
    st.rerun() # Refresquem la pantalla ràpidament

# 4. FILTRES PER DEPARTAMENT
st.subheader("🔍 Filtra per departament")
departaments_seleccionats = st.multiselect(
    "Selecciona quins departaments vols visualitzar:", 
    options=list(equips.keys()), 
    default=list(equips.keys())
)

df_filtrat = st.session_state.ofertes[st.session_state.ofertes["Departament"].isin(departaments_seleccionats)]

st.divider()

# 5. BARRA D'OCUPACIÓ REAL (AGRUPADA PER DEPARTAMENTS)
st.subheader("🔥 Ocupació del Personal (Basat en capacitat mensual de 21 dies)")

if departaments_seleccionats:
    capacitat_mensual = 21 
    
    for dept in departaments_seleccionats:
        st.markdown(f"#### 🏢 {dept}")
        personal_dept = equips[dept]
        columnes = st.columns(len(personal_dept))
        
        for i, persona in enumerate(personal_dept):
            # Calculem només les ofertes D'AQUEST departament per a aquesta persona
            ofertes_persona = st.session_state.ofertes[
                (st.session_state.ofertes["Responsable"] == persona) & 
                (st.session_state.ofertes["Departament"] == dept)
            ]
            
            total_dies_feina = 0
            for _, fila in ofertes_persona.iterrows():
                inici = pd.to_datetime(fila["Inici"]).date()
                final = pd.to_datetime(fila["Final"]).date()
                
                dies_oferta = np.busday_count(inici, final) + 1
                total_dies_feina += dies_oferta
                
            percentatge_real = int((total_dies_feina / capacitat_mensual) * 100)
            percentatge_barra = min(percentatge_real, 100)
            
            with columnes[i]:
                # Mostrem clarament que els dies calculats pertanyen a aquest departament
                st.metric(
                    label=persona, 
                    value=f"{percentatge_real}%", 
                    delta=f"{total_dies_feina} dies aquí", 
                    delta_color="off"
                )
                st.progress(percentatge_barra / 100.0)
        
        st.write("") # Espai en blanc per separar departaments
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
        title="Planificació de projectes per dates"
    )
    
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("Veure la taula de dades d'aquestes ofertes"):
        st.dataframe(df_filtrat, use_container_width=True)
else:
    st.warning("No hi ha cap oferta registrada en els departaments seleccionats. Afegeix-ne una al menú lateral.")
