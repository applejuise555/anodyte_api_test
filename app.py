import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timezone, timedelta
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
import math
from plotly.subplots import make_subplots
import time

# 1. ตั้งค่า Timezone (UTC +7)
ICT = timezone(timedelta(hours=7))
st.set_page_config(page_title="Gissco Production Line and Dashboard", layout="wide")

# --- Configuration ---
COLOR_HEX_MAP = {
    "Black": "#000000", "Red": "#FF0000", "Dark Red": "#8B0000", 
    "Violet": "#9400D3", "Green": "#008000", "Banana leaf Green": "#90EE90", 
    "Gold": "#FFD700", "Orange": "#FFA500", "Light Blue": "#ADD8E6", 
    "Blue": "#0000FF", "Dark Blue": "#00008B", "Pink": "#FFC0CB", 
    "Copper": "#B87333", "Titanium": "#808080", "Dark Titanium": "#4A4E69", 
    "Rose Gold": "#B76E79"
}

TANK_COLOR_MAP = {
    "4DarkBlue": "Dark Blue", "16Blue": "Blue", "1DarkRedA": "Dark Red",
    "1DarkRedB": "Dark Red", "19Copper": "Copper", "12Titanium": "Titanium",
    "13DarkTitanium": "Dark Titanium", "14RoseGold": "Rose Gold",
    "6BananaLeafGreen": "Banana leaf Green", "10LightBlue": "Light Blue",
    "18OrangeOil": "Orange", "9Orange": "Orange", "15Gold": "Gold",
    "11Gold": "Gold", "17Black": "Black", "21Black": "Black",
    "5Black": "Black", "20Black": "Black", "7Pink": "Pink",
    "8Green": "Green", "3Violet": "Violet", "2Red": "Red",
    "HotSealH60": "Black"
}

# --- เชื่อมต่อ Supabase ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error connecting to Supabase: {e}")
        return None

supabase = init_connection()

# --- Helper Functions ---
def get_hex_from_name(name):
    sorted_colors = sorted(COLOR_HEX_MAP.keys(), key=len, reverse=True)
    name_lower = str(name).lower()
    for color_name in sorted_colors:
        if color_name.lower() in name_lower:
            return COLOR_HEX_MAP[color_name]
    return "#CCCCCC"

def render_color_bar(name):
    hex_code = get_hex_from_name(name)
    st.markdown(f"""
        <div style="background-color:{hex_code}; width:100%; height:20px; border-radius:5px; border: 1px solid #ccc; margin-bottom: 10px;"></div>
    """, unsafe_allow_html=True)

def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    if not supabase: return {}
    try:
        query = supabase.table(table).select(f"{id_col}, {name_col}")
        if filter_col and filter_val:
            query = query.eq(filter_col, filter_val)
        response = query.execute()
        return {item[name_col]: item[id_col] for item in response.data}
    except Exception:
        return {}

def get_status_icon(value, min_val, max_val, warn_margin=0.1):
    if value is None:
        return "⚪"
    if value < min_val or value > max_val:
        return "🔴"
    elif value < (min_val + warn_margin) or value > (max_val - warn_margin):
        return "🟡"
    return "🟢"

menu = st.sidebar.radio("เมนู", ["Dashboard","บันทึกข้อมูลการผลิต"])

