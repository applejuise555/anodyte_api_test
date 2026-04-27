import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta

# ==============================
# TIMEZONE
# ==============================
ICT = timezone(timedelta(hours=7))

# ==============================
# COLOR MAP
# ==============================
COLOR_HEX_MAP = {
    "Black": "#000000", "Red": "#FF0000", "Dark Red": "#8B0000", 
    "Violet": "#9400D3", "Green": "#008000", "Banana leaf Green": "#90EE90", 
    "Gold": "#FFD700", "Orange": "#FFA500", "Light Blue": "#ADD8E6", 
    "Blue": "#0000FF", "Dark Blue": "#00008B", "Pink": "#FFC0CB", 
    "Copper": "#B87333", "Titanium": "#808080", "Dark Titanium": "#4A4E69", 
    "Rose Gold": "#B76E79"
}

def get_hex_from_name(name):
    for c in sorted(COLOR_HEX_MAP.keys(), key=len, reverse=True):
        if c.lower() in str(name).lower():
            return COLOR_HEX_MAP[c]
    return "#CCCCCC"

def render_color_bar(name):
    st.markdown(f"""
        <div style="background:{get_hex_from_name(name)};
        height:20px;border-radius:5px;margin-bottom:10px;"></div>
    """, unsafe_allow_html=True)

# ==============================
# CONNECT DB
# ==============================
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"เชื่อมต่อฐานข้อมูลไม่ได้: {e}")
    st.stop()

def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    q = supabase.table(table).select(f"{id_col},{name_col}")
    if filter_col:
        q = q.eq(filter_col, filter_val)
    res = q.execute()
    return {i[name_col]: i[id_col] for i in res.data}

# ==============================
# UI
# ==============================
st.set_page_config(page_title="Production Log System", layout="wide")
st.title("📊 ระบบบันทึกข้อมูลการผลิต")

tab1, tab2, tab3 = st.tabs(["🎨 บ่อสี", "⚙️ บ่ออโนไดซ์", "🧩 งานจิ๊ก"])

# ==============================
# TAB 1: COLOR
# ==============================
with tab1:
    st.header("บันทึกค่าบ่อสี")

    color_tanks = get_options("tanks","tank_id","tank_name","tank_type","Color")

    if color_tanks:
        sel = st.selectbox("เลือกบ่อสี", list(color_tanks.keys()))

        with st.form("color_std"):
            ph = st.number_input("ค่า pH")
            temp = st.number_input("อุณหภูมิ (°C)")
            if st.form_submit_button("💾 บันทึกค่ามาตรฐาน"):
                supabase.table("color_tank_logs").insert({
                    "tank_id": color_tanks[sel],
                    "ph_value": ph,
                    "temperature": temp,
                    "recorded_at": datetime.now(ICT).isoformat()
                }).execute()
                st.success("บันทึกสำเร็จ")

        with st.expander("📈 บันทึกอุณหภูมิแบบความถี่สูง"):
            with st.form("color_hf"):
                target = st.number_input("อุณหภูมิเป้าหมาย")
                actual = st.number_input("อุณหภูมิจริง")

                if st.form_submit_button("💾 บันทึก"):
                    supabase.table("temp_frequent_logs").insert({
                        "tank_id": color_tanks[sel],
                        "temp_target": target,
                        "temp_actual": actual,
                        "recorded_at": datetime.now(ICT).isoformat()
                    }).execute()
                    st.success("บันทึกสำเร็จ")

