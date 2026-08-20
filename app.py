import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import calendar
import json
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

st.set_page_config(page_title="Gestor d'Ofertes", layout="wide")
st.title("📊 Planificador d'Ofertes i Ocupació")

# --- CONFIGURACIÓ DE GOOGLE CALENDAR ---
# Reemplaça aquest valor pel teu ID de Google Calendar (ex: "el_teu_correu@gmail.com" o un ID llarg)
CALENDAR_ID = "https://calendar.google.com/calendar/embed?src=sjuanola%40bianna.com&ctz=Europe%2FMadrid"

# 1. DEFINICIÓ D'EQUIPS I DEPARTAMENTS
equips = {
    "Ofertes França": ["Brendan", "Olivier", "Damien", "Agustín", "JordiVila", "Adria", "StephaneJ", "RicardJoan", "IagoParga", "David", "Samuel", "Nacho Smith"],
    "Ofertes Recycling": ["Brendan", "Olivier", "Damien", "Agustín", "JordiVila", "Adria", "StephaneJ", "RicardJoan", "IagoParga", "David", "Samuel", "Nacho Smith"],
    "Ofertes Internacionals": ["Brendan", "Olivier", "Damien", "Agustín", "JordiVila", "Adria", "StephaneJ", "RicardJoan", "IagoParga", "David", "Samuel", "Nacho Smith"],
    "Ofertes Brasil": ["Brendan", "Olivier", "Damien", "Agustín", "JordiVila", "Adria", "StephaneJ", "RicardJoan", "IagoParga", "David", "Samuel", "Nacho Smith"],
    "Ofertes Mèxic": ["Brendan", "Olivier", "Damien", "Agustín", "JordiVila", "Adria", "StephaneJ", "RicardJoan", "IagoParga", "David", "Samuel", "Nacho Smith"],
    "Ofertes Portugal": ["Brendan", "Olivier", "Damien", "Agustín", "JordiVila", "Adria", "StephaneJ", "RicardJoan", "IagoParga", "David", "Samuel", "Nacho Smith"]
}
# 2. CONNEXIÓ A GOOGLE SHEETS I GOOGLE CALENDAR
@st.cache_resource
def connect_google_services():
    creds_dict = json.loads(st.secrets["google_credentials"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/calendar"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    
    # Client Sheets
    client_sheets = gspread.authorize(creds)
    sheet = client_sheets.open("Gestor_Ofertes").sheet1
    
    # Client Calendar
    calendar_service = build('calendar', 'v3', credentials=creds)
    
    return sheet, calendar_service

try:
    sheet, calendar_service = connect_google_services()
    dades_excel = sheet.get_all_records()
    if dades_excel:
        st.session_state.ofertes = pd.DataFrame(dades_excel)
        st.session_state.ofertes["Inici"] = pd.to_datetime(st.session_state.ofertes["Inici"], errors='coerce')
        st.session_state.ofertes["Final"] = pd.to_datetime(st.session_state.ofertes["Final"], errors='coerce')
    else:
        st.session_state.ofertes = pd.DataFrame(columns=["Projecte", "Departament", "Responsable", "Inici", "Final", "Documents"])
except Exception as e:
    st.error(f"⚠️ Error connectant als serveis de Google: {e}")
    st.stop()

# Funció per crear esdeveniment a Google Calendar
def crear_esdeveniment_calendar(titol, responsable, data_inici, data_final, descripcio=""):
    try:
        summary_text = f"{titol.upper()} - {responsable}"
        event = {
            'summary': summary_text,
            'description': descripcio,
            'start': {'date': str(data_inici)},
            'end': {'date': str(data_final)},
        }
        calendar_service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return True
    except Exception as err:
        st.error(f"⚠️ Error en afegir a Google Calendar: {err}")
        return False

# DETECCIÓ DINÀMICA DE FESTIUS DES DE L'EXCEL
festius_empresa = []
if not st.session_state.ofertes.empty:
    df_festius = st.session_state.ofertes[st.session_state.ofertes["Departament"] == "Festiu Empresa"]
    for _, fila in df_festius.iterrows():
        if pd.notnull(fila["Inici"]) and pd.notnull(fila["Final"]):
            dies = pd.date_range(start=fila["Inici"], end=fila["Final"]).date
            festius_empresa.extend(dies)
festius_np = list(set(festius_empresa))

# Navegació del calendari
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
st.sidebar.info("💡 Les noves entrades es sincronitzaran automàticament amb Google Calendar.")

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
        
        # Sincronització automàtica amb Google Calendar
        crear_esdeveniment_calendar(nom_projecte, responsable, data_inici, data_final, documents)
        
        st.success("✅ Guardat a l'Excel i creat a Google Calendar!")
        st.rerun()

st.sidebar.divider()
st.sidebar.header("🏢 Nou Festiu d'Empresa")
with st.sidebar.form("form_festius"):
    st.write("Afegeix un dia o període on l'empresa està tancada per a tothom.")
    nom_festiu = st.text_input("Motiu (Ex: Nadal, Pont Puríssima)")
    inici_festiu = st.date_input("Data d'inici del festiu")
    final_festiu = st.date_input("Data final del festiu")
    
    if st.form_submit_button("Guardar Festiu Empresa", type="primary"):
        nova_fila = [nom_festiu, "Festiu Empresa", "TOTS", str(inici_festiu), str(final_festiu), ""]
        sheet.append_row(nova_fila)
        
        crear_esdeveniment_calendar(f"FESTIU: {nom_festiu}", "TOTS", inici_festiu, final_festiu)
        
        st.success("✅ Festiu guardat i afegit a Google Calendar!")
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

dies_habils_mes = np.busday_count(inici_mes_dt, final_mes_dt + pd.Timedelta(days=1), holidays=festius_np)

st.markdown(f"<p style='text-align: center; color: gray;'>Aquest mes té <b>{dies_habils_mes} dies hàbils</b> de treball efectiu (descomptant caps de setmana i festius globals).</p>", unsafe_allow_html=True)
st.divider()

# 5. FILTRES
st.subheader("🔍 Filtres de cerca")

col_dept, col_pers = st.columns(2)

with col_dept:
    departaments_seleccionats = st.multiselect(
        "Filtra per departament:", 
        options=list(equips.keys()), 
        default=list(equips.keys())
    )

tots_els_treballadors = sorted(list(set([persona for llista in equips.values() for persona in llista])))

with col_pers:
    persona_seleccionada = st.multiselect(
        "Filtra per persona (opcional):", 
        options=tots_els_treballadors,
        default=[],
        placeholder="Tot el personal"
    )

# 1. Agafem primer les dades dels departaments seleccionats
df_dept = st.session_state.ofertes[
    st.session_state.ofertes["Departament"].isin(departaments_seleccionats)
]

# 2. Identifiquem NOMÉS el personal que té projectes de feina reals (excloent "Vacances")
personal_amb_projectes = df_dept[
    ~df_dept["Projecte"].astype(str).str.lower().str.contains("vacances")
]["Responsable"].unique()

# 3. Filtrem: NOMÉS es mostren les persones amb projecte real en aquest departament (amb la seva feina + les seves vacances)
df_filtrat = st.session_state.ofertes[
    (st.session_state.ofertes["Responsable"].isin(personal_amb_projectes)) &
    (
        (st.session_state.ofertes["Departament"].isin(departaments_seleccionats)) | 
        (st.session_state.ofertes["Projecte"].astype(str).str.lower().str.contains("vacances"))
    )
]

# 4. Si s'utilitza el filtre opcional per persona, apliquem aquesta restricció extra
if persona_seleccionada:
    df_filtrat = df_filtrat[df_filtrat["Responsable"].isin(persona_seleccionada)]

st.divider()
# 6. MÈTRIQUES D'OCUPACIÓ I CAPACITAT
st.subheader(f"📊 Ocupació de l'Equip a {nom_mes_actual}")

data_inici_mes = pd.to_datetime(f"{st.session_state.any_vista}-{st.session_state.mes_vista:02d}-01")
data_final_mes = pd.to_datetime(f"{st.session_state.any_vista}-{st.session_state.mes_vista:02d}-{ultim_dia}")
tot_dies = pd.date_range(start=data_inici_mes, end=data_final_mes)
dies_feiners = [d for d in tot_dies if d.weekday() < 5 and d.strftime('%Y-%m-%d') not in festius_np]
dies_laborables_mes = len(dies_feiners)

if dies_laborables_mes > 0 and not df_filtrat.empty:
    col_graf, col_mètrica = st.columns([3, 1])
    
    personal_filtrat = df_filtrat["Responsable"].unique()
    
    with col_graf:
        ocupacio_persones = []
        for persona in personal_filtrat:
            df_p = df_filtrat[(df_filtrat["Responsable"] == persona) & (~df_filtrat["Projecte"].astype(str).str.lower().str.contains("vacances"))]
            
            dies_ocupats_set = set()
            desglossament_dept = {}
            
            for _, row in df_p.iterrows():
                if pd.notnull(row["Inici"]) and pd.notnull(row["Final"]):
                    ranga = pd.date_range(start=pd.to_datetime(row["Inici"]), end=pd.to_datetime(row["Final"]))
                    dept_row = row["Departament"]
                    
                    if dept_row not in desglossament_dept:
                        desglossament_dept[dept_row] = set()
                        
                    for dia in ranga:
                        if dia in dies_feiners:
                            dies_ocupats_set.add(dia)
                            desglossament_dept[dept_row].add(dia)
            
            dies_of = len(dies_ocupats_set)
            pct = min(100, int((dies_of / dies_laborables_mes) * 100))
            
            # NOMÉS AFEGIM A LA GRÀFICA I TAULA SI TÉ OCUPACIÓ REAL (> 0%)
            if dies_of > 0:
                detall_text = ", ".join([f"{dept}: {len(d_set)}d" for dept, d_set in desglossament_dept.items() if len(d_set) > 0])
                if not detall_text:
                    detall_text = "0 dies"
                    
                ocupacio_persones.append({
                    "Personal": persona, 
                    "Ocupació (%)": pct, 
                    "Dies Ocupats": dies_of,
                    "Desglossament": detall_text
                })
        
        df_ocupacio = pd.DataFrame(ocupacio_persones)
        
        if not df_ocupacio.empty:
            fig_bar = px.bar(
                df_ocupacio, 
                x="Ocupació (%)", 
                y="Personal", 
                orientation='h',
                text="Ocupació (%)",
                color="Ocupació (%)",
                color_continuous_scale="RdYlGn_r",
                range_x=[0, 100],
                hover_data=["Dies Ocupats", "Desglossament"]
            )
            fig_bar.update_traces(texttemplate='%{text}%', textposition='outside')
            fig_bar.update_layout(height=max(250, len(df_ocupacio) * 45), plot_bgcolor='white')
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Taula de detall a sota
            st.dataframe(df_ocupacio[["Personal", "Ocupació (%)", "Dies Ocupats", "Desglossament"]], use_container_width=True, hide_index=True)
        else:
            st.info("No hi ha cap persona amb activitat o projectes assignats en aquest filtre.")

    with col_mètrica:
        st.metric("Capacitat teòrica/persona", f"{dies_laborables_mes} dies")
        st.caption(f"Dies totals mes: {len(tot_dies)}d | Festius/Fins de setmana: {len(tot_dies) - dies_laborables_mes}d")
else:
    st.info("Trieu un departament amb activitat per veure l'ocupació.")
# 7. CALENDARI VISUAL (GANTT I RECURSOS)
st.subheader(f"📅 Calendari d'Ofertes de {nom_mes_actual}")

if not df_filtrat.empty and not df_filtrat["Inici"].isnull().all():
    df_net = df_filtrat.dropna(subset=["Inici", "Final"]).copy()
    
    if not df_net.empty:
        df_net["Projecte"] = df_net["Projecte"].astype(str).str.strip()
        df_net["Responsable"] = df_net["Responsable"].astype(str).str.strip()

        df_net["Final_Grafic"] = pd.to_datetime(df_net["Final"])
        df_net["Inici_Grafic"] = pd.to_datetime(df_net["Inici"])
        
        mask_mismo_dia = df_net["Inici_Grafic"] == df_net["Final_Grafic"]
        df_net.loc[mask_mismo_dia, "Final_Grafic"] = df_net.loc[mask_mismo_dia, "Final_Grafic"] + pd.Timedelta(days=1)

        estil_grafic = st.radio(
            "Tria l'estil de visualització:", 
            ["Vista per Personal (Estil Recursos)", "Vista per Projectes (Estil Gantt)"], 
            horizontal=True
        )
        
        df_net = df_net.sort_values(by=["Departament", "Responsable"], ascending=[False, False])
        
        df_net["Categoria_Color"] = df_net.apply(
            lambda row: "Vacances" if "vacances" in str(row["Projecte"]).lower() 
            else (row["Projecte"] if estil_grafic == "Vista per Personal (Estil Recursos)" else row["Responsable"]),
            axis=1
        )
        
        mapa_colors = {"Vacances": "dimgray"}
        
        if estil_grafic == "Vista per Personal (Estil Recursos)":
            fig = px.timeline(
                df_net, 
                x_start="Inici_Grafic", 
                x_end="Final_Grafic", 
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
                x_start="Inici_Grafic", 
                x_end="Final_Grafic", 
                y="Projecte", 
                color="Categoria_Color",
                color_discrete_map=mapa_colors, 
                hover_data=["Responsable", "Departament", "Documents"]
            )
        
        # BARRES TRANSLÚCIDES AMB VORA PER MARCAR ELS DELIMITADORS DE SOLAPAMENT
        fig.update_traces(
            width=0.65, 
            opacity=0.60,
            marker_line_color="black",
            marker_line_width=2
        )
        
        fig.update_layout(
            barmode="overlay",
            plot_bgcolor='white',
            xaxis=dict(
                showgrid=True, 
                gridcolor='lightgray', 
                gridwidth=1,
                title=f"<b>MES DE {nom_mes_actual.upper()} {st.session_state.any_vista}</b>",
                side="top"
            ),
            yaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=1),
            height=max(400, len(df_net["Responsable"].unique()) * 65 + 150) if estil_grafic == "Vista per Personal (Estil Recursos)" else 500,
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
        
        caps_de_setmana = dies_del_mes[dies_del_mes.weekday.isin([5, 6])]
        for dia in caps_de_setmana:
            fig.add_vrect(
                x0=dia, x1=dia + pd.Timedelta(days=1), 
                fillcolor="lightgray", opacity=0.4, layer="below", line_width=0
            )
            
        for festiu_dt in festius_np:
            if str(festiu_dt)[:7] == f"{st.session_state.any_vista}-{st.session_state.mes_vista:02d}":
                f_inici = pd.to_datetime(festiu_dt)
                f_final = f_inici + pd.Timedelta(days=1)
                
                fig.add_vrect(
                    x0=f_inici, x1=f_final, 
                    fillcolor="dimgray", opacity=0.6, layer="below", line_width=0,
                    annotation_text="FESTIU", annotation_position="top right"
                )
        
        dilluns_mes = dies_del_mes[dies_del_mes.weekday == 0]
        for dilluns in dilluns_mes:
            num_setmana = dilluns.isocalendar().week
            fig.add_vline(x=dilluns, line_width=2, line_color="black")
            fig.add_annotation(
                x=dilluns,
                y=1,
                yref="paper",
                text=f"<b>S{num_setmana}</b>",
                showarrow=False,
                yshift=15,
                font=dict(size=12, color="black")
            )
            
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