# ================= DASHBOARD (FULL SYSTEM VIEW) =================
if menu == "Dashboard":
    st.title("📊 Production Dashboard (System Overview)")

    # --- Standards ---
    PH_MIN, PH_MAX = 5.0, 6.0
    TEMP_COLOR_MIN, TEMP_COLOR_MAX = 30, 40
    PH_ANO_MIN, PH_ANO_MAX = 1, 1.5
    TEMP_ANO_MIN, TEMP_ANO_MAX = 18, 22
    DEN_ANO_MIN, DEN_ANO_MAX = 0.5, 1.5

    @st.cache_data(ttl=10)
    def load_color_logs():
        return supabase.table("color_tank_logs").select("*").order("recorded_at", desc=True).limit(200).execute().data

    @st.cache_data(ttl=10)
    def load_anodize_logs():
        return supabase.table("anodize_tank_logs").select("*").order("recorded_at", desc=True).limit(200).execute().data

    @st.cache_data(ttl=60)
    def load_tanks():
        return get_options("tanks", "tank_id", "tank_name")

    # KPI Section
    col1, col2 = st.columns(2)
    active_jigs_res = supabase.table("jig_status").select("jig_id, current_tank_id").eq("status_type", "In-Process").execute()
    active_jigs_data = active_jigs_res.data if active_jigs_res.data else []
    
    production_count = len(active_jigs_data)
    active_tanks_set = {item["current_tank_id"] for item in active_jigs_data if item["current_tank_id"] is not None}
    active_tanks_count = len(active_tanks_set)

    col1.metric("🟢 กำลังผลิต (จิ๊ก)", production_count)
    col2.metric("🧪 บ่อที่กำลังใช้งาน", active_tanks_count)
    st.markdown("---")

    # Color Tank Analysis
    st.subheader("🎨 วิเคราะห์ข้อมูลบ่อสี (Color Tanks)")
    logs = load_color_logs()
    if logs:
        df = pd.DataFrame(logs)
        df["recorded_at"] = pd.to_datetime(df["recorded_at"])
        tank_map = load_tanks()
        inv_tank_map = {v: k for k, v in tank_map.items()}
        df["tank_name"] = df["tank_id"].map(inv_tank_map)

        latest = df.drop_duplicates("tank_id").copy()
        if not latest.empty:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(x=latest["tank_name"], y=latest["ph_value"], name="ค่า pH", marker_color="#98FB98", text=latest["ph_value"], textposition='auto'), secondary_y=False)
            fig.add_trace(go.Bar(x=latest["tank_name"], y=latest["temperature"], name="อุณหภูมิ (°C)", marker_color="#AFEEEE", text=latest["temperature"], textposition='auto'), secondary_y=True)
            fig.update_yaxes(range=[0, 14], secondary_y=False)
            fig.update_yaxes(range=[0, 100], secondary_y=True)
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("🚨 ตารางแจ้งเตือนบ่อสี")
        alert_data = [{"Tank": row["tank_name"], "pH": f"{get_status_icon(row['ph_value'], PH_MIN, PH_MAX)} {row['ph_value']:.2f}", "Temp (°C)": f"{get_status_icon(row['temperature'], TEMP_COLOR_MIN, TEMP_COLOR_MAX)} {row['temperature']:.1f}"} for _, row in latest.iterrows()]
        st.dataframe(pd.DataFrame(alert_data), use_container_width=True)

    # Anodize Trend Analysis
    st.markdown("---")
    st.subheader("📈 วิเคราะห์แนวโน้มบ่ออโนไดซ์")
    logs_a = load_anodize_logs()
    if logs_a:
        df_a = pd.DataFrame(logs_a)
        df_a["recorded_at"] = pd.to_datetime(df_a["recorded_at"])
        tank_map = load_tanks()
        inv_map = {v: k for k, v in tank_map.items()}
        df_a["tank_name"] = df_a["tank_id"].map(inv_map)
        
        latest_ano = df_a.sort_values("recorded_at").groupby("tank_name").tail(1)
        alert_ano = [{"Tank": row["tank_name"], "pH": f"{get_status_icon(row['ph_value'], PH_ANO_MIN, PH_ANO_MAX)} {row['ph_value']:.2f}", "Temp": f"{get_status_icon(row['temperature'], TEMP_ANO_MIN, TEMP_ANO_MAX)} {row['temperature']:.1f}", "Density": f"{get_status_icon(row['density'], DEN_ANO_MIN, DEN_ANO_MAX)} {row['density']:.3f}"} for _, row in latest_ano.iterrows()]
        st.dataframe(pd.DataFrame(alert_ano), use_container_width=True)

    st_autorefresh(interval=10000, key="dashboard_refresh")

