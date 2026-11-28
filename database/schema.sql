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

-- 5. Học phần / môn học (4.1)
CREATE TABLE IF NOT EXISTS `subjects` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `code` VARCHAR(30) NOT NULL,
    `name` VARCHAR(200) NOT NULL,
    `credits` INT NOT NULL,
    `exam_duration_minutes` INT NOT NULL,
    `description` TEXT DEFAULT NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_subjects_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Chương kiến thức (4.2)
CREATE TABLE IF NOT EXISTS `knowledge_chapters` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `subject_id` INT NOT NULL,
    `name` VARCHAR(200) NOT NULL,
    `description` TEXT DEFAULT NULL,
    `sort_order` INT NOT NULL DEFAULT 1,
    PRIMARY KEY (`id`),
    KEY `ix_chapters_subject_id` (`subject_id`),
    CONSTRAINT `fk_chapters_subject` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Ngân hàng câu hỏi 7 dạng (4.3)
CREATE TABLE IF NOT EXISTS `questions` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `subject_id` INT NOT NULL,
    `chapter_id` INT NOT NULL,
    `question_type` VARCHAR(30) NOT NULL,
    `difficulty` VARCHAR(10) NOT NULL,
    `content` TEXT NOT NULL,
    `options` JSON DEFAULT NULL,
    `answer` JSON DEFAULT NULL,
    `explanation` TEXT DEFAULT NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_by` INT DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `ix_questions_subject_id` (`subject_id`),
    KEY `ix_questions_chapter_id` (`chapter_id`),
    CONSTRAINT `fk_questions_subject` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_questions_chapter` FOREIGN KEY (`chapter_id`) REFERENCES `knowledge_chapters` (`id`) ON DELETE RESTRICT,
    CONSTRAINT `fk_questions_creator` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Ma trận câu hỏi (4.3.3)
CREATE TABLE IF NOT EXISTS `question_matrices` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `subject_id` INT NOT NULL,
    `name` VARCHAR(200) NOT NULL,
    `description` TEXT DEFAULT NULL,
    `matrix` JSON NOT NULL,
    PRIMARY KEY (`id`),
    KEY `ix_matrices_subject_id` (`subject_id`),
    CONSTRAINT `fk_matrices_subject` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
