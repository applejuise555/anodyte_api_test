import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timezone, timedelta

ICT = timezone(timedelta(hours=7))

if "selected_tank" not in st.session_state:
    st.session_state.selected_tank = None

# ------------------ LAYOUT ------------------
html = """
<style>
.wrapper {
    width:100%;
    height:500px;
    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;
    gap:80px;
}

.row {
    display:flex;
    gap:30px;
}

.box {
    width:80px;
    height:60px;
    display:flex;
    justify-content:center;
    align-items:center;
    font-weight:bold;
    cursor:pointer;
}

/* colors */
.black {background:black;color:white;}
.red {background:red;color:white;}
.violet {background:purple;color:white;}
.green {background:green;color:white;}
.gold {background:gold;color:black;}
.orange {background:orange;color:black;}
.lblue {background:#87CEFA;color:black;}
.banana {background:#90EE90;color:black;}
.blue {background:blue;color:white;}
.dblue {background:#00008B;color:white;}
.pink {background:pink;color:black;}
.gray {background:gray;color:white;}
.copper {background:#B87333;color:white;}
.rose {background:#B76E79;color:white;}

</style>

<div class="wrapper">

    <!-- TOP -->
    <div class="row">
        <div class="box black" onclick="go('5 Black')">5</div>
        <div class="box red" onclick="go('2 Red')">2</div>
        <div class="box violet" onclick="go('3 Violet')">3</div>
        <div class="box green" onclick="go('8 Green')">8</div>
        <div class="box black" onclick="go('17 Black')">17</div>
        <div class="box gold" onclick="go('15 Gold')">15</div>
        <div class="box orange" onclick="go('9 Orange')">9</div>
        <div class="box lblue" onclick="go('10 Light Blue')">10</div>
        <div class="box banana" onclick="go('6 Banana leaf Green')">6</div>
        <div class="box blue" onclick="go('16 Blue')">16</div>
        <div class="box dblue" onclick="go('4 Dark Blue')">4</div>
    </div>

    <!-- BOTTOM -->
    <div class="row">
        <div class="box black" onclick="go('20 Black')">20</div>
        <div class="box red" onclick="go('1 Dark Red A')">1A</div>
        <div class="box pink" onclick="go('7 Pink')">7</div>
        <div class="box gray" onclick="go('Hot Seal')">Hot</div>
        <div class="box gold" onclick="go('11 Gold')">11</div>
        <div class="box red" onclick="go('1 Dark Red B')">1B</div>
        <div class="box copper" onclick="go('19 Copper')">19</div>
        <div class="box gray" onclick="go('12 Titanium')">12</div>
        <div class="box rose" onclick="go('14 Rose Gold')">14</div>
    </div>

</div>

<script>
function go(name){
    const url = new URL(window.location);
    url.searchParams.set("tank", name);
    window.location.href = url;
}
</script>
"""

components.html(html, height=550)

# ------------------ GET CLICK ------------------
params = st.query_params
if "tank" in params:
    st.session_state.selected_tank = params["tank"]

# ------------------ POPUP ------------------
if st.session_state.selected_tank:

    tank_name = st.session_state.selected_tank

    with st.modal(f"บันทึกข้อมูล: {tank_name}"):

        with st.form("form"):

            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ", step=0.1)

            density = None
            if "Hot" in tank_name:
                density = st.number_input("Density", step=0.001)

            if st.form_submit_button("💾 บันทึก"):
                try:
                    tank = supabase.table("tanks").select("tank_id").eq("tank_name", tank_name).execute()
                    tank_id = tank.data[0]["tank_id"]

                    data = {
                        "tank_id": tank_id,
                        "ph_value": ph,
                        "temperature": temp,
                        "recorded_at": datetime.now(ICT).isoformat()
                    }

                    # แยก table
                    if "Hot" in tank_name:
                        table = "anodize_tank_logs"
                        if density:
                            data["density"] = density
                    else:
                        table = "color_tank_logs"

                    supabase.table(table).insert(data).execute()

                    st.success("บันทึกสำเร็จ ✅")

                    st.session_state.selected_tank = None
                    st.query_params.clear()
                    st.rerun()

                except Exception as e:
                    st.error(f"Error: {e}")

        if st.button("❌ ปิด"):
            st.session_state.selected_tank = None
            st.query_params.clear()
            st.rerun()
