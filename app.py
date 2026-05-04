import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timezone, timedelta
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
import math
from plotly.subplots import make_subplots

# 1. ตั้งค่า Timezone (UTC +7)
ICT = timezone(timedelta(hours=7))
st.set_page_config(page_title="SCADA Dashboard", layout="wide")

# --- [ADD] Constants & Thresholds ---
PH_MIN, PH_MAX = 5.0, 6.0
PH_ANO_MIN, PH_ANO_MAX = 0.5, 1.5
TEMP_COLOR_MIN, TEMP_COLOR_MAX = 30.0, 40.0
TEMP_ANO_MIN, TEMP_ANO_MAX = 15.0, 25.0
DEN_ANO_MIN, DEN_ANO_MAX = 1.050, 1.150

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

# --- [ADD] Helper Functions ---

def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    """ฟังก์ชันสำหรับดึงข้อมูลจาก Database มาทำ Dropdown"""
    query = supabase.table(table).select(f"{id_col}, {name_col}")
    if filter_col and filter_val:
        query = query.eq(filter_col, filter_val)
    res = query.execute()
    if res.data:
        return {item[name_col]: item[id_col] for item in res.data}
    return {}

def render_color_bar(color_name):
    """แสดงแถบสีตัวอย่างในหน้าบันทึกข้อมูล"""
    hex_code = COLOR_HEX_MAP.get(color_name, "#FFFFFF")
    st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <div style="width: 50px; height: 20px; background-color: {hex_code}; border: 1px solid #ddd; margin-right: 10px;"></div>
            <span>สีที่ตรวจพบ: <b>{color_name}</b></span>
        </div>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_tanks():
    return get_options("tanks", "tank_id", "tank_name")

@st.cache_data(ttl=10)
def load_color_logs():
    return supabase.table("color_tank_logs").select("*").order("recorded_at", desc=True).limit(200).execute().data

@st.cache_data(ttl=10)
def load_anodize_logs():
    return supabase.table("anodize_tank_logs").select("*").order("recorded_at", desc=True).limit(200).execute().data
    
menu = st.sidebar.radio("เมนู", ["Dashboard","บันทึกข้อมูลการผลิต"])

