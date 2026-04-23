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
    "Black": "#333333", "Red": "#D32F2F", "Violet": "#7B1FA2", 
    "Green": "#388E3C", "Banana leaf Green": "#C8E6C9", "Gold": "#FFC107", 
    "Orange": "#F57C00", "Light Blue": "#03A9F4", "Blue": "#1976D2", 
    "Dark Blue": "#0D47A1", "Dark Titanium": "#455A64", "Dark Red": "#B71C1C", 
    "Pink": "#F48FB1", "Copper": "#A1887F", "Titanium": "#757575", "Rose Gold": "#E57373"
}

st.set_page_config(page_title="Production Log System", layout="wide")

# --- CSS สำหรับปรับปุ่ม ---
st.markdown("""
<style>
    div.stButton > button {
        width: 100%;
        height: 70px;
        border-radius: 5px;
        font-size: 11px;
        font-weight: bold;
        border: 1px solid #ccc;
        margin-bottom: 5px;
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
    """ฟังก์ชันวาดปุ่มสำหรับบ่อ (ถ้าไม่มีใน DB จะแสดงปุ่มแบบกดไม่ได้)"""
    # ตรวจหาว่ามีข้อมูลไหม
    is_active = name in tanks
    
    # ดึงรหัสสี (ถ้ามี)
    label_color = next((v for k, v in color_hex_map.items() if k in name), "#F0F0F0")
    
    if is_active:
        info = tanks[name]
        if st.button(f"{name}", key=f"btn_{info['id']}"):
            st.session_state['selected_tank_id'] = info['id']
            st.session_state['selected_tank_name'] = name
            st.session_state['active_type'] = info['type']
            st.rerun()
    else:
        # ปุ่มสำหรับบ่อที่ยังไม่ได้ตั้งค่า
        st.button(f"{name}\n(ไม่พบข้อมูล)", disabled=True, key=f"static_{name}")

# --- หน้าหลัก ---
st.title("🏭 ระบบจัดการบ่ออโนไดซ์และสี")
all_tanks = get_options("tanks")

# ส่วนเลือกบ่อ (Map Layout)
if 'selected_tank_id' not in st.session_state:
    st.subheader("📍 ผังบ่อสีและอโนไดซ์")
    
    # แถวบน
    with st.container():
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        with c1: draw_tank(all_tanks, "5.Black")
        with c2: draw_tank(all_tanks, "2.Red"); draw_tank(all_tanks, "3.Violet")
        with c3: draw_tank(all_tanks, "8.Green"); draw_tank(all_tanks, "17.Black")
        with c4: draw_tank(all_tanks, "15.Gold"); draw_tank(all_tanks, "9.Orange")
        with c5: draw_tank(all_tanks, "10.Light Blue"); draw_tank(all_tanks, "Banana leaf Green")
        with c6: draw_tank(all_tanks, "16.Blue"); draw_tank(all_tanks, "4.Dark Blue")
        with c7: st.info("🧪 Sodium Bicarbonate")

    st.write("---")
    # แถวล่าง
    with st.container():
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        with c1: st.info("🧪 Almite Sealer")
        with c2: draw_tank(all_tanks, "20.Black"); draw_tank(all_tanks, "1.Dark Red")
        with c3: draw_tank(all_tanks, "7.Pink")
        with c4: draw_tank(all_tanks, "Hot Seal (H-60)"); draw_tank(all_tanks, "11.Gold")
        with c5: draw_tank(all_tanks, "19.Copper"); draw_tank(all_tanks, "12.Titanium"); draw_tank(all_tanks, "14.Rose Gold")
        with c6: st.info("🧪 Nitric Acid 68")
        with c7: st.info("🏗️ Anozied Aluminum")

else:
    # ส่วนกรอกข้อมูล (เหมือนเดิม)
    # ... (ส่วนเดิมที่บันทึกข้อมูล)
    if st.button("⬅️ กลับไปหน้าผังบ่อ"):
        del st.session_state['selected_tank_id']
        st.rerun()
    # ...
