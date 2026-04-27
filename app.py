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
# PAGE 1: INPUT
# ==============================
def input_page():

    ICT = timezone(timedelta(hours=7))

    # CONNECT
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

            # STANDARD
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

            # 🔥 HIGH FREQUENCY
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

            # STANDARD
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

            # 🔥 HIGH FREQUENCY
            with st.expander("High Frequency Temp"):
                with st.form("ano_hf"):
                    target = st.selectbox("Target", [18,20,22])
                    actual = st.number_input("Actual Temp")

                    if st.form_submit_button("Save HF"):
                        supabase.table("temp_frequent_logs").insert({
                            "tank_id": anodize[sel],
                            "temp_target": target,
                            "temp_actual": actual,
                            "recorded_at": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("HF Saved")

    # =======================
    # TAB 3: JIG
    # =======================
    with tab3:

        sub_prod, sub_jig, sub_log = st.tabs([
            "1. ลงทะเบียนชิ้นงาน",
            "2. ลงทะเบียนจิ๊ก",
            "3. บันทึกผลผลิต"
        ])

        # PRODUCT
        with sub_prod:
            with st.form("add_prod"):
                code = st.text_input("Product Code")
                name = st.text_input("Product Name")
                if st.form_submit_button("Save"):
                    supabase.table("products").insert({
                        "product_code": code,
                        "product_name": name
                    }).execute()
                    st.success("Saved")

        # JIG
        with sub_jig:
            with st.form("add_jig"):
                code = st.text_input("Jig Code")
                if st.form_submit_button("Save"):
                    supabase.table("jigs").insert({
                        "jig_model_code": code
                    }).execute()
                    st.success("Saved")

        # LOG
        with sub_log:
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

                    if st.form_submit_button("Save"):
                        supabase.table("jig_usage_log").insert({
                            "product_id": prods[sel_p],
                            "jig_id": jig_id,
                            "total_pieces": (pcs*rows)+partial,
                            "recorded_date": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("Saved")


# ==============================
# DASHBOARD
# ==============================
def dashboard_page():

    st.title("📊 Dashboard")

    try:
        supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        st.error("DB ERROR")
        return

    refresh = st.sidebar.slider("Refresh",1,30,5)

    placeholder = st.empty()

    while True:
        df = pd.DataFrame(
            supabase.table("jig_usage_log").select("*").execute().data
        )

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