# ==============================
# TAB 2: ANODIZE
# ==============================
with tab2:
    st.header("บันทึกค่าบ่ออโนไดซ์")

    anodize = get_options("tanks","tank_id","tank_name","tank_type","Anodize")

    if anodize:
        sel = st.selectbox("เลือกบ่ออโนไดซ์", list(anodize.keys()))

        with st.form("ano_std"):
            ph = st.number_input("ค่า pH")
            temp = st.number_input("อุณหภูมิ (°C)")
            den = st.number_input("Density")

            if st.form_submit_button("💾 บันทึกค่ามาตรฐาน"):
                supabase.table("anodize_tank_logs").insert({
                    "tank_id": anodize[sel],
                    "ph_value": ph,
                    "temperature": temp,
                    "density": den,
                    "recorded_at": datetime.now(ICT).isoformat()
                }).execute()
                st.success("บันทึกสำเร็จ")

        with st.expander("📈 บันทึกอุณหภูมิแบบความถี่สูง"):
            with st.form("ano_hf"):
                target = st.selectbox("อุณหภูมิเป้าหมาย", [18,20,22])
                actual = st.number_input("อุณหภูมิจริง")

                if st.form_submit_button("💾 บันทึก"):
                    supabase.table("temp_frequent_logs").insert({
                        "tank_id": anodize[sel],
                        "temp_target": target,
                        "temp_actual": actual,
                        "recorded_at": datetime.now(ICT).isoformat()
                    }).execute()
                    st.success("บันทึกสำเร็จ")

# ==============================
# TAB 3: JIG
# ==============================
with tab3:

    sub_prod, sub_jig, sub_log = st.tabs([
        "📦 ลงทะเบียนสินค้า",
        "🧰 ลงทะเบียนจิ๊ก",
        "📊 บันทึกผลผลิต"
    ])

    # ==========================
    # PRODUCT (เพิ่มรายละเอียดแล้ว)
    # ==========================
    with sub_prod:
        with st.form("add_product", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                code = st.text_input("รหัสสินค้า")
                name = st.text_input("ชื่อสินค้า")
                height = st.number_input("ความสูง", step=0.01)
                width = st.number_input("ความกว้าง", step=0.01)
                thickness = st.number_input("ความหนา", step=0.01)

            with col2:
                depth = st.number_input("ความลึก", step=0.01)
                outer_d = st.number_input("Outer Diameter", step=0.01)
                inner_d = st.number_input("Inner Diameter", step=0.01)
                surface = st.text_input("Surface Finish")

            if st.form_submit_button("💾 บันทึกสินค้า"):
                if not code or not name:
                    st.error("กรุณากรอกรหัสสินค้าและชื่อสินค้า")
                else:
                    supabase.table("products").insert({
                        "product_code": code,
                        "product_name": name,
                        "height": height,
                        "width": width,
                        "thickness": thickness,
                        "depth": depth,
                        "outer_diameter": outer_d,
                        "inner_diameter": inner_d,
                        "surface_finish": surface
                    }).execute()
                    st.success("บันทึกสินค้าเรียบร้อย")

    # ==========================
    # JIG
    # ==========================
    with sub_jig:
        with st.form("add_jig"):
            code = st.text_input("รหัสจิ๊ก")

            if st.form_submit_button("💾 บันทึกจิ๊ก"):
                supabase.table("jigs").insert({
                    "jig_model_code": code
                }).execute()
                st.success("บันทึกจิ๊กสำเร็จ")

    # ==========================
    # LOG
    # ==========================
    with sub_log:
        prods = get_options("products","product_id","product_code")
        jigs = supabase.table("jigs").select("*").execute().data

        if prods and jigs:
            sel_j = st.selectbox("เลือกจิ๊ก", [j["jig_model_code"] for j in jigs])
            jig_id = next(j["jig_id"] for j in jigs if j["jig_model_code"] == sel_j)

            sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))

            with st.form("log"):
                pcs = st.number_input("จำนวนต่อแถว")
                rows = st.number_input("จำนวนแถว")
                partial = st.number_input("เศษ")

                if st.form_submit_button("💾 บันทึกผลผลิต"):
                    supabase.table("jig_usage_log").insert({
                        "product_id": prods[sel_p],
                        "jig_id": jig_id,
                        "total_pieces": (pcs*rows)+partial,
                        "recorded_date": datetime.now(ICT).isoformat()
                    }).execute()

                    st.success("บันทึกข้อมูลเรียบร้อย")
