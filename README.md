# Hệ Thống Thi Trắc Nghiệm Trực Tuyến DAU (TracNghiemDAU)

Dự án **Xây dựng hệ thống thi trắc nghiệm trực tuyến đơn giản cho sinh viên DAU** theo mô hình **Desktop Client – Server (MVC)**.

## Công nghệ sử dụng

| Thành phần | Công nghệ |
| --- | --- |
| **Ngôn ngữ lập trình** | Python 3.11+ |
| **Giao diện Desktop Client** | PySide6 (Qt for Python) |
| **Backend Server** | FastAPI + Real-time Socket Server (TCP / WebSocket) |
| **Cơ sở dữ liệu** | MySQL 8.0+ |
| **ORM** | SQLAlchemy 2.0 |
| **Giao tiếp mạng** | REST API – HTTP/TCP/IP & Real-time Socket (TCP/WebSocket + Heartbeat) |
| **Định dạng trao đổi** | JSON |
| **Kiến trúc mã nguồn** | MVC |

## Các module nền tảng & Quản trị hệ thống (Nguyễn Văn Thạnh)

- **0. Kiến trúc Core Client–Server & Socket**:
  - Khung MVC đầy đủ cho cả `client/` (PySide6) và `server/` (FastAPI + SQLAlchemy).
  - Giao thức gói tin JSON newline-delimited trên cả **TCP Socket** và **WebSocket**, tích hợp cơ chế **Heartbeat + đo RTT Latency + thống kê băng thông** dùng chung cho toàn bộ 7 tác nhân.
- **1.1. Xác thực & phiên đăng nhập (tái sử dụng cho 7 tác nhân)**:
  - Đăng nhập JWT + phiên DB (`1.1.1`), Đăng xuất & đóng Socket an toàn (`1.1.2`), Kiểm tra & chặn trùng phiên đăng nhập song song kèm cưỡng chế đăng xuất phiên cũ qua Socket (`1.1.3`).
- **1.2. Thông tin cá nhân (tái sử dụng cho 7 tác nhân)**:
  - Xem & cập nhật hồ sơ cá nhân (`1.2.1`), Đổi mật khẩu & bắt buộc đổi mật khẩu mặc định (`1.2.2`).
- **1.3. Quản lý tài khoản (Admin)**:
  - Thêm, sửa, khóa/mở khóa tài khoản (`1.3.1`), Đặt lại mật khẩu mặc định (`1.3.2`), Gán vai trò cho 7 nhóm tác nhân (`1.3.3`).
- **1.4. Quản trị mạng (Admin)**:
  - Cấu hình IP/Port REST API & Socket Server (`1.4.1`), Khởi động / Dừng / Khởi động lại Socket Server (`1.4.2`), Theo dõi danh sách kết nối Socket & băng thông thời gian thực (`1.4.3`).
- **1.5. Dữ liệu & vận hành (Admin)**:
  - Sao lưu (Backup) cơ sở dữ liệu ra tệp `.sql` và Phục hồi (Restore) an toàn có tạo bản `pre_restore_*.sql` (`1.5.1`).

## Phân hệ Khoa (4.1–4.3)

- **4.1 Học phần**: CRUD và tìm kiếm mã môn, tên môn, số tín chỉ, thời gian thi.
- **4.2 Chương kiến thức**: CRUD và sắp xếp thứ tự chương theo từng học phần.
- **4.3 Ngân hàng câu hỏi**: CRUD 7 dạng câu hỏi, ẩn/hiện, nhập hàng loạt `.xlsx`/`.docx`, lập ma trận và lọc theo chương/độ khó.

## Tài khoản mặc định (tự động khởi tạo khi chạy Server lần đầu)

| Vai trò | Username | Mật khẩu |
| --- | --- | --- |
| Quản trị hệ thống (`ADMIN`) | `admin` | `Admin@123` |
| Phòng CTSV (`CTSV`) | `ctsv01` | `Dau@123456` |
| Phòng Đào tạo (`DAOTAO`) | `daotao01` | `Dau@123456` |
| Khoa (`KHOA`) | `khoa_cntt` | `Dau@123456` |
| Phòng Khảo thí (`KHAOTHI`) | `khaothi01` | `Dau@123456` |
| Cán bộ coi thi (`COITHI`) | `coithi01` | `Dau@123456` |
| Sinh viên (`SINHVIEN`) | `sv221001` | `Dau@123456` |

## Hướng dẫn cài đặt và khởi chạy

1. **Tạo và kích hoạt môi trường ảo:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Cấu hình môi trường:**
   Sao chép `.env.example` thành `.env` và điền thông tin kết nối MySQL (`DB_USER`, `DB_PASSWORD`, `DB_NAME`). Khi khởi động, Server sẽ tự tạo database `tracnghiem_dau`, bảng biểu và tài khoản mẫu (hoặc có thể chạy thủ công `database/schema.sql` và `database/seed.sql`).

3. **Khởi chạy Backend Server (FastAPI + TCP Socket Server):**
   ```powershell
   python -m server.main
   ```
   *(Tài liệu Swagger REST API mở tại: http://127.0.0.1:8000/docs)*

4. **Khởi chạy Desktop Client (PySide6):**
   ```powershell
   python -m client.main
   ```
