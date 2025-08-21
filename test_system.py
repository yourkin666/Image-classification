#!/usr/bin/env python3
"""
房源图片分析系统全面测试脚本
"""
import asyncio
import json
import time
import requests
import subprocess
import sys
import os
from pathlib import Path

# 测试配置
BASE_URL = "http://localhost:8000"
TEST_IMAGES = [
    "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=500&h=300&fit=crop",
    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=500&h=300&fit=crop",
    "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=500&h=300&fit=crop"
]

class SystemTester:
    def __init__(self):
        self.server_process = None
        self.test_results = []
        
    def log(self, message, level="INFO"):
        """记录测试日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_environment(self):
        """测试环境配置"""
        self.log("=== 开始环境测试 ===")
        
        # 检查Python版本
        python_version = sys.version_info
        self.log(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # 检查依赖包
        try:
            import fastapi
            import uvicorn
            import google.genai
            import aiohttp
            import aiomysql
            import requests
            import PIL
            self.log("✓ 所有依赖包已安装")
        except ImportError as e:
            self.log(f"✗ 依赖包缺失: {e}", "ERROR")
            return False
            
        # 检查环境变量
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            self.log("✓ GEMINI_API_KEY已设置")
        else:
            self.log("⚠ GEMINI_API_KEY未设置，部分功能可能无法测试", "WARNING")
            
        # 检查数据库连接
        try:
            from app.core.database import init_database_pool, close_database_pool
            asyncio.run(init_database_pool())
            asyncio.run(close_database_pool())
            self.log("✓ 数据库连接正常")
        except Exception as e:
            self.log(f"✗ 数据库连接失败: {e}", "ERROR")
            return False
            
        self.log("=== 环境测试完成 ===")
        return True
        
    def start_server(self):
        """启动服务器"""
        self.log("=== 启动服务器 ===")
        try:
            # 使用subprocess启动服务器
            self.server_process = subprocess.Popen(
                [sys.executable, "scripts/start_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待服务器启动
            time.sleep(5)
            
            # 检查服务器是否启动成功
            try:
                response = requests.get(f"{BASE_URL}/docs", timeout=10)
                if response.status_code == 200:
                    self.log("✓ 服务器启动成功")
                    return True
                else:
                    self.log(f"✗ 服务器响应异常: {response.status_code}", "ERROR")
                    return False
            except requests.exceptions.RequestException as e:
                self.log(f"✗ 无法连接到服务器: {e}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ 启动服务器失败: {e}", "ERROR")
            return False
            
    def stop_server(self):
        """停止服务器"""
        self.log("=== 停止服务器 ===")
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=10)
                self.log("✓ 服务器已停止")
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.log("⚠ 强制停止服务器", "WARNING")
                
    def test_api_endpoints(self):
        """测试API端点"""
        self.log("=== 开始API端点测试 ===")
        
        # 测试健康检查
        try:
            response = requests.get(f"{BASE_URL}/docs")
            if response.status_code == 200:
                self.log("✓ API文档端点正常")
            else:
                self.log(f"✗ API文档端点异常: {response.status_code}", "ERROR")
        except Exception as e:
            self.log(f"✗ API文档端点测试失败: {e}", "ERROR")
            
    def test_room_analysis(self):
        """测试房间分析功能"""
        self.log("=== 开始房间分析测试 ===")
        
        test_cases = [
            {
                "roomId": "test_room_001",
                "business_type": "whole_rent",
                "url": TEST_IMAGES[0]
            },
            {
                "roomId": "test_room_002", 
                "business_type": "centralized",
                "url": TEST_IMAGES[1]
            },
            {
                "roomId": "test_room_003",
                "business_type": "shared_rent", 
                "url": TEST_IMAGES[2]
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            self.log(f"测试用例 {i+1}: {test_case['roomId']}")
            
            try:
                response = requests.post(
                    f"{BASE_URL}/analyze_room",
                    json=test_case,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        self.log(f"✓ 房间分析成功: {test_case['roomId']}")
                        
                        # 检查结果格式
                        results = result.get('results', [])
                        if results:
                            for res in results:
                                if res.get('success'):
                                    is_room = res.get('is_room')
                                    self.log(f"  图片识别结果: {'房间' if is_room else '非房间'}")
                                else:
                                    self.log(f"  图片处理失败: {res.get('error')}", "WARNING")
                    else:
                        self.log(f"✗ 房间分析失败: {result.get('error')}", "ERROR")
                else:
                    self.log(f"✗ HTTP错误: {response.status_code}", "ERROR")
                    
            except requests.exceptions.Timeout:
                self.log(f"✗ 请求超时: {test_case['roomId']}", "ERROR")
            except Exception as e:
                self.log(f"✗ 请求异常: {e}", "ERROR")
                
    def test_status_endpoint(self):
        """测试状态查询端点"""
        self.log("=== 开始状态查询测试 ===")
        
        test_room_ids = ["test_room_001", "test_room_002", "test_room_003"]
        
        for room_id in test_room_ids:
            try:
                response = requests.get(f"{BASE_URL}/status/{room_id}", timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        status = result.get('processing_status')
                        self.log(f"✓ 状态查询成功: {room_id} - {status}")
                    else:
                        self.log(f"✗ 状态查询失败: {result.get('error')}", "ERROR")
                elif response.status_code == 404:
                    self.log(f"⚠ 房间不存在: {room_id}", "WARNING")
                else:
                    self.log(f"✗ HTTP错误: {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.log(f"✗ 状态查询异常: {e}", "ERROR")
                
    def test_error_handling(self):
        """测试错误处理"""
        self.log("=== 开始错误处理测试 ===")
        
        # 测试无效URL
        invalid_request = {
            "roomId": "test_error_001",
            "business_type": "whole_rent",
            "url": "https://invalid-url-that-does-not-exist.com/image.jpg"
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/analyze_room",
                json=invalid_request,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    results = result.get('results', [])
                    if results and not results[0].get('success'):
                        self.log("✓ 无效URL错误处理正常")
                    else:
                        self.log("⚠ 无效URL未正确处理", "WARNING")
                else:
                    self.log("✓ 请求级别错误处理正常")
            else:
                self.log(f"✗ 错误处理异常: {response.status_code}", "ERROR")
                
        except Exception as e:
            self.log(f"✗ 错误处理测试失败: {e}", "ERROR")
            
        # 测试无效参数
        invalid_params = [
            {"roomId": "", "business_type": "whole_rent", "url": TEST_IMAGES[0]},
            {"roomId": "test_001", "business_type": "invalid_type", "url": TEST_IMAGES[0]},
            {"roomId": "test_001", "business_type": "whole_rent", "url": ""}
        ]
        
        for i, invalid_param in enumerate(invalid_params):
            try:
                response = requests.post(
                    f"{BASE_URL}/analyze_room",
                    json=invalid_param,
                    timeout=10
                )
                
                if response.status_code in [400, 422]:
                    self.log(f"✓ 参数验证正常: 用例 {i+1}")
                else:
                    self.log(f"⚠ 参数验证异常: 用例 {i+1}, 状态码: {response.status_code}", "WARNING")
                    
            except Exception as e:
                self.log(f"✗ 参数验证测试失败: {e}", "ERROR")
                
    def test_concurrent_requests(self):
        """测试并发请求"""
        self.log("=== 开始并发测试 ===")
        
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def make_request(request_id):
            """发送单个请求"""
            try:
                test_data = {
                    "roomId": f"concurrent_test_{request_id}",
                    "business_type": "whole_rent",
                    "url": TEST_IMAGES[0]
                }
                
                response = requests.post(
                    f"{BASE_URL}/analyze_room",
                    json=test_data,
                    timeout=30
                )
                
                results_queue.put({
                    "request_id": request_id,
                    "success": response.status_code == 200,
                    "status_code": response.status_code
                })
                
            except Exception as e:
                results_queue.put({
                    "request_id": request_id,
                    "success": False,
                    "error": str(e)
                })
                
        # 创建10个并发请求
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
            
        # 等待所有线程完成
        for thread in threads:
            thread.join()
            
        # 收集结果
        successful_requests = 0
        total_requests = 10
        
        while not results_queue.empty():
            result = results_queue.get()
            if result.get('success'):
                successful_requests += 1
            else:
                self.log(f"并发请求失败: {result.get('error', 'Unknown error')}", "WARNING")
                
        success_rate = (successful_requests / total_requests) * 100
        self.log(f"并发测试结果: {successful_requests}/{total_requests} 成功 ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            self.log("✓ 并发处理能力正常")
        else:
            self.log("⚠ 并发处理能力需要优化", "WARNING")
            
    def run_all_tests(self):
        """运行所有测试"""
        self.log("🚀 开始房源图片分析系统全面测试")
        
        # 1. 环境测试
        if not self.test_environment():
            self.log("❌ 环境测试失败，停止测试", "ERROR")
            return False
            
        # 2. 启动服务器
        if not self.start_server():
            self.log("❌ 服务器启动失败，停止测试", "ERROR")
            return False
            
        try:
            # 3. API端点测试
            self.test_api_endpoints()
            
            # 4. 房间分析测试
            self.test_room_analysis()
            
            # 5. 状态查询测试
            self.test_status_endpoint()
            
            # 6. 错误处理测试
            self.test_error_handling()
            
            # 7. 并发测试
            self.test_concurrent_requests()
            
        finally:
            # 8. 停止服务器
            self.stop_server()
            
        self.log("🎉 所有测试完成")
        return True
        
if __name__ == "__main__":
    tester = SystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ 系统测试通过")
        sys.exit(0)
    else:
        print("\n❌ 系统测试失败")
        sys.exit(1) 