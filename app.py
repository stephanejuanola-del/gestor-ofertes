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
    
    # Assegurem que les columnes de dates siguin tipus datetime per evitar errors a l'editor
    st.session_state.ofertes["Inici"] = pd.to_datetime(st.session_state.ofertes["Inici"])
    st.session_state.ofertes["Final"] = pd.to_datetime(st.session_state.ofertes["Final"])

# 3. MENÚ LATERAL (DINÀMIC)
st.sidebar.header("➕ Nova Oferta")
nom_projecte = st.sidebar.text_input("Nom del Projecte/Oferta")

departament = st.sidebar.selectbox("Departament de l'oferta", list(equips.keys()))
responsable = st.sidebar.selectbox("Personal assignat", equips[departament])

data_inici = st.sidebar.date_input("Data d'inici")
data_final = st.sidebar.date_input("Data final")
documents = st.sidebar.text_area("Documents a preparar")

if st.sidebar.button("Guardar Oferta", type="primary"):
    nova_fila = {
        "Projecte": nom_projecte, 
        "Departament": departament, 
        "Responsable": responsable, 
        "Inici": pd.to_datetime(data_inici), 
        "Final": pd.to_datetime(data_final), 
        "Documents": documents
    }
    st.session_state.ofertes = pd.concat([st.session_state.ofertes, pd.DataFrame([nova_fila])], ignore_index=True)
    st.sidebar.success("✅ Oferta afegida correctament!")
    st.rerun()

# 4. TAULA EDITABLE (NOU)
st.subheader("✏️ Base de dades d'Ofertes (Editable)")
st.write("Fes doble clic a qualsevol cel·la per modificar dates, textos o personal. Els canvis s'aplicaran a l'instant.")

st.session_state.ofertes = st.data_editor(
    st.session_state.ofertes,
    use_container_width=True,
    num_rows="dynamic", # Permet afegir o esborrar files manualment des de la taula
    column_config={
        "Inici": st.column_config.DateColumn("Data Inici", format="YYYY-MM-DD"),
        "Final": st.column_config.DateColumn("Data Final", format="YYYY-MM-DD"),
        "Departament": st.column_config.SelectboxColumn("Departament", options=list(equips.keys())),
    }
)

st.divider()

# 5. FILTRES PER DEPARTAMENT
st.subheader("🔍 Filtra per departament")
departaments_seleccionats = st.multiselect(
    "Selecciona quins departaments vols analitzar:", 
    options=list(equips.keys()), 
    default=list(equips.keys())
)

df_filtrat = st.session_state.ofertes[st.session_state.ofertes["Departament"].isin(departaments_seleccionats)]

st.divider()

# 6. BARRA D'OCUPACIÓ REAL
st.subheader("🔥 Ocupació del Personal (Basat en capacitat mensual de 21 dies)")

if departaments_seleccionats:
    capacitat_mensual = 21 
    for dept in departaments_seleccionats:
        st.markdown(f"#### 🏢 {dept}")
        personal_dept = equips[dept]
        columnes = st.columns(len(personal_dept))
        
        for i, persona in enumerate(personal_dept):
            ofertes_persona = st.session_state.ofertes[
                (st.session_state.ofertes["Responsable"] == persona) & 
                (st.session_state.ofertes["Departament"] == dept)
            ]
            
            total_dies_feina = 0
            for _, fila in ofertes_persona.iterrows():
                if pd.notnull(fila["Inici"]) and pd.notnull(fila["Final"]):
                    inici = pd.to_datetime(fila["Inici"]).date()
                    final = pd.to_datetime(fila["Final"]).date()
                    # Evitar errors si la data final és anterior a la inicial per error d'edició
                    if final >= inici: 
                        dies_oferta = np.busday_count(inici, final) + 1
                        total_dies_feina += dies_oferta
                
            percentatge_real = int((total_dies_feina / capacitat_mensual) * 100)
            percentatge_barra = min(percentatge_real, 100)
            
            with columnes[i]:
                st.metric(
                    label=persona, 
                    value=f"{percentatge_real}%", 
                    delta=f"{total_dies_feina} dies aquí", 
                    delta_color="off"
                )
                st.progress(percentatge_barra / 100.0)
        st.write("") 
else:
    st.info("Selecciona com a mínim un departament per veure l'ocupació.")

st.divider()

# 7. CALENDARI VISUAL (GANTT) AMB VISTES
st.subheader("📅 Calendari d'Ofertes")

vista = st.radio("Tipus de visualització del calendari:", ["Setmanal (Per dies)", "Mensual"], horizontal=True)

if not df_filtrat.empty and not df_filtrat["Inici"].isnull().all():
    # Eliminem files que puguin tenir dates buides (per si s'esborren a l'editor)
    df_net = df_filtrat.dropna(subset=["Inici", "Final"]).copy()
    
    if not df_net.empty:
        fig = px.timeline(
            df_net, 
            x_start="Inici", 
            x_end="Final", 
            y="Projecte", 
            color="Responsable", # Això pinta cada barra d'un color diferent segons l'usuari
            hover_data=["Departament", "Documents"],
            title="Planificació de projectes per dates"
        )
        
        fig.update_yaxes(autorange="reversed")
        
        # Opcions segons si es vol veure el detall setmanal o mensual
        if vista == "Setmanal (Per dies)":
            fig.update_xaxes(
                tickformat="%A<br>%d %b", # Mostra el nom del dia (Dilluns, etc) i la data
                dtick=86400000, # Força a mostrar un tick per cada dia (1 dia en milisegons)
                rangebreaks=[dict(bounds=["sat", "mon"])] # Amaga dissabte i diumenge
            )
        else:
            fig.update_xaxes(
                tickformat="%d %b %Y",
                dtick="M1", # Un tick per mes
                rangebreaks=[dict(bounds=["sat", "mon"])]
            )
            
        # Donem una mica més d'alçada al gràfic perquè no quedi aixafat
        fig.update_layout(height=500)
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Has de posar d'inici i final a les ofertes per veure-les al calendari.")
else:
    st.warning("No hi ha cap oferta registrada en els departaments seleccionats per mostrar al calendari.")
