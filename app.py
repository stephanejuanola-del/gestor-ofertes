import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import calendar
import json
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Gestor d'Ofertes", layout="wide")
st.title("📊 Planificador d'Ofertes i Ocupació")

# 1. DEFINICIÓ D'EQUIPS I DEPARTAMENTS
equips = {
    "Ofertes França": ["Brendan", "Olivier", "Damien", "Agustín", "JordiVila", "Adria"],
    "Ofertes Recycling": ["JordiVila", "RicardJoan", "Brendan", "Adria", "Samuel", "David"],
    "Ofertes Internacionals": ["JordiVila", "RicardJoan", "Brendan", "Adria", "Samuel", "David", "IagoParga"]
}

# 2. CONNEXIÓ A GOOGLE SHEETS
@st.cache_resource
def connect_google_sheets():
    creds_dict = json.loads(st.secrets["google_credentials"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open("Gestor_Ofertes").sheet1

try:
    sheet = connect_google_sheets()
    dades_excel = sheet.get_all_records()
    if dades_excel:
        st.session_state.ofertes = pd.DataFrame(dades_excel)
        # Convertir text a format data, ignorant errors si hi ha cel·les buides
        st.session_state.ofertes["Inici"] = pd.to_datetime(st.session_state.ofertes["Inici"], errors='coerce')
        st.session_state.ofertes["Final"] = pd.to_datetime(st.session_state.ofertes["Final"], errors='coerce')
    else:
        st.session_state.ofertes = pd.DataFrame(columns=["Projecte", "Departament", "Responsable", "Inici", "Final", "Documents"])
except Exception as e:
    st.error(f"⚠️ Error connectant a Google Sheets: {e}")
    st.stop()

# Funcions per moure's pel calendari
avui = datetime.today()
if "mes_vista" not in st.session_state:
    st.session_state.mes_vista = avui.month
if "any_vista" not in st.session_state:
    st.session_state.any_vista = avui.year

def canviar_mes(increment):
    nou_mes = st.session_state.mes_vista + increment
    nou_any = st.session_state.any_vista
    if nou_mes > 12:
        nou_mes = 1
        nou_any += 1
    elif nou_mes < 1:
        nou_mes = 12
        nou_any -= 1
    st.session_state.mes_vista = nou_mes
    st.session_state.any_vista = nou_any

# 3. MENÚ LATERAL (FORMULARI)
st.sidebar.header("➕ Nova Oferta")
nom_projecte = st.sidebar.text_input("Nom del Projecte/Oferta")
departament = st.sidebar.selectbox("Departament de l'oferta", list(equips.keys()))
responsable = st.sidebar.selectbox("Personal assignat", equips[departament])
data_inici = st.sidebar.date_input("Data d'inici")
data_final = st.sidebar.date_input("Data final")
documents = st.sidebar.text_area("Documents a preparar")

if st.sidebar.button("Guardar Oferta", type="primary"):
    nova_fila = [nom_projecte, departament, responsable, str(data_inici), str(data_final), documents]
    sheet.append_row(nova_fila) # S'envia directe a Google Sheets
    st.sidebar.success("✅ Oferta guardada a l'Excel!")
    st.rerun()

# 4. NAVEGACIÓ DEL CALENDARI
st.divider()
mesos_noms = ["Gener", "Febrer", "Març", "Abril", "Maig", "Juny", "Juliol", "Agost", "Setembre", "Octubre", "Novembre", "Desembre"]
nom_mes_actual = mesos_noms[st.session_state.mes_vista - 1]

col_esquerra, col_centre, col_dreta = st.columns([1, 2, 1])
with col_esquerra:
    st.button("⬅️ Mes Anterior", on_click=canviar_mes, args=(-1,), use_container_width=True)
with col_centre:
    st.markdown(f"<h3 style='text-align: center;'>🗓️ {nom_mes_actual} {st.session_state.any_vista}</h3>", unsafe_allow_html=True)
with col_dreta:
    st.button("Mes Següent ➡️", on_click=canviar_mes, args=(1,), use_container_width=True)

ultim_dia = calendar.monthrange(st.session_state.any_vista, st.session_state.mes_vista)[1]
inici_mes_dt = pd.to_datetime(f"{st.session_state.any_vista}-{st.session_state.mes_vista:02d}-01").date()
final_mes_dt = pd.to_datetime(f"{st.session_state.any_vista}-{st.session_state.mes_vista:02d}-{ultim_dia}").date()
dies_habils_mes = np.busday_count(inici_mes_dt, final_mes_dt + pd.Timedelta(days=1))

st.markdown(f"<p style='text-align: center; color: gray;'>Aquest mes té <b>{dies_habils_mes} dies hàbils</b> de treball.</p>", unsafe_allow_html=True)
st.divider()

# 5. FILTRES
st.subheader("🔍 Filtra per departament")
departaments_seleccionats = st.multiselect(
    "Selecciona quins departaments vols analitzar:", 
    options=list(equips.keys()), 
    default=list(equips.keys())
)
df_filtrat = st.session_state.ofertes[st.session_state.ofertes["Departament"].isin(departaments_seleccionats)]
st.divider()

# 6. BARRA D'OCUPACIÓ REAL
st.subheader(f"🔥 Ocupació del Personal ({nom_mes_actual} {st.session_state.any_vista})")

if departaments_seleccionats:
    for dept in departaments_seleccionats:
        st.markdown(f"#### 🏢 {dept}")
        personal_dept = equips[dept]
        columnes = st.columns(len(personal_dept))
        
        for i, persona in enumerate(personal_dept):
            ofertes_persona = df_filtrat[df_filtrat["Responsable"] == persona]
            
            total_dies_mes = 0
            for _, fila in ofertes_persona.iterrows():
                if pd.notnull(fila["Inici"]) and pd.notnull(fila["Final"]):
                    inici_oferta = pd.to_datetime(fila["Inici"]).date()
                    final_oferta = pd.to_datetime(fila["Final"]).date()
                    
                    inici_real = max(inici_oferta, inici_mes_dt)
                    final_real = min(final_oferta, final_mes_dt)
                    
                    if inici_real <= final_real:
                        dies = np.busday_count(inici_real, final_real + pd.Timedelta(days=1))
                        total_dies_mes += dies
                
            percentatge_real = int((total_dies_mes / dies_habils_mes) * 100) if dies_habils_mes > 0 else 0
            percentatge_barra = min(percentatge_real, 100)
            
            with columnes[i]:
                st.metric(
                    label=persona, 
                    value=f"{percentatge_real}%", 
                    delta=f"{total_dies_mes} de {dies_habils_mes} dies", 
                    delta_color="off"
                )
                st.progress(percentatge_barra / 100.0)
        st.write("") 
else:
    st.info("Selecciona com a mínim un departament per veure l'ocupació.")

st.divider()

# 7. CALENDARI VISUAL
st.subheader(f"📅 Calendari d'Ofertes de {nom_mes_actual}")

if not df_filtrat.empty and not df_filtrat["Inici"].isnull().all():
    df_net = df_filtrat.dropna(subset=["Inici", "Final"]).copy()
    
    if not df_net.empty:
        fig = px.timeline(
            df_net, 
            x_start="Inici", 
            x_end="Final", 
            y="Projecte", 
            color="Responsable", 
            hover_data=["Departament", "Documents"]
        )
        
        fig.update_traces(width=0.4)
        fig.update_layout(
            plot_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=1),
            yaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=1, autorange="reversed"),
            height=500,
            showlegend=True
        )
        
        data_inici_text = f"{st.session_state.any_vista}-{st.session_state.mes_vista:02d}-01"
        data_final_text = f"{st.session_state.any_vista}-{st.session_state.mes_vista:02d}-{ultim_dia}"
        
        fig.update_xaxes(
            range=[data_inici_text, data_final_text],
            tickformat="%d %b",
            dtick=86400000,
            rangebreaks=[dict(bounds=["sat", "mon"])]
        )
            
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Has de posar dates d'inici i final a les ofertes.")
else:
    st.warning("No hi ha cap oferta que es pugui visualitzar.")

