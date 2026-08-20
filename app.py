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
    "Ofertes França": ["Brendan", "Olivier", "Damien", "Agustín", "JordiVila", "Adrià", "StephaneJ", "RicardJoan", "IagoParga", "David", "Samuel", "Nacho Smith"],
    "Ofertes Recycling": ["Brendan", "Olivier", "Damien", "Agustín", "JordiVila", "Adrià", "StephaneJ", "RicardJoan", "IagoParga", "David", "Samuel", "Nacho Smith"],
    "Ofertes Internacionals": ["Brendan", "Olivier", "Damien", "Agustín", "JordiVila", "Adrià", "StephaneJ", "RicardJoan", "IagoParga", "David", "Samuel", "Nacho Smith"],
    "Ofertes Brasil": ["Brendan", "Olivier", "Damien", "Agustín", "JordiVila", "Adrià", "StephaneJ", "RicardJoan", "IagoParga", "David", "Samuel", "Nacho Smith"],
    "Ofertes Mèxic": ["Brendan", "Olivier", "Damien", "Agustín", "JordiVila", "Adrià", "StephaneJ", "RicardJoan", "IagoParga", "David", "Samuel", "Nacho Smith"]
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
st.subheader("🔍 Filtra per departament")
departaments_seleccionats = st.multiselect(
    "Selecciona quins departaments vols analitzar:", 
    options=list(equips.keys()), 
    default=list(equips.keys())
)

# 1. Agafem les ofertes dels departaments seleccionats
df_dept = st.session_state.ofertes[
    st.session_state.ofertes["Departament"].isin(departaments_seleccionats)
]

# 2. Identifiquem NOMÉS les persones que tenen com a mínim un projecte real de feina (excloent "Vacances")
personal_amb_projectes = df_dept[
    ~df_dept["Projecte"].astype(str).str.lower().str.contains("vacances")
]["Responsable"].unique()

# 3. Filtrem el resultat final: NOMÉS les persones amb feina assignada (i mostrem la seva feina + les seves vacances)
df_filtrat = st.session_state.ofertes[
    (st.session_state.ofertes["Responsable"].isin(personal_amb_projectes)) &
    (
        (st.session_state.ofertes["Departament"].isin(departaments_seleccionats)) |
        (st.session_state.ofertes["Projecte"].astype(str).str.lower().str.contains("vacances"))
    )
]

st.divider()
# 6. MÈTRIQUES D'OCUPACIÓ I CAPACITAT
st.subheader(f"📊 Ocupació de l'Equip a {nom_mes_actual}")

# Calculem la capacitat del mes (dies feiners desglossats)
dies_laborables_mes, festius_mes, dies_totals_mes = calcular_dies_feiners_mes(
    st.session_state.any_vista, st.session_state.mes_vista, festius_np
)

if dies_laborables_mes > 0 and not df_filtrat.empty:
    # 1. Identifiquem NOMÉS les persones amb feina assignada en el filtre actual
    personal_actiu = df_filtrat[
        ~df_filtrat["Projecte"].astype(str).str.lower().str.contains("vacances")
    ]["Responsable"].unique()

    # 2. Mostrem les barres d'ocupació ÚNICAMENT d'aquest personal actiu
    col_graf, col_mètrica = st.columns([3, 1])
    
    with col_graf:
        ocupacio_persones = []
        for persona in personal_actiu:
            dies_of, dies_vac = calcular_dies_ocupats_persona(
                df_filtrat, persona, st.session_state.any_vista, st.session_state.mes_vista, festius_np
            )
            pct = min(100, int((dies_of / dies_laborables_mes) * 100))
            ocupacio_persones.append({"Personal": persona, "Ocupació (%)": pct, "Dies": dies_of})
        
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
                range_x=[0, 100]
            )
            fig_bar.update_traces(texttemplate='%{text}%', textposition='outside')
            fig_bar.update_layout(height=max(250, len(personal_actiu) * 35), plot_bgcolor='white')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No hi ha projectes de feina per mostrar l'ocupació en aquest departament.")

    with col_mètrica:
        st.metric("Capacitat teòrica/persona", f"{dies_laborables_mes} dies")
        st.caption(f"Dies totals mes: {dies_totals_mes}d | Festius/Fins de setmana: {dies_totals_mes - dies_laborables_mes}d")
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
