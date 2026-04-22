import streamlit as st
from supabase import create_client
import datetime

# -------------------------
# ตั้งค่า Page
# -------------------------
st.set_page_config(page_title="Production Log System", layout="wide")
st.title("ระบบบันทึกข้อมูลการผลิต (Full System)")

# -------------------------
# เชื่อมต่อ Supabase
# -------------------------
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"❌ ไม่สามารถเชื่อมต่อ Supabase: {e}")
    st.stop()

# -------------------------
# Helper
# -------------------------
def get_tanks(tank_type):
    try:
        res = supabase.table("tanks").select("tank_id, tank_name").eq("tank_type", tank_type).execute()
        return {i["tank_name"]: i["tank_id"] for i in res.data}
    except Exception as e:
        st.error(f"โหลด tank ไม่ได้: {e}")
        return {}

def get_jigs():
    try:
        res = supabase.table("jigs").select("jig_id, jig_model_code").execute()
        return {i["jig_model_code"]: i["jig_id"] for i in res.data}
    except:
        return {}

# -------------------------
# Tabs
# -------------------------
tab1, tab2, tab3 = st.tabs(["บ่อสี", "บ่ออโนไดซ์", "งานจิ๊ก"])

# =====================================================
# 🟣 TAB 1: COLOR TANK
# =====================================================
with tab1:
    st.header("บันทึกบ่อสี")

    tanks = get_tanks("Color")

    if not tanks:
        st.warning("ไม่มีข้อมูลบ่อสี")
    else:
        sel_tank = st.selectbox("เลือกบ่อ", list(tanks.keys()))

        with st.form("color_form", clear_on_submit=True):
            ph = st.number_input("ค่า pH", format="%.2f")
            temp = st.number_input("อุณหภูมิ (°C)", format="%.2f")

            if st.form_submit_button("บันทึก"):
                supabase.table("color_tank_logs").insert({
                    "tank_id": tanks[sel_tank],
                    "ph_value": ph,
                    "temperature": temp
                }).execute()

                st.success("✅ บันทึกบ่อสีสำเร็จ")

# =====================================================
# 🔵 TAB 2: ANODIZE
# =====================================================
with tab2:
    st.header("บันทึกบ่ออโนไดซ์")

    tanks = get_tanks("Anodize")

    if not tanks:
        st.warning("ไม่มีข้อมูลบ่ออโนไดซ์")
    else:
        sel_tank = st.selectbox("เลือกบ่อ", list(tanks.keys()))

        with st.form("anodize_form", clear_on_submit=True):
            ph = st.number_input("ค่า pH", format="%.2f")
            temp = st.number_input("อุณหภูมิ (°C)", format="%.2f")
            density = st.number_input("ความหนาแน่น", format="%.3f")

            if st.form_submit_button("บันทึก"):
                supabase.table("anodize_tank_logs").insert({
                    "tank_id": tanks[sel_tank],
                    "ph_value": ph,
                    "temperature": temp,
                    "density": density
                }).execute()

                st.success("✅ บันทึกบ่ออโนไดซ์สำเร็จ")

# =====================================================
# 🟢 TAB 3: PRODUCTION
# =====================================================
with tab3:
    st.header("บันทึกผลผลิต")

    jigs = get_jigs()

    if not jigs:
        st.warning("ไม่มีข้อมูล JIG")
    else:
        sel_jig = st.selectbox("เลือก JIG", list(jigs.keys()))

        with st.form("prod_form", clear_on_submit=True):

            col1, col2, col3 = st.columns(3)

            with col1:
                max_rows = st.number_input("จำนวนแถวสูงสุด", min_value=1)

            with col2:
                actual_rows = st.number_input("จำนวนแถวที่ใช้จริง", min_value=0)

            with col3:
                pcs_per_row = st.number_input("จำนวนต่อแถว", min_value=1)

            total = actual_rows * pcs_per_row
            usage = (actual_rows / max_rows * 100) if max_rows else 0

            st.info(f"📦 จำนวนรวม: {total}")
            st.info(f"⚙️ ใช้จิ๊ก: {usage:.2f}%")

            if st.form_submit_button("บันทึก"):
                supabase.table("production_summary").insert({
                    "jig_id": jigs[sel_jig],
                    "total_workpieces": total,
                    "recorded_date": datetime.date.today().isoformat()
                }).execute()

                st.success("✅ บันทึกผลผลิตสำเร็จ")
