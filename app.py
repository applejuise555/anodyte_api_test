import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timezone, timedelta

ICT = timezone(timedelta(hours=7))

if "selected_tank" not in st.session_state:
    st.session_state.selected_tank = None

# ------------------ MAP LAYOUT ------------------
html_map = """
<div style="position:relative; width:100%; height:650px; background:#f5f5f5;">

<!-- ===== TOP ===== -->
<div onclick="go('5 Black')" style="position:absolute; top:40px; left:40px; width:80px; height:60px; background:black; color:white; text-align:center; line-height:60px;">5</div>

<div onclick="go('2 Red')" style="position:absolute; top:40px; left:140px; width:80px; height:60px; background:red; color:white; text-align:center; line-height:60px;">2</div>

<div onclick="go('3 Violet')" style="position:absolute; top:40px; left:240px; width:80px; height:60px; background:purple; color:white; text-align:center; line-height:60px;">3</div>

<div onclick="go('8 Green')" style="position:absolute; top:40px; left:340px; width:80px; height:60px; background:green; color:white; text-align:center; line-height:60px;">8</div>

<div onclick="go('17 Black')" style="position:absolute; top:40px; left:440px; width:80px; height:60px; background:black; color:white; text-align:center; line-height:60px;">17</div>

<div onclick="go('15 Gold')" style="position:absolute; top:40px; left:540px; width:80px; height:60px; background:gold; color:black; text-align:center; line-height:60px;">15</div>

<div onclick="go('9 Orange')" style="position:absolute; top:40px; left:640px; width:80px; height:60px; background:orange; color:black; text-align:center; line-height:60px;">9</div>

<div onclick="go('10 Light Blue')" style="position:absolute; top:40px; left:740px; width:80px; height:60px; background:#87CEFA; color:black; text-align:center; line-height:60px;">10</div>

<div onclick="go('6 Banana leaf Green')" style="position:absolute; top:40px; left:840px; width:80px; height:60px; background:#90EE90; color:black; text-align:center; line-height:60px;">6</div>

<div onclick="go('16 Blue')" style="position:absolute; top:40px; left:940px; width:80px; height:60px; background:blue; color:white; text-align:center; line-height:60px;">16</div>

<div onclick="go('4 Dark Blue')" style="position:absolute; top:40px; left:1040px; width:80px; height:60px; background:#00008B; color:white; text-align:center; line-height:60px;">4</div>

<!-- ===== BOTTOM ===== -->
<div onclick="go('20 Black')" style="position:absolute; top:250px; left:140px; width:80px; height:60px; background:black; color:white; text-align:center; line-height:60px;">20</div>

<div onclick="go('1 Dark Red A')" style="position:absolute; top:250px; left:240px; width:80px; height:60px; background:#8B0000; color:white; text-align:center; line-height:60px;">1A</div>

<div onclick="go('7 Pink')" style="position:absolute; top:250px; left:340px; width:80px; height:60px; background:pink; color:black; text-align:center; line-height:60px;">7</div>

<div onclick="go('Hot Seal')" style="position:absolute; top:250px; left:440px; width:80px; height:60px; background:gray; color:white; text-align:center; line-height:60px;">Hot</div>

<div onclick="go('11 Gold')" style="position:absolute; top:250px; left:540px; width:80px; height:60px; background:gold; color:black; text-align:center; line-height:60px;">11</div>

<div onclick="go('1 Dark Red B')" style="position:absolute; top:250px; left:640px; width:80px; height:60px; background:#8B0000; color:white; text-align:center; line-height:60px;">1B</div>

<div onclick="go('19 Copper')" style="position:absolute; top:250px; left:740px; width:80px; height:60px; background:#B87333; color:white; text-align:center; line-height:60px;">19</div>

<div onclick="go('12 Titanium')" style="position:absolute; top:250px; left:840px; width:80px; height:60px; background:gray; color:white; text-align:center; line-height:60px;">12</div>

<div onclick="go('14 Rose Gold')" style="position:absolute; top:250px; left:940px; width:80px; height:60px; background:#B76E79; color:white; text-align:center; line-height:60px;">14</div>

<script>
function go(name){
    const url = new URL(window.location);
    url.searchParams.set("tank", name);
    window.location.href = url;
}
</script>

</div>
"""

components.html(html_map, height=700)

# ------------------ GET CLICK ------------------
params = st.query_params
if "tank" in params:
    st.session_state.selected_tank = params["tank"]

# ------------------ POPUP FORM ------------------
if st.session_state.selected_tank:

    tank_name = st.session_state.selected_tank

    with st.modal(f"บันทึกข้อมูล: {tank_name}"):

        with st.form("form"):

            ph = st.number_input("ค่า pH", step=0.1)
            temp = st.number_input("อุณหภูมิ", step=0.1)

            # ถ้าเป็นอโนไดซ์ เพิ่ม density
            density = None
            if "Anodize" in tank_name or "Seal" in tank_name:
                density = st.number_input("Density", step=0.001)

            if st.form_submit_button("💾 บันทึก"):

                try:
                    # ดึง tank_id
                    tank = supabase.table("tanks").select("tank_id").eq("tank_name", tank_name).execute()
                    tank_id = tank.data[0]["tank_id"]

                    if "Seal" in tank_name:
                        table = "anodize_tank_logs"
                    else:
                        table = "color_tank_logs"

                    data = {
                        "tank_id": tank_id,
                        "ph_value": ph,
                        "temperature": temp,
                        "recorded_at": datetime.now(ICT).isoformat()
                    }

                    if density:
                        data["density"] = density

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
