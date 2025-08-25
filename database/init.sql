-- 房源图片分析系统数据库初始化脚本
-- 创建时间: 2024年
-- 说明: 初始化房源分析相关的数据库表
-- 数据库配置: rm-m5el7ur6zifx6ankzvo.mysql.rds.aliyuncs.com
-- 数据库名称: qft_ai_test
-- 用户名: qft_ai_test

-- 房源分析结果表
CREATE TABLE IF NOT EXISTS `qft_ai_room_analysis` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `room_id` varchar(64) NOT NULL COMMENT '房间ID',
  `business_type` tinyint NOT NULL COMMENT '业务类型 1 集中 2 整租 3 合租',
  `content` text COMMENT '生成的房源内容(JSON格式，最大64KB)',
  `processing_status` enum('pending','processing','completed','failed') DEFAULT 'pending' COMMENT '处理状态',
  `is_delete` tinyint NOT NULL DEFAULT '0' COMMENT '是否删除：0未删除 1已删除',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_room_id` (`room_id`),
  KEY `idx_business_type` (`business_type`),
  KEY `idx_processing_status` (`processing_status`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='房源分析结果表';

-- 显示创建的表结构
SHOW TABLES LIKE 'qft_ai_%';

-- 显示表结构详情
DESCRIBE `qft_ai_room_analysis`; 