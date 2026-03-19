import streamlit as st
        st.rerun()

# ================= BÁO CÁO =================
elif menu == "Báo cáo":

    st.header("⚠️ Hàng sắp hết")

    df = get_stock()

    limit = st.number_input("Ngưỡng", value=5)

    low = df[df["quantity"] < limit]
    low.columns = ["SKU","Tên","Kho","Số lượng"]

    st.dataframe(low)

# ================= LỊCH SỬ =================
elif menu == "Lịch sử":

    st.header("📜 Lịch sử")

    df = pd.read_sql("""
    SELECT h.id,
           h.sku,
           p.name,
           h.type,
           h.quantity,
           h.date,
           h.warehouse,
           h.note
    FROM history h
    LEFT JOIN products p ON h.sku = p.sku
    ORDER BY h.date DESC
    """, conn)

    df.columns = ["ID","SKU","Tên sản phẩm","Loại","Số lượng","Thời gian","Kho","Ghi chú"]

    df["Thời gian"] = pd.to_datetime(df["Thời gian"], errors="coerce")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Từ ngày", value=None)
    with col2:
        end_date = st.date_input("Đến ngày", value=None)

    if start_date and end_date:
        df = df[
            (df["Thời gian"] >= pd.to_datetime(start_date)) &
            (df["Thời gian"] <= pd.to_datetime(end_date))
        ]

    st.dataframe(df, use_container_width=True)

    df_xuat = df[df["Loại"] == "Xuất"]

    if not df_xuat.empty:
        summary = df_xuat.groupby("Ghi chú")["Số lượng"].sum().reset_index()
        summary.columns = ["Cửa hàng","Tổng xuất"]

        st.dataframe(summary)
        st.bar_chart(summary.set_index("Cửa hàng"))

# ================= EXPORT =================
elif menu == "Xuất Excel":

    st.header("📤 Xuất Excel")

    df = pd.read_sql("SELECT * FROM history", conn)

    if st.button("Tải file"):
        file = "export.xlsx"
        df.to_excel(file, index=False)

        with open(file, "rb") as f:
            st.download_button("Download", f, file_name=file)
