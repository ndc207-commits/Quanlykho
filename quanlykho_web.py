import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ================= DATABASE =================
conn = sqlite3.connect("kho.db", check_same_thread=False)
cursor = conn.cursor()

# ================= CREATE TABLES =================
# Bảng sản phẩm
cursor.execute("""
CREATE TABLE IF NOT EXISTS products(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE,
    product_name TEXT,
    created_at TEXT
)
""")

# Bảng tồn kho
cursor.execute("""
CREATE TABLE IF NOT EXISTS inventory(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT,
    warehouse TEXT,
    quantity INTEGER,
    UNIQUE(sku, warehouse)  -- Đảm bảo sku và warehouse là duy nhất trong bảng
)
""")

# Bảng giao dịch nhập/xuất
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT,
    warehouse TEXT,
    transaction_type TEXT,
    quantity INTEGER,
    transaction_date TEXT
)
""")
conn.commit()

# ================= FUNCTIONS =================
def get_products():
    cursor.execute("SELECT * FROM products")
    return pd.DataFrame(cursor.fetchall(), columns=["ID", "SKU", "Tên sản phẩm", "Ngày tạo"])

def get_inventory():
    cursor.execute("""
    SELECT p.sku, p.product_name, w.warehouse, COALESCE(i.quantity, 0) as quantity
    FROM products p
    LEFT JOIN inventory i ON p.sku = i.sku
    LEFT JOIN warehouses w
    """)
    return pd.DataFrame(cursor.fetchall(), columns=["SKU", "Tên sản phẩm", "Kho", "Số lượng"])

def get_transactions():
    cursor.execute("""
    SELECT t.sku, t.warehouse, t.transaction_type, t.quantity, t.transaction_date, p.product_name
    FROM transactions t
    LEFT JOIN products p ON t.sku = p.sku
    ORDER BY t.transaction_date DESC
    """)
    return pd.DataFrame(cursor.fetchall(), columns=["SKU", "Kho", "Loại giao dịch", "Số lượng", "Ngày giao dịch", "Tên sản phẩm"])

def get_warehouses():
    return ["La Pagode", "Muse", "Metz Ville", "Nancy"]

# ================= SIDEBAR =================
st.sidebar.title("📦 QUẢN LÝ KHO")

menu = st.sidebar.radio(
    "Menu",
    [
        "Kho hàng",
        "Thêm sản phẩm",
        "Cập nhật sản phẩm",
        "Xóa sản phẩm",
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

    if st.button("Thêm sản phẩm"):
        try:
            cursor.execute("SELECT sku FROM products WHERE sku = ?", (sku,))
            if cursor.fetchone():
                st.error("SKU này đã tồn tại. Vui lòng nhập SKU khác.")
            else:
                cursor.execute(
                    "INSERT INTO products(sku, product_name, created_at) VALUES (?,?,?)",
                    (sku, name, datetime.now())
                )
                conn.commit()
                st.success("Đã thêm sản phẩm")
                st.rerun()
        except Exception as e:
            st.error(f"Đã xảy ra lỗi: {e}")

# ================= UPDATE PRODUCT =================
elif menu == "Cập nhật sản phẩm":
    st.header("✏️ Cập nhật sản phẩm")
    
    # Lấy danh sách sản phẩm
    df = get_products()

    sku = st.selectbox("Chọn SKU sản phẩm", df["SKU"])

    new_name = st.text_input("Tên sản phẩm mới")
    if st.button("Cập nhật sản phẩm"):
        try:
            if new_name:
                cursor.execute(
                    "UPDATE products SET product_name = ? WHERE sku = ?",
                    (new_name, sku)
                )
                conn.commit()
                st.success(f"Đã cập nhật tên sản phẩm thành '{new_name}'")
                st.rerun()
            else:
                st.error("Vui lòng nhập tên sản phẩm mới.")
        except Exception as e:
            st.error(f"Đã xảy ra lỗi: {e}")

# ================= DELETE PRODUCT =================
elif menu == "Xóa sản phẩm":
    st.header("🗑️ Xóa sản phẩm")

    # Lấy danh sách sản phẩm
    df = get_products()

    sku_to_delete = st.selectbox("Chọn SKU sản phẩm để xóa", df["SKU"])

    if st.button("Xóa sản phẩm"):
        try:
            # Xóa sản phẩm khỏi bảng products, inventory và transactions
            cursor.execute("DELETE FROM products WHERE sku = ?", (sku_to_delete,))
            cursor.execute("DELETE FROM inventory WHERE sku = ?", (sku_to_delete,))
            cursor.execute("DELETE FROM transactions WHERE sku = ?", (sku_to_delete,))
            conn.commit()

            st.success(f"Đã xóa sản phẩm có SKU: {sku_to_delete}")
            st.rerun()
        except Exception as e:
            st.error(f"Đã xảy ra lỗi khi xóa: {e}")

# ================= IMPORT EXPORT =================
elif menu == "Nhập/Xuất":
    st.header("📥📤 Nhập / Xuất kho")
    
    # Lấy danh sách sản phẩm
    df = get_products()
    product = st.selectbox("Chọn sản phẩm", df["Tên sản phẩm"])

    # Kho có thể là La Pagode, Muse, Metz Ville, Nancy
    warehouses = ["La Pagode", "Muse", "Metz Ville", "Nancy"]
    qty = {w: st.number_input(f"Số lượng {w}", min_value=0) for w in warehouses}

    # Loại giao dịch (Nhập hoặc Xuất)
    type_tx = st.radio("Loại giao dịch", ["Nhập", "Xuất"])

    if st.button("Xác nhận giao dịch"):
        for w, q in qty.items():
            # Kiểm tra thông tin tồn kho hiện tại cho kho cụ thể
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

            # Cập nhật tồn kho tại kho tương ứng
            cursor.execute(
                "INSERT OR REPLACE INTO inventory(sku, warehouse, quantity) VALUES (?,?,?)",
                (df[df["Tên sản phẩm"] == product]["SKU"].values[0], w, new)
            )

            # Lưu lịch sử giao dịch
            cursor.execute(
                "INSERT INTO transactions(sku, warehouse, transaction_type, quantity, transaction_date) VALUES (?,?,?,?,?)",
                (df[df["Tên sản phẩm"] == product]["SKU"].values[0], w, type_tx, q, datetime.now())
            )

        conn.commit()
        st.success("Giao dịch thành công")
        st.rerun()

# ================= TRANSACTION HISTORY =================
elif menu == "Lịch sử giao dịch":
    st.header("📜 Lịch sử giao dịch")
    
    df = get_transactions()

    # Lọc theo kho nếu cần
    search_warehouse = st.selectbox("Chọn kho để xem giao dịch", ["Tất cả", "La Pagode", "Muse", "Metz Ville", "Nancy"])

    if search_warehouse != "Tất cả":
        df = df[df["Kho"] == search_warehouse]

    st.dataframe(df, use_container_width=True)

# ================= EXPORT EXCEL =================
elif menu == "Xuất Excel":
    st.header("📄 Xuất Excel tồn kho")

    df = get_inventory()

    # Đường dẫn file Excel
    file = "ton_kho.xlsx"
    df.to_excel(file, index=False)

    # Cung cấp nút tải về file Excel
    with open(file, "rb") as f:
        st.download_button(
            label="⬇️ Tải file Excel",
            data=f,
            file_name="ton_kho.xlsx"
        )
