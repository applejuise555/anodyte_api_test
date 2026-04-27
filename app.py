import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta

# ---------------------------
# CONFIG
# ---------------------------
ICT = timezone(timedelta(hours=7))

st.set_page_config(page_title="Production Log System", layout="wide")

# ---------------------------
# CONNECT DB (Fail-safe)
# ---------------------------
@st.cache_resource
def init_db():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ DB Connection Error: {e}")
        st.stop()

supabase = init_db()

# ---------------------------
# UTIL SAFE QUERY
# ---------------------------
def safe_insert(table, payload):
    try:
        res = supabase.table(table).insert(payload).execute()
        if not res.data:
            raise Exception("Insert failed")
        return True
    except Exception as e:
        st.error(f"❌ บันทึกไม่สำเร็จ: {e}")
        return False

def safe_fetch(query):
    try:
        return query.execute().data
    except:
        return []

# ---------------------------
# COLOR MAP (STRICT MODE)
# ---------------------------
TANK_COLOR_MAP = {
    "4DarkBlue": "Dark Blue",
    "16Blue": "Blue",
    "1DarkRedA": "Dark Red",
    "1DarkRedB": "Dark Red",
}

def get_color_safe(tank_name):
    if tank_name not in TANK_COLOR_MAP:
        st.error(f"❌ Tank {tank_name} ไม่มี mapping สี")
        st.stop()
    return TANK_COLOR_MAP[tank_name]

# ---------------------------
# INPUT VALIDATION
# ---------------------------
def validate_range(label, value, min_v, max_v):
    if value < min_v or value > max_v:
        st.error(f"{label} ต้องอยู่ระหว่าง {min_v} - {max_v}")
        return False
    return True

# ---------------------------
# JIG STATUS (ANTI RACE)
# ---------------------------
def get_latest_jig_status(jig_id):
    data = safe_fetch(
        supabase.table("jig_status")
        .select("status_type")
        .eq("jig_id", jig_id)
        .order("updated_at", desc=True)
        .limit(1)
    )
    return data[0]["status_type"] if data else "Available"

# ---------------------------
# UI
# ---------------------------
st.title("🏭 Production System (Poka-Yoke Edition)")

# ---------------------------
# LOAD DATA
# ---------------------------
products = safe_fetch(supabase.table("products").select("product_id, product_code"))
jigs = safe_fetch(supabase.table("jigs").select("jig_id, jig_model_code"))
tanks = safe_fetch(supabase.table("tanks").select("tank_id, tank_name"))

if not products or not jigs or not tanks:
    st.warning("⚠️ ข้อมูลไม่ครบ")
    st.stop()

prod_map = {p["product_code"]: p["product_id"] for p in products}
jig_map = {j["jig_model_code"]: j["jig_id"] for j in jigs}
tank_map = {t["tank_name"]: t["tank_id"] for t in tanks}

# ---------------------------
# SELECT
# ---------------------------
sel_jig_code = st.selectbox("เลือกจิ๊ก", list(jig_map.keys()))
jig_id = jig_map[sel_jig_code]

# 🔥 RE-CHECK STATUS ทุกครั้ง (กัน race)
status = get_latest_jig_status(jig_id)

st.info(f"สถานะปัจจุบัน: {status}")

# ---------------------------
# CASE 1: IN PROCESS
# ---------------------------
if status == "In-Process":

    last_log = safe_fetch(
        supabase.table("jig_usage_log")
        .select("color, tank_id")
        .eq("jig_id", jig_id)
        .order("recorded_date", desc=True)
        .limit(1)
    )

    if not last_log:
        st.error("❌ ไม่พบข้อมูลก่อนหน้า")
        st.stop()

    current_color = last_log[0]["color"]
    tank_id = last_log[0]["tank_id"]

    st.warning(f"กำลังผลิต | สี: {current_color}")

    with st.form("add_batch"):

        pcs = st.number_input("ชิ้น/แถว", min_value=1)
        rows = st.number_input("จำนวนแถว", min_value=1)
        partial = st.number_input("เศษ", min_value=0)

        total = pcs * rows + partial
        st.info(f"รวม = {total} ชิ้น")

        confirm = st.checkbox("ยืนยันข้อมูลถูกต้อง")

        submit = st.form_submit_button("เพิ่ม Batch")

        if submit:

            if not confirm:
                st.warning("⚠️ กรุณายืนยันก่อนบันทึก")
                st.stop()

            # 🔥 RE-CHECK (กัน race)
            if get_latest_jig_status(jig_id) != "In-Process":
                st.error("❌ สถานะเปลี่ยนแล้ว")
                st.stop()

            success = safe_insert("jig_usage_log", {
                "product_id": None,
                "jig_id": jig_id,
                "color": current_color,
                "tank_id": tank_id,
                "pcs_per_row": pcs,
                "rows_filled": rows,
                "partial_pieces": partial,
                "total_pieces": total,
                "recorded_date": datetime.now(ICT).isoformat()
            })

            if success:
                st.success("✅ เพิ่ม Batch สำเร็จ")
                st.rerun()

    # FINISH BUTTON
    if st.checkbox("ยืนยันปิดงาน"):
        if st.button("🏁 Finish"):

            if get_latest_jig_status(jig_id) != "In-Process":
                st.error("❌ สถานะเปลี่ยนแล้ว")
                st.stop()

            safe_insert("jig_status", {
                "jig_id": jig_id,
                "status_type": "Finished",
                "updated_at": datetime.now(ICT).isoformat()
            })

            st.success("ปิดงานแล้ว")
            st.rerun()

# ---------------------------
# CASE 2: AVAILABLE
# ---------------------------
else:

    st.success("จิ๊กว่าง")

    sel_prod = st.selectbox("เลือกสินค้า", list(prod_map.keys()))
    sel_tank = st.selectbox("เลือกบ่อ", list(tank_map.keys()))

    # 🔥 SAFE COLOR
    color = get_color_safe(sel_tank)

    with st.form("start_job"):

        pcs = st.number_input("ชิ้น/แถว", min_value=1)
        rows = st.number_input("แถว", min_value=1)
        partial = st.number_input("เศษ", min_value=0)

        total = pcs * rows + partial
        st.info(f"รวม = {total} ชิ้น")

        confirm = st.checkbox("ยืนยันเริ่มงาน")

        submit = st.form_submit_button("Start")

        if submit:

            if not confirm:
                st.warning("⚠️ ต้องยืนยันก่อน")
                st.stop()

            # 🔥 FINAL CHECK
            if get_latest_jig_status(jig_id) != "Available":
                st.error("❌ จิ๊กถูกใช้งานแล้ว")
                st.stop()

            safe_insert("jig_usage_log", {
                "product_id": prod_map[sel_prod],
                "jig_id": jig_id,
                "color": color,
                "tank_id": tank_map[sel_tank],
                "pcs_per_row": pcs,
                "rows_filled": rows,
                "partial_pieces": partial,
                "total_pieces": total,
                "recorded_date": datetime.now(ICT).isoformat()
            })

            safe_insert("jig_status", {
                "jig_id": jig_id,
                "status_type": "In-Process",
                "updated_at": datetime.now(ICT).isoformat()
            })

            st.success("🚀 เริ่มงานสำเร็จ")
            st.rerun()
