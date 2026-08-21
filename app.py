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
# 7. CALENDARI D'OFERTES
st.subheader("📅 Calendari d'Ofertes")

# --- NAVEGADOR TEMPORAL (Moure's de mes cap a l'esquerra / dreta) ---
col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

with col_nav1:
    if st.button("⬅️ Mes Anterior"):
        if st.session_state.mes_vista == 1:
            st.session_state.mes_vista = 12
            st.session_state.any_vista -= 1
        else:
            st.session_state.mes_vista -= 1
        st.rerun()

with col_nav2:
    st.markdown(f"<h4 style='text-align: center;'>{nom_mes_actual.upper()} {st.session_state.any_vista}</h4>", unsafe_allow_html=True)

with col_nav3:
    if st.button("Mes Següent ➡️"):
        if st.session_state.mes_vista == 12:
            st.session_state.mes_vista = 1
            st.session_state.any_vista += 1
        else:
            st.session_state.mes_vista += 1
        st.rerun()

# --- OPIONS DE VISUALITZACIÓ ---
estil_vista = st.radio(
    "Tria l'estil de visualització:",
    ["Vista per Personal (Estil Recursos)", "Vista per Projectes (Estil Gantt)"],
    horizontal=True
)

if not df_filtrat.empty:
    df_gantt = df_filtrat.copy()
    df_gantt["Inici"] = pd.to_datetime(df_gantt["Inici"])
    df_gantt["Final"] = pd.to_datetime(df_gantt["Final"])
    
    # Ajustem la visualització segons l'opció triada
    eix_y = "Responsable" if "Personal" in estil_vista else "Projecte"
    
    fig_gantt = px.timeline(
        df_gantt,
        x_start="Inici",
        x_end="Final",
        y=eix_y,
        color="Projecte",
        hover_data=["Departament", "Responsable", "Projecte"]
    )
    
    fig_gantt.update_yaxes(autorange="reversed")
    fig_gantt.update_layout(
        height=max(400, len(df_gantt[eix_y].unique()) * 35), 
        plot_bgcolor='white',
        margin=dict(t=10, b=10)
    )
    st.plotly_chart(fig_gantt, use_container_width=True)
else:
    st.info("No hi ha dades per mostrar al calendari amb els filtres seleccionats per a aquest mes.")


# 8. TAULA EDITABLE PER DEPARTAMENTS
with st.expander("✏️ Base de dades completa (Organitzada per Departaments)"):
    st.write("Selecciona el departament per editar o afegir ofertes directament a la taula.")
    
    # 1. Creem les pestanyes dinàmicament segons els teus departaments
    llista_pestanyes = ["Tots"] + list(equips.keys()) + ["Festiu Empresa"]
    pestanyes = st.tabs(llista_pestanyes)
    
    df_per_editar = st.session_state.ofertes.copy()
    
    # Configuració visual de les columnes per a Streamlit
    config_columnes = {
        "Inici": st.column_config.DateColumn("Data Inici", format="YYYY-MM-DD"),
        "Final": st.column_config.DateColumn("Data Final", format="YYYY-MM-DD"),
        "Departament": st.column_config.SelectboxColumn("Departament", options=list(equips.keys()) + ["Festiu Empresa"]),
        "Responsable": st.column_config.SelectboxColumn("Responsable", options=sorted(list(set([p for llista in equips.values() for p in llista]))))
    }
    
    canvis_realitzats = False
    dfs_editats = []

    # 2. Generem una taula independent dins de cada pestanya
    for i, nom_pestanya in enumerate(llista_pestanyes):
        with pestanyes[i]:
            if nom_pestanya == "Tots":
                df_sub = df_per_editar.copy()
            else:
                df_sub = df_per_editar[df_per_editar["Departament"] == nom_pestanya].copy()
            
            df_editat_sub = st.data_editor(
                df_sub,
                use_container_width=True,
                num_rows="dynamic",
                column_config=config_columnes,
                key=f"editor_{nom_pestanya}"
            )
            
            # Si no estem a la pestanya "Tots", guardem les modificacions d'aquesta pestanya
            if nom_pestanya != "Tots":
                dfs_editats.append(df_editat_sub)

    st.divider()
    
    # 3. Botó global de desar canvis a Google Sheets
    if st.button("💾 Desar tots els canvis a Google Sheets", type="primary"):
        # Reconstruïm el DataFrame unificant les pestanyes individuals
        if dfs_editats:
            df_final_guardar = pd.concat(dfs_editats, ignore_index=True)
        else:
            df_final_guardar = df_per_editar.copy()
            
        df_final_guardar['Inici'] = pd.to_datetime(df_final_guardar['Inici']).dt.strftime('%Y-%m-%d')
        df_final_guardar['Final'] = pd.to_datetime(df_final_guardar['Final']).dt.strftime('%Y-%m-%d')
        df_final_guardar.fillna("", inplace=True)
        
        sheet.clear()
        llista_dades = [df_final_guardar.columns.values.tolist()] + df_final_guardar.values.tolist()
        sheet.update(llista_dades)
        
        st.success("✅ La base de dades s'ha actualitzat correctament a Google Sheets!")
        st.rerun()
