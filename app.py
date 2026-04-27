import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta
import pandas as pd
import time

# ==============================
# GLOBAL CONFIG
# ==============================
st.set_page_config(page_title="Production System", layout="wide")

# ==============================
# NAVIGATION
# ==============================
page = st.sidebar.radio("📌 เลือกหน้า", ["📝 Input System", "📊 Dashboard"])

# ==============================
# PAGE 1: INPUT (โค้ดเดิม 100%)
# ==============================
def input_page():

    # 1. ตั้งค่า Timezone
    ICT = timezone(timedelta(hours=7))

    # --- COLOR MAP ---
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

    # --- CONNECT ---
    try:
        supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception as e:
        st.error(f"DB ERROR: {e}")
        return

    def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
        q = supabase.table(table).select(f"{id_col},{name_col}")
        if filter_col:
            q = q.eq(filter_col, filter_val)
        res = q.execute()
        return {i[name_col]: i[id_col] for i in res.data}

    st.title("ระบบบันทึกข้อมูลการผลิต")

    tab1, tab2, tab3 = st.tabs(["Color", "Anodize", "Jig"])

    # =======================
    # TAB 1: COLOR
    # =======================
    with tab1:
        st.header("Color Tank")

        color_tanks = get_options("tanks","tank_id","tank_name","tank_type","Color")

        if color_tanks:
            sel = st.selectbox("เลือกบ่อ", list(color_tanks.keys()))

            with st.form("color_std"):
                ph = st.number_input("pH")
                temp = st.number_input("Temp")
                if st.form_submit_button("Save"):
                    supabase.table("color_tank_logs").insert({
                        "tank_id": color_tanks[sel],
                        "ph_value": ph,
                        "temperature": temp,
                        "recorded_at": datetime.now(ICT).isoformat()
                    }).execute()
                    st.success("Saved")

            # 🔥 HIGH FREQUENCY (เพิ่มแล้ว)
            with st.expander("High Frequency Temp"):
                with st.form("color_hf"):
                    target = st.number_input("Target Temp")
                    actual = st.number_input("Actual Temp")
                    if st.form_submit_button("Save HF"):
                        supabase.table("temp_frequent_logs").insert({
                            "tank_id": color_tanks[sel],
                            "temp_target": target,
                            "temp_actual": actual,
                            "recorded_at": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("HF Saved")

    # =======================
    # TAB 2: ANODIZE
    # =======================
    with tab2:
        st.header("Anodize Tank")

        anodize = get_options("tanks","tank_id","tank_name","tank_type","Anodize")

        if anodize:
            sel = st.selectbox("เลือกบ่อ", list(anodize.keys()))

            with st.form("ano_std"):
                ph = st.number_input("pH")
                temp = st.number_input("Temp")
                den = st.number_input("Density")

                if st.form_submit_button("Save"):
                    supabase.table("anodize_tank_logs").insert({
                        "tank_id": anodize[sel],
                        "ph_value": ph,
                        "temperature": temp,
                        "density": den,
                        "recorded_at": datetime.now(ICT).isoformat()
                    }).execute()
                    st.success("Saved")

            # 🔥 HIGH FREQUENCY (เพิ่มแล้ว)
            with st.expander("High Frequency Temp"):
                with st.form("ano_hf"):
                    target = st.selectbox("Target", [18,20,22])
                    actual = st.number_input("Actual")

                    if st.form_submit_button("Save HF"):
                        supabase.table("temp_frequent_logs").insert({
                            "tank_id": anodize[sel],
                            "temp_target": target,
                            "temp_actual": actual,
                            "recorded_at": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("HF Saved")

    # =======================
    # TAB 3: JIG (คง logic เดิม)
    # =======================
with tab3:
    # 1. ประกาศ Tabs ย่อยภายใต้ Tab 3
    sub_prod, sub_jig, sub_log = st.tabs(["1. ลงทะเบียนชิ้นงาน", "2. ลงทะเบียนจิ๊ก", "3. บันทึกผลผลิต"])
    
    # 2. ส่วนลงทะเบียนชิ้นงาน
    with sub_prod:
        with st.form("add_prod_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                p_code = st.text_input("รหัสสินค้า (Product Code)")
                p_name = st.text_input("ชื่อ/รายละเอียดสินค้า")
                height = st.number_input("ความสูง (Height)", step=0.01)
                width = st.number_input("ความกว้าง (Width)", step=0.01)
                thickness = st.number_input("ความหนา (Thickness)", step=0.01)
            with col2:
                depth = st.number_input("ความลึก (Depth)", step=0.01)
                outer_d = st.number_input("Outer Diameter", step=0.01)
                inner_d = st.number_input("Inner Diameter", step=0.01)
                s_finish = st.text_input("พื้นผิว (Surface Finish)")
                
            if st.form_submit_button("ลงทะเบียนชิ้นงาน"):
                if not p_code or not p_name:
                    st.error("กรุณากรอก รหัสสินค้า และ ชื่อสินค้า ให้ครบถ้วน")
                else:
                    supabase.table("products").insert({
                        "product_code": p_code, "product_name": p_name,
                        "height": height, "width": width, "thickness": thickness,
                        "depth": depth, "outer_diameter": outer_d, 
                        "inner_diameter": inner_d, "surface_finish": s_finish
                    }).execute()
                    st.success("ลงทะเบียนชิ้นงานสำเร็จ")

    # 3. ส่วนลงทะเบียนจิ๊ก
    with sub_jig:
        with st.form("add_jig_form", clear_on_submit=True):
            j_code = st.text_input("รหัสจิ๊ก (Jig Model Code)")
            if st.form_submit_button("ลงทะเบียนจิ๊ก"):
                if not j_code:
                    st.error("กรุณากรอกรหัสจิ๊ก")
                else:
                    supabase.table("jigs").insert({"jig_model_code": j_code}).execute()
                    st.success("ลงทะเบียนจิ๊กสำเร็จ")

# 4. ส่วนบันทึกผลผลิต (ส่วนที่แก้ไข Logic กรองจิ๊กใหม่)
with sub_log:
    prods = get_options("products", "product_id", "product_code")

    # 🔥 ดึง jigs ทั้งหมดก่อน
    jigs = supabase.table("jigs").select("jig_id, jig_model_code").execute().data

    available_jigs = []

    # 🔥 เช็คสถานะล่าสุดทีละตัว
    for j in jigs:
        status_res = supabase.table("jig_status") \
            .select("status_type") \
            .eq("jig_id", j["jig_id"]) \
            .order("updated_at", desc=True) \
            .limit(1) \
            .execute()

        if status_res.data and len(status_res.data) > 0:
            latest_status = status_res.data[0].get("status_type", "Available")
        else:
            latest_status = "Available"

        # ✅ เอาเฉพาะตัวที่ยังไม่ Finished
        if latest_status != "Finished":
            available_jigs.append(j)

    # 🔥 mapping สำหรับ selectbox
    jig_map = {j['jig_model_code']: j['jig_id'] for j in available_jigs}

    color_tanks_all = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")

    if prods and available_jigs and color_tanks_all:
        sel_j = st.selectbox("เลือกจิ๊กที่ใช้งานได้", list(jig_map.keys()))
        jig_id = jig_map[sel_j]

        sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))

        # 🔥 ดึงสถานะล่าสุดของจิ๊กที่เลือก
        status_res = supabase.table("jig_status") \
            .select("status_type") \
            .eq("jig_id", jig_id) \
            .order("updated_at", desc=True) \
            .limit(1) \
            .execute()

        if status_res.data and len(status_res.data) > 0:
            status = status_res.data[0].get("status_type", "Available")
        else:
            status = "Available"

        # -------------------------------
        # 🟡 เคส 1: กำลังผลิต
        # -------------------------------
        if status == "In-Process":
            last_log = supabase.table("jig_usage_log") \
                .select("color, tank_id") \
                .eq("jig_id", jig_id) \
                .order("recorded_date", desc=True) \
                .limit(1) \
                .execute()

            current_color = last_log.data[0]['color'] if last_log.data else "ไม่ระบุ"

            st.warning(f"⚠️ จิ๊กนี้กำลังอยู่ในรอบการผลิต | สี: **{current_color}**")

            with st.form("add_more_batch_form", clear_on_submit=True):
                st.subheader("เพิ่ม Batch งาน")
                pcs = st.number_input("จำนวนต่อแถว", min_value=0)
                rows = st.number_input("แถวที่เต็ม", min_value=0)
                partial = st.number_input("เศษชิ้นงาน", min_value=0)

                if st.form_submit_button("บันทึก Batch งานเพิ่ม"):
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

                    st.success("บันทึกข้อมูลเพิ่มสำเร็จ!")
                    st.rerun()

            if st.button("🏁 เสร็จสิ้นงาน (Finish)"):
                supabase.table("jig_status").insert({
                    "jig_id": jig_id,
                    "status_type": "Finished",
                    "updated_at": datetime.now(ICT).isoformat()
                }).execute()

                st.success("จิ๊กถูกปิดการใช้งานแล้ว!")
                st.rerun()

        # -------------------------------
        # 🟢 เคส 2: ว่าง → เริ่มงานใหม่
        # -------------------------------
        else:
            st.info("✅ จิ๊กว่างอยู่ - เริ่มรอบใหม่")

            unique_colors = list(set(TANK_COLOR_MAP.values()))
            sel_c_new = st.selectbox("เลือกสี", options=sorted(unique_colors))
            render_color_bar(sel_c_new)

            filtered_tanks = {
                name: id for name, id in color_tanks_all.items()
                if TANK_COLOR_MAP.get(name) == sel_c_new
            }

            if filtered_tanks:
                sel_tank_name = st.selectbox("เลือกบ่อสี", list(filtered_tanks.keys()))
                sel_tank_id = filtered_tanks[sel_tank_name]

                with st.form("new_cycle_form", clear_on_submit=True):
                    st.subheader("บันทึก Batch แรก")

                    pcs = st.number_input("จำนวนต่อแถว", min_value=0)
                    rows = st.number_input("แถวที่เต็ม", min_value=0)
                    partial = st.number_input("เศษ", min_value=0)

                    if st.form_submit_button("เริ่มผลิต"):
                        supabase.table("jig_usage_log").insert({
                            "product_id": prods[sel_p],
                            "jig_id": jig_id,
                            "color": sel_c_new,
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

                        st.success("เริ่มการผลิตสำเร็จ!")
                        st.rerun()

    else:
        st.warning("ไม่พบข้อมูลที่จำเป็น")

# ==============================
# PAGE 2: DASHBOARD
# ==============================
def dashboard_page():

    st.title("📊 Dashboard")

    try:
        supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        st.error("DB ERROR")
        return

    refresh = st.sidebar.slider("Refresh",1,30,5)

    def load():
        res = supabase.table("jig_usage_log").select("*").execute()
        return pd.DataFrame(res.data)

    placeholder = st.empty()

    while True:
        df = load()

        with placeholder.container():
            if not df.empty:
                st.metric("Total Pieces", int(df["total_pieces"].sum()))
                st.line_chart(df["total_pieces"])
                st.dataframe(df)
            else:
                st.warning("No Data")

        time.sleep(refresh)

# ==============================
# ROUTER
# ==============================
if page == "📝 Input System":
    input_page()
else:
    dashboard_page()
