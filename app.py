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
    "Ofertes França": ["Brendan", "Olivier", "Damien", "Agustín", "JordiVila", "Adria", "StephaneJuanola", "RicardJoan", "IagoParga", "David", "Samuel"],
    "Ofertes Recycling": ["Brendan", "Olivier", "Damien", "Agustín", "JordiVila", "Adria", "StephaneJuanola", "RicardJoan", "IagoParga", "David", "Samuel"],
    "Ofertes Internacionals": ["Brendan", "Olivier", "Damien", "Agustín", "JordiVila", "Adria", "StephaneJuanola", "RicardJoan", "IagoParga", "David", "Samuel"]
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
        st.session_state.ofertes["Inici"] = pd.to_datetime(st.session_state.ofertes["Inici"], errors='coerce')
        st.session_state.ofertes["Final"] = pd.to_datetime(st.session_state.ofertes["Final"], errors='coerce')
    else:
        st.session_state.ofertes = pd.DataFrame(columns=["Projecte", "Departament", "Responsable", "Inici", "Final", "Documents"])
except Exception as e:
    st.error(f"⚠️ Error connectant a Google Sheets: {e}")
    st.stop()

# --- NOU: DETECCIÓ DINÀMICA DE FESTIUS DES DE L'EXCEL ---
festius_empresa = []
if not st.session_state.ofertes.empty:
    # Busquem totes les línies on el departament s'hagi guardat com a "Festiu Empresa"
    df_festius = st.session_state.ofertes[st.session_state.ofertes["Departament"] == "Festiu Empresa"]
    for _, fila in df_festius.iterrows():
        if pd.notnull(fila["Inici"]) and pd.notnull(fila["Final"]):
            dies = pd.date_range(start=fila["Inici"], end=fila["Final"]).date
            festius_empresa.extend(dies)
festius_np = list(set(festius_empresa)) # Convertim a llista única sense duplicats

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

# 3. MENÚ LATERAL (FORMULARIS)
st.sidebar.header("➕ Nova Oferta / Vacances")
st.sidebar.info("💡 Si el projecte es diu 'Vacances', es pintarà de color gris fosc automàticament.")

with st.sidebar.form("form_ofertes"):
    nom_projecte = st.text_input("Nom del Projecte (Ex: Vacances Agost)")
    departament = st.selectbox("Departament de l'oferta", list(equips.keys()))
    responsable = st.selectbox("Personal assignat", equips[departament])
    data_inici = st.date_input("Data d'inici")
    data_final = st.date_input("Data final")
    documents = st.text_area("Documents a preparar")
    
    if st.form_submit_button("Guardar Registre", type="primary"):
        nova_fila = [nom_projecte, departament, responsable, str(data_inici), str(data_final), documents]
        sheet.append_row(nova_fila)
        st.success("✅ Guardat correctament a l'Excel!")
        st.rerun()

st.sidebar.divider()
st.sidebar.header("🏢 Nou Festiu d'Empresa")
with st.sidebar.form("form_festius"):
    st.write("Afegeix un dia o període on l'empresa està tancada per a tothom.")
    nom_festiu = st.text_input("Motiu (Ex: Nadal, Pont Puríssima)")
    inici_festiu = st.date_input("Data d'inici del festiu")
    final_festiu = st.date_input("Data final del festiu")
    
    if st.form_submit_button("Guardar Festiu Empresa", type="primary"):
        # Es guarda a l'Excel amb una "etiqueta" especial perquè el programa sàpiga que és festiu
        nova_fila = [nom_festiu, "Festiu Empresa", "TOTS", str(inici_festiu), str(final_festiu), ""]
        sheet.append_row(nova_fila)
        st.success("✅ Festiu guardat correctament!")
        st.rerun()

# 4. NAVEGACIÓ DEL CALENDARI I CÀLCUL DE DIES
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

# Càlcul precís que ja descompta els caps de setmana i ELS FESTIUS LLEGITS DE L'EXCEL
dies_habils_mes = np.busday_count(inici_mes_dt, final_mes_dt + pd.Timedelta(days=1), holidays=festius_np)

st.markdown(f"<p style='text-align: center; color: gray;'>Aquest mes té <b>{dies_habils_mes} dies hàbils</b> de treball efectiu (descomptant caps de setmana i festius globals).</p>", unsafe_allow_html=True)
st.divider()

