import streamlit as st
from supabase import create_client

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Production Layout", layout="wide")

# ---------------- CSS ----------------
st.markdown("""
<style>
.block {
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    font-weight: bold;
    color: white;
    margin-bottom: 10px;
}
.ro { background-color: #5cc9c9; }
.gray { background-color: #777; }
.red { background-color: #ff3b3b; }
.violet { background-color: #7a2cff; }
.green { background-color: #3a6f00; }
.orange { background-color: #ff7a00; }
.blue { background-color: #1e40ff; }
.darkblue { background-color: #0d1b7e; }
.pink { background-color: #ff66cc; }
.gold { background-color: #f5a623; }
</style>
""", unsafe_allow_html=True)

# ---------------- SUPABASE ----------------
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except:
    st.error("ตรวจสอบ Supabase")
    st.stop()

@st.cache_data(ttl=10)
def get_tanks_data():
    try:
        res = supabase.table("tanks").select("*").execute()
        return {i['tank_name']: i for i in res.data}
    except:
        return {}

tanks = get_tanks_data()

# ---------------- FUNCTION ----------------
def tank_block(label, color="gray"):
    st.markdown(f'<div class="block {color}">{label}</div>', unsafe_allow_html=True)

def ro_block(label):
    st.markdown(f'<div class="block ro">{label}</div>', unsafe_allow_html=True)

# ---------------- MAIN ----------------
if 'sel_id' not in st.session_state:

    st.title("🏭 Production Layout (Anodize)")

    # ---------- TOP ----------
    c1,c2,c3,c4,c5,c6,c7,c8 = st.columns(8)

    with c1:
        tank_block("5 Black")

    with c2:
        tank_block("2 Red","red")
        tank_block("3 Violet","violet")
        ro_block("RO")

    with c3:
        tank_block("8 Green","green")
        tank_block("17 Black")

    with c4:
        tank_block("15 Gold","gold")
        tank_block("9 Orange","orange")
        ro_block("RO")

    with c5:
        tank_block("10 Light Blue","blue")
        tank_block("6 Banana Leaf","green")

    with c6:
        tank_block("16 Blue","blue")
        tank_block("4 Dark Blue","darkblue")
        ro_block("RO")

    with c7:
        st.info("Sodium Bicarbonate")

    st.divider()

    # ---------- BOTTOM ----------
    c1,c2,c3,c4,c5,c6,c7,c8 = st.columns(8)

    with c1:
        st.markdown('<div class="block gray">Almite Sealer</div>', unsafe_allow_html=True)

    with c2:
        tank_block("20 Black")
        tank_block("1 Dark Red","red")

    with c3:
        tank_block("7 Pink","pink")
        ro_block("RO")

    with c4:
        tank_block("Hot Seal")
        tank_block("11 Gold","gold")
        ro_block("RO")

    with c5:
        tank_block("1 Dark Red","red")
        tank_block("19 Copper","orange")
        tank_block("12 Titanium","gray")
        tank_block("14 Rose Gold","pink")

    with c6:
        ro_block("RO")
        ro_block("RO")
        ro_block("RO")
        ro_block("RO")

    with c7:
        st.info("Nitric Acid 68")

    with c8:
        st.markdown('<div class="block gray">Anodized</div>', unsafe_allow_html=True)

# ---------------- DETAIL PAGE ----------------
else:
    if st.button("⬅️ กลับ"):
        del st.session_state['sel_id']
        st.rerun()

    st.subheader(f"บันทึก: {st.session_state['sel_name']}")

    with st.form("form"):
        ph = st.number_input("pH")
        temp = st.number_input("Temp")

        if st.form_submit_button("บันทึก"):
            st.success("บันทึกสำเร็จ")
