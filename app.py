import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta
import pandas as pd
import time

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Production System", layout="wide")

ICT = timezone(timedelta(hours=7))

# ==============================
# CONNECT DB
# ==============================
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"DB ERROR: {e}")
    st.stop()

def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    q = supabase.table(table).select(f"{id_col},{name_col}")
    if filter_col:
        q = q.eq(filter_col, filter_val)
    res = q.execute()
    return {i[name_col]: i[id_col] for i in res.data}

# ==============================
# NAVIGATION
# ==============================
page = st.sidebar.radio("📌 เลือกหน้า", ["📝 Input System", "📊 Dashboard"])

# ==============================
# INPUT PAGE
# ==============================
def input_page():

    st.title("📝 ระบบบันทึกข้อมูลการผลิต")

    tab1, tab2, tab3 = st.tabs(["🎨 บ่อสี", "⚙️ บ่ออโนไดซ์", "🧩 งานจิ๊ก"])

    # ---------------- COLOR ----------------
    with tab1:
        st.header("บันทึกค่าบ่อสี")

        color_tanks = get_options("tanks","tank_id","tank_name","tank_type","Color")

        if color_tanks:
            sel = st.selectbox("เลือกบ่อสี (ค่ามาตรฐาน)", list(color_tanks.keys()))

            # STANDARD
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

            # 🔥 HF (เลือกบ่อแยก)
            st.markdown("---")
            st.subheader("📈 บันทึกอุณหภูมิความถี่สูง (เลือกบ่อแยกได้)")

            hf_tank = st.selectbox(
                "เลือกบ่อสำหรับบันทึก HF",
                list(color_tanks.keys()),
                key="color_hf_tank"
            )

            with st.form("color_hf"):
                target = st.number_input("Target Temp", key="c_target")
                actual = st.number_input("Actual Temp", key="c_actual")

                if st.form_submit_button("💾 บันทึก HF"):
                    supabase.table("temp_frequent_logs").insert({
                        "tank_id": color_tanks[hf_tank],
                        "temp_target": target,
                        "temp_actual": actual,
                        "recorded_at": datetime.now(ICT).isoformat()
                    }).execute()
                    st.success(f"บันทึก HF ที่บ่อ {hf_tank} สำเร็จ")

    # ---------------- ANODIZE ----------------
    with tab2:
        st.header("บันทึกค่าบ่ออโนไดซ์")

        anodize_tanks = get_options("tanks","tank_id","tank_name","tank_type","Anodize")

        if anodize_tanks:
            sel = st.selectbox("เลือกบ่ออโนไดซ์ (ค่ามาตรฐาน)", list(anodize_tanks.keys()))

            # STANDARD
            with st.form("ano_std"):
                ph = st.number_input("ค่า pH")
                temp = st.number_input("อุณหภูมิ (°C)")
                den = st.number_input("Density")

                if st.form_submit_button("💾 บันทึกค่ามาตรฐาน"):
                    supabase.table("anodize_tank_logs").insert({
                        "tank_id": anodize_tanks[sel],
                        "ph_value": ph,
                        "temperature": temp,
                        "density": den,
                        "recorded_at": datetime.now(ICT).isoformat()
                    }).execute()
                    st.success("บันทึกสำเร็จ")

            # 🔥 HF (เลือกบ่อแยก)
            st.markdown("---")
            st.subheader("📈 บันทึกอุณหภูมิความถี่สูง (เลือกบ่อแยกได้)")

            hf_tank = st.selectbox(
                "เลือกบ่อสำหรับบันทึก HF",
                list(anodize_tanks.keys()),
                key="ano_hf_tank"
            )

            with st.form("ano_hf"):
                target = st.selectbox("Target Temp", [18,20,22])
                actual = st.number_input("Actual Temp")

                if st.form_submit_button("💾 บันทึก HF"):
                    supabase.table("temp_frequent_logs").insert({
                        "tank_id": anodize_tanks[hf_tank],
                        "temp_target": target,
                        "temp_actual": actual,
                        "recorded_at": datetime.now(ICT).isoformat()
                    }).execute()
                    st.success(f"บันทึก HF ที่บ่อ {hf_tank} สำเร็จ")

    # ---------------- JIG ----------------
    with tab3:

        sub1, sub2, sub3 = st.tabs(["📦 สินค้า", "🧰 จิ๊ก", "📊 ผลผลิต"])

        # PRODUCT
        with sub1:
            with st.form("prod"):
                code = st.text_input("รหัสสินค้า")
                name = st.text_input("ชื่อสินค้า")

                h = st.number_input("Height")
                w = st.number_input("Width")
                t = st.number_input("Thickness")

                d = st.number_input("Depth")
                od = st.number_input("Outer D")
                id_ = st.number_input("Inner D")

                sf = st.text_input("Surface Finish")

                if st.form_submit_button("💾 บันทึกสินค้า"):
                    supabase.table("products").insert({
                        "product_code": code,
                        "product_name": name,
                        "height": h,
                        "width": w,
                        "thickness": t,
                        "depth": d,
                        "outer_diameter": od,
                        "inner_diameter": id_,
                        "surface_finish": sf
                    }).execute()
                    st.success("บันทึกสินค้าเรียบร้อย")

        # JIG
        with sub2:
            with st.form("jig"):
                code = st.text_input("รหัสจิ๊ก")
                if st.form_submit_button("💾 บันทึก"):
                    supabase.table("jigs").insert({"jig_model_code": code}).execute()
                    st.success("บันทึกจิ๊กสำเร็จ")

        # LOG
        with sub3:
            prods = get_options("products","product_id","product_code")
            jigs = supabase.table("jigs").select("*").execute().data

            if prods and jigs:
                sel_j = st.selectbox("เลือกจิ๊ก", [j["jig_model_code"] for j in jigs])
                jig_id = next(j["jig_id"] for j in jigs if j["jig_model_code"] == sel_j)

                sel_p = st.selectbox("สินค้า", list(prods.keys()))

                with st.form("log"):
                    pcs = st.number_input("pcs")
                    rows = st.number_input("rows")
                    partial = st.number_input("partial")

                    if st.form_submit_button("💾 บันทึก"):
                        supabase.table("jig_usage_log").insert({
                            "product_id": prods[sel_p],
                            "jig_id": jig_id,
                            "total_pieces": (pcs*rows)+partial,
                            "recorded_date": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("บันทึกสำเร็จ")

# ==============================
# DASHBOARD
# ==============================
def dashboard_page():

    st.title("📊 Production Dashboard")

    refresh = st.sidebar.slider("⏱ Refresh (sec)",1,30,5)

    placeholder = st.empty()

    while True:

        df = pd.DataFrame(
            supabase.table("jig_usage_log").select("*").execute().data
        )

        hf = pd.DataFrame(
            supabase.table("temp_frequent_logs").select("*").execute().data
        )

        with placeholder.container():

            if not df.empty:
                col1, col2, col3 = st.columns(3)

                col1.metric("Total Pieces", int(df["total_pieces"].sum()))
                col2.metric("Total Jobs", len(df))
                col3.metric("Avg / Job", int(df["total_pieces"].mean()))

                st.line_chart(df["total_pieces"])
                st.dataframe(df)

            if not hf.empty:
                st.subheader("Temperature Monitoring")
                st.line_chart(hf[["temp_actual","temp_target"]])

        time.sleep(refresh)

# ==============================
# ROUTER
# ==============================
if page == "📝 Input System":
    input_page()
else:
    dashboard_page()
