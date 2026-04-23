import streamlit as st
from supabase import create_client

st.set_page_config(layout="wide")

# ---------------- SUPABASE ----------------
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except:
    st.warning("ยังไม่เชื่อม Supabase")

# ---------------- SESSION ----------------
if "selected_tank" not in st.session_state:
    st.session_state.selected_tank = None

# ---------------- CSS ----------------
st.markdown("""
<style>
.canvas {
    position: relative;
    width: 100%;
    height: 700px;
    background: #f5f5f5;
}

/* กล่องโชว์ */
.box {
    position: absolute;
    width: 90px;
    height: 60px;
    border-radius: 6px;
    text-align: center;
    line-height: 60px;
    font-weight: bold;
    color: white;
}

/* ปุ่มคลิก */
.click {
    position: absolute;
    width: 90px;
    height: 60px;
    opacity: 0;
    cursor: pointer;
}

/* สี */
.black { background:#000; }
.red { background:#ff2d2d; }
.violet { background:#6a00ff; }
.green { background:#2e6b00; }
.orange { background:#ff7a00; }
.blue { background:#2f55ff; }
.darkblue { background:#0b1c7a; }
.pink { background:#ff66cc; }
.gold { background:#f5a623; }
.gray { background:#777; }
.ro { background:#66d1d1; color:#000; }
</style>
""", unsafe_allow_html=True)

# ---------------- FUNCTION ----------------
def click_tank(name):
    st.session_state.selected_tank = name

# ---------------- UI ----------------
st.title("🏭 Production Layout")

# ใช้ columns เพื่อวาง invisible button (hack ให้คลิกได้)
col = st.container()

with col:
    c1, c2 = st.columns([8,1])

    # --------- CANVAS ----------
    with c1:
        st.markdown("""
        <div class="canvas">

        <!-- กล่อง -->
        <div class="box black" style="top:40px; left:40px;">5</div>
        <div class="box red" style="top:40px; left:160px;">2</div>
        <div class="box violet" style="top:40px; left:260px;">3</div>

        <div class="box green" style="top:40px; left:360px;">8</div>
        <div class="box black" style="top:40px; left:460px;">17</div>

        </div>
        """, unsafe_allow_html=True)

        # -------- CLICK LAYER --------
        # ต้องใช้ streamlit button จริง (HTML button กดไม่ได้ใน Streamlit)
        if st.button(" ", key="tank_5"):
            click_tank("5 Black")

        if st.button(" ", key="tank_2"):
            click_tank("2 Red")

        if st.button(" ", key="tank_3"):
            click_tank("3 Violet")

        if st.button(" ", key="tank_8"):
            click_tank("8 Green")

        if st.button(" ", key="tank_17"):
            click_tank("17 Black")

# ---------------- POPUP ----------------
if st.session_state.selected_tank:

    with st.modal(f"บันทึกข้อมูล: {st.session_state.selected_tank}"):

        with st.form("form"):
            ph = st.number_input("pH")
            temp = st.number_input("Temperature")

            if st.form_submit_button("💾 บันทึก"):
                try:
                    supabase.table("records").insert({
                        "tank": st.session_state.selected_tank,
                        "ph": ph,
                        "temp": temp
                    }).execute()

                    st.success("บันทึกสำเร็จ ✅")
                    st.session_state.selected_tank = None
                    st.rerun()

                except:
                    st.error("บันทึกไม่สำเร็จ")

        if st.button("❌ ปิด"):
            st.session_state.selected_tank = None
            st.rerun()
