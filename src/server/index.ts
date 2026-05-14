/**
 * MDE 轻量级监控服务器
 * 功能：提供 API 接口和 Web 看板，实时监控猪周期数据
 * 依赖：无 (仅使用 Node.js 原生 http/fs 模块)
 */

import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { initDatabase } from '../db/init-db';
import { DataCredibilityService } from '../services/DataCredibilityService';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DB_PATH = path.join(__dirname, '../../macro-decision.db');
const PORT = process.env.MDE_PORT || 3000;

// 简单的路由处理
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url || '/', `http://${req.headers.host}`);
  
  // 设置 CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Content-Type', 'application/json');

  try {
    // 1. API: 获取最新决策
    if (url.pathname === '/api/decision') {
      const decision = await getDecision();
      res.writeHead(200);
      res.end(JSON.stringify(decision, null, 2));
      return;
    }

    // 2. API: 获取历史数据 (用于图表)
    if (url.pathname === '/api/history') {
      const history = await getHistoryData();
      res.writeHead(200);
      res.end(JSON.stringify(history, null, 2));
      return;
    }

    // 3. API: 健康检查
    if (url.pathname === '/api/health') {
      res.writeHead(200);
      res.end(JSON.stringify({ status: 'ok', timestamp: Date.now() }));
      return;
    }

    // 4. Web 看板首页
    if (url.pathname === '/') {
      const html = getDashboardHtml();
      res.setHeader('Content-Type', 'text/html; charset=utf-8');
      res.writeHead(200);
      res.end(html);
      return;
    }

    // 404
    res.writeHead(404);
    res.end(JSON.stringify({ error: 'Not Found' }));
  } catch (error: any) {
    console.error('Server Error:', error);
    res.writeHead(500);
    res.end(JSON.stringify({ error: error.message }));
  }
});

/**
 * 获取最新决策逻辑 (复用 CLI 逻辑)
 */
async function getDecision() {
  const db = await initDatabase(DB_PATH);
  const dataService = new DataCredibilityService(db);
  
  const inventoryData = await dataService.loadDataForEvaluation('pig_inventory', 12);
  const change3mData = await dataService.loadDataForEvaluation('pig_inventory_change_3m', 12);
  
  if (inventoryData.length === 0) {
    return { action: 'ERROR', reason: 'No data' };
  }

  const latestInv = inventoryData[0]?.normalized.value as number || 0;
  const latestChange3m = change3mData[0]?.normalized.value as number || 0;
  
  let action = 'HOLD';
  const signals: string[] = [];
  
  // 规则判断
  if (latestInv < 4300) {
    action = 'BUY';
    signals.push('低水位买入');
  }
  if (latestChange3m < -3) {
    action = 'BUY';
    signals.push('加速去化');
  }
  if (latestInv > 5000) {
    action = 'SELL';
    signals.push('周期顶部预警');
  }

  return {
    timestamp: new Date().toISOString(),
    action,
    signals,
    data: {
      inventory: latestInv,
      change_3m: latestChange3m
    }
  };
}

/**
 * 获取历史数据 (用于图表)
 */
async function getHistoryData() {
  const db = await initDatabase(DB_PATH);
  const dataService = new DataCredibilityService(db);
  
  const inventoryData = await dataService.loadDataForEvaluation('pig_inventory', 24);
  
  return inventoryData.reverse().map(d => ({
    date: new Date(d.timestamp).toISOString().split('T')[0],
    value: d.normalized.value
  }));
}

/**
 * 生成 Web 看板 HTML (内联 Chart.js)
 */
function getDashboardHtml() {
  return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MDE 监控看板</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
    .container { max-width: 1200px; margin: 0 auto; }
    .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .header { display: flex; justify-content: space-between; align-items: center; }
    .status { font-size: 24px; font-weight: bold; padding: 8px 16px; border-radius: 4px; }
    .status-BUY { background: #d4edda; color: #155724; }
    .status-SELL { background: #f8d7da; color: #721c24; }
    .status-HOLD { background: #e2e3e5; color: #383d41; }
    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 20px; }
    .metric { text-align: center; }
    .metric-value { font-size: 32px; font-weight: bold; color: #333; }
    .metric-label { color: #666; margin-top: 5px; }
    .signals { margin-top: 10px; }
    .signal-tag { display: inline-block; background: #007bff; color: white; padding: 4px 12px; border-radius: 12px; margin-right: 8px; font-size: 14px; }
    .chart-container { position: relative; height: 400px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="card header">
      <h1>📊 宏观决策引擎监控看板</h1>
      <div id="status" class="status">加载中...</div>
    </div>
    
    <div class="card">
      <div class="metric-grid">
        <div class="metric">
          <div class="metric-value" id="inventory">-</div>
          <div class="metric-label">能繁母猪存栏量 (万头)</div>
        </div>
        <div class="metric">
          <div class="metric-value" id="change3m">-</div>
          <div class="metric-label">3 月变化率 (%)</div>
        </div>
        <div class="metric">
          <div class="metric-value" id="health">-</div>
          <div class="metric-label">市场健康度</div>
        </div>
      </div>
      <div class="signals" id="signals"></div>
    </div>

    <div class="card">
      <h3>📈 存栏量趋势 (近 24 个月)</h3>
      <div class="chart-container">
        <canvas id="chart"></canvas>
      </div>
    </div>
  </div>

  <script>
    async function load() {
      // 加载决策
      const res = await fetch('/api/decision');
      const data = await res.json();
      
      document.getElementById('status').textContent = data.action;
      document.getElementById('status').className = 'status status-' + data.action;
      
      if (data.data) {
        document.getElementById('inventory').textContent = data.data.inventory.toFixed(1);
        document.getElementById('change3m').textContent = (data.data.change_3m || 0).toFixed(2) + '%';
        
        // 计算健康度 (简化版: 越低越健康/适合买入)
        const health = data.data.inventory < 4300 ? '高 (适合布局)' : (data.data.inventory > 5000 ? '低 (风险高)' : '中');
        document.getElementById('health').textContent = health;
      }
      
      // 显示信号
      const signalsDiv = document.getElementById('signals');
      signalsDiv.innerHTML = '';
      if (data.signals && data.signals.length > 0) {
        data.signals.forEach(s => {
          signalsDiv.innerHTML += '<span class="signal-tag">' + s + '</span>';
        });
      } else {
        signalsDiv.innerHTML = '<span style="color:#666">暂无明显信号</span>';
      }

      // 加载图表数据
      const histRes = await fetch('/api/history');
      const histData = await histRes.json();
      
      const ctx = document.getElementById('chart').getContext('2d');
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: histData.map(d => d.date),
          datasets: [{
            label: '存栏量 (万头)',
            data: histData.map(d => d.value),
            borderColor: '#007bff',
            tension: 0.4,
            fill: true,
            backgroundColor: 'rgba(0, 123, 255, 0.1)'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } }
        }
      });
    }
    
    load();
    // 每 5 分钟自动刷新
    setInterval(load, 300000);
  </script>
</body>
</html>
  `;
}

// 启动服务器
server.listen(PORT, () => {
  console.log(`🚀 MDE 监控看板已启动: http://localhost:${PORT}`);
  console.log(`   API: http://localhost:${PORT}/api/decision`);
});
