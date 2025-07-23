import logging
import json as json_lib
from datetime import datetime
from logging.handlers import RotatingFileHandler
from .config import settings


class StructuredLogger:
    def __init__(self, name, log_file=None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 清除现有的处理器
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)
        
        log_file = log_file or settings.LOG_FILE
        
        # 文件处理器 - 轮转日志
        file_handler = RotatingFileHandler(
            log_file, maxBytes=settings.LOG_MAX_BYTES, 
            backupCount=settings.LOG_BACKUP_COUNT, encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 文件日志格式 - 清晰易读的分层格式
        file_handler.setFormatter(ReadableFileFormatter())
        console_handler.setFormatter(LayeredFormatter())
        
        # 额外创建一个JSON备份文件（供程序解析使用）
        json_handler = RotatingFileHandler(
            settings.LOG_BACKUP_FILE, maxBytes=5*1024*1024, 
            backupCount=3, encoding='utf-8'
        )
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(BackupJSONFormatter())
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(json_handler)
    
    def debug(self, message, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message, **kwargs):
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)
    
    def _log(self, level, message, **kwargs):
        extra = {}
        for key, value in kwargs.items():
            extra[key] = value
        self.logger.log(level, message, extra=extra)


class ReadableFileFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        # 级别图标映射
        self.level_icons = {
            'DEBUG': '🔍',
            'INFO': '✅', 
            'WARNING': '⚠️',
            'ERROR': '🔴',
            'CRITICAL': '💥'
        }
    
    def format(self, record):
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%m-%d")
        
        # 获取级别图标
        icon = self.level_icons.get(record.levelname, '📝')
        
        # 获取简化的请求ID
        request_id = getattr(record, 'request_id', None)
        short_request_id = request_id[:8] if request_id and len(request_id) > 8 else request_id
        
        # 构建主要消息行
        main_line = f"[{date_str} {time_str}] {icon} {record.getMessage()}"
        if request_id:
            main_line += f" (请求:{short_request_id})"
        
        # 构建详细信息行
        details = []
        
        # URL信息 (截断长URL)
        if hasattr(record, 'url'):
            url = record.url
            if len(url) > 70:
                url = url[:35] + "..." + url[-32:]
            details.append(f"URL: {url}")
        
        # 路径信息
        if hasattr(record, 'path'):
            details.append(f"路径: {record.path}")
        
        # 状态码
        if hasattr(record, 'status'):
            details.append(f"状态: {record.status}")
        
        # 耗时
        if hasattr(record, 'duration'):
            details.append(f"耗时: {record.duration}")
        
        # 房间识别结果
        if hasattr(record, 'is_room'):
            room_status = "房间" if record.is_room else "非房间"
            details.append(f"识别: {room_status}")
            
        if hasattr(record, 'room_type') and record.room_type:
            details.append(f"类型: {record.room_type}")
        
        # 错误信息
        if hasattr(record, 'error_type'):
            error_msg = record.error_type
            if record.levelname == 'ERROR':
                if 'timeout' in error_msg.lower() or 'connecttimeout' in error_msg.lower():
                    error_msg = "连接超时"
                elif 'ssl' in error_msg.lower():
                    error_msg = "SSL证书错误"
                elif 'notfound' in error_msg.lower() or '404' in str(record.getMessage()):
                    error_msg = "资源未找到"
                elif 'network' in error_msg.lower():
                    error_msg = "网络错误"
            details.append(f"错误: {error_msg}")
        
        # 客户端IP
        if hasattr(record, 'client_ip') and record.client_ip != 'unknown':
            details.append(f"客户端: {record.client_ip}")
        
        # HTTP方法
        if hasattr(record, 'method'):
            details.append(f"方法: {record.method}")
        
        # 数据大小
        if hasattr(record, 'data_size') and record.data_size:
            if record.data_size > 1024*1024:
                size_str = f"{record.data_size/(1024*1024):.1f}MB"
            elif record.data_size > 1024:
                size_str = f"{record.data_size/1024:.1f}KB"
            else:
                size_str = f"{record.data_size}字节"
            details.append(f"大小: {size_str}")
        
        # 组装完整消息
        if details:
            # 如果详细信息太多，分行显示
            if len(details) > 3:
                detail_lines = []
                for detail in details:
                    detail_lines.append(f"    ├─ {detail}")
                return main_line + "\n" + "\n".join(detail_lines)
            else:
                # 简单情况，放在一行
                return main_line + f"\n    └─ {' | '.join(details)}"
        else:
            return main_line


