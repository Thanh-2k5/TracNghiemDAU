-- =====================================================================
--  SCHEMA CƠ SỞ DỮ LIỆU HỆ THỐNG THI TRẮC NGHIỆM TRỰC TUYẾN DAU
--  Hệ quản trị CSDL: MySQL 8.0+ (UTF8MB4)
--  Phân hệ nền tảng (Core, Xác thực, Phân quyền 7 tác nhân, Quản trị mạng)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `tracnghiem_dau`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `tracnghiem_dau`;

-- 1. Bảng vai trò (7 nhóm tác nhân của hệ thống)
CREATE TABLE IF NOT EXISTS `roles` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `code` VARCHAR(20) NOT NULL COMMENT 'ADMIN, CTSV, DAOTAO, KHOA, KHAOTHI, COITHI, SINHVIEN',
    `name` VARCHAR(100) NOT NULL,
    `description` VARCHAR(255) DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_roles_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Bảng tài khoản người dùng (dùng chung cho cả 7 tác nhân)
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `username` VARCHAR(50) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `full_name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(100) DEFAULT NULL,
    `phone` VARCHAR(20) DEFAULT NULL,
    `role_id` INT NOT NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `must_change_password` TINYINT(1) NOT NULL DEFAULT 0,
    `last_login_at` DATETIME DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_users_username` (`username`),
    KEY `ix_users_role_id` (`role_id`),
    CONSTRAINT `fk_users_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Bảng phiên đăng nhập (chặn trùng phiên song song & gắn kết nối Socket)
CREATE TABLE IF NOT EXISTS `user_sessions` (
    `id` VARCHAR(36) NOT NULL,
    `user_id` INT NOT NULL,
    `ip_address` VARCHAR(64) DEFAULT NULL,
    `client_info` VARCHAR(255) DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `last_activity_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `expires_at` DATETIME NOT NULL,
    `revoked_at` DATETIME DEFAULT NULL,
    `revoke_reason` VARCHAR(255) DEFAULT NULL,
    `socket_connection_id` VARCHAR(36) DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `ix_user_sessions_user_id` (`user_id`),
    CONSTRAINT `fk_sessions_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Bảng cấu hình hệ thống (lưu IP/Port REST API & Socket Server)
CREATE TABLE IF NOT EXISTS `system_configs` (
    `config_key` VARCHAR(64) NOT NULL,
    `config_value` TEXT DEFAULT NULL,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
