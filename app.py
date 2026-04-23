import streamlit as st
from supabase import create_client

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="Production Layout", layout="wide")

# เชื่อมต่อ Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

@st.cache_data(ttl=60)
def get_tanks_data():
    res = supabase.table("tanks").select("tank_id, tank_name, tank_type").execute()
    return {i['tank_name']: {"id": i['tank_id'], "type": i['tank_type']} for i in res.data}

# ฟังก์ชันแสดงปุ่ม
def tank_button(data, label, db_name):
    if db_name in data:
        if st.button(label, key=f"btn_{db_name}", use_container_width=True):
            st.session_state['sel_id'] = data[db_name]['id']
            st.session_state['sel_name'] = label
            st.session_state['sel_type'] = data[db_name]['type']
            st.rerun()
    else:
        st.button(f"{label} (ไม่พบ)", disabled=True, use_container_width=True)

data = get_tanks_data()

# --- เริ่มวาด Layout ---
if 'sel_id' not in st.session_state:
    st.title("🏭 ผังบ่ออโนไดซ์และสี")
    
    # ROW 1: ส่วนบน
    r1_cols = st.columns(7)
    with r1_cols[0]: tank_button(data, "5.Black", "5Black")
    with r1_cols[1]: tank_button(data, "2.Red", "2Red"); tank_button(data, "3.Violet", "3Violet")
    with r1_cols[2]: tank_button(data, "8.Green", "8Green"); tank_button(data, "17.Black", "17Black")
    with r1_cols[3]: tank_button(data, "15.Gold", "15Gold"); tank_button(data, "9.Orange", "9Orange")
    with r1_cols[4]: tank_button(data, "10.Light Blue", "10LightBlue"); tank_button(data, "6.Banana", "6BananaLeafGreen")
    with r1_cols[5]: tank_button(data, "16.Blue", "16Blue"); tank_button(data, "4.Dark Blue", "4DarkBlue")
    with r1_cols[6]: st.info("Sodium Bicarbonate")

    st.divider()

    # ROW 2: ส่วนล่าง (กลุ่ม 1 Dark Red ฝั่งซ้าย)
    r2_cols = st.columns(7)
    with r2_cols[0]: st.info("Almite Sealer")
    with r2_cols[1]: tank_button(data, "20.Black", "20Black"); tank_button(data, "1.Dark Red (Left)", "1DarkRed_Left")
    with r2_cols[2]: tank_button(data, "7.Pink", "7Pink"); tank_button(data, "RO 3", "RO3")
    with r2_cols[3]: tank_button(data, "Hot Seal", "HotSealH60"); tank_button(data, "11.Gold", "11Gold"); tank_button(data, "RO 5", "RO5")
    with r2_cols[4]: # กลุ่ม 1 Dark Red ฝั่งขวา
        tank_button(data, "1.Dark Red (Right)", "1DarkRed_Right")
        tank_button(data, "19.Copper", "19Copper")
        tank_button(data, "12.Titanium", "12Titanium")
        tank_button(data, "14.Rose Gold", "14RoseGold")
    with r2_cols[5]: 
        for i in range(6, 10): tank_button(data, f"RO {i}", f"RO{i}")
    with r2_cols[6]: st.info("Nitric Acid 68"); st.info("Anodized Alum.")

else:
    # หน้าบันทึกข้อมูล (เหมือนเดิม)
    if st.button("⬅️ กลับ"): del st.session_state['sel_id']; st.rerun()
    st.subheader(f"บันทึก: {st.session_state['sel_name']}")
    with st.form("entry"):
        ph = st.number_input("pH")
        temp = st.number_input("Temp")
        if st.form_submit_button("บันทึก"):
            st.success("บันทึกสำเร็จ")
