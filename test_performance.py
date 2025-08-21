#!/usr/bin/env python3
"""
房源图片分析系统性能测试脚本
"""
import asyncio
import time
import requests
import threading
import statistics
import subprocess
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://localhost:8000"
TEST_IMAGES = [
    "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=500&h=300&fit=crop",
    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=500&h=300&fit=crop",
    "https://images.unsplash.com/photo-1502672260266-1c1efd93688?w=500&h=300&fit=crop",
    "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=500&h=300&fit=crop",
    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=500&h=300&fit=crop"
]

class PerformanceTester:
    def __init__(self):
        self.server_process = None
        self.results = []
        
    def log(self, message, level="INFO"):
        """记录测试日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def start_server(self):
        """启动服务器"""
        self.log("=== 启动服务器 ===")
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, "scripts/start_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            time.sleep(5)
            
            # 检查服务器是否启动成功
            response = requests.get(f"{BASE_URL}/docs", timeout=10)
            if response.status_code == 200:
                self.log("✓ 服务器启动成功")
                return True
            else:
                self.log(f"✗ 服务器响应异常: {response.status_code}", "ERROR")
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
                
    def test_single_request_performance(self):
        """测试单个请求性能"""
        self.log("=== 单个请求性能测试 ===")
        
        test_data = {
            "roomId": "perf_test_single",
            "business_type": "whole_rent",
            "url": TEST_IMAGES[0]
        }
        
        response_times = []
        success_count = 0
        total_requests = 10
        
        for i in range(total_requests):
            start_time = time.time()
            try:
                response = requests.post(
                    f"{BASE_URL}/analyze_room",
                    json=test_data,
                    timeout=30
                )
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # 转换为毫秒
                response_times.append(response_time)
                
                if response.status_code == 200:
                    success_count += 1
                    self.log(f"请求 {i+1}: {response_time:.2f}ms")
                else:
                    self.log(f"请求 {i+1} 失败: {response.status_code}", "WARNING")
                    
            except Exception as e:
                self.log(f"请求 {i+1} 异常: {e}", "ERROR")
                
        # 计算统计信息
        if response_times:
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            std_dev = statistics.stdev(response_times) if len(response_times) > 1 else 0
            
            self.log(f"性能统计:")
            self.log(f"  平均响应时间: {avg_time:.2f}ms")
            self.log(f"  最小响应时间: {min_time:.2f}ms")
            self.log(f"  最大响应时间: {max_time:.2f}ms")
            self.log(f"  标准差: {std_dev:.2f}ms")
            self.log(f"  成功率: {success_count}/{total_requests} ({success_count/total_requests*100:.1f}%)")
            
            # 性能评估
            if avg_time < 5000:  # 5秒
                self.log("✓ 响应时间优秀")
            elif avg_time < 10000:  # 10秒
                self.log("✓ 响应时间良好")
            else:
                self.log("⚠ 响应时间需要优化", "WARNING")
                
    def test_concurrent_performance(self):
        """测试并发性能"""
        self.log("=== 并发性能测试 ===")
        
        def make_request(request_id):
            """发送单个请求"""
            test_data = {
                "roomId": f"perf_test_concurrent_{request_id}",
                "business_type": "whole_rent",
                "url": TEST_IMAGES[request_id % len(TEST_IMAGES)]
            }
            
            start_time = time.time()
            try:
                response = requests.post(
                    f"{BASE_URL}/analyze_room",
                    json=test_data,
                    timeout=30
                )
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                return {
                    "request_id": request_id,
                    "success": response.status_code == 200,
                    "response_time": response_time,
                    "status_code": response.status_code
                }
            except Exception as e:
                return {
                    "request_id": request_id,
                    "success": False,
                    "response_time": 0,
                    "error": str(e)
                }
                
        # 测试不同并发级别
        concurrency_levels = [5, 10, 20, 30]
        
        for concurrency in concurrency_levels:
            self.log(f"测试并发级别: {concurrency}")
            
            start_time = time.time()
            results = []
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(make_request, i) for i in range(concurrency)]
                
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
                    
            end_time = time.time()
            total_time = (end_time - start_time) * 1000
            
            # 分析结果
            successful_requests = sum(1 for r in results if r['success'])
            response_times = [r['response_time'] for r in results if r['success']]
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                throughput = successful_requests / (total_time / 1000)  # 请求/秒
                
                self.log(f"  并发 {concurrency}:")
                self.log(f"    成功率: {successful_requests}/{concurrency} ({successful_requests/concurrency*100:.1f}%)")
                self.log(f"    平均响应时间: {avg_response_time:.2f}ms")
                self.log(f"    总耗时: {total_time:.2f}ms")
                self.log(f"    吞吐量: {throughput:.2f} 请求/秒")
                
                # 性能评估
                if throughput > 2:
                    self.log("    ✓ 吞吐量优秀")
                elif throughput > 1:
                    self.log("    ✓ 吞吐量良好")
                else:
                    self.log("    ⚠ 吞吐量需要优化", "WARNING")
            else:
                self.log(f"  并发 {concurrency}: 所有请求失败", "ERROR")
                
    def test_memory_usage(self):
        """测试内存使用情况"""
        self.log("=== 内存使用测试 ===")
        
        import psutil
        
        # 获取服务器进程
        if self.server_process:
            process = psutil.Process(self.server_process.pid)
            
            # 测试前内存
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            self.log(f"初始内存使用: {initial_memory:.2f}MB")
            
            # 发送一些请求
            test_data = {
                "roomId": "memory_test",
                "business_type": "whole_rent",
                "url": TEST_IMAGES[0]
            }
            
            for i in range(5):
                try:
                    response = requests.post(
                        f"{BASE_URL}/analyze_room",
                        json=test_data,
                        timeout=30
                    )
                    time.sleep(1)
                except Exception as e:
                    self.log(f"内存测试请求失败: {e}", "WARNING")
                    
            # 测试后内存
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            self.log(f"最终内存使用: {final_memory:.2f}MB")
            self.log(f"内存增长: {memory_increase:.2f}MB")
            
            # 内存评估
            if memory_increase < 50:  # 50MB
                self.log("✓ 内存使用稳定")
            elif memory_increase < 100:  # 100MB
                self.log("⚠ 内存增长较多", "WARNING")
            else:
                self.log("✗ 内存泄漏可能", "ERROR")
                
    def test_error_recovery(self):
        """测试错误恢复能力"""
        self.log("=== 错误恢复测试 ===")
        
        # 测试无效请求
        invalid_requests = [
            {"roomId": "", "business_type": "whole_rent", "url": TEST_IMAGES[0]},
            {"roomId": "test", "business_type": "invalid_type", "url": TEST_IMAGES[0]},
            {"roomId": "test", "business_type": "whole_rent", "url": "https://invalid-url.com/image.jpg"},
            {"roomId": "test", "business_type": "whole_rent", "url": ""}
        ]
        
        for i, invalid_request in enumerate(invalid_requests):
            try:
                start_time = time.time()
                response = requests.post(
                    f"{BASE_URL}/analyze_room",
                    json=invalid_request,
                    timeout=10
                )
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                if response.status_code in [400, 422]:
                    self.log(f"✓ 错误处理正常: 用例 {i+1} ({response_time:.2f}ms)")
                else:
                    self.log(f"⚠ 错误处理异常: 用例 {i+1}, 状态码: {response.status_code}", "WARNING")
                    
            except Exception as e:
                self.log(f"✗ 错误处理测试失败: 用例 {i+1}, 错误: {e}", "ERROR")
                
        # 测试正常请求是否仍能工作
        try:
            normal_request = {
                "roomId": "recovery_test",
                "business_type": "whole_rent",
                "url": TEST_IMAGES[0]
            }
            
            response = requests.post(
                f"{BASE_URL}/analyze_room",
                json=normal_request,
                timeout=30
            )
            
            if response.status_code == 200:
                self.log("✓ 系统恢复能力正常")
            else:
                self.log("✗ 系统恢复能力异常", "ERROR")
                
        except Exception as e:
            self.log(f"✗ 恢复测试失败: {e}", "ERROR")
            
    def test_stability(self):
        """测试系统稳定性"""
        self.log("=== 稳定性测试 ===")
        
        def continuous_request(thread_id):
            """持续发送请求"""
            test_data = {
                "roomId": f"stability_test_{thread_id}",
                "business_type": "whole_rent",
                "url": TEST_IMAGES[thread_id % len(TEST_IMAGES)]
            }
            
            success_count = 0
            total_count = 0
            
            for i in range(10):  # 每个线程发送10个请求
                try:
                    response = requests.post(
                        f"{BASE_URL}/analyze_room",
                        json=test_data,
                        timeout=30
                    )
                    total_count += 1
                    
                    if response.status_code == 200:
                        success_count += 1
                        
                    time.sleep(1)  # 间隔1秒
                    
                except Exception as e:
                    self.log(f"稳定性测试请求失败: 线程{thread_id}, 请求{i+1}, 错误: {e}", "WARNING")
                    
            return {"thread_id": thread_id, "success_count": success_count, "total_count": total_count}
            
        # 启动多个线程进行稳定性测试
        threads = []
        results = []
        
        for i in range(5):  # 5个线程
            thread = threading.Thread(target=lambda: results.append(continuous_request(i)))
            threads.append(thread)
            thread.start()
            
        # 等待所有线程完成
        for thread in threads:
            thread.join()
            
        # 分析结果
        total_success = sum(r['success_count'] for r in results)
        total_requests = sum(r['total_count'] for r in results)
        
        if total_requests > 0:
            success_rate = total_success / total_requests * 100
            self.log(f"稳定性测试结果:")
            self.log(f"  总请求数: {total_requests}")
            self.log(f"  成功请求数: {total_success}")
            self.log(f"  成功率: {success_rate:.1f}%")
            
            if success_rate >= 90:
                self.log("✓ 系统稳定性优秀")
            elif success_rate >= 80:
                self.log("✓ 系统稳定性良好")
            else:
                self.log("⚠ 系统稳定性需要改进", "WARNING")
        else:
            self.log("✗ 稳定性测试失败", "ERROR")
            
    def run_all_performance_tests(self):
        """运行所有性能测试"""
        self.log("🚀 开始房源图片分析系统性能测试")
        
        # 启动服务器
        if not self.start_server():
            self.log("❌ 服务器启动失败，停止测试", "ERROR")
            return False
            
        try:
            # 1. 单个请求性能测试
            self.test_single_request_performance()
            
            # 2. 并发性能测试
            self.test_concurrent_performance()
            
            # 3. 内存使用测试
            self.test_memory_usage()
            
            # 4. 错误恢复测试
            self.test_error_recovery()
            
            # 5. 稳定性测试
            self.test_stability()
            
        finally:
            # 停止服务器
            self.stop_server()
            
        self.log("🎉 性能测试完成")
        return True
        
if __name__ == "__main__":
    tester = PerformanceTester()
    success = tester.run_all_performance_tests()
    
    if success:
        print("\n✅ 性能测试完成")
        sys.exit(0)
    else:
        print("\n❌ 性能测试失败")
        sys.exit(1) 