# ================= RECORD PAGE =================
elif menu == "บันทึกข้อมูลการผลิต":
    st.title("📝 ระบบบันทึกข้อมูล")
    tab_main = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig System)"])

    # --- Tab 1: บ่อสี ---
    with tab_main[0]:
        st.header("🎨 บันทึกข้อมูลบ่อสี")
        color_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")
        if color_tanks:
            selected_tank_name = st.selectbox("เลือกบ่อสี", list(color_tanks.keys()))
            render_color_bar(TANK_COLOR_MAP.get(selected_tank_name, "Black"))
            with st.form("color_log_form", clear_on_submit=True):
                ph = st.number_input("ค่า pH", step=0.1, format="%.2f")
                temp = st.number_input("อุณหภูมิ (°C)", step=0.1, format="%.1f")
                if st.form_submit_button("บันทึกค่า"):
                    supabase.table("color_tank_logs").insert({"tank_id": color_tanks[selected_tank_name], "ph_value": ph, "temperature": temp, "recorded_at": datetime.now(ICT).isoformat()}).execute()
                    st.success("✅ บันทึกข้อมูลบ่อสีสำเร็จ")
                    time.sleep(1.5)
                    st.rerun()

    # --- Tab 2: บ่ออโนไดซ์ ---
    with tab_main[1]:
        st.header("🧪 บันทึกข้อมูลบ่ออโนไดซ์")
        ano_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Anodize")
        if ano_tanks:
            sel_ano = st.selectbox("เลือกบ่ออโนไดซ์", list(ano_tanks.keys()))
            with st.form("ano_form", clear_on_submit=True):
                ph_a = st.number_input("ค่า pH", step=0.01, format="%.2f")
                temp_a = st.number_input("อุณหภูมิ (°C)", step=0.1, format="%.1f")
                den_a = st.number_input("ความหนาแน่น (Density)", step=0.001, format="%.3f")
                if st.form_submit_button("บันทึกข้อมูลอโนไดซ์"):
                    supabase.table("anodize_tank_logs").insert({"tank_id": ano_tanks[sel_ano], "ph_value": ph_a, "temperature": temp_a, "density": den_a, "recorded_at": datetime.now(ICT).isoformat()}).execute()
                    st.success("บันทึกข้อมูลอโนไดซ์สำเร็จ")
                    time.sleep(1.5)
                    st.rerun()

    # --- Tab 3: ระบบงานจิ๊ก (Jig System) ---
    with tab_main[2]:
        sub_prod, sub_jig, sub_log = st.tabs(["📦 1. ลงทะเบียนสินค้า", "🛠️ 2. ลงทะเบียนจิ๊ก", "⚡ 3. บันทึกผลผลิต"])

        with sub_prod:
            st.subheader("เพิ่มสินค้าใหม่ลงระบบ")
            shape = st.selectbox("📐 เลือกรูปทรง", ["สี่เหลี่ยม", "ทรงกระบอกทึบ", "ทรงกระบอกกลวง"])
            with st.form("add_prod_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                p_code = c1.text_input("รหัสสินค้า *")
                p_name = c1.text_input("ชื่อสินค้า")
                s_finish = c1.text_input("พื้นผิว *", value="-")
                height = c2.number_input("ความยาว/ความสูง (H) [mm]", min_value=0.0)
                width, thickness, od, u_vol, id_inner = 0.0, 0.0, 0.0, 0.0, 0.0
                if shape == "สี่เหลี่ยม":
                    width = c2.number_input("กว้าง [mm]", min_value=0.0)
                    thickness = c2.number_input("สูง/หนา [mm]", min_value=0.0)
                    u_vol = height * width * thickness
                elif shape == "ทรงกระบอกทึบ":
                    od = c2.number_input("เส้นผ่านศูนย์กลาง (OD) [mm]", min_value=0.0)
                    u_vol = math.pi * ((od/2)**2) * height
                else:
                    od = c2.number_input("เส้นผ่านศูนย์กลาง (OD) [mm]", min_value=0.0)
                    thickness = c2.number_input("ความหนาของเนื้อชิ้นงาน [mm]", min_value=0.0)
                    id_inner = max(0.0, od - (2*thickness))
                    u_vol = math.pi * ((od/2)**2 - (id_inner/2)**2) * height

                if st.form_submit_button("➕ ลงทะเบียนสินค้า"):
                    if p_code:
                        supabase.table("products").insert({"product_code": p_code, "product_name": p_name, "surface_finish": s_finish, "unit_volume": u_vol, "shape": shape}).execute()
                        st.success(f"✅ ลงทะเบียน {p_code} สำเร็จ!")
                    else: st.error("กรุณาระบุรหัสสินค้า")

        with sub_jig:
            st.subheader("เพิ่มรหัสจิ๊กและ Lot ใหม่")
            today_prefix = datetime.now(ICT).strftime("%Y%m%d")
            jig_count_res = supabase.table("jigs").select("jig_model_code").like("jig_model_code", f"{today_prefix}%").execute()
            auto_jig_code = f"{today_prefix}{len(jig_count_res.data) + 1:03d}"
            
            st.info(f"🆔 รหัสจิ๊กถัดไป: **{auto_jig_code}**")
            with st.form("add_jig_auto", clear_on_submit=True):
                j_code = st.text_input("รหัสจิ๊ก", value=auto_jig_code, disabled=True)
                # --- 1. เพิ่มตัวกรอก Lot No. ---
                lot_no = st.text_input("หมายเลข Lot (Lot No.) *")
                
                if st.form_submit_button("➕ ลงทะเบียนจิ๊ก"):
                    if not lot_no:
                        st.error("กรุณาระบุ Lot Number")
                    else:
                        supabase.table("jigs").insert({"jig_model_code": j_code, "lot_no": lot_no, "total_pcs_in_jig": 0}).execute()
                        st.success(f"✅ ลงทะเบียนจิ๊ก {j_code} (Lot: {lot_no}) สำเร็จ!")
                        time.sleep(1.5)
                        st.rerun()

        with sub_log:
            prods_res = supabase.table("products").select("product_id, product_code, product_name").execute().data
            jigs_data = supabase.table("jigs").select("jig_id, jig_model_code, lot_no").execute().data
            status_all = supabase.table("jig_status").select("jig_id, status_type").execute().data
            status_dict = {item["jig_id"]: item["status_type"] for item in (status_all or [])}
            
            available_jigs = [j for j in (jigs_data or []) if status_dict.get(j["jig_id"]) != "Finished"]

            if not available_jigs:
                st.warning("❌ ไม่มีจิ๊กที่ใช้งานได้")
            else:
                action = st.radio("การทำงาน", ["🔵 บันทึกงานต่อ", "🟢 เสร็จสิ้นงาน"])

                if action == "🔵 บันทึกงานต่อ":
                    # --- 2. แสดง Lot No. เวลาเลือกรหัสจิ๊ก ---
                    jig_map = {f"Jig: {j['jig_model_code']} | Lot: {j['lot_no']}": j['jig_id'] for j in available_jigs}
                    sel_j_display = st.selectbox("เลือกจิ๊ก (รหัส | Lot)", list(jig_map.keys()))
                    jig_id = jig_map[sel_j_display]
                    
                    display_options = {f"{p['product_code']} | {p['product_name']}": p['product_id'] for p in (prods_res or [])}
                    selected_display = st.selectbox("เลือกสินค้า", options=list(display_options.keys()))
                    
                    color_tanks_all = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")
                    sel_c_new = st.selectbox("เลือกสี", sorted(set(TANK_COLOR_MAP.values())))
                    filtered_tanks = {n: i for n, i in color_tanks_all.items() if TANK_COLOR_MAP.get(n) == sel_c_new}
                    
                    if filtered_tanks:
                        sel_tank_name = st.selectbox("เลือกบ่อสี", list(filtered_tanks.keys()))
                        with st.form("continue_form", clear_on_submit=True):
                            c1, c2 = st.columns(2)
                            pcs = c1.number_input("จำนวนต่อแถว", min_value=0)
                            rows = c1.number_input("แถวที่เต็ม", min_value=0)
                            partial = c1.number_input("เศษ", min_value=0)
                            total_pcs = (rows * pcs) + partial
                            c2.metric("จำนวนรวม (Pcs)", total_pcs)
                            
                            if st.form_submit_button("💾 บันทึก"):
                                supabase.table("jig_usage_log").insert({
                                    "product_id": display_options[selected_display], "jig_id": jig_id, 
                                    "color": sel_c_new, "tank_id": filtered_tanks[sel_tank_name], 
                                    "total_pieces": total_pcs, "recorded_date": datetime.now(ICT).isoformat()
                                }).execute()
                                supabase.table("jig_status").upsert({"jig_id": jig_id, "status_type": "In-Process", "current_tank_id": filtered_tanks[sel_tank_name], "updated_at": datetime.now(ICT).isoformat()}).execute()
                                supabase.table("jigs").update({"total_pcs_in_jig": total_pcs}).eq("jig_id", jig_id).execute()
                                st.success("✅ บันทึกข้อมูลสำเร็จ")
                                time.sleep(1.2)
                                st.rerun()

                elif action == "🟢 เสร็จสิ้นงาน":
                    # --- 3. แสดงเฉพาะรหัสจิ๊ก ---
                    jig_finish_map = {f"{j['jig_model_code']}": j['jig_id'] for j in available_jigs}
                    sel_j_finish = st.selectbox("เลือกรหัสจิ๊กที่ต้องการเสร็จสิ้นงาน", list(jig_finish_map.keys()))
                    jig_id_finish = jig_finish_map[sel_j_finish]

                    if st.button("🏁 ยืนยันเสร็จสิ้นงาน"):
                        check_log = supabase.table("jig_usage_log").select("*").eq("jig_id", jig_id_finish).limit(1).execute()
                        if not check_log.data:
                            st.warning("⚠️ จิ๊กนี้ยังไม่มีการบันทึกข้อมูลการผลิต")
                        else:
                            supabase.table("jig_status").upsert({"jig_id": jig_id_finish, "status_type": "Finished", "current_tank_id": None, "updated_at": datetime.now(ICT).isoformat()}).execute()
                            st.success(f"✅ เสร็จสิ้นงานสำหรับจิ๊ก {sel_j_finish}")
                            time.sleep(1.2)
                            st.rerun()