# ================= DASHBOARD (CLEAN VERSION) =================
# ================= DASHBOARD (CLEAN VERSION) =================
if menu == "Dashboard":
    st.title("📊 Production Overview")
    
    # 1. Load Data
    inv_tank_map = load_tank_mapping() # เรียกใช้ฟังก์ชันที่สร้างใหม่
    color_logs = load_color_logs()
    ano_logs = load_anodize_logs()

    df_c = pd.DataFrame(color_logs) if color_logs else pd.DataFrame()
    df_a = pd.DataFrame(ano_logs) if ano_logs else pd.DataFrame()

    # 2. Alerts Analysis
    bad_color = []
    bad_ano = []
    
    if not df_c.empty:
        latest_c = df_c.drop_duplicates("tank_id")
        bad_color = latest_c[(latest_c["ph_value"] < PH_MIN) | (latest_c["ph_value"] > PH_MAX)].to_dict('records')
        
    if not df_a.empty:
        latest_a = df_a.drop_duplicates("tank_id")
        bad_ano = latest_a[(latest_a["ph_value"] < PH_ANO_MIN) | (latest_a["ph_value"] > PH_ANO_MAX)].to_dict('records')

    total_alerts = len(bad_color) + len(bad_ano)

    # 3. KPI Metrics
    m1, m2, m3 = st.columns(3)
    jig_res = supabase.table("jig_status").select("jig_id").eq("status_type", "In-Process").execute()
    active_jigs = len(jig_res.data) if jig_res.data else 0
    
    m1.metric("📦 Production (Jigs)", active_jigs)
    m2.metric("🧪 Active Tanks", (df_c["tank_id"].nunique() if not df_c.empty else 0) + (df_a["tank_id"].nunique() if not df_a.empty else 0))
    m3.metric("⚠️ Total Issues", total_alerts, delta=f"{total_alerts} abnormal", delta_color="inverse" if total_alerts > 0 else "normal")

    # 4. Smart Alerts
    if total_alerts > 0:
        with st.expander(f"🔴 พบความผิดปกติ {total_alerts} รายการ", expanded=True):
            for row in bad_color:
                st.error(f"🎨 **{inv_tank_map.get(row['tank_id'], 'Unknown')}**: pH {row['ph_value']:.2f} (เกณฑ์: {PH_MIN}-{PH_MAX})")
            for row in bad_ano:
                st.error(f"🧪 **{inv_tank_map.get(row['tank_id'], 'Unknown')}**: pH {row['ph_value']:.2f} (เกณฑ์: {PH_ANO_MIN}-{PH_ANO_MAX})")
    else:
        st.success("✨ ระบบทำงานปกติ: ค่าทางเคมีอยู่ในเกณฑ์มาตรฐาน")

    # 5. Visualizations
    tabs = st.tabs(["🎨 Color Status", "📈 Detailed Trends"])
    
    with tabs[0]:
        if not df_c.empty:
            latest_c = df_c.drop_duplicates("tank_id").copy()
            latest_c["tank_name"] = latest_c["tank_id"].map(inv_tank_map)
            fig_c = go.Figure(go.Bar(
                x=latest_c["tank_name"], y=latest_c["ph_value"],
                marker_color=['#ff4b4b' if (v < PH_MIN or v > PH_MAX) else '#00cc96' for v in latest_c["ph_value"]],
                text=latest_c["ph_value"], textposition='outside'
            ))
            fig_c.update_layout(title="Current pH Level", yaxis_range=[0, 10])
            st.plotly_chart(fig_c, use_container_width=True)

    with tabs[1]:
        st.subheader("🔍 วิเคราะห์ข้อมูลรายบ่อ")
        all_recorded_tanks = []
        if not df_c.empty: all_recorded_tanks += df_c["tank_id"].unique().tolist()
        if not df_a.empty: all_recorded_tanks += df_a["tank_id"].unique().tolist()
        
        selection_map = {inv_tank_map.get(tid, f"ID:{tid}"): tid for tid in set(all_recorded_tanks)}
        if selection_map:
            selected_name = st.selectbox("เลือกบ่อที่ต้องการดูประวัติ", list(selection_map.keys()))
            sid = selection_map[selected_name]
            
            t_df = df_c[df_c["tank_id"] == sid] if not df_c.empty and sid in df_c["tank_id"].values else (df_a[df_a["tank_id"] == sid] if not df_a.empty else pd.DataFrame())
            
            if not t_df.empty:
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(x=t_df["recorded_at"], y=t_df["ph_value"], mode='lines+markers', name='pH'))
                st.plotly_chart(fig_trend, use_container_width=True)

    # --- ส่วน Color Tank Analysis ด้านล่าง ---
    if not df_c.empty:
        st.subheader("🎨 วิเคราะห์ข้อมูลบ่อสี (Color Tanks)")
        df_c_viz = df_c.copy()
        df_c_viz["tank_name"] = df_c_viz["tank_id"].map(inv_tank_map)
        latest_c_viz = df_c_viz.drop_duplicates("tank_id")

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=latest_c_viz["tank_name"], y=latest_c_viz["ph_value"], name="pH (5.0-6.0)", marker_color="#98FB98", offsetgroup=1), secondary_y=False)
        fig.add_trace(go.Bar(x=latest_c_viz["tank_name"], y=latest_c_viz["temperature"], name="Temp (30-40°C)", marker_color="#AFEEEE", offsetgroup=2), secondary_y=True)
        
        fig.update_layout(title="เปรียบเทียบค่า pH และอุณหภูมิ (ล่าสุด)", barmode="group")
        st.plotly_chart(fig, use_container_width=True)

    st_autorefresh(interval=30000, key="auto_refresh_dashboard")

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
            detected_color = TANK_COLOR_MAP.get(selected_tank_name, "Black")
            render_color_bar(detected_color)
            
            with st.form("color_log_form"):
                ph = st.number_input("ค่า pH", step=0.1, format="%.2f")
                temp = st.number_input("อุณหภูมิ (°C)", step=0.1, format="%.1f")
                if st.form_submit_button("บันทึกค่า"):
                    supabase.table("color_tank_logs").insert({
                        "tank_id": color_tanks[selected_tank_name], 
                        "ph_value": ph, "temperature": temp, 
                        "recorded_at": datetime.now(ICT).isoformat()
                    }).execute()
                    st.success("บันทึกข้อมูลบ่อสีสำเร็จ")

    # --- Tab 2: บ่ออโนไดซ์ ---
    with tab_main[1]:
        st.header("🧪 บันทึกข้อมูลบ่ออโนไดซ์")
        ano_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Anodize")
        if ano_tanks:
            sel_ano = st.selectbox("เลือกบ่ออโนไดซ์", list(ano_tanks.keys()))
            with st.form("ano_form"):
                ph_a = st.number_input("ค่า pH", step=0.01, format="%.2f")
                temp_a = st.number_input("อุณหภูมิ (°C)", step=0.1, format="%.1f")
                den_a = st.number_input("ความหนาแน่น (Density)", step=0.001, format="%.3f")
                if st.form_submit_button("บันทึกข้อมูลอโนไดซ์"):
                    supabase.table("anodize_tank_logs").insert({
                        "tank_id": ano_tanks[sel_ano], "ph_value": ph_a,
                        "temperature": temp_a, "density": den_a,
                        "recorded_at": datetime.now(ICT).isoformat()
                    }).execute()
                    st.success("บันทึกข้อมูลอโนไดซ์สำเร็จ")

