# inventory_web_full_pro5_2.py
import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

# ==== Kết nối Database ====
conn = sqlite3.connect("inventory_web_full_pro5_2.db", check_same_thread=False)
cursor = conn.cursor()

# ==== Tạo bảng nếu chưa có ====
cursor.execute("""
CREATE TABLE IF NOT EXISTS products(
id INTEGER PRIMARY KEY AUTOINCREMENT,
sku TEXT UNIQUE,
name TEXT,
created_at TEXT
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
employee TEXT,
warehouse TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS employees(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
role TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS warehouses(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT
)
""")
conn.commit()

# ==== Dữ liệu mẫu ====
cursor.execute("SELECT COUNT(*) FROM employees")
if cursor.fetchone()[0]==0:
    employees = [("Admin","Manager"), ("Hanh","Staff"), ("Linh","Staff")]
    cursor.executemany("INSERT INTO employees(name, role) VALUES (?,?)", employees)
    conn.commit()

cursor.execute("SELECT COUNT(*) FROM warehouses")
if cursor.fetchone()[0]==0:
    warehouses = [("Kho La Pagode",), ("Kho Muse",), ("Kho Metz Ville",), ("Kho Nancy",)]
    cursor.executemany("INSERT INTO warehouses(name) VALUES (?)", warehouses)
    conn.commit()

# ==== Sidebar menu ====
st.sidebar.title("QUẢN LÝ KHO AMME THE")
menu = st.sidebar.radio("Điều hướng", ["Kho hàng","Thêm sản phẩm","Cập nhật/Xóa sản phẩm","Nhập/Xuất","Báo cáo hàng sắp hết","Lịch sử giao dịch","Xuất Excel"])

# ==== Hàm tiện ích ====
def refresh_products():
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=["ID","SKU","Tên sản phẩm","Ngày tạo"])
    return df

def refresh_stock():
    cursor.execute("""
    SELECT p.id, p.sku, p.name, w.name as Kho, IFNULL(s.quantity,0) as Số_lượng
    FROM products p
    CROSS JOIN warehouses w
    LEFT JOIN stock_by_warehouse s ON p.id=s.product_id AND s.warehouse=w.name
    """)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=["ID","SKU","Tên sản phẩm","Kho","Số lượng"])
    return df

def highlight_low(x):
    return ['background-color: #FFAAAA' if v<5 else '' for v in x["Số lượng"]]

# ==== Kho hàng ====
if menu=="Kho hàng":
    st.header("Tồn kho theo từng kho")
    df_stock = refresh_stock()
    st.dataframe(df_stock.style.apply(highlight_low, axis=None))

# ==== Thêm sản phẩm ====
elif menu=="Thêm sản phẩm":
    st.header("Thêm sản phẩm mới với số lượng từng kho")
    sku = st.text_input("Mã sản phẩm (SKU)")
    name = st.text_input("Tên sản phẩm")

    # Lấy danh sách kho
    cursor.execute("SELECT name FROM warehouses")
    warehouses_list = [row[0] for row in cursor.fetchall()]

    # Nhập số lượng cho từng kho
    qty_dict = {}
    for wh in warehouses_list:
        qty_dict[wh] = st.number_input(f"Số lượng kho {wh}", min_value=0, step=1, key=f"qty_{wh}")

    if st.button("Thêm sản phẩm"):
        if sku and name:
            try:
                # Thêm vào bảng products
                cursor.execute("INSERT INTO products(sku,name,created_at) VALUES (?,?,?)",
                               (sku,name,datetime.now().strftime("%Y-%m-%d")))
                pid = cursor.lastrowid

                # Thêm số lượng từng kho
                for wh, qty in qty_dict.items():
                    if qty>0:
                        cursor.execute("INSERT INTO stock_by_warehouse(product_id,warehouse,quantity) VALUES (?,?,?)",
                                       (pid, wh, qty))

                conn.commit()
                st.success(f"Thêm sản phẩm '{name}' thành công với số lượng từng kho!")
            except sqlite3.IntegrityError:
                st.error("SKU đã tồn tại!")
        else:
            st.warning("Vui lòng nhập đầy đủ SKU và tên sản phẩm")

