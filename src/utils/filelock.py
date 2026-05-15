# src/utils/filelock.py
"""
文件锁模块 (生产级)

功能:
1. 跨进程文件锁
2. 超时自动释放
3. 上下文管理器支持

使用示例:
    with FileLock("latest_state.json"):
        # 临界区代码
        write_file()
"""

import fcntl
import os
import time
import logging
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)


class FileLock:
    """文件锁类"""
    
    def __init__(self, lock_file: str, timeout: int = 10):
        """
        初始化文件锁
        
        Args:
            lock_file: 锁文件路径
            timeout: 超时时间 (秒)
        """
        self.lock_file = lock_file + ".lock" if not lock_file.endswith(".lock") else lock_file
        self.timeout = timeout
        self.fd = None
    
    def acquire(self) -> bool:
        """
        获取锁
        
        Returns:
            bool: 是否成功获取
        """
        start_time = time.time()
        
        while True:
            try:
                # 创建锁目录
                os.makedirs(os.path.dirname(self.lock_file) or ".", exist_ok=True)
                
                # 打开锁文件
                self.fd = open(self.lock_file, 'w')
                
                # 尝试获取排他锁
                fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                logger.debug(f"获取锁成功：{self.lock_file}")
                return True
                
            except (IOError, OSError) as e:
                # 锁已被占用
                if self.fd:
                    try:
                        self.fd.close()
                    except:
                        pass
                    self.fd = None
                
                # 检查超时
                if time.time() - start_time > self.timeout:
                    logger.error(f"获取锁超时：{self.lock_file} (等待{self.timeout}秒)")
                    return False
                
                # 等待后重试
                time.sleep(0.1)
    
    def release(self):
        """释放锁"""
        if self.fd:
            try:
                fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
                self.fd.close()
                # 删除锁文件
                if os.path.exists(self.lock_file):
                    os.remove(self.lock_file)
                logger.debug(f"释放锁：{self.lock_file}")
            except Exception as e:
                logger.error(f"释放锁失败：{e}")
            finally:
                self.fd = None
    
    def __enter__(self):
        """上下文管理器入口"""
        if not self.acquire():
            raise TimeoutError(f"无法获取文件锁：{self.lock_file}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.release()
        return False


@contextmanager
def file_lock(lock_file: str, timeout: int = 10):
    """
    文件锁上下文管理器 (便捷函数)
    
    使用示例:
        with file_lock("latest_state.json"):
            write_file()
    """
    lock = FileLock(lock_file, timeout)
    try:
        if not lock.acquire():
            raise TimeoutError(f"无法获取文件锁：{lock_file}")
        yield lock
    finally:
        lock.release()


def locked_write(file_path: str, content: str, timeout: int = 10):
    """
    加锁写入文件 (便捷函数)
    
    Args:
        file_path: 文件路径
        content: 文件内容
        timeout: 超时时间
    """
    lock = FileLock(file_path, timeout)
    
    try:
        if not lock.acquire():
            logger.error(f"写入失败：无法获取锁 {file_path}")
            return False
        
        # 写入内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.debug(f"加锁写入成功：{file_path}")
        return True
        
    except Exception as e:
        logger.error(f"加锁写入失败：{e}")
        return False
        
    finally:
        lock.release()


if __name__ == "__main__":
    # 测试文件锁
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    test_file = "test_lock.json"
    
    # 测试 1: 正常加锁写入
    print("测试 1: 正常加锁写入")
    success = locked_write(test_file, '{"test": 1}', timeout=5)
    print(f"写入结果：{success}")
    
    # 测试 2: 并发写入测试
    print("\n测试 2: 并发写入测试")
    import threading
    
    def writer(i):
        with file_lock(test_file, timeout=5):
            time.sleep(0.5)
            with open(test_file, 'w') as f:
                f.write(f'{{"writer": {i}}}')
            print(f"Writer {i} 完成")
    
    threads = []
    for i in range(3):
        t = threading.Thread(target=writer, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    print("\n测试完成")