# 5. FILTRES
st.subheader("🔍 Filtra per departament")
departaments_seleccionats = st.multiselect(
    "Selecciona quins departaments vols analitzar:", 
    options=list(equips.keys()), 
    default=list(equips.keys())
)
# Filtrem només els departaments triats (ignorem els "Festiu Empresa" perquè no surtin a les ofertes del calendari com una feina més)
df_filtrat = st.session_state.ofertes[st.session_state.ofertes["Departament"].isin(departaments_seleccionats)]
st.divider()

# 6. BARRA D'OCUPACIÓ REAL (GLOBAL PER PERSONA I DESGLOSSADA PER DEPARTAMENT)
st.subheader(f"🔥 Ocupació Global del Personal ({nom_mes_actual} {st.session_state.any_vista})")

if departaments_seleccionats:
    # Obtenemos la lista única de todo el personal activo en los departamentos seleccionados
    personal_unic = sorted(list(set([persona for dept in departaments_seleccionats for persona in equips[dept]])))
    
    # Creamos columnas para mostrar a todo el personal en una sola rejilla limpia
    num_columnes = 4  # Ajusta según cuántos trabajadores quieras ver por fila
    columnes = st.columns(num_columnes)
    
    for idx, persona in enumerate(personal_unic):
        col = columnes[idx % num_columnes]
        
        # Filtramos todas las ofertas asignadas a esta persona en el mes seleccionado
        ofertes_persona = df_filtrat[df_filtrat["Responsable"] == persona]
        
        total_dies_mes = 0
        desglos_dept = {}
        
        for _, fila in ofertes_persona.iterrows():
            if pd.notnull(fila["Inici"]) and pd.notnull(fila["Final"]):
                inici_oferta = pd.to_datetime(fila["Inici"]).date()
                final_oferta = pd.to_datetime(fila["Final"]).date()
                
                inici_real = max(inici_oferta, inici_mes_dt)
                final_real = min(final_oferta, final_mes_dt)
                
                if inici_real <= final_real:
                    dies = np.busday_count(inici_real, final_real + pd.Timedelta(days=1), holidays=festius_np)
                    total_dies_mes += dies
                    
                    # Sumamos los días al departamento correspondiente
                    dept = fila["Departament"]
                    desglos_dept[dept] = desglos_dept.get(dept, 0) + dies
        
        percentatge_real = int((total_dies_mes / dies_habils_mes) * 100) if dies_habils_mes > 0 else 0
        percentatge_barra = min(percentatge_real, 100)
        
        with col:
            # Color de alerta si supera el 100% de carga
            indicador = "🔴" if percentatge_real > 100 else ("🟡" if percentatge_real >= 80 else "🟢")
            
            st.metric(
                label=f"{indicador} {persona}", 
                value=f"{percentatge_real}%", 
                delta=f"{total_dies_mes} de {dies_habils_mes} dies hàbils", 
                delta_color="off"
            )
            st.progress(percentatge_barra / 100.0)
            
            # Muestra el desglose por departamentos en texto pequeño debajo de la barra
            if desglos_dept:
                text_desglos = " | ".join([f"**{d.replace('Ofertes ', '')}:** {v}d" for d, v in desglos_dept.items()])
                st.caption(f"📌 {text_desglos}")
            else:
                st.caption("✨ Sense feina assignada")
            st.write("")
else:
    st.info("Selecciona com a mínim un departament per veure l'ocupació.")

# 7. CALENDARI VISUAL (GANTT I RECURSOS)
st.subheader(f"📅 Calendari d'Ofertes de {nom_mes_actual}")

