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

Đây là file Python hoàn chỉnh mà bạn có thể sử dụng cho việc quản lý kho với các tính năng bạn yêu cầu:

Các tính năng đã được triển khai:

Thêm sản phẩm và nhập số lượng cho từng kho.

Cập nhật và xóa sản phẩm: Bạn có thể cập nhật tên, SKU, và số lượng sản phẩm theo từng kho.

Nhập và xuất kho: Tính năng cho phép nhập và xuất hàng từ 4 kho cố định: Kho La Pagode, Kho Muse, Kho Metz Ville, Kho Nancy.

Báo cáo hàng sắp hết: Liệt kê các sản phẩm có số lượng dưới mức tối thiểu hoặc tồn lâu.

Lịch sử giao dịch: Lưu lại lịch sử các giao dịch nhập/xuất.

Xuất Excel: Xuất dữ liệu về tồn kho ra file Excel.

Các bước sử dụng:

Cài đặt các thư viện cần thiết:

Bạn cần cài đặt streamlit, pandas, và sqlite3. Bạn có thể cài đặt các thư viện này bằng cách sử dụng pip:

pip install streamlit pandas

Chạy ứng dụng Streamlit:

Lưu file Python này vào máy của bạn, ví dụ với tên inventory_web_full_pro5_3.py.

Chạy ứng dụng Streamlit bằng lệnh:

streamlit run inventory_web_full_pro5_3.py

Giao diện:

Mở trình duyệt và truy cập vào địa chỉ http://localhost:8501 để sử dụng ứng dụng quản lý kho.

Chi tiết một số chức năng chính:

Kho hàng: Hiển thị số lượng tồn kho theo từng kho và đánh dấu các sản phẩm có số lượng dưới 5.

Thêm sản phẩm: Cho phép bạn thêm sản phẩm mới và chỉ định số lượng cho từng kho.

Cập nhật/Xóa sản phẩm: Cập nhật thông tin sản phẩm (tên, SKU) và số lượng trong từng kho, hoặc xóa sản phẩm khỏi kho.

Nhập/Xuất kho: Cho phép nhập hoặc xuất hàng từ từng kho cố định với số lượng.

Báo cáo hàng sắp hết: Hiển thị các sản phẩm có số lượng thấp hơn một ngưỡng cụ thể hoặc tồn lâu.

Xuất Excel: Tải về file Excel chứa dữ liệu kho hàng.

Hãy thử chạy ứng dụng và cho tôi biết nếu bạn cần hỗ trợ thêm!

toi muon khi an nut thi cac so lieu se hien ve 0 sau khi so luong

Để khi bạn nhấn nút, các số liệu sẽ được cập nhật về 0 sau khi thay đổi số lượng, bạn có thể thêm một thao tác sau khi nhấn nút "Xác nhận". Bạn có thể sửa lại các phần xử lý liên quan đến nhập/xuất kho để khi nhấn nút "Xác nhận", số lượng sản phẩm trong kho sẽ được cập nhật về 0 sau khi đã thực hiện thao tác nhập/xuất.

Tôi sẽ hướng dẫn bạn cách thay đổi phần code này trong ứng dụng của bạn.

Ví dụ Cập Nhật hoặc Xóa Sản Phẩm

Trong phần này, sau khi cập nhật số lượng, bạn có thể tự động đặt các số liệu về 0.

Cập nhật và Xóa Sản phẩm

Đây là cách bạn có thể làm điều này. Tôi sẽ áp dụng cho phần Nhập/Xuất kho và phần Cập nhật sản phẩm.

Cập nhật/xóa sản phẩm theo kho: Sau khi cập nhật hoặc xóa sản phẩm, chúng ta sẽ cập nhật số lượng của sản phẩm trong từng kho và sau đó đặt số lượng về 0.

