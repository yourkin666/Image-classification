#!/usr/bin/env python3
"""
停止脚本 - 简化版本
"""
import os
import signal
import psutil
import sys

def find_server_process():
    """查找服务器进程"""
    server_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any('uvicorn' in arg or 'start_server.py' in arg for arg in cmdline):
                server_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return server_processes

def stop_server():
    """停止服务器"""
    print("正在查找服务器进程...")
    
    server_processes = find_server_process()
    
    if not server_processes:
        print("未找到运行中的服务器进程")
        return
    
    print(f"找到 {len(server_processes)} 个服务器进程:")
    
    for proc in server_processes:
        print(f"  PID: {proc.pid}, 命令: {' '.join(proc.cmdline())}")
        
        try:
            # 发送SIGINT信号（Ctrl+C）
            print(f"正在停止进程 {proc.pid}...")
            proc.send_signal(signal.SIGINT)
            
            # 等待进程结束
            try:
                proc.wait(timeout=5)
                print(f"进程 {proc.pid} 已停止")
            except psutil.TimeoutExpired:
                # 如果5秒后还没结束，强制杀死
                print(f"进程 {proc.pid} 未在5秒内停止，强制终止...")
                proc.kill()
                proc.wait()
                print(f"进程 {proc.pid} 已强制终止")
                
        except psutil.NoSuchProcess:
            print(f"进程 {proc.pid} 已经不存在")
        except Exception as e:
            print(f"停止进程 {proc.pid} 时出错: {e}")

if __name__ == "__main__":
    try:
        stop_server()
        print("服务器停止完成")
    except KeyboardInterrupt:
        print("\n操作被用户中断")
    except Exception as e:
        print(f"停止服务器时出错: {e}")
        sys.exit(1) 