import sqlite3

def export_sqlite_to_sql(db_path, output_sql_path):
    # Kết nối đến tệp SQLite
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    
    # Mở tệp output .sql để ghi
    with open(output_sql_path, 'w') as f:
        # Ghi các lệnh DDL và DML của mỗi bảng
        for line in connection.iterdump():
            f.write(f'{line}\n')
    
    # Đóng kết nối
    connection.close()
    print(f"Đã xuất tệp {db_path} sang {output_sql_path}")

# Sử dụng hàm với đường dẫn tới tệp .db và tên tệp .sql đầu ra
db_file = 'test.db'
output_sql_file = 'onlineshop.sql'
export_sqlite_to_sql(db_file, output_sql_file)
