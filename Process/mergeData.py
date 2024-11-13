import pandas as pd

# Đọc dữ liệu từ các file CSV (hoặc định dạng dữ liệu tương tự)
olist_product = pd.read_csv("../brazilian-ecommerce/olist_products_dataset.csv")  # Bảng Olist_Product
category_translation = pd.read_csv("../brazilian-ecommerce/product_category_name_translation.csv")  # Bảng product_categoryname_translation

# Tích hợp hai bảng dựa trên cột 'product_category_name'
merged_product = pd.merge(
    olist_product,
    category_translation,
    how='left',  # Giữ tất cả các dòng từ bảng olist_product
    on='product_category_name'  # Tích hợp dựa trên cột product_category_name
)

# Kiểm tra dữ liệu sau khi tích hợp
print(merged_product.head(10))

# Lưu kết quả ra file CSV mới (nếu cần)
merged_product.to_csv("Olist_Product_with_English_Category.csv", index=False)
