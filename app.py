import streamlit as st
import pandas as pd
import numpy as np
import datetime

st.set_page_config(page_title="Gestor d'Ofertes", layout="wide")

st.title("📊 Planificador d'Ofertes i Ocupació")

# Llista de personal (es pot connectar a una base de dades)
personal = ["Brendan Kerdaffreck", "Jordi Vila", "Olivier Ma", "Damien Pacaud", "Agustin Pomponio"]

# Formulari per entrar noves ofertes
with st.sidebar.form("nova_oferta"):
    st.header("➕ Nova Oferta")
    nom_projecte = st.text_input("Nom del Projecte/Oferta")
    responsable = st.selectbox("Personal assignat", personal)
    data_inici = st.date_input("Data d'inici")
    data_final = st.date_input("Data final")
    documents = st.text_area("Documents a preparar")
    guardar = st.form_submit_button("Guardar Oferta")

# Simulació de dades guardades
if "ofertes" not in st.session_state:
    st.session_state.ofertes = pd.DataFrame(columns=["Projecte", "Responsable", "Inici", "Final", "Documents"])

if guardar:
    nova_fila = {"Projecte": nom_projecte, "Responsable": responsable, "Inici": data_inici, "Final": data_final, "Documents": documents}
    st.session_state.ofertes = pd.concat([st.session_state.ofertes, pd.DataFrame([nova_fila])], ignore_index=True)

# 1. BARRA D'OCUPACIÓ GENERAL
st.subheader("🔥 Ocupació del Personal (Aquest mes)")
# Càlcul simulat d'ocupació (es pot ajustar segons els dies feiners de les ofertes)
ocupacio_simulada = np.random.randint(40, 95, size=len(personal)) 

columnes = st.columns(len(personal))

for i, persona in enumerate(personal):
    with columnes[i]:
        st.metric(label=persona, value=f"{ocupacio_simulada[i]}%")
        st.progress(ocupacio_simulada[i] / 100.0)

st.divider()

# 2. VISTA DE DADES I CALENDARI
st.subheader("📅 Calendari de Projectes Actius")
if not st.session_state.ofertes.empty:
    st.dataframe(st.session_state.ofertes, use_container_width=True)
    st.info("💡 Aquí s'integraria un gràfic de Gantt interactiu filtrant només de dilluns a divendres.")
else:
    st.warning("No hi ha cap oferta registrada. Afegeix-ne una al menú lateral.")