class BackupJSONFormatter(logging.Formatter):
    def format(self, record):
        now = datetime.now()
        log_entry = {
            "时间": now.strftime("%Y-%m-%d %H:%M:%S"),
            "级别": record.levelname,
            "日志器": record.name,
            "消息": record.getMessage(),
            "模块": record.module,
            "函数": record.funcName,
            "行号": record.lineno
        }
        
        # 添加额外的字段
        if hasattr(record, 'request_id'):
            log_entry['请求ID'] = record.request_id
        if hasattr(record, 'url'):
            log_entry['URL'] = record.url
        if hasattr(record, 'path'):
            log_entry['路径'] = record.path
        if hasattr(record, 'duration'):
            log_entry['耗时'] = record.duration
        if hasattr(record, 'status'):
            log_entry['状态码'] = record.status
        if hasattr(record, 'error_type'):
            log_entry['错误类型'] = record.error_type
        if hasattr(record, 'client_ip'):
            log_entry['客户端IP'] = record.client_ip
        if hasattr(record, 'method'):
            log_entry['HTTP方法'] = record.method
        if hasattr(record, 'is_room'):
            log_entry['是否房间'] = "是" if record.is_room else "否"
        if hasattr(record, 'room_type'):
            log_entry['房间类型'] = record.room_type
        if hasattr(record, 'data_size'):
            log_entry['数据大小'] = f"{record.data_size}字节" if hasattr(record, 'data_size') else None
        if hasattr(record, 'stack_trace'):
            log_entry['错误堆栈'] = record.stack_trace
        
        return json_lib.dumps(log_entry, ensure_ascii=False)


class LayeredFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        # 级别图标映射
        self.level_icons = {
            'DEBUG': '🔍',
            'INFO': '✅', 
            'WARNING': '⚠️',
            'ERROR': '🔴',
            'CRITICAL': '💥'
        }
    
    def format(self, record):
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        
        # 获取级别图标
        icon = self.level_icons.get(record.levelname, '📝')
        
        # 获取简化的请求ID
        request_id = getattr(record, 'request_id', 'unknown')
        short_request_id = request_id[:8] if len(request_id) > 8 else request_id
        
        # 构建主要消息行
        main_line = f"[{time_str}] {icon} {record.getMessage()}"
        if request_id != 'unknown':
            main_line += f" (请求: {short_request_id})"
        
        # 构建详细信息行
        details = []
        
        # URL信息 (截断长URL)
        if hasattr(record, 'url'):
            url = record.url
            if len(url) > 60:
                url = url[:30] + "..." + url[-27:]
            details.append(f"URL: {url}")
        
        # 路径信息
        if hasattr(record, 'path'):
            details.append(f"路径: {record.path}")
        
        # 状态码
        if hasattr(record, 'status'):
            details.append(f"状态: {record.status}")
        
        # 耗时
        if hasattr(record, 'duration'):
            details.append(f"耗时: {record.duration}")
        
        # 房间识别结果
        if hasattr(record, 'is_room'):
            room_status = "是房间" if record.is_room else "非房间"
            details.append(f"识别: {room_status}")
            
        if hasattr(record, 'room_type') and record.room_type:
            details.append(f"类型: {record.room_type}")
        
        # 错误信息
        if hasattr(record, 'error_type'):
            error_msg = record.error_type
            if record.levelname == 'ERROR':
                if 'timeout' in error_msg.lower() or 'connecttimeout' in error_msg.lower():
                    error_msg = "连接超时"
                elif 'ssl' in error_msg.lower():
                    error_msg = "SSL证书错误"
                elif 'notfound' in error_msg.lower() or '404' in str(record.getMessage()):
                    error_msg = "资源未找到"
                elif 'network' in error_msg.lower():
                    error_msg = "网络错误"
            details.append(f"错误: {error_msg}")
        
        # 客户端IP
        if hasattr(record, 'client_ip') and record.client_ip != 'unknown':
            details.append(f"客户端: {record.client_ip}")
        
        # HTTP方法
        if hasattr(record, 'method'):
            details.append(f"方法: {record.method}")
        
        # 数据大小
        if hasattr(record, 'data_size') and record.data_size:
            if record.data_size > 1024*1024:
                size_str = f"{record.data_size/(1024*1024):.1f}MB"
            elif record.data_size > 1024:
                size_str = f"{record.data_size/1024:.1f}KB"
            else:
                size_str = f"{record.data_size}字节"
            details.append(f"大小: {size_str}")
        
        # 组装完整消息
        if details:
            # 如果详细信息太多，分行显示
            if len(details) > 2:
                detail_lines = []
                for detail in details:
                    detail_lines.append(f"         {detail}")
                return main_line + "\n" + "\n".join(detail_lines)
            else:
                # 简单情况，放在一行
                return main_line + "\n         " + " | ".join(details)
        else:
            return main_line


# 创建全局日志器
logger = StructuredLogger(__name__) 