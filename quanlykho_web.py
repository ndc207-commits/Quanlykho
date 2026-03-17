import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ================= DATABASE =================
conn = sqlite3.connect("kho.db", check_same_thread=False)
cursor = conn.cursor()

# ================= CREATE TABLES =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS products(
id INTEGER PRIMARY KEY AUTOINCREMENT,
sku TEXT UNIQUE,
name TEXT,
created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS warehouses(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS stock_by_warehouse(
id INTEGER PRIMARY KEY AUTOINCREMENT,
product_id INTEGER,
warehouse TEXT,
quantity INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS history(
id INTEGER PRIMARY KEY AUTOINCREMENT,
product_id INTEGER,
type TEXT,
quantity INTEGER,
date TEXT,
warehouse TEXT
)
""")

conn.commit()

# ================= DEFAULT WAREHOUSE =================
cursor.execute("SELECT COUNT(*) FROM warehouses")
if cursor.fetchone()[0] == 0:
    cursor.executemany(
        "INSERT INTO warehouses(name) VALUES (?)",
        [
            ("Kho A",),
            ("Kho B",),
            ("Kho C",)
        ]
    )
    conn.commit()

# ================= FUNCTIONS =================
def get_products():
    cursor.execute("SELECT * FROM products")
    return pd.DataFrame(cursor.fetchall(), columns=["ID","SKU","Tên sản phẩm","Ngày tạo"])

def get_stock():
    cursor.execute("""
    SELECT p.id, p.sku, p.name, w.name as warehouse, 
           COALESCE(s.quantity, 0) as quantity
    FROM products p
    CROSS JOIN warehouses w
    LEFT JOIN stock_by_warehouse s ON p.id = s.product_id AND s.warehouse = w.name
    """)

    return pd.DataFrame(
        cursor.fetchall(),
        columns=["ID", "SKU", "Tên sản phẩm", "Kho", "Số lượng"]
    )

def get_warehouses():
    cursor.execute("SELECT name FROM warehouses")
    return [x[0] for x in cursor.fetchall()]

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
    df = get_stock()

    search = st.text_input("🔎 Tìm theo SKU hoặc tên")

    if search:
        df = df[
            df["SKU"].str.contains(search,case=False) |
            df["Tên sản phẩm"].str.contains(search,case=False)
        ]

    st.dataframe(df,use_container_width=True)

    # Cập nhật và xóa sản phẩm
    st.subheader("Quản lý sản phẩm")
    product_id_to_update = st.selectbox("Chọn sản phẩm cần cập nhật hoặc xóa", df["Tên sản phẩm"])

    if product_id_to_update:
        # Lấy ID của sản phẩm được chọn
        pid = df[df["Tên sản phẩm"] == product_id_to_update]["ID"].values[0]
        
        # Cập nhật thông tin sản phẩm
        if st.button("Cập nhật sản phẩm"):
            new_sku = st.text_input("Cập nhật SKU", value=df[df["ID"] == pid]["SKU"].values[0])
            new_name = st.text_input("Cập nhật tên sản phẩm", value=df[df["ID"] == pid]["Tên sản phẩm"].values[0])

            if new_sku and new_name:
                try:
                    cursor.execute(
                        "UPDATE products SET sku = ?, name = ? WHERE id = ?",
                        (new_sku, new_name, pid)
                    )
                    conn.commit()
                    st.success("Đã cập nhật sản phẩm thành công")
                    st.rerun()
                except Exception as e:
                    st.error(f"Đã xảy ra lỗi khi cập nhật: {e}")
            else:
                st.error("Vui lòng nhập đầy đủ thông tin SKU và tên sản phẩm.")

        # Xóa sản phẩm
        if st.button("Xóa sản phẩm"):
            confirm_delete = st.checkbox("Xác nhận xóa sản phẩm này?")
            if confirm_delete:
                try:
                    cursor.execute("DELETE FROM products WHERE id = ?", (pid,))
                    cursor.execute("DELETE FROM stock_by_warehouse WHERE product_id = ?", (pid,))
                    cursor.execute("DELETE FROM history WHERE product_id = ?", (pid,))
                    conn.commit()
                    st.success("Đã xóa sản phẩm thành công")
                    st.rerun()
                except Exception as e:
                    st.error(f"Đã xảy ra lỗi khi xóa sản phẩm: {e}")
            else:
                st.warning("Vui lòng xác nhận để xóa sản phẩm.")

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
            # Kiểm tra trùng SKU trước khi thêm
            cursor.execute("SELECT sku FROM products WHERE sku = ?", (sku,))
            if cursor.fetchone():
                st.error("SKU này đã tồn tại. Vui lòng nhập SKU khác.")
            else:
                # Thêm sản phẩm mới
                cursor.execute(
                    "INSERT INTO products(sku,name,created_at) VALUES (?,?,?)",
                    (sku, name, datetime.now())
                )

                pid = cursor.lastrowid

                for w, q in qty.items():
                    cursor.execute(
                        "INSERT INTO stock_by_warehouse(product_id,warehouse,quantity) VALUES (?,?,?)",
                        (pid, w, q)
                    )

                conn.commit()
                st.success("Đã thêm sản phẩm")
                st.rerun()
        except Exception as e:
            st.error(f"Đã xảy ra lỗi: {e}")

# ================= IMPORT EXPORT =================
elif menu == "Nhập/Xuất":
    st.header("📥📤 Nhập / Xuất kho")
    df = get_products()
    product = st.selectbox("Chọn sản phẩm", df["Tên sản phẩm"])

    pid = df[df["Tên sản phẩm"] == product]["ID"].values[0]
    warehouses = get_warehouses()

    qty = {}
    for w in warehouses:
        qty[w] = st.number_input(f"{w}", min_value=0)

    type_tx = st.radio("Loại giao dịch", ["Nhập", "Xuất"])

    if st.button("Xác nhận giao dịch"):
        try:
            for w, q in qty.items():
                cursor.execute(
                    "SELECT quantity FROM stock_by_warehouse WHERE product_id=? AND warehouse=?",
                    (pid, w)
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

                cursor.execute(
                    "SELECT id FROM stock_by_warehouse WHERE product_id=? AND warehouse=?",
                    (pid, w)
                )

                exist = cursor.fetchone()

                if exist:
                    cursor.execute(
                        "UPDATE stock_by_warehouse SET quantity=? WHERE product_id=? AND warehouse=?",
                        (new, pid, w)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO stock_by_warehouse(product_id,warehouse,quantity) VALUES (?,?,?)",
                        (pid, w, new)
                    )

                cursor.execute(
                    "INSERT INTO history(product_id,type,quantity,date,warehouse) VALUES (?,?,?,?,?)",
                    (pid, type_tx, q, datetime.now(), w)
                )

            conn.commit()
            st.success("Giao dịch thành công")
            st.rerun()

        except Exception as e:
            st.error(f"Đã xảy ra lỗi: {e}")

# ================= HISTORY =================
elif menu == "Lịch sử giao dịch":
    st.header("📜 Lịch sử giao dịch")

    cursor.execute("""
    SELECT p.name,h.type,h.quantity,h.date,h.warehouse
    FROM history h
    LEFT JOIN products p
    ON p.id=h.product_id
    ORDER BY h.date DESC
    """)

    df = pd.DataFrame(
        cursor.fetchall(),
        columns=[
            "Sản phẩm",
            "Loại",
            "Số lượng",
            "Ngày",
            "Kho"
        ]
    )

    st.dataframe(df)

# ================= EXPORT EXCEL =================
elif menu == "Xuất Excel":
    st.header("📄 Xuất Excel tồn kho")
    
    # Lấy dữ liệu tồn kho từ get_stock() (bao gồm sản phẩm và số lượng tồn kho)
    df = get_stock()

    # Lưu file Excel vào ổ đĩa
    file = "ton_kho.xlsx"
    df.to_excel(file, index=False)

    # Tạo nút tải file
    with open(file, "rb") as f:
        st.download_button(
            "⬇️ Tải file Excel",  # Đảm bảo chuỗi này được đóng đúng cách
            f,
            file_name="ton_kho.xlsx"
        )
