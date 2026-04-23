import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta

# --- 1. ตั้งค่าพื้นฐาน (ต้องอยู่บนสุด) ---
st.set_page_config(page_title="Production Log System", layout="wide")
ICT = timezone(timedelta(hours=7))

# Initial Session State (ป้องกัน KeyError)
if 'selected_tank_id' not in st.session_state: st.session_state.selected_tank_id = None
if 'selected_tank_name' not in st.session_state: st.session_state.selected_tank_name = None
if 'active_type' not in st.session_state: st.session_state.active_type = None

# --- 2. การเชื่อมต่อ Database ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"เชื่อมต่อ Supabase ล้มเหลว: {e}")

# --- 3. ฟังก์ชันดึงข้อมูลและแสดงผล ---
def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    try:
        query = supabase.table(table).select(f"{id_col}, {name_col}")
        if filter_col and filter_val:
            query = query.eq(filter_col, filter_val)
        response = query.execute()
        return {item[name_col]: item[id_col] for item in response.data}
    except: return {}

def render_tank_grid(tanks_dict, type_label):
    st.subheader(f"📍 {type_label}")
    cols = st.columns(4)
    i = 0
    for name, tid in tanks_dict.items():
        with cols[i % 4]:
            if st.button(f"{name}", key=f"btn_{tid}_{type_label}"):
                st.session_state.selected_tank_id = tid
                st.session_state.selected_tank_name = name
                st.session_state.active_type = type_label
                st.rerun()
        i += 1

# --- 4. ส่วนแสดงผล UI ---
st.title("🏭 ระบบบันทึกข้อมูลการผลิต")

# สร้าง Tabs หลัก
tab1, tab2, tab3 = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig)"])

# --- TAB 1 & 2: ระบบจัดการบ่อ ---
def tank_tab_logic(type_val, log_table):
    if st.session_state.selected_tank_id is None:
        tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", type_val)
        render_tank_grid(tanks, type_val)
    else:
        st.info(f"เลือกบ่อ: **{st.session_state.selected_tank_name}**")
        if st.button("⬅️ กลับไปหน้าเลือกบ่อ"):
            st.session_state.selected_tank_id = None
            st.rerun()
        
        with st.form("tank_log_form"):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            density = st.number_input("ความหนาแน่น", step=0.001, format="%.3f") if type_val == "Anodize" else None
            
            if st.form_submit_button("บันทึกข้อมูล"):
                try:
                    data = {"tank_id": st.session_state.selected_tank_id, "ph_value": ph, "temperature": temp}
                    if density is not None: data["density"] = density
                    supabase.table(log_table).insert(data).execute()
                    st.success("บันทึกสำเร็จ!")
                except Exception as e: st.error(f"Error: {e}")

with tab1: tank_tab_logic("Color", "color_tank_logs")
with tab2: tank_tab_logic("Anodize", "anodize_tank_logs")

# --- TAB 3: งานจิ๊ก ---
with tab3:
    sub1, sub2, sub3 = st.tabs(["1. ลงทะเบียนชิ้นงาน", "2. ลงทะเบียนจิ๊ก", "3. บันทึกผลผลิต"])
    
    with sub1:
        with st.form("prod_form"):
            p_code = st.text_input("รหัสสินค้า")
            p_name = st.text_input("ชื่อชิ้นงาน")
            if st.form_submit_button("บันทึกสินค้า"):
                try:
                    supabase.table("products").insert({"product_code": p_code, "product_name": p_name}).execute()
                    st.success("สำเร็จ")
                except Exception as e: st.error(e)

    with sub2:
        with st.form("jig_form"):
            j_code = st.text_input("รหัสจิ๊ก")
            if st.form_submit_button("บันทึกจิ๊ก"):
                try:
                    supabase.table("jigs").insert({"jig_model_code": j_code}).execute()
                    st.success("สำเร็จ")
                except Exception as e: st.error(e)

    with sub3:
        prods = get_options("products", "product_id", "product_code")
        jigs = get_options("jigs", "jig_id", "jig_model_code")
        if prods and jigs:
            sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))
            sel_j = st.selectbox("เลือกจิ๊ก", list(jigs.keys()))
            with st.form("usage_form"):
                pcs = st.number_input("จำนวน", step=1)
                if st.form_submit_button("บันทึก"):
                    try:
                        supabase.table("jig_usage_log").insert({
                            "product_id": prods[sel_p], "jig_id": jigs[sel_j],
                            "total_pieces": pcs, "recorded_date": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("บันทึกการผลิตสำเร็จ!")
                    except Exception as e: st.error(e)