if not df_filtrat.empty and not df_filtrat["Inici"].isnull().all():
    df_net = df_filtrat.dropna(subset=["Inici", "Final"]).copy()
    
    if not df_net.empty:
        estil_grafic = st.radio(
            "Tria l'estil de visualització:", 
            ["Vista per Personal (Estil Recursos)", "Vista per Projectes (Estil Gantt)"], 
            horizontal=True
        )
        
        df_net = df_net.sort_values(by=["Departament", "Responsable"], ascending=[False, False])
        
        # DETECCIÓ DE VACANCES PER FORÇAR EL COLOR A LES OFERTES PERSONALS
        df_net["Categoria_Color"] = df_net.apply(
            lambda row: "Vacances" if "vacances" in str(row["Projecte"]).lower() 
            else (row["Projecte"] if estil_grafic == "Vista per Personal (Estil Recursos)" else row["Responsable"]),
            axis=1
        )
        
        mapa_colors = {"Vacances": "dimgray"}
        
        if estil_grafic == "Vista per Personal (Estil Recursos)":
            fig = px.timeline(
                df_net, 
                x_start="Inici", 
                x_end="Final", 
                y="Responsable", 
                color="Categoria_Color", 
                color_discrete_map=mapa_colors,
                hover_data=["Projecte", "Departament", "Documents"],
                text="Projecte"
            )
            fig.update_traces(textposition='inside', insidetextanchor='middle')
        else:
            fig = px.timeline(
                df_net, 
                x_start="Inici", 
                x_end="Final", 
                y="Projecte", 
                color="Categoria_Color",
                color_discrete_map=mapa_colors, 
                hover_data=["Responsable", "Departament", "Documents"]
            )
        
        fig.update_traces(width=0.85)
        
        fig.update_layout(
            plot_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=1),
            yaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=1),
            height=max(400, len(df_net["Responsable"].unique()) * 40 + 150) if estil_grafic == "Vista per Personal (Estil Recursos)" else 500,
            showlegend=True,
            legend_title_text='Llegenda'
        )
        
        data_inici_text = f"{st.session_state.any_vista}-{st.session_state.mes_vista:02d}-01"
        data_final_text = f"{st.session_state.any_vista}-{st.session_state.mes_vista:02d}-{ultim_dia}"
        
        fig.update_xaxes(
            range=[data_inici_text, data_final_text],
            tickformat="%d %b", 
            dtick=86400000     
        )
        
        dies_del_mes = pd.date_range(start=data_inici_text, end=data_final_text)
        
        # OMBREJAT GRIS PELS CAPS DE SETMANA (Gris clar)
        caps_de_setmana = dies_del_mes[dies_del_mes.weekday.isin([5, 6])]
        for dia in caps_de_setmana:
            fig.add_vrect(
                x0=dia, x1=dia + pd.Timedelta(days=1), 
                fillcolor="lightgray", opacity=0.4, layer="below", line_width=0
            )
            
        # --- CORRECCIÓ: OMBREJAT PELS FESTIUS GLOBALS ---
        for festiu_dt in festius_np:
            if str(festiu_dt)[:7] == f"{st.session_state.any_vista}-{st.session_state.mes_vista:02d}":
                # Convertim explícitament al format Timestamp de Pandas perquè el gràfic no falli
                f_inici = pd.to_datetime(festiu_dt)
                f_final = f_inici + pd.Timedelta(days=1)
                
                fig.add_vrect(
                    x0=f_inici, x1=f_final, 
                    fillcolor="dimgray", opacity=0.6, layer="below", line_width=0,
                    annotation_text="FESTIU", annotation_position="top right"
                )
        
        dilluns_mes = dies_del_mes[dies_del_mes.weekday == 0]
        for dilluns in dilluns_mes:
            fig.add_vline(x=dilluns, line_width=2, line_color="black")
            
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Has de posar dates d'inici i final a les ofertes per veure-les al calendari.")
else:
    st.warning("No hi ha cap oferta que es pugui visualitzar. Afegeix-ne una al menú lateral.")

# 8. TAULA EDITABLE AMB SINCRONITZACIÓ A GOOGLE SHEETS
with st.expander("✏️ Base de dades completa (Clica per obrir i editar)"):
    st.write("Fes doble clic a qualsevol cel·la per modificar dates o personal. Pots gestionar els festius globals aquí també.")
    
    df_editat = st.data_editor(
        st.session_state.ofertes,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Inici": st.column_config.DateColumn("Data Inici", format="YYYY-MM-DD"),
            "Final": st.column_config.DateColumn("Data Final", format="YYYY-MM-DD"),
            # Afegim "Festiu Empresa" a la llista d'opcions perquè no doni error en editar un festiu
            "Departament": st.column_config.SelectboxColumn("Departament", options=list(equips.keys()) + ["Festiu Empresa"]),
        }
    )
    
    if st.button("💾 Desar canvis manuals a Google Sheets"):
        df_per_guardar = df_editat.copy()
        df_per_guardar['Inici'] = df_per_guardar['Inici'].dt.strftime('%Y-%m-%d')
        df_per_guardar['Final'] = df_per_guardar['Final'].dt.strftime('%Y-%m-%d')
        df_per_guardar.fillna("", inplace=True)
        
        sheet.clear()
        llista_dades = [df_per_guardar.columns.values.tolist()] + df_per_guardar.values.tolist()
        sheet.update(llista_dades)
        
        st.success("✅ Canvis guardats correctament a l'Excel!")
        st.rerun()
