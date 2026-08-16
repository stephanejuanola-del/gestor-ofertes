import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import calendar

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
    st.session_state.ofertes["Inici"] = pd.to_datetime(st.session_state.ofertes["Inici"])
    st.session_state.ofertes["Final"] = pd.to_datetime(st.session_state.ofertes["Final"])

# 3. MENÚ LATERAL (FORMULARI)
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

# --- NOU: SELECCIÓ DE MES PER A L'ANÀLISI ---
st.subheader("🗓️ Selecciona el mes a analitzar")
col_mes, col_any, col_buit = st.columns([1, 1, 2])
mesos_noms = ["Gener", "Febrer", "Març", "Abril", "Maig", "Juny", "Juliol", "Agost", "Setembre", "Octubre", "Novembre", "Desembre"]
avui = datetime.today()

amb_mes = col_mes.selectbox("Mes", mesos_noms, index=avui.month - 1)
amb_any = col_any.number_input("Any", min_value=2024, max_value=2030, value=avui.year)

mes_num = mesos_noms.index(amb_mes) + 1
ultim_dia = calendar.monthrange(amb_any, mes_num)[1]

# Calculem exactament quants dies laborables (dilluns-divendres) té aquest mes
inici_mes_dt = pd.to_datetime(f"{amb_any}-{mes_num:02d}-01").date()
final_mes_dt = pd.to_datetime(f"{amb_any}-{mes_num:02d}-{ultim_dia}").date()
dies_habils_mes = np.busday_count(inici_mes_dt, final_mes_dt + pd.Timedelta(days=1))

st.info(f"💡 El mes de **{amb_mes} de {amb_any}** té un total de **{dies_habils_mes} dies hàbils** de treball (sense comptar caps de setmana).")
st.divider()

# 4. TAULA EDITABLE
with st.expander("✏️ Base de dades d'Ofertes (Clica per obrir i editar)"):
    st.write("Fes doble clic a qualsevol cel·la per modificar dates o personal.")
    st.session_state.ofertes = st.data_editor(
        st.session_state.ofertes,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Inici": st.column_config.DateColumn("Data Inici", format="YYYY-MM-DD"),
            "Final": st.column_config.DateColumn("Data Final", format="YYYY-MM-DD"),
            "Departament": st.column_config.SelectboxColumn("Departament", options=list(equips.keys())),
        }
    )

# 5. FILTRES
st.subheader("🔍 Filtra per departament")
departaments_seleccionats = st.multiselect(
    "Selecciona quins departaments vols analitzar:", 
    options=list(equips.keys()), 
    default=list(equips.keys())
)

df_filtrat = st.session_state.ofertes[st.session_state.ofertes["Departament"].isin(departaments_seleccionats)]
st.divider()

# 6. BARRA D'OCUPACIÓ REAL (SEGONS EL MES SELECCIONAT)
st.subheader(f"🔥 Ocupació del Personal ({amb_mes} {amb_any})")

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
                    
                    # Intersequem les dates de l'oferta amb les dates del mes triat
                    inici_real = max(inici_oferta, inici_mes_dt)
                    final_real = min(final_oferta, final_mes_dt)
                    
                    # Només sumem si l'oferta cau dins d'aquest mes
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

# 7. CALENDARI VISUAL (GANTT) - QUADRÍCULA I BARRES FINES
st.subheader("📅 Calendari d'Ofertes")

vista = st.radio("Tipus de visualització del calendari:", ["Vista Mensual (Mes sencer)", "Vista Setmanal (Detall de dies)"], horizontal=True)

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
        
        # Fem les barres més estretes
        fig.update_traces(width=0.4)
        
        # Creem la quadrícula d'estil calendari/Project
        fig.update_layout(
            plot_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=1),
            yaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=1, autorange="reversed"),
            height=500,
            showlegend=True
        )
        
        # Opcions de vista de calendari
        if vista == "Vista Mensual (Mes sencer)":
            # Forcem que es vegi exactament des del dia 1 fins a l'últim del mes seleccionat
            fig.update_xaxes(
                range=[f"{amb_any}-{mes_num:02d}-01", f"{amb_any}-{mes_num:02d}-{ultim_dia}"],
                tickformat="%d %b",
                dtick=86400000, # Tick cada dia perquè es vegi la quadrícula diària
                rangebreaks=[dict(bounds=["sat", "mon"])] # Amaga el cap de setmana
            )
        else:
            # Vista setmanal més lliure, però mostrant el nom del dia (Dilluns, Dimarts...)
            fig.update_xaxes(
                tickformat="%A<br>%d %b",
                dtick=86400000,
                rangebreaks=[dict(bounds=["sat", "mon"])]
            )
            
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Has de posar dates d'inici i final a les ofertes per veure-les al calendari.")
else:
    st.warning("No hi ha cap oferta registrada en els departaments seleccionats per mostrar al calendari.")
