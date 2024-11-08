import psycopg2

try:
    # Kết nối tới cơ sở dữ liệu PostgreSQL
    connection = psycopg2.connect(
        user="postgres",
        password="12345678",
        host="localhost",  # Ví dụ: "localhost" nếu chạy trên máy cá nhân
        port="5432",          # Cổng mặc định là 5432
        database="postgres"
    )

    # Tạo một con trỏ để thực hiện các câu truy vấn
    cursor = connection.cursor()

    # Thực hiện truy vấn (ví dụ: lấy danh sách các bảng)
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    tables = cursor.fetchall()

    print("Danh sách các bảng:")
    for table in tables:
        print(table)

except (Exception, psycopg2.Error) as error:
    print("Lỗi khi kết nối tới PostgreSQL", error)

finally:
    # Đóng kết nối sau khi xong
    if connection:
        cursor.close()
        connection.close()
        print("Kết nối PostgreSQL đã đóng.")
