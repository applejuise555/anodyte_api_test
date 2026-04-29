import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timezone, timedelta
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
# 1. ตั้งค่า Timezone (UTC +7)
ICT = timezone(timedelta(hours=7))
st.set_page_config(page_title="SCADA Dashboard", layout="wide")

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

st.set_page_config(page_title="Production Log System", layout="wide")

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

menu = st.sidebar.radio("เมนู", ["Dashboard","บันทึกข้อมูลการผลิต"])

if menu == "Dashboard":

    import plotly.graph_objects as go

    st.title("🖥️ SCADA Production Monitoring")

    # ================= STANDARD =================
    PH_MIN, PH_MAX = 5.0, 6.0
    TEMP_COLOR_MIN, TEMP_COLOR_MAX = 30, 40
    TEMP_ANO_MIN, TEMP_ANO_MAX = 18, 22

    # ================= LOAD =================
    # ================= LOAD =================
@st.cache_data(ttl=10)
def load_color():
    return supabase.table("color_tank_logs")\
        .select("*").order("recorded_at", desc=True).limit(200).execute().data

@st.cache_data(ttl=10)
def load_ano():
    return supabase.table("anodize_tank_logs")\
        .select("*").order("recorded_at", desc=True).limit(200).execute().data

@st.cache_data(ttl=60)
def load_tanks():
    return get_options("tanks", "tank_id", "tank_name")

tank_map = load_tanks()
inv = {v: k for k, v in tank_map.items()}

logs_c = load_color()
logs_a = load_ano()

# ================= DATAFRAME =================
df_c = pd.DataFrame(logs_c) if logs_c else pd.DataFrame()
df_a = pd.DataFrame(logs_a) if logs_a else pd.DataFrame()

# 🔥 FIX TYPE + TIMEZONE
if not df_c.empty:
    df_c["recorded_at"] = pd.to_datetime(df_c["recorded_at"], errors="coerce")
    df_c = df_c.dropna(subset=["recorded_at"])
    df_c["recorded_at"] = df_c["recorded_at"].dt.tz_localize(None)  # กัน timezone เพี้ยน
    df_c["tank_name"] = df_c["tank_id"].map(inv)
    latest_c = df_c.sort_values("recorded_at", ascending=False).drop_duplicates("tank_id")
else:
    latest_c = pd.DataFrame()

if not df_a.empty:
    df_a["recorded_at"] = pd.to_datetime(df_a["recorded_at"], errors="coerce")
    df_a = df_a.dropna(subset=["recorded_at"])
    df_a["recorded_at"] = df_a["recorded_at"].dt.tz_localize(None)
    df_a["tank_name"] = df_a["tank_id"].map(inv)
    latest_a = df_a.sort_values("recorded_at", ascending=False).drop_duplicates("tank_id")
else:
    latest_a = pd.DataFrame()

# =========================================================
# ================= TREND PANEL ============================
# =========================================================
st.markdown("---")
st.subheader("📈 Trend Analysis")

