import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timezone, timedelta
from streamlit_autorefresh import st_autorefresh

# ================== TIMEZONE ==================
ICT = timezone(timedelta(hours=7))

# ================== CONFIG ==================
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

# ================== PAGE ==================
st.set_page_config(page_title="Production Log System", layout="wide")

# ================== DB ==================
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# ================== HELPER ==================
def get_hex_from_name(name):
    for k in COLOR_HEX_MAP:
        if k.lower() in str(name).lower():
            return COLOR_HEX_MAP[k]
    return "#CCCCCC"

def render_color_bar(name):
    hex_code = get_hex_from_name(name)
    st.markdown(
        f"<div style='background:{hex_code};height:20px;border-radius:5px'></div>",
        unsafe_allow_html=True
    )

def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    query = supabase.table(table).select(f"{id_col}, {name_col}")
    if filter_col and filter_val:
        query = query.eq(filter_col, filter_val)
    res = query.execute()
    return {i[name_col]: i[id_col] for i in res.data}

# ================== MENU ==================
st.sidebar.title("เมนูระบบ")
menu = st.sidebar.radio("เลือกหน้า", ["Dashboard", "บันทึกข้อมูลการผลิต"])

# =========================================================
# ======================= DASHBOARD =======================
# =========================================================
if menu == "Dashboard":
    st.title("📊 Production Dashboard")

    today = datetime.now(ICT).strftime("%Y-%m-%d")

    col1, col2, col3 = st.columns(3)

    active_jigs = supabase.table("jig_status") \
        .select("jig_id") \
        .eq("status_type", "In-Process") \
        .execute()

    col1.metric("🟢 จิ๊กที่กำลังผลิต", len(active_jigs.data))

    today_logs = supabase.table("jig_usage_log") \
        .select("total_pieces") \
        .gte("recorded_date", f"{today}T00:00:00") \
        .execute()

    col2.metric("📦 ผลิตวันนี้", sum(x['total_pieces'] for x in today_logs.data))

    tanks_today = supabase.table("color_tank_logs") \
        .select("tank_id") \
        .gte("recorded_at", f"{today}T00:00:00") \
        .execute()

    col3.metric("🧪 บ่อที่ใช้", len(set(x['tank_id'] for x in tanks_today.data)))

    st.markdown("---")

    # ===== COLOR =====
    st.subheader("🎨 Color Bath")

    logs = supabase.table("color_tank_logs") \
        .select("*") \
        .order("recorded_at", desc=True) \
        .limit(200) \
        .execute()

    if logs.data:
        df = pd.DataFrame(logs.data)
        df['recorded_at'] = pd.to_datetime(df['recorded_at'])

        tank_map = get_options("tanks", "tank_id", "tank_name")
        inv = {v: k for k, v in tank_map.items()}
        df['tank_name'] = df['tank_id'].map(inv)

        latest = df.drop_duplicates("tank_id")

        c1, c2 = st.columns(2)
        c1.bar_chart(latest.set_index('tank_name')['ph_value'])
        c2.bar_chart(latest.set_index('tank_name')['temperature'])

        tank = st.selectbox("เลือกบ่อ", df['tank_name'].unique())
        dff = df[df['tank_name'] == tank]

        st.line_chart(dff.set_index('recorded_at')[['ph_value', 'temperature']])

    # ===== ANODIZE =====
    st.markdown("---")
    st.subheader("⚙️ Anodize")

    logs_a = supabase.table("anodize_tank_logs") \
        .select("*") \
        .order("recorded_at", desc=True) \
        .limit(200) \
        .execute()

    if logs_a.data:
        df = pd.DataFrame(logs_a.data)
        df['recorded_at'] = pd.to_datetime(df['recorded_at'])

        tank_map = get_options("tanks", "tank_id", "tank_name")
        inv = {v: k for k, v in tank_map.items()}
        df['tank_name'] = df['tank_id'].map(inv)

        latest = df.drop_duplicates("tank_id")

        c1, c2, c3 = st.columns(3)
        c1.bar_chart(latest.set_index('tank_name')['ph_value'])
        c2.bar_chart(latest.set_index('tank_name')['temperature'])
        c3.bar_chart(latest.set_index('tank_name')['density'])

    st_autorefresh(interval=10000, key="refresh")

