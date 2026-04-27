import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta
import pandas as pd
import time

# ==============================
# CONFIG
# ==============================
ICT = timezone(timedelta(hours=7))

st.set_page_config(page_title="Production System", layout="wide")

# ==============================
# CONNECT
# ==============================
@st.cache_resource
def init_conn():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_conn()

# ==============================
# NAVIGATION (สำคัญ)
# ==============================
page = st.sidebar.radio("เมนู", ["📥 Input", "📊 Dashboard"])

# ==============================
# COLOR SYSTEM
# ==============================
COLOR_HEX_MAP = {
    "Black": "#000000","Red": "#FF0000","Dark Red": "#8B0000",
    "Violet": "#9400D3","Green": "#008000","Banana leaf Green": "#90EE90",
    "Gold": "#FFD700","Orange": "#FFA500","Light Blue": "#ADD8E6",
    "Blue": "#0000FF","Dark Blue": "#00008B","Pink": "#FFC0CB",
    "Copper": "#B87333","Titanium": "#808080","Dark Titanium": "#4A4E69",
    "Rose Gold": "#B76E79"
}

def get_hex(name):
    for k in sorted(COLOR_HEX_MAP, key=len, reverse=True):
        if k.lower() in str(name).lower():
            return COLOR_HEX_MAP[k]
    return "#ccc"

def color_bar(name):
    st.markdown(f"<div style='height:20px;background:{get_hex(name)}'></div>", unsafe_allow_html=True)

# ==============================
# UTIL
# ==============================
def now():
    return datetime.now(ICT).isoformat()

def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    q = supabase.table(table).select(f"{id_col},{name_col}")
    if filter_col:
        q = q.eq(filter_col, filter_val)
    res = q.execute()
    return {i[name_col]: i[id_col] for i in res.data}

# =========================================================
# 📥 PAGE 1: INPUT
# =========================================================
if page == "📥 Input":

    st.title("📥 ระบบบันทึกข้อมูลการผลิต")

    tab1, tab2, tab3 = st.tabs(["Color", "Anodize", "Jig"])

    # ---------------- COLOR ----------------
    with tab1:
        st.header("Color Tank")

        TANK_COLOR_MAP = {
            "4DarkBlue": "Dark Blue","16Blue": "Blue","1DarkRedA": "Dark Red",
            "1DarkRedB": "Dark Red","19Copper": "Copper","12Titanium": "Titanium",
            "13DarkTitanium": "Dark Titanium","14RoseGold": "Rose Gold"
        }

        tanks = get_options("tanks","tank_id","tank_name","tank_type","Color")

        if tanks:
            t_name = st.selectbox("เลือกบ่อ", list(tanks.keys()))
            color = TANK_COLOR_MAP.get(t_name,"Black")

            st.write(f"สี: {color}")
            color_bar(color)

            with st.form("color"):
                ph = st.number_input("pH",0.0,14.0)
                temp = st.number_input("Temp",0.0,100.0)

                if st.form_submit_button("Save"):
                    supabase.table("color_tank_logs").insert({
                        "tank_id": tanks[t_name],
                        "ph_value": ph,
                        "temperature": temp,
                        "recorded_at": now()
                    }).execute()
                    st.success("บันทึกแล้ว")

    # ---------------- ANODIZE ----------------
    with tab2:
        st.header("Anodize")

        tanks = get_options("tanks","tank_id","tank_name","tank_type","Anodize")

        if tanks:
            t = st.selectbox("เลือกบ่อ", list(tanks.keys()))

            with st.form("ano"):
                ph = st.number_input("pH",0.0,14.0)
                temp = st.number_input("Temp",0.0,100.0)
                density = st.number_input("Density",0.0,5.0)

                if st.form_submit_button("Save"):
                    supabase.table("anodize_tank_logs").insert({
                        "tank_id": tanks[t],
                        "ph_value": ph,
                        "temperature": temp,
                        "density": density,
                        "recorded_at": now()
                    }).execute()
                    st.success("บันทึกแล้ว")

    # ---------------- JIG ----------------
    with tab3:

        sub1, sub2, sub3 = st.tabs(["Product","Jig","Production"])

        # Product
        with sub1:
            with st.form("prod"):
                code = st.text_input("Code")
                name = st.text_input("Name")

                if st.form_submit_button("Add"):
                    supabase.table("products").insert({
                        "product_code": code,
                        "product_name": name
                    }).execute()
                    st.success("เพิ่มสินค้า")

        # Jig
        with sub2:
            with st.form("jig"):
                j = st.text_input("Jig Code")

                if st.form_submit_button("Add"):
                    supabase.table("jigs").insert({
                        "jig_model_code": j
                    }).execute()
                    st.success("เพิ่มจิ๊ก")

        # Production
        with sub3:

            prods = get_options("products","product_id","product_code")

            jigs = supabase.table("jigs").select("*").execute().data

            jig_map = {j["jig_model_code"]: j["jig_id"] for j in jigs}

            if jig_map:
                sel_j = st.selectbox("Jig", list(jig_map.keys()))
                sel_p = st.selectbox("Product", list(prods.keys()))

                pcs = st.number_input("pcs",1)
                rows = st.number_input("rows",1)

                total = pcs * rows
                st.info(f"Total = {total}")

                if st.button("Start"):
                    supabase.table("jig_usage_log").insert({
                        "jig_id": jig_map[sel_j],
                        "product_id": prods[sel_p],
                        "total_pieces": total,
                        "recorded_date": now()
                    }).execute()

                    st.success("เริ่มผลิต")

# =========================================================
# 📊 PAGE 2: DASHBOARD (Realtime)
# =========================================================
else:

    st.title("📊 Production Dashboard")

    refresh = st.sidebar.slider("Refresh (sec)",1,30,5)

    placeholder = st.empty()

    while True:

        # โหลดข้อมูล
        data = supabase.table("jig_usage_log").select("*").execute().data
        df = pd.DataFrame(data)

        with placeholder.container():

            if not df.empty:

                # KPI
                c1,c2 = st.columns(2)
                c1.metric("Total Pieces", int(df["total_pieces"].sum()))
                c2.metric("Records", len(df))

                # Chart
                st.subheader("Production")
                st.bar_chart(df["total_pieces"])

                # Table
                st.dataframe(df)

            else:
                st.warning("ยังไม่มีข้อมูล")

        time.sleep(refresh)