# --- Tab หลัก 3: ระบบงานจิ๊ก (Jig System) ---
    with tab_main[2]:
        sub_prod, sub_jig, sub_log = st.tabs(["📦 1. ลงทะเบียนสินค้า", "🛠️ 2. ลงทะเบียนจิ๊ก", "⚡ 3. บันทึกผลผลิต"])

        with sub_prod:
            st.subheader("เพิ่มสินค้าใหม่ลงระบบ")
            shape = st.selectbox("📐 เลือกรูปทรง", ["สี่เหลี่ยม", "ทรงกระบอกทึบ", "ทรงกระบอกกลวง"], key="shape_sel")
            with st.form("add_prod_form_fixed", clear_on_submit=True):
                c1, c2 = st.columns(2)
                p_code = c1.text_input("รหัสสินค้า *")
                p_name = c1.text_input("ชื่อสินค้า")
                s_finish = c1.text_input("พื้นผิว *", value="-")
                height = c2.number_input("ความยาว (H) [mm]", min_value=0.0)
                width, thickness, od, u_vol = 0.0, 0.0, 0.0, 0.0
                if shape == "สี่เหลี่ยม":
                    width = c2.number_input("กว้าง [mm]", min_value=0.0)
                    thickness = c2.number_input("หนา [mm]", min_value=0.0)
                    u_vol = height * width * thickness
                elif shape == "ทรงกระบอกทึบ":
                    od = c2.number_input("เส้นผ่านศูนย์กลาง (OD) [mm]", min_value=0.0)
                    u_vol = math.pi * ((od/2)**2) * height
                else:
                    od = c2.number_input("OD [mm]", min_value=0.0)
                    thickness = c2.number_input("ความหนาเนื้อ [mm]", min_value=0.0)
                    id_inner = max(0.0, od - (2*thickness))
                    u_vol = math.pi * ((od/2)**2 - (id_inner/2)**2) * height

                st.info(f"💡 ปริมาตร: {u_vol:,.2f} mm³")
                if st.form_submit_button("➕ ลงทะเบียนสินค้า"):
                    if p_code:
                        # --- ส่วนตรวจสอบการซ้ำ ---
                        check_exist = supabase.table("products").select("product_code").eq("product_code", p_code).execute()
                        
                        if check_exist.data:
                            st.error(f"❌ รหัสสินค้า '{p_code}' นี้มีอยู่ในระบบแล้ว ไม่สามารถลงทะเบียนซ้ำได้")
                        else:
                            payload = {
                                "product_code": p_code, 
                                "product_name": p_name, 
                                "surface_finish": s_finish, 
                                "unit_volume": u_vol, 
                                "height": height, 
                                "width": width, 
                                "thickness": thickness, 
                                "depth": thickness, 
                                "shape": shape, 
                                "outer_diameter": od, 
                                "inner_diameter": id_inner if 'id_inner' in locals() else 0.0
                            }
                            supabase.table("products").insert(payload).execute()
                            st.success(f"✅ ลงทะเบียนรหัส {p_code} สำเร็จ!")
                    else: 
                        st.error("กรุณาระบุรหัสสินค้า")

        with sub_jig:
            st.subheader("เพิ่มรหัสจิ๊กใหม่")
            with st.form("add_jig_fixed", clear_on_submit=True):
                j_code = st.text_input("รหัสจิ๊ก", key="j_code_input").strip()
                if st.form_submit_button("ลงทะเบียนจิ๊ก"):
                    if j_code:
                        # --- ส่วนตรวจสอบการซ้ำ ---
                        check_jig = supabase.table("jigs").select("jig_model_code").eq("jig_model_code", j_code).execute()
                        
                        if check_jig.data:
                            st.error(f"❌ รหัสจิ๊ก '{j_code}' นี้มีอยู่ในระบบแล้ว")
                        else:
                            supabase.table("jigs").insert({"jig_model_code": j_code, "total_pcs_in_jig": 0}).execute()
                            st.success(f"✅ ลงทะเบียนจิ๊ก {j_code} สำเร็จ")
                    else: 
                        st.error("กรุณากรอกรหัสจิ๊ก")

        with sub_log:
            # 1. ดึงข้อมูลสินค้ามาทั้งหมด (เอาทั้ง ID, Code และ Name)
            prods_res = supabase.table("products").select("product_id, product_code, product_name").execute().data
            
            # 2. สร้าง Dictionary สำหรับ Mapping และ List สำหรับแสดงผลใน Selectbox
            if prods_res:
                # สร้างข้อความแสดงผล เช่น "P001 | อะลูมิเนียมเส้น"
                display_options = {
                    f"{p['product_code']} | {p['product_name']}": p['product_id'] 
                    for p in prods_res
                }
                
                jigs_data = supabase.table("jigs").select("jig_id, jig_model_code").execute().data
                available_jigs = []
                for j in (jigs_data or []):
                    status_res = supabase.table("jig_status").select("status_type").eq("jig_id", j["jig_id"]).order("updated_at", desc=True).limit(1).execute()
                    if not status_res.data or status_res.data[0]["status_type"] != "Finished":
                        available_jigs.append(j)

                if not available_jigs:
                    st.warning("❌ ไม่มีจิ๊กที่ใช้งานได้")
                else:
                    jig_map = {j['jig_model_code']: j['jig_id'] for j in available_jigs}
                    color_tanks_all = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")
                    
                    if display_options and color_tanks_all:
                        sel_j = st.selectbox("เลือกจิ๊ก", list(jig_map.keys()), key="sel_j_log")
                        jig_id = jig_map[sel_j]
                        
                        # --- ส่วนที่เปลี่ยน: เลือกสินค้า ---
                        selected_display = st.selectbox(
                            "เลือกสินค้า (รหัส | ชื่อ)", 
                            options=list(display_options.keys()), 
                            key="sel_p_log"
                        )
                        # ดึง product_id จริงๆ ออกมาใช้งาน
                        selected_prod_id = display_options[selected_display]
                        
                        # ดึงข้อมูลสินค้าตัวที่เลือกมาเพื่อคำนวณปริมาตร
                        p_info = supabase.table("products").select("*").eq("product_id", selected_prod_id).single().execute().data
                        
                        action = st.radio("การทำงาน", ["🔵 บันทึกงานต่อ", "🟢 เสร็จสิ้นงาน"], key="action_radio")

                        if action == "🔵 บันทึกงานต่อ":
                            sel_c_new = st.selectbox("เลือกสี", sorted(set(TANK_COLOR_MAP.values())), key="sel_c_log")
                            filtered_tanks = {n: i for n, i in color_tanks_all.items() if TANK_COLOR_MAP.get(n) == sel_c_new}
                            sel_tank_name = st.selectbox("เลือกบ่อสี", list(filtered_tanks.keys()), key="sel_t_log")
                            
                            with st.form("continue_form_fixed", clear_on_submit=True):
                                c1, c2 = st.columns(2)
                                pcs = c1.number_input("จำนวนต่อแถว", min_value=0)
                                rows = c1.number_input("แถวที่เต็ม", min_value=0)
                                partial = c1.number_input("เศษ", min_value=0)
                                
                                total_pcs = (rows * pcs) + partial
                                unit_vol = p_info.get('unit_volume', 0)
                                total_vol = unit_vol * total_pcs
                                
                                c2.metric("จำนวนรวม (Pcs)", total_pcs)
                                c2.metric("ปริมาตรรวม (mm³)", f"{total_vol:,.2f}")
                                
                                if st.form_submit_button("💾 บันทึก"):
                                    # ใช้ selected_prod_id ในการบันทึก
                                    supabase.table("jig_usage_log").insert({
                                        "product_id": selected_prod_id, 
                                        "jig_id": jig_id, 
                                        "color": sel_c_new, 
                                        "tank_id": filtered_tanks[sel_tank_name], 
                                        "total_pieces": total_pcs, 
                                        "total_volume": total_vol, 
                                        "recorded_date": datetime.now(ICT).isoformat()
                                    }).execute()
                                    
                                    supabase.table("jig_status").upsert({
                                        "jig_id": jig_id, 
                                        "status_type": "In-Process", 
                                        "current_tank_id": filtered_tanks[sel_tank_name], 
                                        "updated_at": datetime.now(ICT).isoformat()
                                    }).execute()
                                    
                                    st.success("บันทึกสำเร็จ")
                                    st.rerun()
                    elif action == "🟢 เสร็จสิ้นงาน":
                        if st.button("🏁 ยืนยันเสร็จสิ้นงาน"):
                            supabase.table("jig_status").upsert({"jig_id": jig_id, "status_type": "Finished", "current_tank_id": None, "updated_at": datetime.now(ICT).isoformat()}).execute()
                            st.success("งานเสร็จสิ้น")
                            st.rerun()
