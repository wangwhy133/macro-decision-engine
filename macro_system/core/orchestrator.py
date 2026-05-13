"""Macro Decision Support Orchestrator.

Encapsulates the full decision pipeline, separating workflow orchestration
from business logic implementation.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional, Callable, List, Tuple

from macro_system.data.collector import DataCollector, CollectResult
from macro_system.core.standard_output import build_and_persist_standard_decision
from macro_system.engines.ai_agents import run_ai_layers
from macro_system.engines.narrative import (
    calculate_fear_greed,
    classify_sentiment_state,
    interpret_narrative,
)
from macro_system.output.formatter import format_legacy_report
from macro_system.review.daily_runs import save_daily_run
from macro_system.data.repository import MacroRepository
from macro_system.config.loader import load_config
from macro_system.utils.logger import get_logger
from macro_system.utils.heartbeat import update_status
from macro_system.utils.disk_utils import check_disk_space
from macro_system.utils.notification import send_notification
from macro_system.data.history import get_history_manager

logger = get_logger("macro_system.orchestrator")

# Local helper for normalizing concepts
def _normalize_top_concepts(concepts_data, limit=10):
    if not concepts_data:
        return []
    items = concepts_data.get('top_5', []) if isinstance(concepts_data, dict) else concepts_data
    result = []
    for item in list(items)[:limit]:
        if isinstance(item, dict):
            name = item.get('name') or item.get('concept')
            heat = item.get('heat') or item.get('score')
        else:
            continue
        if name:
            result.append({'name': str(name), 'heat': heat})
    return result

# Forward imports for legacy compatibility in tests
try:
    from macro_push import (
        fetch_news_sentiment,
        fetch_hot_concepts,
        get_narrative_summary,
        save_narrative_data,
    )
except ImportError:
    # Fallback mocks if macro_push functions are not available
    def fetch_news_sentiment(zt_emotion: Dict) -> Dict[str, Any]:
        return {"sentiment": "neutral", "score": 50}

    def fetch_hot_concepts() -> Dict[str, Any]:
        return {"top_5": []}

    def get_narrative_summary() -> str:
        return "Narrative summary not available."

    def save_narrative_data(narrative, concepts, fear_greed, interp=""):
        pass


class MacroOrchestrator:
    """Orchestrates the macro decision support pipeline."""

    def __init__(
        self,
        config: Dict[str, Any],
        dry_run: bool = False,
        log_handler: Optional[Callable[[str, str], None]] = None,
    ):
        self.config = config
        self.dry_run = dry_run
        self.log = log_handler or (lambda msg, level=None: print(f"[{level}] {msg}" if level else msg))
        self.db_path = os.getenv("MACRO_DB_PATH", "/opt/macro-push/data/macro.db")
        self.repository = MacroRepository(self.db_path)
        self.repository.init()

    def run(self) -> None:
        """Execute the full decision pipeline."""
        logger.info("Starting macro decision pipeline...", "INFO")
        try:
            # 1. Data Collection
            logger.info("Collecting market data...", "INFO")
            collector = DataCollector(self.config, dry_run=self.dry_run, log=self.log)
            collect_result = collector.collect()
            data = collect_result.data
            data["run_timestamp"] = datetime.now().isoformat()

            # Persist raw data
            logger.info("Persisting market data...", "INFO")
            self.repository.save_market_data(data)

            # 2. Narrative Context
            logger.info("Building narrative context...", "INFO")
            narrative_text = self._build_narrative_context(data)
            data["narrative_summary"] = narrative_text

            # 3. Standard Output & AI Analysis
            logger.info("Generating standard output and AI analysis...", "INFO")
            standard_payload = self._build_standard_payload(data, narrative_text)
            if standard_payload:
                data["standard_payload"] = standard_payload
                ai, risk = run_ai_layers(data, timeout_seconds=60)

                # 4. Delivery
                logger.info("Delivering report...", "INFO")
                now = datetime.now()
                content = format_legacy_report(
                    data, ai, risk, narrative_text, now=now, standard_payload=standard_payload
                )
                self._print_report(content)

                if not self.dry_run:
                    self._send_push_notifications(content, now)

                # 5. Review Persistence
                logger.info("Persisting daily run for review...", "INFO")
                if standard_payload:
                    save_daily_run(self.db_path, data, standard_payload)

            logger.info("Pipeline completed successfully.", "INFO")
        except Exception as e:
            logger.info(f"Pipeline failed: {e}", "ERROR")
            raise

    def _build_narrative_context(self, data: Dict) -> str:
        try:
            zt_emotion = data.get('zt_emotion') or {}
            fg_history = self.repository.get_fg_history(20)
            narrative_data = fetch_news_sentiment(zt_emotion)
            concepts_data = fetch_hot_concepts()
            narrative_data['sentiment_state'] = classify_sentiment_state(narrative_data, concepts_data)
            fg_data = calculate_fear_greed(narrative_data, concepts_data, fg_history)
            
            # Trend/momentum must include today's score
            fg_history_with_today = list(fg_history or []) + [(datetime.now().strftime("%Y-%m-%d"), fg_data.get('score', 50))]
            fg_data = calculate_fear_greed(narrative_data, concepts_data, fg_history_with_today)
            fg_interp = interpret_narrative(fg_data, narrative_data, concepts_data, fg_history_with_today)
            fg_data['interp'] = fg_interp
            
            save_narrative_data(narrative_data, concepts_data, fg_data, fg_interp)
            
            if isinstance(zt_emotion, dict):
                zt_emotion.setdefault('fear_greed_score', fg_data.get('score'))
            top_concepts = _normalize_top_concepts(concepts_data, limit=10)
            if top_concepts:
                zt_emotion.setdefault('top_concepts', top_concepts)
            data['zt_emotion'] = zt_emotion
            
            narrative_text = get_narrative_summary()
            logger.info(f"[Narrative] {narrative_text[:80]}", "INFO")
            return narrative_text
        except Exception as e:
            logger.info(f"[Narrative] Failed: {e}", "ERROR")
            return ""

    def _build_standard_payload(self, data: Dict, narrative_text: str) -> Optional[Dict]:
        try:
            return build_and_persist_standard_decision(
                data,
                narrative_text,
                data_dir=os.path.dirname(self.db_path),
                lineage=data.get('metadata', {}).get('lineage', {}),
                repository=self.repository,
                log=self.log,
                run_timestamp=data.get("run_timestamp"),
            )
        except Exception as e:
            logger.info(f"[StandardOutput] Failed: {e}", "ERROR")
            return None

    def _print_report(self, content: str) -> None:
        print(content)
        print("-" * 50)

    def _send_push_notifications(self, content: str, now: datetime) -> None:
        title = f"📊 每日宏观简报 {now.strftime('%m/%d %H:%M')}"
        logger.info(f"Pushing notification: {title}", "INFO")


def create_orchestrator(dry_run: bool = False) -> MacroOrchestrator:
    """Factory function to create an orchestrator with production config."""
    config = load_config()
    return MacroOrchestrator(config, dry_run=dry_run)