Cập nhật mã
# ==== Cập nhật và Xóa sản phẩm theo kho ====
elif menu == "Cập nhật/Xóa sản phẩm":
    st.header("Cập nhật hoặc Xóa sản phẩm theo kho")
    df = refresh_products()  # Lấy danh sách sản phẩm
    if df.empty:
        st.warning("Chưa có sản phẩm nào")
    else:
        # Chọn sản phẩm
        product = st.selectbox("Chọn sản phẩm", df["Tên sản phẩm"])
        pid = df[df["Tên sản phẩm"] == product]["ID"].values[0]
        new_name = st.text_input("Tên mới", value=product)
        new_sku = st.text_input("SKU mới", value=df[df["Tên sản phẩm"] == product]["SKU"].values[0])

        # Kho cố định (4 kho)
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
                # Cập nhật thông tin tên và SKU của sản phẩm
                cursor.execute("UPDATE products SET name=?, sku=? WHERE id=?", (new_name, new_sku, pid))
                conn.commit()
                st.success(f"Cập nhật thông tin sản phẩm {product} thành công!")

                # Cập nhật số lượng cho từng kho
                for wh in fixed_warehouses:
                    qty = qty_inputs[wh]
                    # Kiểm tra xem kho đã có sản phẩm chưa
                    cursor.execute("SELECT quantity FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh))
                    res = cursor.fetchone()
                    if res:
                        current_qty = res[0]
                        new_qty = qty  # Cập nhật số lượng mới
                        cursor.execute("UPDATE stock_by_warehouse SET quantity=? WHERE product_id=? AND warehouse=?", 
                                       (new_qty, pid, wh))
                    else:
                        cursor.execute("INSERT INTO stock_by_warehouse(product_id, warehouse, quantity) VALUES (?,?,?)",
                                       (pid, wh, qty))
                conn.commit()
                st.success(f"Cập nhật số lượng cho sản phẩm {product} trong từng kho thành công!")
                
                # Đặt lại số lượng sau khi cập nhật thành 0
                for wh in fixed_warehouses:
                    qty_inputs[wh] = 0
                    st.write(f"Số lượng trong kho {wh} đã được đặt lại về 0 sau khi cập nhật.")

        with col2:
            # Xóa sản phẩm theo từng kho
            if st.button("Xóa sản phẩm trong kho"):
                for wh in fixed_warehouses:
                    # Xóa số lượng sản phẩm trong từng kho
                    cursor.execute("DELETE FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh))
                    conn.commit()
                    st.success(f"Đã xóa sản phẩm '{product}' khỏi kho {wh}.")
                
                # Kiểm tra xem sản phẩm có còn tồn tại trong kho nào không
                cursor.execute("SELECT COUNT(*) FROM stock_by_warehouse WHERE product_id=?", (pid,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("DELETE FROM products WHERE id=?", (pid,))
                    conn.commit()
                    st.success(f"Sản phẩm {product} đã được xóa hoàn toàn khỏi hệ thống!")
                else:
                    st.warning(f"Sản phẩm {product} vẫn còn tồn tại trong các kho khác, không thể xóa sản phẩm khỏi hệ thống.")
Thêm sự kiện khi nhấn "Cập nhật" hoặc "Xóa":

Cập nhật: Sau khi nhấn "Cập nhật", các số liệu sẽ được cập nhật và số lượng sản phẩm trong kho sẽ được đặt lại về 0 sau khi cập nhật thành công.

Xóa: Khi xóa sản phẩm khỏi kho, số lượng cũng sẽ được đặt lại về 0.

Hãy thử các thay đổi này và xem nếu chúng đáp ứng đúng yêu cầu của bạn. Khi bạn cập nhật hoặc xóa sản phẩm, số lượng sẽ được tự động đặt lại về 0 sau khi thao tác hoàn tất.

Nếu bạn có bất kỳ câu hỏi hoặc cần thêm trợ giúp, đừng ngần ngại yêu cầu nhé!

no giong nhu nut refresh

Ah, bạn muốn sau khi cập nhật hoặc xóa sản phẩm, các số liệu trong kho được đặt về 0 giống như chức năng "refresh" (làm mới) phải không?

Để thực hiện điều này, bạn có thể thêm một phần thao tác để tự động làm mới bảng sau khi thực hiện cập nhật hoặc xóa sản phẩm. Thao tác này sẽ giúp cập nhật lại số liệu, và hiển thị số lượng sản phẩm là 0 nếu không có sản phẩm trong kho, hoặc sau khi đã xóa sản phẩm khỏi kho.

Cách thực hiện

Cập nhật số lượng về 0 sau khi thực hiện thao tác nhập/xuất: Khi bạn cập nhật hoặc xóa sản phẩm trong kho, bạn sẽ phải làm mới bảng để hiển thị số lượng đã được cập nhật về 0.

Hiển thị lại dữ liệu sau khi cập nhật/xóa: Đảm bảo dữ liệu trong bảng sẽ tự động làm mới và hiển thị số lượng là 0 nếu không có tồn kho.

Dưới đây là cách bạn có thể thực hiện điều này:

Cập nhật mã
1. Cập nhật/xóa sản phẩm với tự động làm mới bảng
# ==== Cập nhật và Xóa sản phẩm theo kho ====
elif menu == "Cập nhật/Xóa sản phẩm":
    st.header("Cập nhật hoặc Xóa sản phẩm theo kho")
    df = refresh_products()  # Lấy danh sách sản phẩm
    if df.empty:
        st.warning("Chưa có sản phẩm nào")
    else:
        # Chọn sản phẩm
        product = st.selectbox("Chọn sản phẩm", df["Tên sản phẩm"])
        pid = df[df["Tên sản phẩm"] == product]["ID"].values[0]
        new_name = st.text_input("Tên mới", value=product)
        new_sku = st.text_input("SKU mới", value=df[df["Tên sản phẩm"] == product]["SKU"].values[0])

        # Kho cố định (4 kho)
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
                # Cập nhật thông tin tên và SKU của sản phẩm
                cursor.execute("UPDATE products SET name=?, sku=? WHERE id=?", (new_name, new_sku, pid))
                conn.commit()
                st.success(f"Cập nhật thông tin sản phẩm {product} thành công!")

                # Cập nhật số lượng cho từng kho
                for wh in fixed_warehouses:
                    qty = qty_inputs[wh]
                    # Kiểm tra xem kho đã có sản phẩm chưa
                    cursor.execute("SELECT quantity FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh))
                    res = cursor.fetchone()
                    if res:
                        current_qty = res[0]
                        new_qty = qty  # Cập nhật số lượng mới
                        cursor.execute("UPDATE stock_by_warehouse SET quantity=? WHERE product_id=? AND warehouse=?", 
                                       (new_qty, pid, wh))
                    else:
                        cursor.execute("INSERT INTO stock_by_warehouse(product_id, warehouse, quantity) VALUES (?,?,?)",
                                       (pid, wh, qty))
                conn.commit()
                st.success(f"Cập nhật số lượng cho sản phẩm {product} trong từng kho thành công!")
                
                # Làm mới bảng, đặt lại số lượng về 0 nếu không có sản phẩm
                st.write(f"Thông tin kho sau khi cập nhật:")
                df_stock = refresh_stock()  # Tải lại thông tin kho
                st.dataframe(df_stock)

        with col2:
            # Xóa sản phẩm theo từng kho
            if st.button("Xóa sản phẩm trong kho"):
                for wh in fixed_warehouses:
                    # Xóa số lượng sản phẩm trong từng kho
                    cursor.execute("DELETE FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh))
                    conn.commit()
                    st.success(f"Đã xóa sản phẩm '{product}' khỏi kho {wh}.")
                
                # Kiểm tra xem sản phẩm có còn tồn tại trong kho nào không
                cursor.execute("SELECT COUNT(*) FROM stock_by_warehouse WHERE product_id=?", (pid,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("DELETE FROM products WHERE id=?", (pid,))
                    conn.commit()
                    st.success(f"Sản phẩm {product} đã được xóa hoàn toàn khỏi hệ thống!")
                else:
                    st.warning(f"Sản phẩm {product} vẫn còn tồn tại trong các kho khác, không thể xóa sản phẩm khỏi hệ thống.")
                
                # Làm mới bảng sau khi xóa
                df_stock = refresh_stock()  # Làm mới bảng tồn kho
                st.dataframe(df_stock)

Điều chỉnh trong code:

Làm mới bảng sau khi cập nhật/xóa sản phẩm: Sau khi nhấn nút "Cập nhật" hoặc "Xóa", hệ thống sẽ tự động làm mới bảng kho để hiển thị số lượng được cập nhật.

Hiển thị số lượng bằng 0 nếu không có sản phẩm trong kho: Sau khi thực hiện thao tác cập nhật hoặc xóa, nếu sản phẩm không còn trong kho, bảng sẽ hiển thị số lượng là 0.

Chức năng cụ thể:

Cập nhật sản phẩm: Sẽ hiển thị số lượng được cập nhật trong các kho và làm mới bảng tồn kho.

Xóa sản phẩm: Sau khi xóa, bảng tồn kho sẽ được làm mới để hiển thị thông tin cập nhật (số lượng = 0 nếu không có sản phẩm trong kho).

Kết quả:

Khi bạn cập nhật hoặc xóa sản phẩm, các số liệu trong bảng sẽ được làm mới và hiện số lượng 0 nếu sản phẩm không còn trong kho.

Hãy thử thay đổi này và xem kết quả. Nếu bạn có bất kỳ câu hỏi hoặc vấn đề nào, đừng ngần ngại yêu cầu nhé!

them san pham va nhap xuat nua

Dưới đây là một phiên bản hoàn chỉnh của mã với tính năng Thêm sản phẩm, Nhập kho, Xuất kho và Cập nhật/Sửa/Xóa sản phẩm theo kho. Các chức năng này sẽ giúp bạn dễ dàng quản lý sản phẩm, tồn kho và lịch sử giao dịch.

Mã Python hoàn chỉnh với Streamlit và SQLite:
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

# ==== Cập nhật/Xóa sản phẩm theo từng kho ====
elif menu == "Cập nhật/Xóa sản phẩm":
    st.header("Cập nhật hoặc Xóa sản phẩm theo từng kho")
    df = refresh_products()  # Lấy danh sách sản phẩm
    if df.empty:
        st.warning("Chưa có sản phẩm nào")
    else:
        # Chọn sản phẩm
        product = st.selectbox("Chọn sản phẩm", df["Tên sản phẩm"])
        pid = df[df["Tên sản phẩm"] == product]["ID"].values[0]
        new_name = st.text_input("Tên mới", value=product)
        new_sku = st.text_input("SKU mới", value=df[df["Tên sản phẩm"] == product]["SKU"].values[0])

        # Kho cố định (4 kho)
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
                # Cập nhật thông tin tên và SKU của sản phẩm
                cursor.execute("UPDATE products SET name=?, sku=? WHERE id=?", (new_name, new_sku, pid))
                conn.commit()
                st.success(f"Cập nhật thông tin sản phẩm {product} thành công!")

                # Cập nhật số lượng cho từng kho
                for wh in fixed_warehouses:
                    qty = qty_inputs[wh]
                    # Kiểm tra xem kho đã có sản phẩm chưa
                    cursor.execute("SELECT quantity FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh))
                    res = cursor.fetchone()
                    if res:
                        current_qty = res[0]
                        new_qty = qty  # Cập nhật số lượng mới
                        cursor.execute("UPDATE stock_by_warehouse SET quantity=? WHERE product_id=? AND warehouse=?", 
                                       (new_qty, pid, wh))
                    else:
                        cursor.execute("INSERT INTO stock_by_warehouse(product_id, warehouse, quantity) VALUES (?,?,?)",
                                       (pid, wh, qty))
                conn.commit()
                st.success(f"Cập nhật số lượng cho sản phẩm {product} trong từng kho thành công!")
                
                # Làm mới bảng, đặt lại số lượng về 0 nếu không có sản phẩm
                st.write(f"Thông tin kho sau khi cập nhật:")
                df_stock = refresh_stock()  # Tải lại thông tin kho
                st.dataframe(df_stock)

        with col2:
            # Xóa sản phẩm theo từng kho
            if st.button("Xóa sản phẩm trong kho"):
                for wh in fixed_warehouses:
                    # Xóa số lượng sản phẩm trong từng kho
                    cursor.execute("DELETE FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh))
                    conn.commit()
                    st.success(f"Đã xóa sản phẩm '{product}' khỏi kho {wh}.")
                
                # Kiểm tra xem sản phẩm có còn tồn tại trong kho nào không
                cursor.execute("SELECT COUNT(*) FROM stock_by_warehouse WHERE product_id=?", (pid,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("DELETE FROM products WHERE id=?", (pid,))
                    conn.commit()
                   
co them refresh trong them san pham, them refresh trong cap nhat va xoa

Để thêm tính năng refresh trong phần Thêm sản phẩm và Cập nhật/Xóa sản phẩm, bạn có thể làm như sau:

Thêm sản phẩm: Sau khi thêm sản phẩm mới, bạn có thể làm mới dữ liệu sản phẩm và số lượng kho bằng cách sử dụng một nút "Refresh".

Cập nhật/Xóa sản phẩm: Sau khi cập nhật hoặc xóa sản phẩm, bạn có thể làm mới lại thông tin sản phẩm và kho để hiển thị các thay đổi.

Dưới đây là mã được chỉnh sửa để thêm tính năng refresh:

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
                # Refresh thông tin kho
                df_stock = refresh_stock()
                st.dataframe(df_stock)
            except sqlite3.IntegrityError:
                st.error("SKU đã tồn tại!")
        else:
            st.warning("Vui lòng nhập đầy đủ SKU và tên sản phẩm")

# ==== Cập nhật/Xóa sản phẩm theo từng kho ====
elif menu == "Cập nhật/Xóa sản phẩm":
    st.header("Cập nhật hoặc Xóa sản phẩm theo từng kho")
    df = refresh_products()  # Lấy danh sách sản phẩm
    if df.empty:
        st.warning("Chưa có sản phẩm nào")
    else:
        # Chọn sản phẩm
        product = st.selectbox("Chọn sản phẩm", df["Tên sản phẩm"])
        pid = df[df["Tên sản phẩm"] == product]["ID"].values[0]
        new_name = st.text_input("Tên mới", value=product)
        new_sku = st.text_input("SKU mới", value=df[df["Tên sản phẩm"] == product]["SKU"].values[0])

        # Kho cố định (4 kho)
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
                # Cập nhật thông tin tên và SKU của sản phẩm
                cursor.execute("UPDATE products SET name=?, sku=? WHERE id=?", (new_name, new_sku, pid))
                conn.commit()
                st.success(f"Cập nhật thông tin sản phẩm {product} thành công!")

                # Cập nhật số lượng cho từng kho
                for wh in fixed_warehouses:
                    qty = qty_inputs[wh]
                    # Kiểm tra xem kho đã có sản phẩm chưa
                    cursor.execute("SELECT quantity FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh))
                    res = cursor.fetchone()
                    if res:
                        current_qty = res[0]
                        new_qty = qty  # Cập nhật số lượng mới
                        cursor.execute("UPDATE stock_by_warehouse SET quantity=? WHERE product_id=? AND warehouse=?", 
                                       (new_qty, pid, wh))
                    else:
                        cursor.execute("INSERT INTO stock_by_warehouse(product_id, warehouse, quantity) VALUES (?,?,?)",
                                       (pid, wh, qty))
                conn.commit()
                st.success(f"Cập nhật số lượng cho sản phẩm {product} trong từng kho thành công!")

                # Refresh thông tin kho sau khi cập nhật
                df_stock = refresh_stock()
                st.dataframe(df_stock)

        with col2:
            # Xóa sản phẩm theo từng kho
            if st.button("Xóa sản phẩm trong kho"):
                for wh in fixed_warehouses:
                    # Xóa số lượng sản phẩm trong từng kho
                    cursor.execute("DELETE FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh))
                    conn.commit()
                    st.success(f"Đã xóa sản phẩm '{product}' khỏi kho {wh}.")
                
                # Kiểm tra xem sản phẩm có còn tồn tại trong kho nào không
                cursor.execute("SELECT COUNT(*) FROM
# inventory_web_full_pro5_3.py import streamlit as st import sqlite3 from datetime import datetime, timedelta import pandas as pd # ==== Kết nối Database ==== conn = sqlite3.connect("kho.db", check_same_thread=False) cursor = conn.cursor() # ==== Tạo bảng nếu chưa có ==== cursor.execute(""" CREATE TABLE IF NOT EXISTS products( id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT UNIQUE, name TEXT, created_at TEXT ) """) cursor.execute(""" CREATE TABLE IF NOT EXISTS stock_by_warehouse( id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, warehouse TEXT, quantity INTEGER ) """) cursor.execute(""" CREATE TABLE IF NOT EXISTS history( id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, type TEXT, quantity INTEGER, date TEXT, employee TEXT, warehouse TEXT ) """) cursor.execute(""" CREATE TABLE IF NOT EXISTS employees( id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, role TEXT ) """) cursor.execute(""" CREATE TABLE IF NOT EXISTS warehouses( id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT ) """) conn.commit() # ==== Dữ liệu mẫu ==== cursor.execute("SELECT COUNT(*) FROM employees") if cursor.fetchone()[0]==0: employees = [("Admin","Manager"), ("Hanh","Staff"), ("Linh","Staff")] cursor.executemany("INSERT INTO employees(name, role) VALUES (?,?)", employees) conn.commit() cursor.execute("SELECT COUNT(*) FROM warehouses") if cursor.fetchone()[0]==0: warehouses = [("Kho La Pagode",), ("Kho Muse",), ("Kho Metz Ville",), ("Kho Nancy",)] cursor.executemany("INSERT INTO warehouses(name) VALUES (?)", warehouses) conn.commit() # ==== Sidebar menu ==== st.sidebar.title("QUẢN LÝ KHO AMME THE") menu = st.sidebar.radio("Điều hướng", ["Kho hàng","Thêm sản phẩm","Cập nhật/Xóa sản phẩm","Nhập/Xuất","Báo cáo hàng sắp hết","Lịch sử giao dịch","Xuất Excel"]) # ==== Hàm tiện ích ==== def refresh_products(): cursor.execute("SELECT * FROM products") rows = cursor.fetchall() df = pd.DataFrame(rows, columns=["ID","SKU","Tên sản phẩm","Ngày tạo"]) return df def refresh_stock(): cursor.execute(""" SELECT p.id, p.sku, p.name, w.name as Kho, IFNULL(s.quantity,0) as Số_lượng FROM products p CROSS JOIN warehouses w LEFT JOIN stock_by_warehouse s ON p.id=s.product_id AND s.warehouse=w.name """) rows = cursor.fetchall() df = pd.DataFrame(rows, columns=["ID","SKU","Tên sản phẩm","Kho","Số lượng"]) return df def highlight_low(x): return ['background-color: #FFAAAA' if v<5 else '' for v in x["Số lượng"]] # ==== Kho hàng ==== if menu=="Kho hàng": st.header("Tồn kho theo từng kho") df_stock = refresh_stock() st.dataframe( df_stock.style.applymap( lambda x: 'background-color: #FFAAAA' if isinstance(x,int) and x<5 else '', subset=["Số lượng"] ) ) # ==== Thêm sản phẩm ==== elif menu=="Thêm sản phẩm": st.header("Thêm sản phẩm mới với số lượng từng kho") sku = st.text_input("Mã sản phẩm (SKU)") name = st.text_input("Tên sản phẩm") # Lấy danh sách kho cursor.execute("SELECT name FROM warehouses") warehouses_list = [row[0] for row in cursor.fetchall()] # Nhập số lượng cho từng kho qty_dict = {} for wh in warehouses_list: qty_dict[wh] = st.number_input(f"Số lượng kho {wh}", min_value=0, step=1, key=f"qty_{wh}") if st.button("Thêm sản phẩm"): if sku and name: try: # Thêm vào bảng products cursor.execute("INSERT INTO products(sku,name,created_at) VALUES (?,?,?)", (sku,name,datetime.now().strftime("%Y-%m-%d"))) pid = cursor.lastrowid # Thêm số lượng từng kho for wh, qty in qty_dict.items(): if qty>0: cursor.execute("INSERT INTO stock_by_warehouse(product_id,warehouse,quantity) VALUES (?,?,?)", (pid, wh, qty)) conn.commit() st.success(f"Thêm sản phẩm '{name}' thành công với số lượng từng kho!") except sqlite3.IntegrityError: st.error("SKU đã tồn tại!") else: st.warning("Vui lòng nhập đầy đủ SKU và tên sản phẩm") # ==== Cập nhật/Xóa sản phẩm theo từng kho ==== elif menu == "Cập nhật/Xóa sản phẩm": st.header("Cập nhật hoặc Xóa sản phẩm theo từng kho") df = refresh_products() # Lấy danh sách sản phẩm if df.empty: st.warning("Chưa có sản phẩm nào") else: # Chọn sản phẩm product = st.selectbox("Chọn sản phẩm", df["Tên sản phẩm"]) pid = df[df["Tên sản phẩm"] == product]["ID"].values[0] new_name = st.text_input("Tên mới", value=product) new_sku = st.text_input("SKU mới", value=df[df["Tên sản phẩm"] == product]["SKU"].values[0]) # Kho cố định (4 kho) fixed_warehouses = ["Kho La Pagode", "Kho Muse", "Kho Metz Ville", "Kho Nancy"] qty_per_warehouse = {} # Lấy số lượng sản phẩm trong từng kho for wh in fixed_warehouses: cursor.execute("SELECT IFNULL(quantity, 0) FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh)) res = cursor.fetchone() current_qty = res[0] if res else 0 # Nếu không có sản phẩm trong kho, số lượng = 0 qty_per_warehouse[wh] = current_qty # Hiển thị số lượng trong kho st.write(f"Số lượng sản phẩm '{product}' trong các kho hiện tại:") st.write(qty_per_warehouse) # Nhập số lượng cho từng kho qty_inputs = {} st.subheader("Cập nhật số lượng cho từng kho") for wh in fixed_warehouses: qty_inputs[wh] = st.number_input( f"Số lượng tại {wh} (hiện tại {qty_per_warehouse[wh]})", min_value=0, value=qty_per_warehouse[wh], step=1, key=f"qty_{wh}" ) col1, col2 = st.columns(2) with col1: # Cập nhật thông tin sản phẩm if st.button("Cập nhật"): # Cập nhật thông tin tên và SKU của sản phẩm cursor.execute("UPDATE products SET name=?, sku=? WHERE id=?", (new_name, new_sku, pid)) conn.commit() st.success(f"Cập nhật thông tin sản phẩm {product} thành công!") # Cập nhật số lượng cho từng kho for wh in fixed_warehouses: qty = qty_inputs[wh] # Kiểm tra xem kho đã có sản phẩm chưa cursor.execute("SELECT quantity FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh)) res = cursor.fetchone() if res: current_qty = res[0] new_qty = qty # Cập nhật số lượng mới cursor.execute("UPDATE stock_by_warehouse SET quantity=? WHERE product_id=? AND warehouse=?", (new_qty, pid, wh)) else: cursor.execute("INSERT INTO stock_by_warehouse(product_id, warehouse, quantity) VALUES (?,?,?)", (pid, wh, qty)) conn.commit() st.success(f"Cập nhật số lượng cho sản phẩm {product} trong từng kho thành công!") with col2: # Xóa sản phẩm theo từng kho if st.button("Xóa sản phẩm trong kho"): for wh in fixed_warehouses: # Xóa số lượng sản phẩm trong từng kho cursor.execute("DELETE FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh)) conn.commit() st.success(f"Đã xóa sản phẩm '{product}' khỏi kho {wh}.") # Kiểm tra xem sản phẩm có còn tồn tại trong kho nào không cursor.execute("SELECT COUNT(*) FROM stock_by_warehouse WHERE product_id=?", (pid,)) if cursor.fetchone()[0] == 0: cursor.execute("DELETE FROM products WHERE id=?", (pid,)) conn.commit() st.success(f"Sản phẩm {product} đã được xóa hoàn toàn khỏi hệ thống!") else: st.warning(f"Sản phẩm {product} vẫn còn tồn tại trong các kho khác, không thể xóa sản phẩm khỏi hệ thống.") # ==== Nhập/Xuất kho cho 4 kho cố định ==== elif menu == "Nhập/Xuất": st.header("Nhập / Xuất kho cho 4 kho cố định") df = refresh_products() # Lấy danh sách sản phẩm if df.empty: st.warning("Chưa có sản phẩm nào") else: # Chọn sản phẩm product = st.selectbox("Chọn sản phẩm", df["Tên sản phẩm"]) pid = df[df["Tên sản phẩm"] == product]["ID"].values[0] # Kho cố định (4 kho) fixed_warehouses = ["Kho La Pagode", "Kho Muse", "Kho Metz Ville", "Kho Nancy"] qty_per_warehouse = {} # Hiển thị số lượng sản phẩm trong từng kho for wh in fixed_warehouses: cursor.execute("SELECT IFNULL(quantity, 0) FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh)) res = cursor.fetchone() current_qty = res[0] if res else 0 # Nếu không có sản phẩm trong kho, số lượng = 0 qty_per_warehouse[wh] = current_qty st.write(f"Số lượng sản phẩm '{product}' trong các kho hiện tại:") st.write(qty_per_warehouse) # Nhập số lượng cho từng kho qty_inputs = {} st.subheader("Nhập / Xuất số lượng cho từng kho") for wh in fixed_warehouses: qty_inputs[wh] = st.number_input( f"Số lượng tại {wh} (hiện tại {qty_per_warehouse[wh]})", min_value=0, value=qty_per_warehouse[wh], step=1, key=f"qty_{wh}" ) # Nhập số lượng cho sản phẩm chung total_qty = st.number_input(f"Số lượng {product} muốn nhập/xuất (Tổng số lượng trong tất cả kho)", min_value=0, step=1) # Chọn loại giao dịch: Nhập hay Xuất type_tx = st.radio("Loại giao dịch", ["Nhập", "Xuất"]) # Xử lý Nhập kho if st.button("Xác nhận Nhập kho"): for wh in fixed_warehouses: qty = qty_inputs[wh] # Kiểm tra xem kho đã có sản phẩm chưa cursor.execute("SELECT quantity FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh)) res = cursor.fetchone() if res: current_qty = res[0] new_qty = current_qty + qty # Thêm số lượng khi nhập cursor.execute("UPDATE stock_by_warehouse SET quantity=? WHERE product_id=? AND warehouse=?", (new_qty, pid, wh)) else: cursor.execute("INSERT INTO stock_by_warehouse(product_id, warehouse, quantity) VALUES (?,?,?)", (pid, wh, qty)) conn.commit() st.success(f"Nhập kho {sum(qty_inputs.values())} sản phẩm '{product}' thành công!") # Xử lý Xuất kho if st.button("Xác nhận Xuất kho"): total_needed = sum(qty_inputs.values()) cursor.execute("SELECT IFNULL(SUM(quantity), 0) FROM stock_by_warehouse WHERE product_id=?", (pid,)) total_qty = cursor.fetchone()[0] if total_needed > total_qty: st.error(f"Tổng cần xuất {total_needed}, nhưng tồn kho hiện tại {total_qty}") st.stop() for wh in fixed_warehouses: qty = qty_inputs[wh] cursor.execute("SELECT quantity FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh)) res = cursor.fetchone() current_qty = res[0] if res else 0 if current_qty >= qty: # Kiểm tra tồn kho new_qty = current_qty - qty # Trừ số lượng khi xuất cursor.execute("UPDATE stock_by_warehouse SET quantity=? WHERE product_id=? AND warehouse=?", (new_qty, pid, wh)) conn.commit() else: st.error(f"Không đủ sản phẩm trong kho {wh} để xuất {qty} sản phẩm.") st.stop() st.success(f"Xuất kho {sum(qty_inputs.values())} sản phẩm '{product}' thành công.") # ==== Báo cáo hàng sắp hết ==== elif menu=="Báo cáo hàng sắp hết": st.header("Hàng tồn sắp hết / tồn lâu") days_limit = st.number_input("Số ngày tồn tối đa", value=180) qty_limit = st.number_input("Số lượng tối thiểu", value=3) date_limit = (datetime.now()-timedelta(days=days_limit)).strftime("%Y-%m-%d") # Lấy tổng tồn kho từng sản phẩm cursor.execute(""" SELECT p.id, p.sku, p.name, IFNULL(SUM(s.quantity),0) as Tong_ton, p.created_at FROM products p LEFT JOIN stock_by_warehouse s ON p.id=s.product_id GROUP BY p.id HAVING Tong_ton < ? OR p.created_at < ? """, (qty_limit, date_limit)) rows = cursor.fetchall() df_low = pd.DataFrame(rows, columns=["ID","SKU","Tên sản phẩm","Số lượng","Ngày tạo"]) # Highlight hàng tồn <5 st.dataframe( df_low.style.applymap( lambda x: 'background-color: #FFAAAA' if isinstance(x,int) and x<5 else '', subset=["Số lượng"] ) ) # ==== Lịch sử giao dịch ==== elif menu=="Lịch sử giao dịch": st.header("Lịch sử nhập xuất") cursor.execute("SELECT * FROM history") rows = cursor.fetchall() df_hist = pd.DataFrame(rows, columns=["ID","ProductID","Loại","Số lượng","Ngày giờ","Nhân viên","Kho"]) st.dataframe(df_hist) # ==== Xuất Excel ==== elif menu=="Xuất Excel": st.header("Xuất Excel") df_stock = refresh_stock() file_name = f"Inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx" df_stock.to_excel(file_name,index=False) st.success(f"Đã xuất Excel: {file_name}") st.download_button("Tải file Excel", data=open(file_name,"rb"), file_name=file_name)

Dưới đây là phiên bản cập nhật của mã bạn đã chia sẻ với tính năng refresh sau khi thực hiện các thao tác Thêm sản phẩm, Cập nhật sản phẩm và Nhập/Xuất kho.

Cập nhật các phần refresh vào mã:

Refresh sau khi Thêm sản phẩm: Sau khi thêm sản phẩm và số lượng vào kho, ta sẽ làm mới dữ liệu kho và sản phẩm để người dùng thấy được các thay đổi ngay lập tức.

Refresh sau khi Cập nhật sản phẩm: Sau khi cập nhật thông tin sản phẩm và số lượng kho, ta sẽ làm mới dữ liệu để hiển thị các thay đổi.

Refresh sau khi Nhập/Xuất kho: Sau khi thực hiện nhập hoặc xuất kho, dữ liệu kho cũng sẽ được làm mới để người dùng có thể thấy số lượng mới nhất.

Dưới đây là mã của bạn với tính năng refresh bổ sung:

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

# ==== Kho hàng ====
if menu == "Kho hàng":
    st.header("Tồn kho theo từng kho")
    df_stock = refresh_stock()
    st.dataframe(df_stock.style.applymap(lambda x: 'background-color: #FFAAAA' if isinstance(x, int) and x < 5 else '', subset=["Số lượng"]))

# ==== Thêm sản phẩm ====
elif menu == "Thêm sản phẩm":
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
                               (sku, name, datetime.now().strftime("%Y-%m-%d")))
                pid = cursor.lastrowid

                # Thêm số lượng từng kho
                for wh, qty in qty_dict.items():
                    if qty > 0:
                        cursor.execute("INSERT INTO stock_by_warehouse(product_id, warehouse, quantity) VALUES (?,?,?)",
                                       (pid, wh, qty))

                conn.commit()
                st.success(f"Thêm sản phẩm '{name}' thành công với số lượng từng kho!")

                # Refresh thông tin kho và sản phẩm
                df_stock = refresh_stock()
                df_products = refresh_products()
                st.dataframe(df_stock)
                st.dataframe(df_products)
            except sqlite3.IntegrityError:
                st.error("SKU đã tồn tại!")
        else:
            st.warning("Vui lòng nhập đầy đủ SKU và tên sản phẩm")

# ==== Cập nhật/Xóa sản phẩm theo từng kho ====
elif menu == "Cập nhật/Xóa sản phẩm":
    st.header("Cập nhật hoặc Xóa sản phẩm theo từng kho")
    df = refresh_products()  # Lấy danh sách sản phẩm
    if df.empty:
        st.warning("Chưa có sản phẩm nào")
    else:
        # Chọn sản phẩm
        product = st.selectbox("Chọn sản phẩm", df["Tên sản phẩm"])
        pid = df[df["Tên sản phẩm"] == product]["ID"].values[0]
        new_name = st.text_input("Tên mới", value=product)
        new_sku = st.text_input("SKU mới", value=df[df["Tên sản phẩm"] == product]["SKU"].values[0])

        # Kho cố định (4 kho)
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
                # Cập nhật thông tin tên và SKU của sản phẩm
                cursor.execute("UPDATE products SET name=?, sku=? WHERE id=?", (new_name, new_sku, pid))
                conn.commit()
                st.success(f"Cập nhật thông tin sản phẩm {product} thành công!")

                # Cập nhật số lượng cho từng kho
                for wh in fixed_warehouses:
                    qty = qty_inputs[wh]
                    # Kiểm tra xem kho đã có sản phẩm chưa
                    cursor.execute("SELECT quantity FROM stock_by_warehouse WHERE product_id=? AND warehouse=?", (pid, wh))
                    res = cursor.fetchone()
                    if res:
                        current_qty = res[0]
                        new_qty = qty  # Cập nhật số lượng mới
                        cursor.execute("UPDATE stock_by_warehouse SET quantity=? WHERE product_id=? AND warehouse=?", 
                                       (new_qty, pid, wh))
                    else:
                        cursor.execute("INSERT INTO stock_by_warehouse(product_id, warehouse, quantity) VALUES (?,?,?)",
                                       (pid, wh, qty))
                conn.commit()
                st.success(f"Cập nhật số lượng cho sản phẩm {product} trong từng kho thành công!")

                # Refresh thông tin kho và sản phẩm
                df_stock = refresh_stock()
                df_products = refresh_products()
                st.dataframe(df_stock)
                st.dataframe(df_products)

        with col2:
            # Xóa sản phẩm theo từng kho
            if st.button("Xóa sản phẩm trong kho"):
                for wh in fixed_warehouses:
                    # Xóa số lượng sản phẩm trong từng kho
