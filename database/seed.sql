-- =====================================================================
--  DỮ LIỆU MẪU (SEED DATA) - HỆ THỐNG THI TRẮC NGHIỆM TRỰC TUYẾN DAU
--  Lưu ý: Khi khởi chạy `python -m server.main`, hệ thống cũng tự động
--  khởi tạo 7 vai trò và 7 tài khoản mẫu (mật khẩu Admin: Admin@123,
--  các tác nhân còn lại: Dau@123456) nếu CSDL đang trống.
-- =====================================================================

USE `tracnghiem_dau`;

INSERT IGNORE INTO `roles` (`id`, `code`, `name`, `description`) VALUES
(1, 'ADMIN',    'Quản trị hệ thống',        'Quản lý tài khoản, phân quyền, mạng và dữ liệu hệ thống'),
(2, 'CTSV',     'Phòng Công tác Sinh viên', 'Quản lý hồ sơ và trạng thái học tập sinh viên'),
(3, 'DAOTAO',   'Phòng Đào tạo',            'Xét điều kiện và lập danh sách dự thi'),
(4, 'KHOA',     'Khoa',                     'Quản lý học phần, chương kiến thức và ngân hàng câu hỏi'),
(5, 'KHAOTHI',  'Phòng Khảo thí',           'Tổ chức kỳ thi, ca thi, phòng thi, sinh đề và kết quả'),
(6, 'COITHI',   'Cán bộ coi thi',           'Điều khiển và giám sát phòng thi thời gian thực'),
(7, 'SINHVIEN', 'Sinh viên',                'Tham gia thi trắc nghiệm trực tuyến');

INSERT IGNORE INTO `system_configs` (`config_key`, `config_value`) VALUES
('network.api_host',    '127.0.0.1'),
('network.api_port',    '8000'),
('network.socket_host', '0.0.0.0'),
('network.socket_port', '9000');

-- Tài khoản mẫu (Mật khẩu: admin -> Admin@123 | các vai trò khác -> Dau@123456)
-- Hash bcrypt tương ứng sẽ được tạo tự động bởi `server.database.init_db.seed_defaults()`
INSERT IGNORE INTO `users`
    (`username`, `password_hash`, `full_name`, `email`, `phone`, `role_id`, `is_active`, `must_change_password`)
VALUES
('admin',     '$2b$12$ZczoVR8q6IPu8xIXp7QN.OGIjzPQadNlVAkBFIGMGwQz3uSJtYFwO', 'Nguyễn Văn Thạnh (Admin)',  'admin@dau.edu.vn',    '0905111222', 1, 1, 0),
('ctsv01',    '$2b$12$zQCX9qyG489LaH5A6Qnj4..Thgbcui1.UprhRtUAQKMCXYQsLUcG2', 'Chuyên viên Phòng CTSV',    'ctsv@dau.edu.vn',     '0905111223', 2, 1, 0),
('daotao01',  '$2b$12$zQCX9qyG489LaH5A6Qnj4..Thgbcui1.UprhRtUAQKMCXYQsLUcG2', 'Chuyên viên Phòng Đào tạo', 'daotao@dau.edu.vn',   '0905111224', 3, 1, 0),
('khoa_cntt', '$2b$12$zQCX9qyG489LaH5A6Qnj4..Thgbcui1.UprhRtUAQKMCXYQsLUcG2', 'Giảng viên Khoa CNTT',      'khoacntt@dau.edu.vn', '0905111225', 4, 1, 0),
('khaothi01', '$2b$12$zQCX9qyG489LaH5A6Qnj4..Thgbcui1.UprhRtUAQKMCXYQsLUcG2', 'Chuyên viên Phòng Khảo thí','khaothi@dau.edu.vn',  '0905111226', 5, 1, 0),
('coithi01',  '$2b$12$zQCX9qyG489LaH5A6Qnj4..Thgbcui1.UprhRtUAQKMCXYQsLUcG2', 'Cán bộ Coi thi 01',         'coithi01@dau.edu.vn', '0905111227', 6, 1, 0),
('sv221001',  '$2b$12$zQCX9qyG489LaH5A6Qnj4..Thgbcui1.UprhRtUAQKMCXYQsLUcG2', 'Trần Minh Khoa (SV)',       'sv221001@dau.edu.vn', '0905111228', 7, 1, 0);
