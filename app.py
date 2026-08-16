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

# 2. INICIALITZACIÓ DE MEMÒRIA (Dades i Calendari)
if "ofertes" not in st.session_state:
    st.session_state.ofertes = pd.DataFrame(columns=["Projecte", "Departament", "Responsable", "Inici", "Final", "Documents"])
    st.session_state.ofertes["Inici"] = pd.to_datetime(st.session_state.ofertes["Inici"])
    st.session_state.ofertes["Final"] = pd.to_datetime(st.session_state.ofertes["Final"])

avui = datetime.today()
if "mes_vista" not in st.session_state:
    st.session_state.mes_vista = avui.month
if "any_vista" not in st.session_state:
    st.session_state.any_vista = avui.year

# Funcions per moure's pel calendari
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

# Càlcul de dies de treball per al mes seleccionat
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

# 6. BARRA D'OCUPACIÓ REAL (LLIGADA AL MES SELECCIONAT)
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
                    
                    # Intersequem les dates de l'oferta amb les dates del mes triat
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

# 7. CALENDARI VISUAL EN FORMA DE QUADRÍCULA (NOMÉS MOSTRA EL MES ACTUAL)
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
        
        # Opcions de vista de calendari: Fixem l'eix X exclusivament al mes triat
        data_inici_text = f"{st.session_state.any_vista}-{st.session_state.mes_vista:02d}-01"
        data_final_text = f"{st.session_state.any_vista}-{st.session_state.mes_vista:02d}-{ultim_dia}"
        
        fig.update_xaxes(
            range=[data_inici_text, data_final_text],
            tickformat="%d %b", # Mostra el dia i el mes a cada columna
            dtick=86400000,     # Força que hi hagi una ratlla per cada dia
            rangebreaks=[dict(bounds=["sat", "mon"])] # Amaga els caps de setmana
        )
            
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Has de posar dates d'inici i final a les ofertes per veure-les al calendari.")
else:
    st.warning(f"No hi ha cap oferta que es pugui visualitzar. Afegeix-ne una al menú lateral.")

# 8. TAULA EDITABLE
with st.expander("✏️ Base de dades d'Ofertes completa (Clica per obrir i editar)"):
    st.write("Fes doble clic a qualsevol cel·la per modificar dates o personal. Els canvis es guarden al moment.")
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
