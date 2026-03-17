import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ================= DATABASE =================
conn = sqlite3.connect("kho.db", check_same_thread=False)
cursor = conn.cursor()

# ================= CREATE TABLE =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS inventory(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE,
    product_name TEXT,
    warehouse TEXT,
    quantity INTEGER,
    transaction_type TEXT,
    transaction_date TEXT
)
""")

conn.commit()

# ================= FUNCTIONS =================
def get_inventory():
    cursor.execute("SELECT * FROM inventory")
    return pd.DataFrame(cursor.fetchall(), columns=["ID", "SKU", "Tên sản phẩm", "Kho", "Số lượng", "Loại giao dịch", "Ngày giao dịch"])

def get_warehouses():
    return ["Kho A", "Kho B", "Kho C"]

# ================= SIDEBAR =================
st.sidebar.title("📦 QUẢN LÝ KHO")

menu = st.sidebar.radio(
    "Menu",
    [
        "Kho hàng",
        "Thêm sản phẩm",
        "Nhập/Xuất",
        "Lịch sử giao dịch",
        "Xuất Excel"
    ]
)

# ================= VIEW STOCK =================
if menu == "Kho hàng":
    st.header("📦 Tồn kho")
    df = get_inventory()

    search = st.text_input("🔎 Tìm theo SKU hoặc tên")

    if search:
        df = df[
            df["SKU"].str.contains(search, case=False) |
            df["Tên sản phẩm"].str.contains(search, case=False)
        ]

    st.dataframe(df, use_container_width=True)

# ================= ADD PRODUCT =================
elif menu == "Thêm sản phẩm":
    st.header("➕ Thêm sản phẩm")

    sku = st.text_input("SKU")
    name = st.text_input("Tên sản phẩm")

    warehouses = get_warehouses()

    qty = {}
    for w in warehouses:
        qty[w] = st.number_input(f"Số lượng {w}", min_value=0)

    if st.button("Thêm sản phẩm"):
        try:
            # Thêm sản phẩm vào bảng inventory
            for w in warehouses:
                cursor.execute(
                    "INSERT INTO inventory(sku, product_name, warehouse, quantity, transaction_type, transaction_date) VALUES (?,?,?,?,?,?)",
                    (sku, name, w, qty[w], "Thêm", datetime.now())
                )
            conn.commit()
            st.success("Đã thêm sản phẩm")
            st.rerun()
        except Exception as e:
            st.error(f"Đã xảy ra lỗi: {e}")

# ================= IMPORT EXPORT =================
elif menu == "Nhập/Xuất":
    st.header("📥📤 Nhập / Xuất kho")
    df = get_inventory()

    product = st.selectbox("Chọn sản phẩm", df["Tên sản phẩm"])

    warehouses = get_warehouses()
    qty = {w: st.number_input(f"Số lượng {w}", min_value=0) for w in warehouses}

    type_tx = st.radio("Loại giao dịch", ["Nhập", "Xuất"])

    if st.button("Xác nhận giao dịch"):
        for w, q in qty.items():
            cursor.execute(
                "SELECT quantity FROM inventory WHERE sku=? AND warehouse=?",
                (df[df["Tên sản phẩm"] == product]["SKU"].values[0], w)
            )
            res = cursor.fetchone()
            current = res[0] if res else 0

            if type_tx == "Nhập":
                new = current + q
            else:
                if q > current:
                    st.error(f"{w} không đủ hàng")
                    st.stop()
                new = current - q

            # Cập nhật hoặc chèn dữ liệu tồn kho
            cursor.execute(
                "INSERT OR REPLACE INTO inventory(sku, product_name, warehouse, quantity, transaction_type, transaction_date) VALUES (?,?,?,?,?,?)",
                (df[df["Tên sản phẩm"] == product]["SKU"].values[0], product, w, new, type_tx, datetime.now())
            )

            # Lưu lịch sử giao dịch
            cursor.execute(
                "INSERT INTO inventory(sku, product_name, warehouse, quantity, transaction_type, transaction_date) VALUES (?,?,?,?,?,?)",
                (df[df["Tên sản phẩm"] == product]["SKU"].values[0], product, w, q, type_tx, datetime.now())
            )

        conn.commit()
        st.success("Giao dịch thành công")
        st.rerun()

# ================= EXPORT EXCEL =================
elif menu == "Xuất Excel":
    st.header("📄 Xuất Excel tồn kho")

    df = get_inventory()

    file = "ton_kho.xlsx"
    df.to_excel(file, index=False)

    with open(file, "rb") as f:
        st.download_button(
            "⬇️ Tải file Excel",
            f,
            file_name="ton_kho.xlsx"
        )