if not df_c.empty:

    col1, col2 = st.columns([1,3])

    with col1:
        hours = st.selectbox("ย้อนหลัง (ชั่วโมง)", [1, 6, 12, 24], index=1)
        selected_tank = st.selectbox("เลือกบ่อ", ["ทั้งหมด"] + list(df_c["tank_name"].dropna().unique()))

    # 🔥 filter เวลา
    cutoff = datetime.now() - timedelta(hours=hours)
    trend = df_c[df_c["recorded_at"] >= cutoff]

    # 🔥 filter tank
    if selected_tank != "ทั้งหมด":
        trend = trend[trend["tank_name"] == selected_tank]

    if not trend.empty:

        fig = go.Figure()

        # Temp
        fig.add_trace(go.Scatter(
            x=trend["recorded_at"],
            y=trend["temperature"],
            name="Temp",
            mode="lines",
            line=dict(color="#3b82f6", width=3)
        ))

        # pH
        fig.add_trace(go.Scatter(
            x=trend["recorded_at"],
            y=trend["ph_value"],
            name="pH",
            mode="lines",
            line=dict(color="#22c55e", width=2)
        ))

        # 🔥 เส้นมาตรฐาน (SCADA style)
        fig.add_hline(y=TEMP_COLOR_MIN, line_dash="dash", line_color="red")
        fig.add_hline(y=TEMP_COLOR_MAX, line_dash="dash", line_color="red")

        fig.update_layout(
            title="Trend Monitoring",
            xaxis_title="Time",
            yaxis_title="Value",
            hovermode="x unified"
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("ไม่มีข้อมูลในช่วงเวลานี้")

        # =========================================================
    # ================= ANODIZE =================
    # =========================================================
    st.markdown("---")
    st.subheader("🧪 Anodize Tanks (Smart Monitoring)")

    logs_a = load_anodize_logs()

    if logs_a:
        df_a = pd.DataFrame(logs_a)
        df_a["recorded_at"] = pd.to_datetime(df_a["recorded_at"])

        tank_map = load_tanks()
        inv = {v: k for k, v in tank_map.items()}
        df_a["tank_name"] = df_a["tank_id"].map(inv)

        latest = df_a.drop_duplicates("tank_id")

        alerts = []

        ph_colors, temp_colors, den_colors = [], [], []

        for _, row in latest.iterrows():

            # pH
            if PH_MIN <= row["ph_value"] <= PH_MAX:
                ph_colors.append("#22c55e")
            else:
                ph_colors.append("#ef4444")
                alerts.append(f"{row['tank_name']} → pH ผิด ({row['ph_value']:.2f})")

            # Temp
            if TEMP_ANO_MIN <= row["temperature"] <= TEMP_ANO_MAX:
                temp_colors.append("#3b82f6")
            else:
                temp_colors.append("#ef4444")
                alerts.append(f"{row['tank_name']} → Temp ผิด ({row['temperature']:.1f})")

            # Density
            den_colors.append("#a855f7")

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=latest["tank_name"],
            y=latest["ph_value"],
            name="pH",
            marker_color=ph_colors
        ))

        fig.add_trace(go.Bar(
            x=latest["tank_name"],
            y=latest["temperature"],
            name="Temperature",
            marker_color=temp_colors
        ))

        fig.add_trace(go.Bar(
            x=latest["tank_name"],
            y=latest["density"],
            name="Density",
            marker_color=den_colors
        ))

        fig.update_layout(barmode="group")

        st.plotly_chart(fig, use_container_width=True)

        if alerts:
            st.error("🚨 พบค่าผิดปกติในบ่ออโนไดซ์")
            for a in alerts:
                st.write("•", a)
        else:
            st.success("✅ ทุกบ่ออยู่ในมาตรฐาน")

    else:
        st.info("ไม่มีข้อมูล Anodize")



    # =========================================================
    # ================= AUTO REFRESH ===========================
    # =========================================================
    st_autorefresh(interval=10000, key="refresh")