# 8. TAULA EDITABLE AMB SINCRONITZACIÓ A GOOGLE SHEETS
with st.expander("✏️ Base de dades d'Ofertes completa"):
    st.write("Fes doble clic a qualsevol cel·la per modificar dates o personal. Quan acabis, prem el botó de sota per guardar els canvis a Google Sheets.")
    
    df_editat = st.data_editor(
        st.session_state.ofertes,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Inici": st.column_config.DateColumn("Data Inici", format="YYYY-MM-DD"),
            "Final": st.column_config.DateColumn("Data Final", format="YYYY-MM-DD"),
            "Departament": st.column_config.SelectboxColumn("Departament", options=list(equips.keys())),
        }
    )
    
    if st.button("💾 Desar canvis manuals a Google Sheets"):
        # Converteix les dates a text perquè Google Sheets les entengui
        df_per_guardar = df_editat.copy()
        df_per_guardar['Inici'] = df_per_guardar['Inici'].dt.strftime('%Y-%m-%d')
        df_per_guardar['Final'] = df_per_guardar['Final'].dt.strftime('%Y-%m-%d')
        df_per_guardar.fillna("", inplace=True) # Omple espais buits
        
        # Sobreescriu l'Excel amb les dades actualitzades
        sheet.clear()
        llista_dades = [df_per_guardar.columns.values.tolist()] + df_per_guardar.values.tolist()
        sheet.update(llista_dades)
        
        st.success("✅ Canvis guardats correctament a l'Excel!")
        st.rerun()
