import streamlit as st
from supabase import create_client
from datetime import datetime, timezone, timedelta

# 1. ตั้งค่า Timezone (UTC +7)
ICT = timezone(timedelta(hours=7))

# --- การตั้งค่าเชื่อมต่อ ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"ไม่สามารถเชื่อมต่อ Supabase: {e}")

# --- กำหนดค่าสี ---
color_hex_map = {
    "Black": "#000000", "Red": "#FF0000", "Violet": "#9400D3", 
    "Green": "#008000", "Banana leaf Green": "#90EE90", "Gold": "#FFD700", 
    "Orange": "#FFA500", "Light Blue": "#ADD8E6", "Blue": "#0000FF", 
    "Dark Blue": "#00008B", "Dark Titanium": "#4A4E69", "Dark Red": "#8B0000", 
    "Pink": "#FFC0CB", "Copper": "#B87333", "Titanium": "#808080", "Rose Gold": "#B76E79"
}

st.set_page_config(page_title="Production Log System", layout="wide")

# --- CSS สำหรับปรับปุ่มให้เป็นกล่องสี ---
st.markdown("""
<style>
    div.stButton > button {
        width: 100%;
        height: 80px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: bold;
        border: 2px solid #ddd;
    }
    .tank-label {
        text-align: center;
        font-size: 10px;
        margin-top: 5px;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# --- Functions ---
def get_options(table):
    try:
        response = supabase.table(table).select("tank_id, tank_name, tank_type").execute()
        return {item['tank_name']: {"id": item['tank_id'], "type": item['tank_type']} for item in response.data}
    except: return {}

def draw_tank(tanks, name):
    """ฟังก์ชันวาดปุ่มสำหรับบ่อ"""
    if name in tanks:
        info = tanks[name]
        color = color_hex_map.get(name.split('.')[-1], "#FFFFFF")
        
        # ใช้ container เพื่อคุมปุ่ม
        if st.button(name, key=f"btn_{info['id']}"):
            st.session_state['selected_tank_id'] = info['id']
            st.session_state['selected_tank_name'] = name
            st.session_state['active_type'] = info['type']
            st.rerun()
    else:
        st.button(name, disabled=True, key=f"static_{name}")

# --- หน้าหลัก ---
st.title("🏭 ระบบจัดการบ่ออโนไดซ์และสี")
all_tanks = get_options("tanks")

# ส่วนเลือกบ่อ (Map Layout)
if 'selected_tank_id' not in st.session_state:
    st.subheader("📍 เลือกบ่อที่ต้องการบันทึกข้อมูล")
    
    # วาด Layout ตามรูป
    with st.container():
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        with c1: draw_tank(all_tanks, "5.Black")
        with c2: draw_tank(all_tanks, "2.Red"); draw_tank(all_tanks, "3.Violet")
        with c3: draw_tank(all_tanks, "8.Green"); draw_tank(all_tanks, "17.Black")
        with c4: draw_tank(all_tanks, "15.Gold"); draw_tank(all_tanks, "9.Orange")
        with c5: draw_tank(all_tanks, "10.Light Blue"); draw_tank(all_tanks, "Banana leaf Green")
        with c6: draw_tank(all_tanks, "16.Blue"); draw_tank(all_tanks, "4.Dark Blue")
        with c7: st.write("🧪 Sodium Bicarbonate")

    st.write("---")
    with st.container():
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        with c1: st.write("🧪 Almite Sealer")
        with c2: draw_tank(all_tanks, "20.Black"); draw_tank(all_tanks, "1.Dark Red")
        with c3: draw_tank(all_tanks, "7.Pink")
        with c4: draw_tank(all_tanks, "Hot Seal (H-60)"); draw_tank(all_tanks, "11.Gold")
        with c5: draw_tank(all_tanks, "19.Copper"); draw_tank(all_tanks, "12.Titanium"); draw_tank(all_tanks, "14.Rose Gold")
        with c6: st.write("🧪 Nitric Acid 68")
        with c7: st.write("🏗️ Anozied Aluminum")

else:
    # ส่วนกรอกข้อมูล
    st.info(f"กำลังบันทึกข้อมูล: **{st.session_state['selected_tank_name']}** ({st.session_state['active_type']})")
    if st.button("⬅️ กลับไปหน้าผังบ่อ"):
        del st.session_state['selected_tank_id']
        st.rerun()

    with st.form("input_form", clear_on_submit=True):
        ph = st.number_input("ค่า pH", step=0.1)
        temp = st.number_input("อุณหภูมิ (°C)", step=0.1)
        if st.session_state['active_type'] == "Anodize":
            density = st.number_input("ความหนาแน่น (Density)", step=0.001, format="%.3f")
        else: density = None

        if st.form_submit_button("บันทึกข้อมูล"):
            table_name = "color_tank_logs" if st.session_state['active_type'] == "Color Bath" else "anodize_tank_logs"
            data = {"tank_id": st.session_state['selected_tank_id'], "ph_value": ph, "temperature": temp}
            if density: data["density"] = density
            try:
                supabase.table(table_name).insert(data).execute()
                st.success("บันทึกสำเร็จ!")
            except Exception as e: st.error(f"Error: {e}")

# --- TAB 3: งานจิ๊ก (คงไว้เหมือนเดิม) ---
# (ใส่โค้ดส่วน Tab 3 ตรงนี้ได้เลย)