# ==== Cập nhật/Xóa sản phẩm ====
elif menu=="Cập nhật/Xóa sản phẩm":
    st.header("Cập nhật hoặc Xóa sản phẩm")
    df = refresh_products()
    if df.empty:
        st.warning("Chưa có sản phẩm nào")
    else:
        product = st.selectbox("Chọn sản phẩm", df["Tên sản phẩm"])
        pid = df[df["Tên sản phẩm"]==product]["ID"].values[0]
        new_name = st.text_input("Tên mới", value=product)
        new_sku = st.text_input("SKU mới", value=df[df["Tên sản phẩm"]==product]["SKU"].values[0])
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Cập nhật"):
                cursor.execute("UPDATE products SET name=?, sku=? WHERE id=?",(new_name,new_sku,pid))
                conn.commit()
                st.success(f"Cập nhật sản phẩm {product} thành công!")
        with col2:
            if st.button("Xóa sản phẩm"):
                cursor.execute("DELETE FROM products WHERE id=?",(pid,))
                cursor.execute("DELETE FROM stock_by_warehouse WHERE product_id=?",(pid,))
                conn.commit()
                st.success(f"Đã xóa sản phẩm {product}!")

# ==== Nhập/Xuất kho ====
elif menu=="Nhập/Xuất":
    st.header("Nhập / Xuất kho")
    df = refresh_products()
    if df.empty:
        st.warning("Chưa có sản phẩm nào")
    else:
        product = st.selectbox("Chọn sản phẩm", df["Tên sản phẩm"])
        pid = df[df["Tên sản phẩm"]==product]["ID"].values[0]
        type_tx = st.radio("Loại giao dịch", ["Nhập","Xuất"])
        qty = st.number_input("Số lượng mỗi kho", min_value=1, step=1)
        employees_list = st.multiselect(
            "Nhân viên thực hiện",
            [row[0] for row in cursor.execute("SELECT name FROM employees").fetchall()],
            default=["Hanh"]
        )
        warehouses_list = st.multiselect(
            "Kho thực hiện",
            [row[0] for row in cursor.execute("SELECT name FROM warehouses").fetchall()],
            default=["Kho La Pagode"]
        )

        if st.button("Xác nhận"):
            if type_tx=="Xuất":
                # Kiểm tra tổng tồn tất cả kho
                cursor.execute("SELECT IFNULL(SUM(quantity),0) FROM stock_by_warehouse WHERE product_id=?",(pid,))
                total_qty = cursor.fetchone()[0]
                total_needed = qty * len(warehouses_list)
                if total_needed > total_qty:
                    st.error(f"Không đủ hàng để xuất! Tồn tổng {total_qty}, cần {total_needed}")
                    st.stop()
            for emp in employees_list:
                for wh in warehouses_list:
                    # Cập nhật stock_by_warehouse
                    cursor.execute("SELECT quantity FROM stock_by_warehouse WHERE product_id=? AND warehouse=?",(pid,wh))
                    res = cursor.fetchone()
                    if res:
                        current_qty = res[0]
                        new_qty = current_qty + qty if type_tx=="Nhập" else current_qty - qty
                        cursor.execute("UPDATE stock_by_warehouse SET quantity=? WHERE product_id=? AND warehouse=?",
                                       (new_qty,pid,wh))
                    else:
                        if type_tx=="Nhập":
                            cursor.execute("INSERT INTO stock_by_warehouse(product_id,warehouse,quantity) VALUES (?,?,?)",
                                           (pid,wh,qty))
                        else:
                            st.error(f"Kho {wh} chưa có sản phẩm này!")
                            st.stop()
                    # Lưu lịch sử
                    cursor.execute(
                        "INSERT INTO history(product_id,type,quantity,date,employee,warehouse) VALUES (?,?,?,?,?,?)",
                        (pid,type_tx,qty,datetime.now().strftime("%Y-%m-%d %H:%M:%S"),emp,wh)
                    )
            conn.commit()
            st.success(f"{type_tx} thành công {qty} sản phẩm '{product}' cho {len(warehouses_list)} kho và {len(employees_list)} nhân viên.")

# ==== Báo cáo hàng sắp hết ====
elif menu=="Báo cáo hàng sắp hết":
    st.header("Hàng tồn sắp hết")
    df_stock = refresh_stock()
    df_low = df_stock[df_stock["Số lượng"]<5]
    st.dataframe(df_low.style.apply(highlight_low, axis=None))

# ==== Lịch sử giao dịch ====
elif menu=="Lịch sử giao dịch":
    st.header("Lịch sử nhập xuất")
    cursor.execute("SELECT * FROM history")
    rows = cursor.fetchall()
    df_hist = pd.DataFrame(rows, columns=["ID","ProductID","Loại","Số lượng","Ngày giờ","Nhân viên","Kho"])
    st.dataframe(df_hist)

# ==== Xuất Excel ====
elif menu=="Xuất Excel":
    st.header("Xuất Excel")
    df_stock = refresh_stock()
    file_name = f"Inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df_stock.to_excel(file_name,index=False)
    st.success(f"Đã xuất Excel: {file_name}")
    st.download_button("Tải file Excel", data=open(file_name,"rb"), file_name=file_name)
