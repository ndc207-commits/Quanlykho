# inventory_web_full_pro5.py
import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

# ==== Kết nối Database ====
conn = sqlite3.connect("inventory_web_full_pro5.db", check_same_thread=False)
cursor = conn.cursor()

# ==== Tạo bảng nếu chưa có ====
cursor.execute("""
CREATE TABLE IF NOT EXISTS products(
id INTEGER PRIMARY KEY AUTOINCREMENT,
sku TEXT UNIQUE,
name TEXT,
quantity INTEGER,
created_at TEXT
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
name TEXT,
location TEXT
)
""")
conn.commit()

# ==== Thêm dữ liệu mẫu ====
cursor.execute("SELECT COUNT(*) FROM employees")
if cursor.fetchone()[0]==0:
    employees = [("Admin","Manager"), ("Hanh","Staff"), ("Linh","Staff")]
    cursor.executemany("INSERT INTO employees(name, role) VALUES (?,?)", employees)
    conn.commit()

cursor.execute("SELECT COUNT(*) FROM warehouses")
if cursor.fetchone()[0]==0:
    warehouses = [("Kho La Pagode","Metz"), ("Kho Muse","Muse"), ("Kho Metz Vilee","Metz Ville"), ("Kho Nancy","Nancy")]
    cursor.executemany("INSERT INTO warehouses(name, location) VALUES (?,?)", warehouses)
    conn.commit()

# ==== Sidebar menu ====
st.sidebar.title("Quản Lý Kho Amme Thé")
menu = st.sidebar.radio("Điều hướng", ["Kho hàng","Thêm sản phẩm","Cập nhật/Xóa sản phẩm","Nhập/Xuất","Báo cáo hàng sắp hết","Lịch sử giao dịch","Xuất Excel"])

# ==== Hàm tiện ích ====
def refresh_products():
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=["ID","SKU","Tên sản phẩm","Số lượng","Ngày tạo"])
    return df

def highlight_low(x):
    return ['background-color: #FFAAAA' if v<5 else '' for v in x["Số lượng"]]

# ==== Kho hàng ====
if menu=="Kho hàng":
    st.header("Danh sách sản phẩm")
    df = refresh_products()
    st.dataframe(df.style.apply(highlight_low, axis=None))

# ==== Thêm sản phẩm ====
elif menu=="Thêm sản phẩm":
    st.header("Thêm sản phẩm mới")
    sku = st.text_input("Mã sản phẩm (SKU)")
    name = st.text_input("Tên sản phẩm")
    qty = st.number_input("Số lượng ban đầu", min_value=0, step=1)
    if st.button("Thêm sản phẩm"):
        if sku and name:
            try:
                cursor.execute("INSERT INTO products(sku,name,quantity,created_at) VALUES (?,?,?,?)",
                               (sku,name,qty,datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.success(f"Thêm sản phẩm {name} thành công!")
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
        qty = st.number_input("Số lượng", min_value=1, step=1)
        employees_list = st.multiselect("Nhân viên", [row[0] for row in cursor.execute("SELECT name FROM employees").fetchall()], default=["Hanh"])
        warehouses_list = st.multiselect("Kho", [row[0] for row in cursor.execute("SELECT name FROM warehouses").fetchall()], default=["Kho La Pagode"])
        if st.button("Xác nhận"):
            for emp in employees_list:
                for wh in warehouses_list:
                    if type_tx=="Nhập":
                        cursor.execute("UPDATE products SET quantity=quantity+? WHERE id=?",(qty,pid))
                    else:
                        if cursor.execute("SELECT quantity FROM products WHERE id=?",(pid,)).fetchone()[0]<qty:
                            st.error("Không đủ hàng để xuất!")
                            st.stop()
                        cursor.execute("UPDATE products SET quantity=quantity-? WHERE id=?",(qty,pid))
                    cursor.execute("INSERT INTO history(product_id,type,quantity,date,employee,warehouse) VALUES (?,?,?,?,?,?)",
                                   (pid,type_tx,qty,datetime.now().strftime("%Y-%m-%d %H:%M:%S"),emp,wh))
            conn.commit()
            st.success(f"{type_tx} thành công {qty} sản phẩm {product}")

# ==== Báo cáo hàng sắp hết ====
elif menu=="Báo cáo hàng sắp hết":
    st.header("Hàng tồn sắp hết / tồn lâu")
    days_limit = st.number_input("Số ngày tồn tối đa", value=180)
    qty_limit = st.number_input("Số lượng tối thiểu", value=3)
    date_limit = (datetime.now()-timedelta(days=days_limit)).strftime("%Y-%m-%d")
    cursor.execute("SELECT * FROM products WHERE quantity<? OR created_at<?",(qty_limit,date_limit))
    rows = cursor.fetchall()
    df_low = pd.DataFrame(rows, columns=["ID","SKU","Tên sản phẩm","Số lượng","Ngày tạo"])
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
    df = refresh_products()
    file_name = f"Kho{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(file_name,index=False)
    st.success(f"Đã xuất Excel: {file_name}")
    st.download_button("Tải file Excel", data=open(file_name,"rb"), file_name=file_name)
