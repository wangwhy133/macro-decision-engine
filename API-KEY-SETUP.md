# 🔑 API Key 配置指南

本系统需要以下 API Keys 才能获取完整数据和分析能力。

---

## 1. FRED API Key (必需 - 美国宏观数据)

**用途**: 获取美国 CPI、失业率、联邦基金利率等核心数据  
**免费额度**: 每日 5000 次调用 (足够个人使用)  
**获取难度**: ⭐ (简单，立即获取)

### 获取步骤:
1. 访问: https://fred.stlouisfed.org/docs/api/api_key.html
2. 点击右上角 "Request API Key"
3. 填写邮箱和用途 (个人使用选 Personal)
4. 立即获得 Key (32 位字符串)

### 配置方法:
编辑 `.env` 文件:
```bash
nano .env
```

填入:
```env
FRED_API_KEY=你复制的 32 位 Key
```

---

## 2. 智谱 AI API Key (可选 - 智能分析)

**用途**: AI 驱动的市场情绪分析、叙事解读  
**免费额度**: 新用户赠送额度，足够测试  
**获取难度**: ⭐⭐ (需手机号注册)

### 获取步骤:
1. 访问: https://open.bigmodel.cn/
2. 注册/登录账号
3. 进入控制台 -> API Key 管理
4. 创建新 Key

### 配置方法:
在 `.env` 文件中填入:
```env
ZHIPU_API_KEY=你的智谱 API Key
AI_MODEL=glm-4
```

---

## 3. Telegram Bot Token (可选 - 消息推送)

**用途**: 数据异常时推送告警到手机  
**获取难度**: ⭐⭐ (需翻墙)

### 获取步骤:
1. 搜索 @BotFather
2. 发送 /newbot 创建机器人
3. 复制 Bot Token

### 配置方法:
```env
TELEGRAM_BOT_TOKEN=你的 Bot Token
TELEGRAM_CHAT_ID=你的 Chat ID
```

---

## ✅ 验证配置

配置完成后，运行以下命令验证:

```bash
cd /root/.openclaw/workspace/macro-system-repo
./venv/bin/python -m macro_system check
```

如果显示 "✓ 所有配置校验通过"，则配置成功！

---

## 📞 常见问题

**Q: 不配置 FRED Key 会怎样？**  
A: 系统仍可运行，但无法获取美国数据，只能看中国数据。

**Q: 不配置 AI Key 会怎样？**  
A: 系统使用简化分析模式，仍能正常运行。

**Q: Key 泄露了怎么办？**  
A: 立即在对应平台撤销 Key 并重新生成。

---

**下一步**: 获取 Key 后，运行 `./venv/bin/python -m macro_system run` 开始数据采集！
