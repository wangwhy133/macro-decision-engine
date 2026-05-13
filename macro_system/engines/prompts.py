"""Prompt builders for AI market commentary.

Keep long natural-language prompt templates out of macro_push.py so the entry
script remains an orchestrator.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List


def _structured_opportunity_points(data: Dict[str, Any]) -> List[str]:
    """Render StandardOutput opportunity observations for AI prompts.

    The structured opportunity engine is the source of truth.  Legacy
    ``build_opportunity_points`` remains as a fallback for direct callers/tests,
    but prompts should not let AI see a second, inconsistent opportunity list.
    """
    payload = data.get("standard_payload") if isinstance(data.get("standard_payload"), dict) else {}
    observations = ((payload.get("metadata") or {}).get("opportunity_observations") or []) if payload else []
    points: List[str] = []
    for idx, item in enumerate(observations, 1):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "机会观察")
        status = str(item.get("status") or "unknown")
        confidence = str(item.get("confidence") or "unknown")
        logic = str(item.get("logic") or "")
        watch = "；".join(map(str, (item.get("watch_points") or [])[:3]))
        invalidation = "；".join(map(str, (item.get("invalidation_conditions") or [])[:2]))
        constraints = "；".join(map(str, (item.get("data_quality_constraints") or [])[:3]))
        text = f"{idx}. {title} [{status}/confidence={confidence}]。逻辑：{logic}"
        if watch:
            text += f" 观察点：{watch}。"
        if invalidation:
            text += f" 否定条件：{invalidation}。"
        if constraints:
            text += f" 约束：{constraints}。"
        points.append(text)
    return points


def _structured_opportunity_only(data: Dict[str, Any]) -> List[str]:
    """Return ONLY structured opportunities; do NOT fall back to legacy engine.

    Use this in prompt builders so AI never sees a second, inconsistent list
    when the structured engine has something to say.
    """
    return _structured_opportunity_points(data)


def build_opportunity_points(data: Dict[str, Any], narrative_str: str = "") -> List[str]:
    """Legacy-compatible wrapper for opportunity points.
    
    This function exists for backward compatibility with macro_push.py imports.
    New code should use _structured_opportunity_points() or _structured_opportunity_only().
    
    Args:
        data: Full data dict containing standard_payload
        narrative_str: Deprecated, kept for signature compatibility
    
    Returns:
        List of formatted opportunity point strings
    """
    return _structured_opportunity_points(data)


def _build_analyze_prompt_data_context(data: Dict[str, Any]) -> Dict[str, Any]:
    """Build context dictionary for prompt templates."""
    m, pe = data["macro"], data["pe"]
    futures_list = data.get("futures", [])
    us = data.get("us_macro", {})
    ub = data.get("us_bond", {})
    zt = data.get("zt_emotion", {})
    narrative_str = data.get("narrative_summary", "")
    top_concepts = narrative_str.split("热门:", 1)[1].strip() if "热门:" in narrative_str else "N/A"
    return locals()


def _parse_number_text(value):
    if value is None:
        return None
    try:
        import re
        m = re.search(r"[-+]?\d+(?:\.\d+)?", str(value))
        return float(m.group(0)) if m else None
    except Exception:
        return None


def _get_risk_constraint_instructions(data: Dict[str, Any]) -> str:
    """Generate hard constraint instructions based on risk level and data quality.
    
    Trading Logic Hardening:
    - If risk_level >= 70: Forbid 'buy', 'add position' etc. Only 'observe', 'wait' allowed.
    - If data quality is low: Forbid certainty claims.
    """
    standard_payload = data.get("standard_payload") if isinstance(data.get("standard_payload"), dict) else {}
    if not standard_payload:
        return ""
    
    risk_level = standard_payload.get("risk_level", 0)
    metadata = standard_payload.get("metadata") or {}
    reliability = metadata.get("judgment_reliability") or {}
    level = reliability.get("level", "unknown")
    
    instructions = []
    
    # Hard risk constraints
    if risk_level >= 70:
        instructions.append(
            "【高风险约束】当前风险等级≥70，禁止使用'买入'、'加仓'、'追涨'、'重仓'等激进词汇。"
            "仅允许使用'观察'、'等待'、'跟踪'、'验证'、'防御'等保守表述。"
            "必须强调仓位控制和风险规避。"
        )
    
    # Data quality constraints
    if level in ("low", "very_low"):
        instructions.append(
            "【数据质量约束】关键数据缺失或可靠性低，禁止做出确定性判断。"
            "必须说明'数据不足'、'需进一步验证'、'存在较大不确定性'。"
        )
    
    # Asset caps constraint
    asset_caps = metadata.get("asset_caps") or {}
    if asset_caps:
        caps = asset_caps.get("caps") or {}
        china_eq = caps.get("china_equities", 0)
        if china_eq <= 0.1:  # <= 10%
            instructions.append(
                f"【仓位上限约束】A 股权益上限仅为{china_eq:.0%}，严禁建议提高股票仓位。"
            )
    
    return " ".join(instructions) if instructions else ""


def _safe(x, default="N/A"):
    return default if x is None else x


def _safe_cp(x):
    try:
        return f"{float(x):+.2f}%"
    except Exception:
        return "N/A"


def _common_context(
    data: Dict,
    build_global_risk_snapshot: Callable[[Dict], Dict[str, str]],
    build_china_macro_inference: Callable[[Dict[str, str]], Dict[str, object]],
    build_opportunity_points: Callable[[Dict, str], List[str]],
) -> Dict[str, object]:
    m, pe = data["macro"], data["pe"]
    futures_list = data.get("futures", [])
    us = data.get("us_macro", {})
    ub = data.get("us_bond", {})
    zt = data.get("zt_emotion", {})
    narrative_str = data.get("narrative_summary", "")
    top_concepts = narrative_str.split("热门:", 1)[1].strip() if "热门:" in narrative_str else "N/A"
    gr = build_global_risk_snapshot(data)
    ci = build_china_macro_inference(m)
    china_inference = f"状态={ci['regime']}，分数={ci['score']}，数据覆盖={ci['quality']}；" + "；".join(ci['bullets'])
    structured_points = _structured_opportunity_points(data)
    opportunity_points = "\n".join(structured_points or build_opportunity_points(data, narrative_str))
    opportunity_paused = "暂停高置信机会输出" in opportunity_points

    fut_map = {f["symbol"]: f for f in futures_list if isinstance(f, dict) and "symbol" in f}
    dow = fut_map.get("gb_dji", {})
    nas = fut_map.get("gb_ixic", {})
    gold = fut_map.get("hf_GC", {})
    oil = fut_map.get("hf_CL", {})
    dxy = fut_map.get("USDCNY", {})

    hs300 = pe.get("沪深300", {})
    pe_val = hs300.get("pe", "N/A")
    pe_pct = hs300.get("pct", "N/A")
    pe_pct_num = _parse_number_text(pe_pct)
    pe_zone = "高估/历史高位" if pe_pct_num is not None and pe_pct_num >= 70 else "低估/历史低位" if pe_pct_num is not None and pe_pct_num <= 30 else "中位区间" if pe_pct_num is not None else "数据缺失"
    oil_cp = _parse_number_text(oil.get("cp"))
    oil_direction = "上涨" if oil_cp is not None and oil_cp > 0 else "下跌" if oil_cp is not None and oil_cp < 0 else "持平"
    pmi_val = _parse_number_text(m.get("pmi_mfg"))
    pmi_state = "荣枯线上方/制造业扩张" if pmi_val is not None and pmi_val >= 50 else "荣枯线下方/制造业收缩" if pmi_val is not None else "数据缺失/待验证"
    spread_val = _parse_number_text(ub.get("us10y_2y_spread"))
    spread_state = "正利差/未倒挂" if spread_val is not None and spread_val >= 0 else "负利差/倒挂" if spread_val is not None else "数据缺失/待验证"
    us30_val = _parse_number_text(ub.get("us30y"))
    spread30_10_val = _parse_number_text(ub.get("us30y_10y_spread"))
    us30_state = "长端高压" if us30_val is not None and us30_val >= 5.0 else "长端偏高" if us30_val is not None and us30_val >= 4.6 else "长端压力缓和" if us30_val is not None else "数据缺失/待验证"
    spread30_10_state = "超长端走陡/期限溢价上升" if spread30_10_val is not None and spread30_10_val >= 0.30 else "超长端倒挂/增长预期偏弱" if spread30_10_val is not None and spread30_10_val < 0 else "相对平稳" if spread30_10_val is not None else "数据缺失/待验证"
    fg_line = next((line for line in narrative_str.splitlines() if "恐慌贪婪" in line), "N/A")

    return locals()


def build_analyze_prompt(data: Dict, build_global_risk_snapshot, build_china_macro_inference, build_opportunity_points) -> str:
    c = _common_context(data, build_global_risk_snapshot, build_china_macro_inference, build_opportunity_points)
    m, pe, us, ub, zt = c["m"], c["pe"], c["us"], c["ub"], c["zt"]
    gr = c["gr"]
    
    # Get risk-based constraints
    risk_constraints = _get_risk_constraint_instructions(data)
    constraint_section = f"\n## 【系统硬约束】\n{risk_constraints}\n" if risk_constraints else ""
    
    return f'''你是盘后投资简报助手{constraint_section}，风格要像交易员写给自己的复盘：直接、可读、有风险意识，不要写学院派宏观长文。

## 【硬性事实校验】
- 禁止写出与数字方向相反的判断：正数=上涨/扩张，负数=下跌/收缩。
- PMI >= 50 必须表述为荣枯线上方/扩张；PMI < 50 才能说荣枯线下方/收缩。
- PE分位 >=70% 必须表述为历史高位/偏贵；<=30% 才能说低位/便宜。
- 10Y-2Y和30Y-10Y利差为正表示未倒挂；为负才是倒挂；30Y-10Y大幅为正通常表示超长端走陡/期限溢价上升。
- 若字段为 N/A，只能说“数据缺失/待验证”，禁止推导确定结论。
- 炸板率 <0.15 才能说封板稳定/分歧低；炸板率 >=0.35 才能说分歧较大；炸板率 >=0.50 才能说分歧极大/炸板率高。
- 不要输出“核心判断/多市场联动/决策指令”这种标题，必须严格使用下面模板。

## 【可用数据】
- 沪深300 PE={c['pe_val']}，历史分位={c['pe_pct']}，估值象限={c['pe_zone']}
- 恐慌贪婪={c['fg_line']}
- 涨停={zt.get('zt_count','N/A')}只，强势={zt.get('zt_strong_count','N/A')}只，炸板率={zt.get('zt_fuse_rate','N/A')}
- 热门概念={c['top_concepts']}
- CPI={m.get('cpi','N/A')}，PPI={m.get('ppi','N/A')}，PMI={m.get('pmi_mfg','N/A')}
- 新增贷款={m.get('new_credit','N/A')}，新增贷款累计YoY={m.get('new_credit_ytd_yoy','N/A')}，社融存量YoY={m.get('total_social_financing','N/A')}
- 中国宏观推导={c['china_inference']}
- 出口={m.get('export_yoy','N/A')}，进口={m.get('import_yoy','N/A')}，贸易顺差={m.get('trade_balance','N/A')}
- 美债10年={ub.get('us10y','N/A')}，30年={ub.get('us30y','N/A')}({c['us30_state']})，10Y-2Y={ub.get('us10y_2y_spread','N/A')}，30Y-10Y={ub.get('us30y_10y_spread','N/A')}({c['spread30_10_state']})，VIX={us.get('us_vix','N/A')}
- 全球风险定价：美元指数={gr['dollar']}，实际利率={gr['real10y']}，高收益债利差={gr['hy_oas']}，NFCI={gr['nfci']}，铜金比={gr['copper_gold']}，油金比={gr['oil_gold']}，风险状态={gr['regime']}
- 规则机会观察：
{c['opportunity_points']}
- 道指={_safe(c['dow'].get('price'))}({_safe_cp(c['dow'].get('cp'))})，纳指={_safe(c['nas'].get('price'))}({_safe_cp(c['nas'].get('cp'))})
- 黄金={_safe(c['gold'].get('price'))}({_safe_cp(c['gold'].get('cp'))})，原油={_safe(c['oil'].get('price'))}({_safe_cp(c['oil'].get('cp'))})，原油方向={c['oil_direction']}
- 美元/人民币={_safe(c['dxy'].get('price'))}({_safe_cp(c['dxy'].get('cp'))})

## 【输出模板：必须保持这个感觉】
今日风险：
1. 估值风险：结合沪深300PE和分位说明，不超过2句。
2. 情绪过热风险：结合涨停/强势/恐慌贪婪说明，不超过2句。
3. 宏观或外部风险：从PMI、出口、美债10Y/30Y/期限利差、VIX、原油、汇率中选一个真实有效字段；若没有有效字段，就写“数据缺失，暂不下结论”。

今日机会：
1. 若“规则机会观察”包含“暂停高置信机会输出”，本节必须只写“暂停高置信机会输出：按规则引擎给出的暂停原因，当前只做观察不做追涨”，禁止再列任何概念机会。
2. 若未暂停：从热门概念里挑第1个，说明为什么值得跟踪，不要承诺收益。
3. 若未暂停：从热门概念里挑第2/3个说明观察点；如果没有第3个，写“无第三条高置信机会”。

五位大师点评：
巴菲特：两句，围绕估值和安全边际。
索罗斯：两句，围绕情绪反身性和拐点。
彼得·林奇：两句，围绕行业景气和基本面验证。
约翰·邓普顿：两句，围绕逆向和分散。
霍华德·马克斯：两句，围绕周期位置和风险控制。

要求：
- 每条都要贴合今天的数据，不要空泛名言。
- 不要编造个股，不要给买卖指令。
- 今日机会必须服从“规则机会观察”；若规则已暂停，AI不得自行恢复机会清单。
- 今日机会必须使用“观察/跟踪/验证”语气，禁止使用“有望持续受益/巨大潜力/迎来机遇”等确定性宣传语。
- 若概念热度低于50，只能写“低热度观察”，不得包装成高置信机会。
- 保持中文自然表达，像你给的样例，但更克制、更有交易纪律。
'''


def build_risk_prompt(data: Dict, build_global_risk_snapshot, build_china_macro_inference, build_opportunity_points) -> str:
    c = _common_context(data, build_global_risk_snapshot, build_china_macro_inference, build_opportunity_points)
    m, us, ub, zt = c["m"], c["us"], c["ub"], c["zt"]
    gr = c["gr"]
    return f'''你是系统性风险顾问，职责是发现"房间里的大象"——那些明明在场却被集体忽视的风险。用交易员的思路写，不是学术报告。

## 【硬性事实校验】
- 禁止写出与数字方向相反的判断。
- PMI >= 50 必须说荣枯线上方/扩张；PMI < 50 才能说荣枯线下方/收缩。
- 10Y-2Y和30Y-10Y利差为正时不能称为"倒挂"；为负时才是倒挂；30Y-10Y大幅为正不能说长端走平或期限溢价下降。
- N/A 字段只能标记"数据缺失"，不得当作有效信号。
- 炸板率 <0.15 才能说封板稳定/分歧低；炸板率 >=0.35 才能说分歧较大；炸板率 >=0.50 才能说分歧极大/炸板率高。
- 必须严格使用下面的输出模板。

## 【可用数据】
CPI={m.get('cpi','N/A')}，PPI={m.get('ppi','N/A')}，PMI={m.get('pmi_mfg','N/A')}({c['pmi_state']})
新增贷款={m.get('new_credit','N/A')}，新增贷款累计YoY={m.get('new_credit_ytd_yoy','N/A')}，社融存量YoY={m.get('total_social_financing','N/A')}
中国宏观推导={c['china_inference']}
出口={m.get('export_yoy','N/A')}，贸易顺差={m.get('trade_balance','N/A')}
美债10年={ub.get('us10y','N/A')}，30年={ub.get('us30y','N/A')}({c['us30_state']})，10Y-2Y={ub.get('us10y_2y_spread','N/A')}({c['spread_state']})，30Y-10Y={ub.get('us30y_10y_spread','N/A')}({c['spread30_10_state']})，VIX={us.get('us_vix','N/A')}
全球风险定价：美元指数={gr['dollar']}，实际利率={gr['real10y']}，高收益债利差={gr['hy_oas']}，NFCI={gr['nfci']}，铜金比={gr['copper_gold']}，油金比={gr['oil_gold']}，风险状态={gr['regime']}
规则机会观察：
{c['opportunity_points']}
沪深300 PE={c['pe_val']}，分位={c['pe_pct']}，估值象限={c['pe_zone']}
道指={_safe(c['dow'].get('price'))}({_safe_cp(c['dow'].get('cp'))})，纳指={_safe(c['nas'].get('price'))}({_safe_cp(c['nas'].get('cp'))})
黄金={_safe(c['gold'].get('price'))}({_safe_cp(c['gold'].get('cp'))})，原油={_safe(c['oil'].get('price'))}({_safe_cp(c['oil'].get('cp'))})
美元/人民币={_safe(c['dxy'].get('price'))}({_safe_cp(c['dxy'].get('cp'))})
热门概念={c['top_concepts']}
涨停={zt.get('zt_count','N/A')}只，强势={zt.get('zt_strong_count','N/A')}只，炸板率={zt.get('zt_fuse_rate','N/A')}

## 【输出模板：必须保持这个感觉】
今日风险：
1. 估值风险：结合沪深300PE和分位说明，不超过2句。
2. 情绪过热风险：结合涨停/强势/恐慌贪婪说明，不超过2句。
3. 宏观或外部风险：从PMI、出口、美债10Y/30Y/期限利差、VIX、原油、汇率中选一个真实有效字段；若没有有效字段，就写"数据缺失，暂不下结论"。

今日机会：
1. 若“规则机会观察”包含“暂停高置信机会输出”，本节必须只写“暂停高置信机会输出：按规则引擎给出的暂停原因，当前只做观察不做追涨”，禁止再列任何概念机会。
2. 若未暂停：必须只从“热门概念”字段里挑第1个，说明为什么值得跟踪，不要承诺收益，不要把黄金/原油/汇率当概念机会。
3. 若未暂停：必须只从“热门概念”字段里挑第2/3个说明观察点；如果没有第3个，写"无第三条高置信机会"。

五位大师点评：
巴菲特：两句，围绕估值和安全边际。
索罗斯：两句，围绕情绪反身性和拐点。
彼得·林奇：两句，围绕行业景气和基本面验证。
约翰·邓普顿：两句，围绕逆向和分散。
霍华德·马克斯：两句，围绕周期位置和风险控制。

要求：
- 每条都要贴合今天的数据，不要空泛名言。
- 不要编造个股，不要给买卖指令。
- 今日机会必须服从“规则机会观察”；若规则已暂停，AI不得自行恢复机会清单。
- 今日机会必须使用“观察/跟踪/验证”语气，禁止使用“有望持续受益/巨大潜力/迎来机遇”等确定性宣传语。
- 若概念热度低于50，只能写“低热度观察”，不得包装成高置信机会。
- 保持中文自然表达，像你给的样例，但更克制、更有交易纪律。
'''
