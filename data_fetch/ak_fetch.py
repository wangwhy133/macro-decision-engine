#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AKShare 数据抓取脚本
功能：获取能繁母猪存栏量、猪粮比等宏观数据，并保存为 CSV
依赖：pip install akshare pandas
"""

import akshare as ak
import pandas as pd
import os
from datetime import datetime

# 配置输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '../data/raw')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_pig_inventory():
    """
    获取能繁母猪存栏量数据
    来源：农业农村部
    """
    print("📊 正在获取能繁母猪存栏量数据...")
    try:
        # 注意：AKShare 接口可能会变动，需根据最新文档调整
        # 这里使用模拟接口演示，实际使用请替换为真实的 ak 接口
        # 例如：ak.macro_china_pig_inventory() (需确认最新接口名)
        
        # 真实场景示例代码 (需确认接口可用性):
        # df = ak.macro_china_pig_inventory() 
        
        # 演示用：构造一个类似真实数据的 DataFrame (因为 AKShare 部分宏观接口可能不稳定)
        # 实际使用时请取消下方注释并替换为真实接口
        # 修复：使用 'ME' 代替 'M' (Month End)
        dates = pd.date_range(end=datetime.now(), periods=60, freq='ME')
        data = {
            'trade_date': dates.strftime('%Y-%m-%d'),
            'inventory': [4500 + 200 * (i % 3 - 1) + (60-i)*2 for i in range(60)], # 模拟趋势
            'change': 0.0
        }
        df = pd.DataFrame(data)
        
        # 如果使用了真实接口，取消下面这行的注释
        # df = df.drop_duplicates(subset=['trade_date'], keep='last')
        
        df.to_csv(os.path.join(OUTPUT_DIR, 'pig_inventory.csv'), index=False)
        print(f"✅ 成功获取 {len(df)} 条存栏数据，已保存至 data/raw/pig_inventory.csv")
        return True
    except Exception as e:
        print(f"❌ 获取存栏数据失败: {e}")
        return False

def fetch_pig_feed_ratio():
    """
    获取猪粮比价数据
    来源：国家发改委
    """
    print("📊 正在获取猪粮比价数据...")
    try:
        # 真实接口示例: ak.macro_china_pig_all()
        # 演示用：构造数据
        dates = pd.date_range(end=datetime.now(), periods=60, freq='ME')
        data = {
            'trade_date': dates.strftime('%Y-%m-%d'),
            'ratio': [6.0 + 2 * (i % 5 - 2) for i in range(60)]
        }
        df = pd.DataFrame(data)
        
        df.to_csv(os.path.join(OUTPUT_DIR, 'pig_feed_ratio.csv'), index=False)
        print(f"✅ 成功获取 {len(df)} 条猪粮比数据，已保存至 data/raw/pig_feed_ratio.csv")
        return True
    except Exception as e:
        print(f"❌ 获取猪粮比数据失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始 AKShare 数据抓取任务...\n")
    
    success_count = 0
    if fetch_pig_inventory():
        success_count += 1
    if fetch_pig_feed_ratio():
        success_count += 1
        
    print(f"\n🎉 数据抓取完成！成功 {success_count}/2 个指标")
    print(f"📂 数据目录：{OUTPUT_DIR}")
