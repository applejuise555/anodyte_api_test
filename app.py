with tab3:
    # 1. ประกาศ Tab ก่อนเสมอ เพื่อไม่ให้เกิด NameError
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
                # เช็คซ้ำใน Database
                check_dup = supabase.table("products").select("product_code").eq("product_code", p_code).execute()
                if check_dup.data:
                    st.error(f"รหัสสินค้า '{p_code}' มีอยู่ในระบบแล้ว!")
                else:
                    try:
                        supabase.table("products").insert({
                            "product_code": p_code, "product_name": p_name,
                            "surface_finish": surface_finish,
                            "height": h, "width": w, "thickness": t, 
                            "depth": d, "outer_diameter": od, "inner_diameter": id_val
                        }).execute()
                        st.success("บันทึกสินค้าสำเร็จ!")
                    except Exception as e:
                        st.error(f"Error Database: {e}") # ดู Error จริงที่นี่

    with sub_jig:
        with st.form("new_jig_form", clear_on_submit=True):
            jig_code = st.text_input("รหัสจิ๊ก")
            if st.form_submit_button("บันทึกจิ๊ก"):
                # เช็คซ้ำใน Database
                check_dup = supabase.table("jigs").select("jig_model_code").eq("jig_model_code", jig_code).execute()
                if check_dup.data:
                    st.error(f"รหัสจิ๊ก '{jig_code}' มีอยู่ในระบบแล้ว!")
                else:
                    try:
                        supabase.table("jigs").insert({"jig_model_code": jig_code}).execute()
                        st.success("บันทึกจิ๊กสำเร็จ!")
                    except Exception as e:
                        st.error(f"Error Database: {e}")

    with sub_log:
        prods = get_options("products", "product_id", "product_code")
        jigs = get_options("jigs", "jig_id", "jig_model_code")
        all_colors = get_options("colors", "color_id", "color_name") 

        if prods and jigs:
            sel_p = st.selectbox("เลือกสินค้า", list(prods.keys()))
            sel_j = st.selectbox("เลือกจิ๊ก", list(jigs.keys()))
            
            jig_id = jigs[sel_j]
            first_color = None
            
            # ดึงสีแรกที่เคยใช้
            try:
                hist = supabase.table("jig_usage_log").select("color").eq("jig_id", jig_id).order("recorded_date", desc=False).limit(1).execute()
                if hist.data: first_color = hist.data[0]['color']
            except: pass
            
            # ล็อกสีถ้าเคยมีประวัติ
            if first_color:
                st.warning(f"จิ๊กนี้ถูกกำหนดสีไว้แล้ว: {first_color}")
                sel_c = st.selectbox("เลือกสี", [first_color], disabled=True)
            else:
                sel_c = st.selectbox("เลือกสี", list(all_colors.keys()))
            
            # แสดงกล่องสี
            if sel_c in color_hex_map:
                st.markdown(f'<div style="background-color:{color_hex_map[sel_c]}; width:100%; height:30px; border-radius:5px;"></div>', unsafe_allow_html=True)
            
            with st.form("log_prod_form", clear_on_submit=True):
                pcs_per_row = st.number_input("จำนวนต่อแถว", min_value=0, step=1)
                rows_filled = st.number_input("จำนวนแถวที่เต็ม", min_value=0, step=1)
                partial_pieces = st.number_input("เศษชิ้นงาน", min_value=0, step=1)
                
                if st.form_submit_button("บันทึกการผลิต"):
                    try:
                        supabase.table("jig_usage_log").insert({
                            "product_id": prods[sel_p],
                            "jig_id": jig_id,
                            "color": sel_c,
                            "pcs_per_row": pcs_per_row,
                            "rows_filled": rows_filled,
                            "partial_pieces": partial_pieces,
                            "total_pieces": (rows_filled * pcs_per_row) + partial_pieces,
                            "recorded_date": datetime.now(ICT).isoformat()
                        }).execute()
                        st.success("บันทึกสำเร็จ!")
                    except Exception as e:
                        st.error(f"Error: {e}")
