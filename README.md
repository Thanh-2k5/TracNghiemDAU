# Hệ Thống Thi Trắc Nghiệm DAU (TracNghiemDAU)

Dự án phần mềm thi và quản lý trắc nghiệm trực tuyến theo mô hình **Client – Server**.

## Công nghệ sử dụng

| Thành phần | Công nghệ |
| --- | --- |
| **Ngôn ngữ lập trình** | Python |
| **Giao diện Desktop Client** | PySide6 |
| **Backend Server** | FastAPI + Socket Server (TCP / WebSocket) |
| **Cơ sở dữ liệu** | MySQL |
| **ORM** | SQLAlchemy |
| **Giao tiếp mạng** | REST API – HTTP/TCP/IP & Real-time Socket (TCP/WebSocket) |
| **Định dạng trao đổi** | JSON |
| **Kiến trúc mã nguồn** | MVC |
| **Quản lý mã nguồn** | GitHub |

## Cấu trúc thư mục

```text
TracNghiemDAU/
├── client/
│   ├── models/
│   ├── views/
│   │   ├── admin/
│   │   ├── ctsv/
│   │   ├── daotao/
│   │   ├── khoa/
│   │   ├── khaothi/
│   │   ├── coithi/
│   │   └── sinhvien/
│   ├── controllers/
│   ├── api/
│   ├── socket_client/
│   └── main.py
│
├── server/
│   ├── models/
│   ├── schemas/
│   ├── controllers/
│   ├── services/
│   ├── routers/
│   ├── socket_server/
│   ├── database/
│   ├── core/
│   └── main.py
│
├── database/
│   ├── schema.sql
│   └── seed.sql
│
├── docs/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Hướng dẫn cài đặt và khởi chạy

1. **Tạo và kích hoạt môi trường ảo (Virtual Environment):**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. **Cài đặt thư viện:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Cấu hình biến môi trường:**
   Sao chép file `.env.example` thành `.env` và cập nhật thông tin kết nối MySQL.

4. **Khởi chạy Backend Server (FastAPI):**
   ```bash
   python -m server.main
   ```

5. **Khởi chạy Desktop Client (PySide6):**
   ```bash
   python -m client.main
   ```
