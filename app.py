import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta

# --- 1. ตั้งค่าพื้นฐาน ---
ICT = timezone(timedelta(hours=7))

# --- 2. Initial Session State (ป้องกัน KeyError) ---
if 'selected_tank_id' not in st.session_state: st.session_state.selected_tank_id = None
if 'selected_tank_name' not in st.session_state: st.session_state.selected_tank_name = None
if 'active_type' not in st.session_state: st.session_state.active_type = None

# --- 3. การตั้งค่าเชื่อมต่อ ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ Supabase: {e}")

# --- 4. ฟังก์ชันสนับสนุน ---
color_hex_map = {
    "Black": "#000000", "Red": "#FF0000", "Violet": "#9400D3", "Green": "#008000",
    "Banana leaf Green": "#90EE90", "Gold": "#FFD700", "Orange": "#FFA500",
    "Light Blue": "#ADD8E6", "Blue": "#0000FF", "Dark Blue": "#00008B",
    "Dark Titanium": "#4A4E69", "Dark Red": "#8B0000", "Pink": "#FFC0CB",
    "Copper": "#B87333", "Titanium": "#808080", "Rose Gold": "#B76E79"
}

def get_options(table, id_col, name_col, filter_col=None, filter_val=None):
    try:
        query = supabase.table(table).select(f"{id_col}, {name_col}")
        if filter_col and filter_val:
            query = query.eq(filter_col, filter_val)
        response = query.execute()
        return {item[name_col]: item[id_col] for item in response.data}
    except:
        return {}

def render_tank_grid(tanks_dict, type_label):
    cols = st.columns(4) 
    i = 0
    for name, tid in tanks_dict.items():
        with cols[i % 4]:
            if st.button(f"{name}", key=f"btn_{tid}_{type_label}"):
                st.session_state['selected_tank_id'] = tid
                st.session_state['selected_tank_name'] = name
                st.session_state['active_type'] = type_label
                st.rerun()
        i += 1

# --- 5. หน้า UI หลัก ---
st.set_page_config(page_title="Production Log System", layout="wide")
st.title("ระบบบันทึกข้อมูลการผลิต")

tab1, tab2, tab3 = st.tabs(["บ่อสี (Color Bath)", "บ่ออโนไดซ์ (Anodize)", "งานจิ๊ก (Jig)"])

# --- TAB 1 & 2: ระบบจัดการบ่อ (แบบ Grid) ---
def handle_tank_tab(type_label, table_log):
    if st.session_state.selected_tank_id is None:
        tanks = get_options("tanks", "tank_id", "tank_name", "tank_type", type_label)
        render_tank_grid(tanks, type_label)
    else:
        st.subheader(f"กำลังบันทึก: {st.session_state.selected_tank_name}")
        if st.button("⬅️ เปลี่ยนบ่อ"):
            st.session_state.selected_tank_id = None
            st.rerun()
        
        with st.form("input_form", clear_on_submit=True):
            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
            density = None
            if type_label == "Anodize":
                density = st.number_input("ความหนาแน่น (Density)", step=0.001, format="%.3f")
            
            if st.form_submit_button("บันทึกข้อมูล"):
                try:
                    data = {"tank_id": st.session_state.selected_tank_id, "ph_value": ph, "temperature": temp}
                    if density: data["density"] = density
                    supabase.table(table_log).insert(data).execute()
                    st.success("บันทึกสำเร็จ!")
                except Exception as e:
                    st.error(f"Error Database: {e}")

with tab1:
    handle_tank_tab("Color", "color_tank_logs")

with tab2:
    handle_tank_tab("Anodize", "anodize_tank_logs")

# --- TAB 3: งานจิ๊ก ---
with tab3:
    sub_prod, sub_jig, sub_log = st.tabs(["1. ลงทะเบียนชิ้นงาน", "2. ลงทะเบียนจิ๊ก", "3. บันทึกผลผลิต"])
    
    with sub_prod:
        with st.form("new_product_form", clear_on_submit=True):
            p_code = st.text_input("รหัสสินค้า *")
            p_name = st.text_input("ชื่อชิ้นงาน *")
            surface_finish = st.text_input("ลักษณะพื้นผิว (Surface Finish) *")
            col1, col2 = st.columns(2)
            with col1:
                h = st.number_input("Height", 0.0, format="%.2f")
                w = st.number_input("Width", 0.0, format="%.2f")
                t = st.number_input("Thickness", 0.0, format="%.2f")
            with col2:
                d = st.number_input("Depth", 0.0, format="%.2f")
                od = st.number_input("Outer Diameter", 0.0, format="%.2f")
                id_val = st.number_input("Inner Diameter", 0.0, format="%.2f")
            
            if st.form_submit_button("บันทึกสินค้า"):
                try:
                    supabase.table("products").insert({"product_code": p_code, "product_name": p_name, "surface_finish": surface_finish, "height": h, "width": w, "thickness": t, "depth": d, "outer_diameter": od, "inner_diameter": id_val}).execute()
                    st.success("บันทึกสินค้าสำเร็จ!")
                except Exception as e:
                    st.error(f"Error: {e}")

    with sub_jig:
        with st.form("new_jig_form", clear_on_submit=True):
            jig_code = st.text_input("รหัสจิ๊ก")
            if st.form_submit_button("บันทึกจิ๊ก"):
                try:
                    supabase.table("jigs").insert({"jig_model_code": jig_code}).execute()
                    st.success("บันทึกจิ๊กสำเร็จ!")
                except Exception as e:
                    st.error(f"Error: {e}")

    with sub_log:
        prods = get_options("products", "product_id", "product_code")
        jigs = get_options("jigs", "jig_id", "jig_model_code")
        all_colors = get_options("colors", "color_id", "color_name") 

        if prods and jigs:
            sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))
            sel_j = st.selectbox("เลือกจิ๊ก", list(jigs.keys()))
            jig_id = jigs[sel_j]
            
            # ดึงข้อมูลสีเก่า
            try:
                hist = supabase.table("jig_usage_log").select("color").eq("jig_id", jig_id).order("recorded_date", desc=True).limit(1).execute()
                first_color = hist.data[0]['color'] if hist.data else None
            except: first_color = None
            
            if first_color:
                st.warning(f"จิ๊กนี้ถูกกำหนดสีไว้แล้ว: {first_color}")
                sel_c = st.selectbox("เลือกสี", [first_color], disabled=True)
            else:
                sel_c = st.selectbox("เลือกสี", list(all_colors.keys()))
            
            if sel_c in color_hex_map:
                st.markdown(f'<div style="background-color:{color_hex_map[sel_c]}; width:100%; height:30px; border-radius:5px;"></div>', unsafe_allow_html=True)
            
            with st.form("log_prod_form", clear_on_submit=True):
                pcs_per_row = st.number_input("จำนวนต่อแถว", min_value=0, step=1)
                rows_filled = st.number_input("จำนวนแถวที่เต็ม", min_value=0, step=1)
                partial_pieces = st.number_input("เศษชิ้นงาน", min_value=0, step=1)
                if st.form_submit_button("บันทึกการผลิต"):
                    try:
                        supabase.table("jig_usage_log").insert({
                            "product_id": prods[sel_p], "jig_id": jig_id, "color": sel_c,
                            "pcs_per_row": pcs_per_row, "rows_filled": rows_filled,
                            "partial_pieces": partial_pieces,
                            "total_pieces": (rows_filled * pcs_per_row) + partial_pieces,
                            "recorded_date": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("บันทึกสำเร็จ!")
                    except Exception as e:
                        st.error(f"Error: {e}")
