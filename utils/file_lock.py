"""
文件锁工具
防止多进程同时写入数据库
"""
import os
import fcntl
import time
from contextlib import contextmanager
from typing import Optional

class FileLock:
    """基于文件的互斥锁"""
    def __init__(self, lock_file: str):
        self.lock_file = lock_file
        self.fd: Optional[int] = None
    
    def acquire(self, timeout: float = 10.0) -> bool:
        """
        获取锁
        :param timeout: 超时时间（秒）
        :return: 是否成功获取
        """
        start = time.time()
        while True:
            try:
                self.fd = os.open(self.lock_file, os.O_CREAT | os.O_RDWR)
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except (IOError, OSError):
                if self.fd:
                    os.close(self.fd)
                
                if time.time() - start > timeout:
                    return False  # 超时
                
                time.sleep(0.1)  # 等待 100ms 后重试
    
    def release(self):
        """释放锁"""
        if self.fd:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
                os.close(self.fd)
            except:
                pass
            self.fd = None

@contextmanager
def db_lock(db_path: str, timeout: float = 10.0):
    """
    数据库锁上下文管理器
    用法: with db_lock('/path/to/db.db'): ...
    """
    lock_file = db_path + ".lock"
    lock = FileLock(lock_file)
    
    if not lock.acquire(timeout):
        raise TimeoutError(f"无法获取数据库锁：{lock_file} (超时 {timeout}s)")
    
    try:
        yield lock
    finally:
        lock.release()

if __name__ == "__main__":
    import tempfile
    import threading
    
    lock_file = tempfile.mktemp(".lock")
    results = []
    
    def worker(i: int):
        with db_lock(lock_file):
            results.append(f"Worker {i} got lock")
            time.sleep(0.5)
    
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    print(results)  # 应只有一个 worker 获得锁