# ================= RECORD PAGE =================
elif menu == "บันทึกข้อมูลการผลิต":
    st.title("ระบบบันทึกข้อมูลการผลิต")
    
    tab1, tab2, tab3 = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig)"])

    with tab1:
        st.header("บันทึกข้อมูลบ่อสี")
        color_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")
        if color_tanks:
            selected_tank_name = st.selectbox("เลือกบ่อสี", list(color_tanks.keys()), key="tank_select_t1")
            detected_color = TANK_COLOR_MAP.get(selected_tank_name, "Black")
            st.write(f"ระบบตรวจพบสี: **{detected_color}**")
            render_color_bar(detected_color)
            
            with st.form("color_log_form", clear_on_submit=True):
                ph = st.number_input("ค่า pH", step=0.1)
                temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
                if st.form_submit_button("บันทึกค่ามาตรฐาน"):
                    try:
                        supabase.table("color_tank_logs").insert({
                            "tank_id": color_tanks[selected_tank_name], 
                            "ph_value": ph, 
                            "temperature": temp, 
                            "recorded_at": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("บันทึกสำเร็จ")
                    except Exception as e:
                        st.error(f"Error: {e}")

    with tab2:
        st.header("บันทึกข้อมูลบ่ออโนไดซ์")
        anodize_tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Anodize")
        if anodize_tanks:
            selected_tank_name = st.selectbox("เลือกบ่ออโนไดซ์", list(anodize_tanks.keys()))
            with st.form("anodize_log_form", clear_on_submit=True):
                ph = st.number_input("ค่า pH", step=0.1)
                temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
                density = st.number_input("ความหนาแน่น (Density)", step=0.001, format="%.3f")
                if st.form_submit_button("บันทึก"):
                    try:
                        supabase.table("anodize_tank_logs").insert({
                            "tank_id": anodize_tanks[selected_tank_name], 
                            "ph_value": ph, 
                            "temperature": temp, 
                            "density": density, 
                            "recorded_at": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("บันทึกสำเร็จ")
                    except Exception as e:
                        st.error(f"Error: {e}")

    with tab3:
        sub_prod, sub_jig, sub_log = st.tabs(["1. ลงทะเบียนชิ้นงาน", "2. ลงทะเบียนจิ๊ก", "3. บันทึกผลผลิต"])
        
        with sub_prod:
            with st.form("add_prod_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    p_code = st.text_input("รหัสสินค้า (Product Code)")
                    p_name = st.text_input("ชื่อ/รายละเอียดสินค้า")
                    height = st.number_input("ความสูง (Height)", step=0.01)
                    width = st.number_input("ความว้าง (Width)", step=0.01)
                    thickness = st.number_input("ความหนา (Thickness)", step=0.01)
                with col2:
                    depth = st.number_input("ความลึก (Depth)", step=0.01)
                    outer_d = st.number_input("Outer Diameter", step=0.01)
                    inner_d = st.number_input("Inner Diameter", step=0.01)
                    s_finish = st.text_input("พื้นผิว (Surface Finish)")
                
                if st.form_submit_button("ลงทะเบียนชิ้นงาน"):
                    if not p_code or not p_name:
                        st.error("กรุณากรอก รหัสสินค้า และ ชื่อสินค้า")
                    else:
                        try:
                            supabase.table("products").insert({
                                "product_code": p_code, "product_name": p_name,
                                "height": height, "width": width, "thickness": thickness,
                                "depth": depth, "outer_diameter": outer_d, 
                                "inner_diameter": inner_d, "surface_finish": s_finish
                            }).execute()
                            st.success("ลงทะเบียนชิ้นงานสำเร็จ")
                        except Exception as e:
                            st.error(f"Error: {e}")

        with sub_jig:
            with st.form("add_jig_form", clear_on_submit=True):
                j_code = st.text_input("รหัสจิ๊ก")
                if st.form_submit_button("ลงทะเบียนจิ๊ก"):
                    if not j_code:
                        st.error("กรุณากรอกรหัสจิ๊ก")
                    else:
                        try:
                            supabase.table("jigs").insert({
                                "jig_model_code": j_code, 
                                "total_pcs_in_jig": 0
                            }).execute()
                            st.success("ลงทะเบียนจิ๊กสำเร็จ")
                        except Exception as e:
                            st.error(f"Error: {e}")

        with sub_log:
            prods = get_options("products", "product_id", "product_code")
            
            jigs_data_res = supabase.table("jigs").select("jig_id, jig_model_code").execute()
            jigs_data = jigs_data_res.data
            available_jigs = []
            for j in jigs_data:
                status_res = supabase.table("jig_status").select("status_type").eq("jig_id", j["jig_id"]).order("updated_at", desc=True).limit(1).execute()
                latest_status = status_res.data[0].get("status_type", "Available") if (status_res.data and len(status_res.data) > 0) else "Available"
                if latest_status != "Finished":
                    available_jigs.append(j)
            
            jig_map = {j['jig_model_code']: j['jig_id'] for j in available_jigs}
            color_tanks_all = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")

            if prods and jigs_data and color_tanks_all:
                sel_j = st.selectbox("เลือกจิ๊ก", list(jig_map.keys()))
                if sel_j in jig_map:
                    jig_id = jig_map[sel_j]
                    sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))
                    
                    status_res = supabase.table("jig_status").select("status_type").eq("jig_id", jig_id).order("updated_at", desc=True).limit(1).execute()
                    status = status_res.data[0].get("status_type", "Available") if (status_res.data and len(status_res.data) > 0) else "Available"

                    if status == "In-Process":
                        last_log = supabase.table("jig_usage_log").select("color, tank_id").eq("jig_id", jig_id).order("recorded_date", desc=True).limit(1).execute()
                        current_color = last_log.data[0]['color'] if last_log.data else "ไม่ระบุ"
                        st.warning(f"⚠️ กำลังผลิต | สี: **{current_color}**")
                        
                        with st.form("add_more_batch_form", clear_on_submit=True):
                            pcs = st.number_input("จำนวนต่อแถว", min_value=0)
                            rows = st.number_input("แถวที่เต็ม", min_value=0)
                            partial = st.number_input("เศษ", min_value=0)
                            if st.form_submit_button("บันทึกเพิ่ม"):
                                try:
                                    supabase.table("jig_usage_log").insert({
                                        "product_id": prods[sel_p], "jig_id": jig_id, "color": current_color, 
                                        "tank_id": last_log.data[0]['tank_id'], "pcs_per_row": pcs, "rows_filled": rows, 
                                        "partial_pieces": partial, "total_pieces": (rows * pcs) + partial, 
                                        "recorded_date": datetime.now(ICT).isoformat()
                                    }).execute()
                                    st.success("บันทึกสำเร็จ!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        
                        if st.button("🏁 เสร็จสิ้นงาน"):
                            try:
                                supabase.table("jig_status").upsert({
                                    "jig_id": jig_id, 
                                    "status_type": "Finished", 
                                    "current_tank_id": None, 
                                    "updated_at": datetime.now(ICT).isoformat()
                                }).execute()
                                st.success("ปิดงานสำเร็จ!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                    else:
                        st.info("✅ จิ๊กว่าง - เริ่มรอบใหม่")
                        sel_c_new = st.selectbox("เลือกสี", options=sorted(list(set(TANK_COLOR_MAP.values()))))
                        render_color_bar(sel_c_new)
                        filtered_tanks = {name: id for name, id in color_tanks_all.items() if TANK_COLOR_MAP.get(name) == sel_c_new}
                        
                        if filtered_tanks:
                            sel_tank_name = st.selectbox("เลือกบ่อสี", list(filtered_tanks.keys()))
                            sel_tank_id = filtered_tanks[sel_tank_name]
                            
                            with st.form("new_cycle_form", clear_on_submit=True):
                                pcs = st.number_input("จำนวนต่อแถว", min_value=0)
                                rows = st.number_input("แถวที่เต็ม", min_value=0)
                                partial = st.number_input("เศษ", min_value=0)
                                
                                if st.form_submit_button("เริ่มผลิต"):
                                    try:
                                        supabase.table("jig_usage_log").insert({
                                            "product_id": prods[sel_p], "jig_id": jig_id, "color": sel_c_new, 
                                            "tank_id": sel_tank_id, "pcs_per_row": pcs, "rows_filled": rows, 
                                            "partial_pieces": partial, "total_pieces": (rows * pcs) + partial, 
                                            "recorded_date": datetime.now(ICT).isoformat()
                                        }).execute()

                                        supabase.table("jig_status").upsert({
                                            "jig_id": jig_id, 
                                            "status_type": "In-Process", 
                                            "current_tank_id": sel_tank_id, 
                                            "updated_at": datetime.now(ICT).isoformat()
                                        }).execute()

                                        st.success("เริ่มสำเร็จ!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