# 9. SECCIÓ PROTEGIDA PER A DIRECCIÓ (CEO / CCO)
st.divider()
st.subheader("🔒 Àrea Executiva (KPIs i Direcció)")

if "autenticat_direccio" not in st.session_state:
    st.session_state.autenticat_direccio = False

if not st.session_state.autenticat_direccio:
    contrasenya_input = st.text_input("Introdueix la contrasenya d'accés executiu:", type="password")
    if st.button("Accedir al Panell de Direcció"):
        if contrasenya_input == "Bianna7412!100":
            st.session_state.autenticat_direccio = True
            st.success("Accés autoritzat.")
            st.rerun()
        else:
            st.error("Contrasenya incorrecta.")
else:
    if st.button("🔒 Tancar sessió de direcció"):
        st.session_state.autenticat_direccio = False
        st.rerun()
        
    st.markdown(f"### 📈 Panell de Gestió Executiva — {nom_mes_actual.upper()} {st.session_state.any_vista}")
    
    # --- PREPARACIÓ DE DADES GLOBALS ---
    df_global = st.session_state.ofertes.copy()
    df_ofertes_reals = df_global[
        (~df_global["Projecte"].astype(str).str.lower().str.contains("vacances")) &
        (df_global["Departament"] != "Festiu Empresa") &
        (pd.notnull(df_global["Inici"])) & 
        (pd.notnull(df_global["Final"]))
    ].copy()
    
    data_inici_m = pd.to_datetime(f"{st.session_state.any_vista}-{st.session_state.mes_vista:02d}-01")
    data_final_m = pd.to_datetime(f"{st.session_state.any_vista}-{st.session_state.mes_vista:02d}-{ultim_dia}")
    dies_feiners_mes = [d for d in pd.date_range(data_inici_m, data_final_m) if d.weekday() < 5 and d.strftime('%Y-%m-%d') not in festius_np]
    capacitat_unitaria = len(dies_feiners_mes)
    tots_els_treballadors = list(set([p for llista in equips.values() for p in llista]))
    
    esforc_per_dept = {dept: 0 for dept in equips.keys()}
    propostes_per_dept = {dept: set() for dept in equips.keys()}
    esforc_per_persona = {p: 0 for p in tots_els_treballadors}
    propostes_per_persona = {p: set() for p in tots_els_treballadors}
    lliuraments_per_dia = {}
    
    ofertes_actives_mes = set()
    personal_actiu_mes = set()
    total_dies_home_investits = 0

    for _, row in df_ofertes_reals.iterrows():
        ranga = pd.date_range(start=pd.to_datetime(row["Inici"]), end=pd.to_datetime(row["Final"]))
        dept = row["Departament"]
        persona = row["Responsable"]
        projecte = row["Projecte"]
        data_final_proj = pd.to_datetime(row["Final"])
        
        dies_dins_mes = [d for d in ranga if d in dies_feiners_mes]
        num_dies = len(dies_dins_mes)
        
        if num_dies > 0:
            ofertes_actives_mes.add(projecte)
            personal_actiu_mes.add(persona)
            total_dies_home_investits += num_dies
            
            if dept in esforc_per_dept:
                esforc_per_dept[dept] += num_dies
                propostes_per_dept[dept].add(projecte)
            if persona in esforc_per_persona:
                esforc_per_persona[persona] += num_dies
                propostes_per_persona[persona].add(projecte)
                
            # Registre de lliuraments finals dins del mes
            if data_final_proj in dies_feiners_mes:
                str_dia = data_final_proj.strftime('%d/%m')
                lliuraments_per_dia[str_dia] = lliuraments_per_dia.get(str_dia, 0) + 1

    capacitat_total_equip = len(tots_els_treballadors) * capacitat_unitaria
    ratio_carrega_global = min(100, int((total_dies_home_investits / capacitat_total_equip) * 100)) if capacitat_total_equip > 0 else 0

    # ==========================================
    # PUNT 1: MÈTRIQUES ESTRATÈGIQUES GLOBALS
    # ==========================================
    st.markdown("#### 1. Mètriques Estratègiques Globals")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Ofertes Actives", f"{len(ofertes_actives_mes)} propostes")
    kpi2.metric("Dies/Home Invertits", f"{total_dies_home_investits} dies")
    kpi3.metric("Ràtio Càrrega Global", f"{ratio_carrega_global}%")
    kpi4.metric("Personal Encarregat", f"{len(personal_actiu_mes)} / {len(tots_els_treballadors)}")

    df_esforc = pd.DataFrame([
        {
            "Departament": dept, 
            "Nº Propostes": len(propostes_per_dept[dept]),
            "Dies/Home": dies
        } 
        for dept, dies in esforc_per_dept.items() if dies > 0
    ])

    col_pie, col_resum = st.columns([2, 1])
    with col_pie:
        st.caption("🌎 **Repartiment de l'Esforç Tècnic per Mercat**")
        if not df_esforc.empty:
            fig_pie = px.pie(
                df_esforc, values="Dies/Home", names="Departament", hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(showlegend=False, height=280, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sense activitat en aquest mes.")

    with col_resum:
        st.caption("📋 **Resum Executiu per Àrea**")
        if not df_esforc.empty:
            df_esforc["% Esforç"] = ((df_esforc["Dies/Home"] / total_dies_home_investits) * 100).round(1).astype(str) + "%"
            st.dataframe(
                df_esforc[["Departament", "Nº Propostes", "Dies/Home", "% Esforç"]].sort_values(by="Dies/Home", ascending=False), 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.write("Sense dades.")

    st.divider()

    # ==========================================
    # PUNT 2: CONTROL DE TALENT I RISC DE PERSONES CLAU
    # ==========================================
    st.markdown("#### 2. Control de Capacitat i Risc de Dependència")
    
    dies_lliures_globals = max(0, capacitat_total_equip - total_dies_home_investits)
    
    # 2.1 Càlcul de Risc de Persones Clau (més del 30% de les ofertes o saturats >= 80%)
    total_ofertes_count = len(ofertes_actives_mes)
    persones_clau_risc = []
    
    for p, propostes in propostes_per_persona.items():
        count_p = len(propostes)
        d_p = esforc_per_persona[p]
        pct_d = int((d_p / capacitat_unitaria) * 100) if capacitat_unitaria > 0 else 0
        pct_prop = (count_p / total_ofertes_count * 100) if total_ofertes_count > 0 else 0
        
        if pct_d >= 80 or pct_prop >= 30:
            persones_clau_risc.append({
                "Responsable": p,
                "Propostes": count_p,
                "% Ofertes": f"{pct_prop:.0f}%",
                "Ocupació": f"{pct_d}%"
            })

    # 2.2 Càlcul de Solapaments Crítics de Lliurament (dies amb >= 3 lliuraments)
    dias_solapats = [f"{dia} ({num} ofertes)" for dia, num in lliuraments_per_dia.items() if num >= 3]

    col_t1, col_t2 = st.columns([1, 2])
    
    with col_t1:
        st.metric("Capacitat Disponible Immediata", f"{dies_lliures_globals} dies/home")
        
        if persones_clau_risc:
            st.warning("⚠️ **Risc de Persones Clau / Saturació:**")
            st.dataframe(pd.DataFrame(persones_clau_risc), use_container_width=True, hide_index=True)
        else:
            st.success("✅ Distribució equilibrada sense dependències crítiques.")
            
        if dias_solapats:
            st.error(f"🔥 **Solapament Crític de Lliuraments:**\n\nDirectes a lliurar el mateix dia: {', '.join(dias_solapats)}")
        else:
            st.info("📅 Sense concentració crítica de lliuraments en un mateix dia.")

    with col_t2:
        st.caption("📊 **Ràtio d'Ocupació Individual Global (% sobre capacitat mes)**")
        data_talent = []
        for p, d in esforc_per_persona.items():
            pct_p = min(100, int((d / capacitat_unitaria) * 100)) if capacitat_unitaria > 0 else 0
            data_talent.append({"Personal": p, "Ocupació (%)": pct_p})
            
        df_talent = pd.DataFrame(data_talent).sort_values(by="Ocupació (%)", ascending=True)
        fig_talent = px.bar(
            df_talent, x="Ocupació (%)", y="Personal", orientation='h',
            color="Ocupació (%)", color_continuous_scale="RdYlGn_r", range_x=[0, 100]
        )
        fig_talent.update_layout(height=max(220, len(tots_els_treballadors) * 22), plot_bgcolor='white')
        st.plotly_chart(fig_talent, use_container_width=True)

    st.divider()

    # ==========================================
    # PUNT 3: PROJECCIÓ I TENDÈNCIA TEMPORAL (3 MESOS)
    # ==========================================
    st.markdown("#### 3. Projecció Temporal de la Càrrega (Trimestre Actiu)")
    
    mes_act = st.session_state.mes_vista
    any_act = st.session_state.any_vista
    projeccio_dades = []
    
    for i in range(3):
        m = (mes_act - 1 + i) % 12 + 1
        a = any_act + ((mes_act - 1 + i) // 12)
        
        ultim_d_proj = calendar.monthrange(a, m)[1]
        d_inici_p = pd.to_datetime(f"{a}-{m:02d}-01")
        d_final_p = pd.to_datetime(f"{a}-{m:02d}-{ultim_d_proj}")
        d_feiners_p = [d for d in pd.date_range(d_inici_p, d_final_p) if d.weekday() < 5 and d.strftime('%Y-%m-%d') not in festius_np]
        
        cap_total_p = len(tots_els_treballadors) * len(d_feiners_p)
        esforc_p = 0
        
        for _, row in df_ofertes_reals.iterrows():
            ranga = pd.date_range(start=pd.to_datetime(row["Inici"]), end=pd.to_datetime(row["Final"]))
            esforc_p += len([d for d in ranga if d in d_feiners_p])
            
        nom_m_p = calendar.month_name[m].capitalize()
        pct_proj = min(100, int((esforc_p / cap_total_p) * 100)) if cap_total_p > 0 else 0
        
        projeccio_dades.append({
            "Mes": f"{nom_m_p} {a}",
            "Dies/Home Invertits": esforc_p,
            "Càrrega Global (%)": pct_proj
        })
        
    df_projeccio = pd.DataFrame(projeccio_dades)
    col_p1, col_p2 = st.columns([1, 2])
    
    with col_p1:
        st.caption("📈 **Resum Trimestral Prevista**")
        st.dataframe(df_projeccio, use_container_width=True, hide_index=True)
        
    with col_p2:
        st.caption("🔮 **Evolució de la Càrrega (%) Pròxims 3 Mesos**")
        fig_proj = px.line(
            df_projeccio, x="Mes", y="Càrrega Global (%)", markers=True, text="Càrrega Global (%)",
            range_y=[0, 100]
        )
        fig_proj.update_traces(textposition="top center", line_color="firebrick", line_width=3)
        fig_proj.update_layout(height=240, plot_bgcolor='white')
        st.plotly_chart(fig_proj, use_container_width=True)
