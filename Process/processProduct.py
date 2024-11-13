import pandas as pd

# Đọc dữ liệu từ file CSV
olist_product = pd.read_csv("../brazilian-ecommerce/olist_products_dataset.csv")  # Thay đường dẫn file nếu cần

# Kiểm tra thông tin dữ liệu
print("Thông tin bảng Olist_Product:")
print(olist_product.info())

# Kiểm tra số lượng giá trị null ở từng cột
print("\nSố lượng giá trị null ở từng cột:")
print(olist_product.isnull().sum())

# Tỷ lệ null theo phần trăm
print("\nTỷ lệ giá trị null (%):")
print((olist_product.isnull().mean() * 100).round(2))

# --- Tiền xử lý dữ liệu ---
# Ví dụ 1: Điền giá trị mặc định cho các cột null
olist_product['product_name_lenght'] = olist_product['product_name_lenght'].fillna(0)  # Điền 0 cho các cột số
olist_product['product_category_name'] = olist_product['product_category_name'].fillna('unknown')  # Điền 'unknown' cho cột danh mục

# Ví dụ 2: Loại bỏ các dòng có quá nhiều giá trị null (nếu cần)
threshold = 0.5  # Ngưỡng (50% null trong một dòng)
olist_product_cleaned = olist_product.dropna(thresh=len(olist_product.columns) * (1 - threshold))

# Kiểm tra lại sau khi xử lý
print("\nDữ liệu sau khi xử lý:")
print(olist_product_cleaned.info())

# Lưu dữ liệu đã xử lý ra file CSV (nếu cần)
olist_product_cleaned.to_csv("Olist_Product_Cleaned.csv", index=False)