# =========================================================
# ======================= RECORD ==========================
# =========================================================
else:
    st.title("📥 บันทึกข้อมูล")

    tab1, tab2, tab3 = st.tabs(["บ่อสี", "บ่ออโนไดซ์", "งานจิ๊ก"])

    # ================= COLOR =================
    with tab1:
        tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")
        name = st.selectbox("เลือกบ่อสี", list(tanks.keys()))

        color = TANK_COLOR_MAP.get(name, "Black")
        render_color_bar(color)

        with st.form("f1"):
            ph = st.number_input("pH")
            temp = st.number_input("Temp")

            if st.form_submit_button("บันทึก"):
                supabase.table("color_tank_logs").insert({
                    "tank_id": tanks[name],
                    "ph_value": ph,
                    "temperature": temp,
                    "recorded_at": datetime.now(ICT).isoformat()
                }).execute()
                st.success("บันทึกแล้ว")

    # ================= ANODIZE =================
    with tab2:
        tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Anodize")
        name = st.selectbox("เลือกบ่อ", list(tanks.keys()))

        with st.form("f2"):
            ph = st.number_input("pH")
            temp = st.number_input("Temp")
            den = st.number_input("Density")

            if st.form_submit_button("บันทึก"):
                supabase.table("anodize_tank_logs").insert({
                    "tank_id": tanks[name],
                    "ph_value": ph,
                    "temperature": temp,
                    "density": den,
                    "recorded_at": datetime.now(ICT).isoformat()
                }).execute()
                st.success("บันทึกแล้ว")

    # ================= JIG ================
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
                        st.error("กรุณากรอกรหัสสินค้า และ ชื่อสินค้า")
                    else:
                        try:
                            supabase.table("products").insert({
                                "product_code": p_code, 
                                "product_name": p_name, 
                                "height": height, 
                                "width": width, 
                                "thickness": thickness, 
                                "depth": depth, 
                                "outer_diameter": outer_d, 
                                "inner_diameter": inner_d, 
                                "surface_finish": s_finish
                            }).execute()
                            st.success("บันทึกข้อมูลสินค้าสำเร็จ")
                        except Exception as e:
                            st.error(f"Error: {e}")

        with sub_jig:
            with st.form("add_jig_form", clear_on_submit=True):
                jig_m_code = st.text_input("กรุณาตั้งรหัสจิ๊ก เป็น ปปปปดดวว001(จิ๊กที่เท่าไหร่ของวัน) เช่น 20260428001")
                if st.form_submit_button("ลงทะเบียนจิ๊ก"):
                    try:
                        # เพิ่มค่า total_pcs_in_jig เป็น 0 เพื่อแก้ error not-null constraint
                        supabase.table("jigs").insert({
                            "jig_model_code": jig_m_code,
                            "total_pcs_in_jig": 0 
                        }).execute()
                        st.success("ลงทะเบียนจิ๊กสำเร็จ")
                    except Exception as e:
                        st.error(f"Error: {e}")
        with sub_log:

    # ======================
    # โหลดข้อมูลพื้นฐาน
    # ======================
    prods = get_options("products", "product_id", "product_code")

    jigs = supabase.table("jigs") \
        .select("jig_id, jig_model_code") \
        .execute().data

    available_jigs = []

    # ======================
    # เช็คสถานะจิ๊กล่าสุด
    # ======================
    for j in jigs:
        status_res = supabase.table("jig_status") \
            .select("status_type") \
            .eq("jig_id", j["jig_id"]) \
            .order("updated_at", desc=True) \
            .limit(1) \
            .execute()

        if status_res.data:
            latest_status = status_res.data[0].get("status_type", "Available")
        else:
            latest_status = "Available"

        if latest_status != "Finished":
            available_jigs.append(j)

    # ======================
    # Mapping
    # ======================
    jig_map = {j['jig_model_code']: j['jig_id'] for j in available_jigs}

    color_tanks_all = get_options(
        "tanks", "tank_id", "tank_name", "tank_type", "Color"
    )

    # ======================
    # ตรวจว่ามีข้อมูลครบไหม
    # ======================
    if not (prods and available_jigs and color_tanks_all):
        st.warning("⚠️ ไม่พบข้อมูลที่จำเป็น")
        st.stop()

    # ======================
    # เลือกข้อมูล
    # ======================
    sel_j = st.selectbox("🔧 เลือกจิ๊ก", list(jig_map.keys()))
    jig_id = jig_map[sel_j]

    sel_p = st.selectbox("📦 เลือกสินค้า", list(prods.keys()))

    # ======================
    # ดึงสถานะล่าสุด
    # ======================
    status_res = supabase.table("jig_status") \
        .select("status_type") \
        .eq("jig_id", jig_id) \
        .order("updated_at", desc=True) \
        .limit(1) \
        .execute()

    if status_res.data:
        status = status_res.data[0].get("status_type", "Available")
    else:
        status = "Available"

    # ======================
    # 🟡 กำลังผลิต
    # ======================
    if status == "In-Process":

        last_log = supabase.table("jig_usage_log") \
            .select("color, tank_id") \
            .eq("jig_id", jig_id) \
            .order("recorded_date", desc=True) \
            .limit(1) \
            .execute()

        current_color = last_log.data[0]['color'] if last_log.data else "ไม่ระบุ"

        st.warning(f"⚠️ กำลังผลิตอยู่ | สี: **{current_color}**")

        # ➕ เพิ่ม batch
        with st.form("add_batch", clear_on_submit=True):
            st.subheader("➕ เพิ่มงาน")

            pcs = st.number_input("จำนวน/แถว", min_value=0)
            rows = st.number_input("จำนวนแถว", min_value=0)
            partial = st.number_input("เศษ", min_value=0)

            if st.form_submit_button("💾 บันทึก"):
                tank_id = last_log.data[0]['tank_id']

                supabase.table("jig_usage_log").insert({
                    "product_id": prods[sel_p],
                    "jig_id": jig_id,
                    "color": current_color,
                    "tank_id": tank_id,
                    "pcs_per_row": pcs,
                    "rows_filled": rows,
                    "partial_pieces": partial,
                    "total_pieces": (rows * pcs) + partial,
                    "recorded_date": datetime.now(ICT).isoformat()
                }).execute()

                st.success("✅ บันทึกเพิ่มสำเร็จ")
                st.rerun()

        # ✅ ปิดงาน
        if st.button("🏁 จบงาน"):
            supabase.table("jig_status").insert({
                "jig_id": jig_id,
                "status_type": "Finished",
                "updated_at": datetime.now(ICT).isoformat()
            }).execute()

            st.success("✅ ปิดงานเรียบร้อย")
            st.rerun()

    # ======================
    # 🟢 เริ่มงานใหม่
    # ======================
    else:
        st.info("🟢 จิ๊กว่าง → เริ่มงานใหม่")

        unique_colors = list(set(TANK_COLOR_MAP.values()))
        sel_color = st.selectbox("🎨 เลือกสี", sorted(unique_colors))

        render_color_bar(sel_color)

        # filter tank ตามสี
        filtered_tanks = {
            name: id for name, id in color_tanks_all.items()
            if TANK_COLOR_MAP.get(name) == sel_color
        }

        if not filtered_tanks:
            st.warning("ไม่มีบ่อสีสำหรับสีนี้")
            st.stop()

        sel_tank_name = st.selectbox("🧪 เลือกบ่อสี", list(filtered_tanks.keys()))
        sel_tank_id = filtered_tanks[sel_tank_name]

        # ➕ เริ่ม batch แรก
        with st.form("start_job", clear_on_submit=True):
            st.subheader("🚀 เริ่มผลิต")

            pcs = st.number_input("จำนวน/แถว", min_value=0)
            rows = st.number_input("จำนวนแถว", min_value=0)
            partial = st.number_input("เศษ", min_value=0)

            if st.form_submit_button("▶️ เริ่ม"):
                supabase.table("jig_usage_log").insert({
                    "product_id": prods[sel_p],
                    "jig_id": jig_id,
                    "color": sel_color,
                    "tank_id": sel_tank_id,
                    "pcs_per_row": pcs,
                    "rows_filled": rows,
                    "partial_pieces": partial,
                    "total_pieces": (rows * pcs) + partial,
                    "recorded_date": datetime.now(ICT).isoformat()
                }).execute()

                supabase.table("jig_status").insert({
                    "jig_id": jig_id,
                    "status_type": "In-Process",
                    "updated_at": datetime.now(ICT).isoformat()
                }).execute()

                st.success("✅ เริ่มผลิตสำเร็จ")
                st.rerun()
