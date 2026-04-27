import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta

# ==============================
# CONFIG
# ==============================
ICT = timezone(timedelta(hours=7))

st.set_page_config(page_title="Production Log System", layout="wide")
st.title("ระบบบันทึกข้อมูลการผลิต (Poka-Yoke Edition)")

# ==============================
# SAFE CONNECT
# ==============================
@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception as e:
        st.error(f"❌ DB Connection Failed: {e}")
        st.stop()

supabase = init_connection()

# ==============================
# GLOBAL UTIL (Poka-Yoke Core)
# ==============================
def safe_insert(table, data):
    try:
        res = supabase.table(table).insert(data).execute()
        if not res.data:
            st.error("❌ บันทึกไม่สำเร็จ (DB ไม่ตอบกลับ)")
            return False
        return True
    except Exception as e:
        st.error(f"❌ DB ERROR: {e}")
        return False

def validate_range(value, name, min_v=None, max_v=None):
    if value is None:
        st.error(f"❌ {name} ห้ามว่าง")
        return False
    if min_v is not None and value < min_v:
        st.error(f"❌ {name} ต่ำเกินไป")
        return False
    if max_v is not None and value > max_v:
        st.error(f"❌ {name} สูงเกินไป")
        return False
    return True

def prevent_double_submit(key):
    if st.session_state.get(key):
        st.warning("⚠️ รายการนี้ถูกบันทึกแล้ว")
        return True
    st.session_state[key] = True
    return False

def now():
    return datetime.now(ICT).isoformat()

# ==============================
# COLOR SYSTEM
# ==============================
COLOR_HEX_MAP = {
    "Black": "#000000", "Red": "#FF0000", "Dark Red": "#8B0000",
    "Violet": "#9400D3", "Green": "#008000", "Banana leaf Green": "#90EE90",
    "Gold": "#FFD700", "Orange": "#FFA500", "Light Blue": "#ADD8E6",
    "Blue": "#0000FF", "Dark Blue": "#00008B", "Pink": "#FFC0CB",
    "Copper": "#B87333", "Titanium": "#808080", "Dark Titanium": "#4A4E69",
    "Rose Gold": "#B76E79"
}

def render_color_bar(name):
    hex_code = COLOR_HEX_MAP.get(name)
    if not hex_code:
        st.error("❌ สีไม่ถูกต้อง (Mapping Error)")
        st.stop()

    st.markdown(f"""
    <div style="background:{hex_code};height:20px;border-radius:5px"></div>
    """, unsafe_allow_html=True)

# ==============================
# SAFE QUERY
# ==============================
def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    try:
        q = supabase.table(table).select(f"{id_col},{name_col}")
        if filter_col:
            q = q.eq(filter_col, filter_val)
        res = q.execute()
        return {i[name_col]: i[id_col] for i in res.data}
    except:
        return {}

# ==============================
# TABS
# ==============================
tab1, tab2, tab3 = st.tabs(["Color", "Anodize", "Jig"])

# =========================================================
# TAB 1 COLOR (Enhanced)
# =========================================================
with tab1:
    st.header("Color Tank")

    tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Color")

    if not tanks:
        st.warning("ไม่มีข้อมูลบ่อ")
        st.stop()

    tank = st.selectbox("เลือกบ่อ", list(tanks.keys()))

    # ===== INPUT WITH LIMIT =====
    with st.form("color_form"):
        ph = st.number_input("pH", min_value=0.0, max_value=14.0)
        temp = st.number_input("Temp", min_value=0.0, max_value=100.0)

        total_warning = ""
        if temp > 35:
            total_warning = "🔥 อุณหภูมิสูงผิดปกติ"
            st.error(total_warning)

        confirm = st.checkbox("ยืนยันข้อมูลถูกต้อง")

        if st.form_submit_button("Save"):
            if prevent_double_submit("color_submit"):
                st.stop()

            if not confirm:
                st.error("❌ กรุณายืนยัน")
                st.stop()

            if not validate_range(ph, "pH", 0, 14):
                st.stop()

            if not validate_range(temp, "Temp", 0, 100):
                st.stop()

            ok = safe_insert("color_tank_logs", {
                "tank_id": tanks[tank],
                "ph_value": ph,
                "temperature": temp,
                "recorded_at": now()
            })

            if ok:
                st.success("✅ บันทึกสำเร็จ")

