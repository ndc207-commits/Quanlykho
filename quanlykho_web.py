# inventory_web_full_pro5_3.py
import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

# ==== Kết nối Database ====
conn = sqlite3.connect("kho.db", check_same_thread=False)
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
    st.dataframe(
        df_stock.style.applymap(
            lambda x: 'background-color: #FFAAAA' if isinstance(x,int) and x<5 else '',
            subset=["Số lượng"]
        )
    )

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
elif menu == "Cập nhật/Xóa sản phẩm":
    st.header("Cập nhật hoặc Xóa sản phẩm")
    df = refresh_products()  # Lấy danh sách sản phẩm
    if df.empty:
        st.warning("Chưa có sản phẩm nào")
    else:
        # Chọn sản phẩm
        product = st.selectbox("Chọn sản phẩm", df["Tên sản phẩm"])
        pid = df[df["Tên sản phẩm"] == product]["ID"].values[0]
        new_name = st.text_input("Tên mới", value=product)
        new_sku = st.text_input("SKU mới", value=df[df["Tên sản phẩm"] == product]["SKU"].values[0])
        
        # Hiển thị số lượng trong các kho
        fixed_warehouses = ["Kho La Pagode", "Kho Muse", "Kho Metz Ville", "Kho Nancy"]
        qty_per_warehouse = {}

        # Lấy số lượng sản phẩm trong từng kho
        for wh in fixed_warehouses:
            cursor.execute("SELECT IFNULL(quantity, 0) FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh))
            res = cursor.fetchone()
            current_qty = res[0] if res else 0  # Nếu không có sản phẩm trong kho, số lượng = 0
            qty_per_warehouse[wh] = current_qty
        
        # Hiển thị số lượng trong kho
        st.write(f"Số lượng sản phẩm '{product}' trong các kho hiện tại:")
        st.write(qty_per_warehouse)

        # Nhập số lượng cho từng kho
        qty_inputs = {}
        st.subheader("Cập nhật số lượng cho từng kho")
        for wh in fixed_warehouses:
            qty_inputs[wh] = st.number_input(
                f"Số lượng tại {wh} (hiện tại {qty_per_warehouse[wh]})", 
                min_value=0, 
                value=qty_per_warehouse[wh], 
                step=1, 
                key=f"qty_{wh}"
            )

        col1, col2 = st.columns(2)
        with col1:
            # Cập nhật thông tin sản phẩm
            if st.button("Cập nhật"):
                cursor.execute("UPDATE products SET name=?, sku=? WHERE id=?", (new_name, new_sku, pid))
                conn.commit()
                st.success(f"Cập nhật sản phẩm {product} thành công!")

        with col2:
            # Xóa sản phẩm
            if st.button("Xóa sản phẩm"):
                # Xóa sản phẩm trong từng kho
                for wh in fixed_warehouses:
                    cursor.execute("DELETE FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh))
                    conn.commit()

                # Kiểm tra xem sản phẩm có còn tồn tại trong kho nào không
                cursor.execute("SELECT COUNT(*) FROM stock_by_warehouse WHERE product_id=?", (pid,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("DELETE FROM products WHERE id=?", (pid,))
                    conn.commit()
                    st.success(f"Đã xóa sản phẩm {product} khỏi tất cả các kho và danh sách sản phẩm!")
                else:
                    st.warning(f"Sản phẩm {product} vẫn còn tồn tại trong kho, không thể xóa sản phẩm.")
# ==== Nhập/Xuất kho cho 4 kho cố định ====
elif menu == "Nhập/Xuất":
    st.header("Nhập / Xuất kho cho 4 kho cố định")
    df = refresh_products()  # Lấy danh sách sản phẩm
    if df.empty:
        st.warning("Chưa có sản phẩm nào")
    else:
        # Chọn sản phẩm
        product = st.selectbox("Chọn sản phẩm", df["Tên sản phẩm"])
        pid = df[df["Tên sản phẩm"] == product]["ID"].values[0]

        # Kho cố định (4 kho)
        fixed_warehouses = ["Kho La Pagode", "Kho Muse", "Kho Metz Ville", "Kho Nancy"]
        qty_per_warehouse = {}

        # Hiển thị số lượng sản phẩm trong từng kho
        for wh in fixed_warehouses:
            cursor.execute("SELECT IFNULL(quantity, 0) FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh))
            res = cursor.fetchone()
            current_qty = res[0] if res else 0  # Nếu không có sản phẩm trong kho, số lượng = 0
            qty_per_warehouse[wh] = current_qty

        st.write(f"Số lượng sản phẩm '{product}' trong các kho hiện tại:")
        st.write(qty_per_warehouse)

        # Nhập số lượng cho từng kho
        qty_inputs = {}
        st.subheader("Nhập / Xuất số lượng cho từng kho")
        for wh in fixed_warehouses:
            qty_inputs[wh] = st.number_input(
                f"Số lượng tại {wh} (hiện tại {qty_per_warehouse[wh]})", 
                min_value=0, 
                value=qty_per_warehouse[wh], 
                step=1, 
                key=f"qty_{wh}"
            )

        # Nhập số lượng cho sản phẩm chung
        total_qty = st.number_input(f"Số lượng {product} muốn nhập/xuất (Tổng số lượng trong tất cả kho)", min_value=0, step=1)

        # Chọn loại giao dịch: Nhập hay Xuất
        type_tx = st.radio("Loại giao dịch", ["Nhập", "Xuất"])

        # Xử lý Nhập kho
        if st.button("Xác nhận Nhập kho"):
            for wh in fixed_warehouses:
                qty = qty_inputs[wh]
                # Kiểm tra xem kho đã có sản phẩm chưa
                cursor.execute("SELECT quantity FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh))
                res = cursor.fetchone()
                if res:
                    current_qty = res[0]
                    new_qty = current_qty + qty  # Thêm số lượng khi nhập
                    cursor.execute("UPDATE stock_by_warehouse SET quantity=? WHERE product_id=? AND warehouse=?", 
                                   (new_qty, pid, wh))
                else:
                    cursor.execute("INSERT INTO stock_by_warehouse(product_id, warehouse, quantity) VALUES (?,?,?)",
                                   (pid, wh, qty))
                conn.commit()

            st.success(f"Nhập kho {sum(qty_inputs.values())} sản phẩm '{product}' thành công!")

        # Xử lý Xuất kho
        if st.button("Xác nhận Xuất kho"):
            total_needed = sum(qty_inputs.values())
            cursor.execute("SELECT IFNULL(SUM(quantity), 0) FROM stock_by_warehouse WHERE product_id=?", (pid,))
            total_qty = cursor.fetchone()[0]

            if total_needed > total_qty:
                st.error(f"Tổng cần xuất {total_needed}, nhưng tồn kho hiện tại {total_qty}")
                st.stop()

            for wh in fixed_warehouses:
                qty = qty_inputs[wh]
                cursor.execute("SELECT quantity FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh))
                res = cursor.fetchone()
                current_qty = res[0] if res else 0
                if current_qty >= qty:  # Kiểm tra tồn kho
                    new_qty = current_qty - qty  # Trừ số lượng khi xuất
                    cursor.execute("UPDATE stock_by_warehouse SET quantity=? WHERE product_id=? AND warehouse=?",
                                   (new_qty, pid, wh))
                    conn.commit()
                else:
                    st.error(f"Không đủ sản phẩm trong kho {wh} để xuất {qty} sản phẩm.")
                    st.stop()

            st.success(f"Xuất kho {sum(qty_inputs.values())} sản phẩm '{product}' thành công.")
# ==== Báo cáo hàng sắp hết ====
elif menu=="Báo cáo hàng sắp hết":
    st.header("Hàng tồn sắp hết / tồn lâu")
    days_limit = st.number_input("Số ngày tồn tối đa", value=180)
    qty_limit = st.number_input("Số lượng tối thiểu", value=3)
    date_limit = (datetime.now()-timedelta(days=days_limit)).strftime("%Y-%m-%d")

    # Lấy tổng tồn kho từng sản phẩm
    cursor.execute("""
        SELECT p.id, p.sku, p.name, IFNULL(SUM(s.quantity),0) as Tong_ton, p.created_at
        FROM products p
        LEFT JOIN stock_by_warehouse s ON p.id=s.product_id
        GROUP BY p.id
        HAVING Tong_ton < ? OR p.created_at < ?
    """, (qty_limit, date_limit))

    rows = cursor.fetchall()
    df_low = pd.DataFrame(rows, columns=["ID","SKU","Tên sản phẩm","Số lượng","Ngày tạo"])

    # Highlight hàng tồn <5
    st.dataframe(
        df_low.style.applymap(
            lambda x: 'background-color: #FFAAAA' if isinstance(x,int) and x<5 else '',
            subset=["Số lượng"]
        )
    )
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