# =========================================================
# TAB 2 ANODIZE
# =========================================================
with tab2:
    st.header("Anodize")

    tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", "Anodize")

    if not tanks:
        st.warning("ไม่มีข้อมูล")
        st.stop()

    tank = st.selectbox("เลือกบ่อ", list(tanks.keys()))

    with st.form("anodize_form"):
        ph = st.number_input("pH", 0.0, 14.0)
        temp = st.number_input("Temp", 0.0, 100.0)
        density = st.number_input("Density", 0.0, 5.0)

        confirm = st.checkbox("ยืนยัน")

        if st.form_submit_button("Save"):
            if prevent_double_submit("ano_submit"):
                st.stop()

            if not confirm:
                st.error("❌ ต้องยืนยัน")
                st.stop()

            if not all([
                validate_range(ph, "pH", 0, 14),
                validate_range(temp, "Temp", 0, 100),
                validate_range(density, "Density", 0, 5)
            ]):
                st.stop()

            ok = safe_insert("anodize_tank_logs", {
                "tank_id": tanks[tank],
                "ph_value": ph,
                "temperature": temp,
                "density": density,
                "recorded_at": now()
            })

            if ok:
                st.success("✅ สำเร็จ")

# =========================================================
# TAB 3 JIG (Critical Poka-Yoke Zone)
# =========================================================
with tab3:
    st.header("Jig System")

    prods = get_options("products", "product_id", "product_code")

    jigs = supabase.table("jigs").select("*").execute().data

    available = []

    for j in jigs:
        res = supabase.table("jig_status")\
            .select("status_type")\
            .eq("jig_id", j["jig_id"])\
            .order("updated_at", desc=True)\
            .limit(1).execute()

        status = res.data[0]["status_type"] if res.data else "Available"

        if status != "Finished":
            available.append(j)

    jig_map = {j["jig_model_code"]: j["jig_id"] for j in available}

    if not jig_map:
        st.warning("ไม่มี jig ว่าง")
        st.stop()

    jig_sel = st.selectbox("เลือก jig", list(jig_map.keys()))
    jig_id = jig_map[jig_sel]

    # 🔴 DOUBLE CHECK STATUS (กัน race)
    res = supabase.table("jig_status")\
        .select("status_type")\
        .eq("jig_id", jig_id)\
        .order("updated_at", desc=True)\
        .limit(1).execute()

    status = res.data[0]["status_type"] if res.data else "Available"

    st.info(f"สถานะ: {status}")

    if status == "In-Process":
        st.warning("กำลังผลิต")

        if st.checkbox("ยืนยันการปิดงาน"):
            if st.button("Finish"):
                safe_insert("jig_status", {
                    "jig_id": jig_id,
                    "status_type": "Finished",
                    "updated_at": now()
                })
                st.success("ปิดงานแล้ว")
                st.rerun()

    else:
        st.success("พร้อมเริ่มงาน")

        pcs = st.number_input("pcs", min_value=1)
        rows = st.number_input("rows", min_value=1)
        partial = st.number_input("partial", min_value=0)

        total = (pcs * rows) + partial
        st.info(f"รวม = {total}")

        confirm = st.checkbox("ยืนยันเริ่มงาน")

        if st.button("Start"):
            if not confirm:
                st.error("ต้องยืนยัน")
                st.stop()

            # 🔴 RECHECK AGAIN (กันชน DB)
            res2 = supabase.table("jig_status")\
                .select("status_type")\
                .eq("jig_id", jig_id)\
                .order("updated_at", desc=True)\
                .limit(1).execute()

            status2 = res2.data[0]["status_type"] if res2.data else "Available"

            if status2 != "Available":
                st.error("❌ jig ถูกใช้ไปแล้ว")
                st.stop()

            safe_insert("jig_usage_log", {
                "jig_id": jig_id,
                "pcs_per_row": pcs,
                "rows_filled": rows,
                "partial_pieces": partial,
                "total_pieces": total,
                "recorded_date": now()
            })

            safe_insert("jig_status", {
                "jig_id": jig_id,
                "status_type": "In-Process",
                "updated_at": now()
            })

            st.success("เริ่มงานสำเร็จ")
            st.rerun()
