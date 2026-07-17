import os
import re
import time
import uuid
import json
from pydantic import BaseModel, ConfigDict
from typing import Optional, Any

from modules.events.generation_ended import OnGenerationEndedEvent, onGenerationEnded


class MismatchData(BaseModel):
  """入力にはあるが出力にないLostと、入力にないが出力で強く検出されたGhost"""
  model_config = ConfigDict(populate_by_name=True)
  Lost: list[str]
  Ghost: list[str]
  lost: Optional[list[str]] = None
  ghost: Optional[list[str]] = None


class GenerationLogRecord(BaseModel):
  """1回の生成ごとに作成される生成ログのレコード構造"""
  model_config = ConfigDict(populate_by_name=True)
  id: str
  timestamp: float
  user_action: str
  prompt_tags: list[str]
  inferred_tags: dict[str, float]
  mismatch_data: dict[str, list[str]]
  info_text: str
  param: str


class TagStatsMaster(BaseModel):
  """全ログから集計・更新されるタグごとの成績表（IOベース管理）"""
  model_config = ConfigDict(populate_by_name=True)
  tag_name: str
  usage_count: int = 0
  detection_rate: float = 0.0
  keep_rate: float = 0.0
  co_occurrence: dict[str, int] = {}
  conflicts: list[str] = []
  detection_count: int = 0
  keep_count: int = 0
  co_detected: dict[str, int] = {}


class OutputLogger:
  """今後の機能のための出力保存機構の統合管理クラス"""

  @classmethod
  def get_logs_dir(cls) -> str:
    """ログルートディレクトリ (/logs) を取得または作成"""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    logs_dir = os.path.join(base_dir, "logs")
    if not os.path.exists(logs_dir):
      os.makedirs(logs_dir, exist_ok=True)
    return logs_dir

  @classmethod
  def sanitize_tag_name(cls, tag_name: str) -> str:
    """特殊文字を全角疑問符に置換してファイル名を正規化"""
    return re.sub(r'[\\/:*?"<>|\x00-\x1f]', "？", tag_name)

  @classmethod
  def get_tag_stats_path(cls, tag_name: str) -> str:
    """タグマスタJSONファイルのパスを取得"""
    stats_dir = os.path.join(cls.get_logs_dir(), "tag_stats")
    if not os.path.exists(stats_dir):
      os.makedirs(stats_dir, exist_ok=True)
    safe_name = cls.sanitize_tag_name(tag_name)
    return os.path.join(stats_dir, f"{safe_name}.json")

  @classmethod
  def extract_normalized_tags(cls, event: Optional[OnGenerationEndedEvent] = None, raw_tags: Optional[list[str]] = None) -> list[str]:
    """プロンプトまたはイベントから正規化済みタグリストを生成"""
    targets: list[str] = []
    if raw_tags is not None:
      targets = raw_tags
    elif event is not None and getattr(event, "prompt_score", None) is not None:
      for p in event.prompt_score:
        t_str = getattr(p, "tag", p[0] if isinstance(p, (tuple, list)) and len(p) > 0 else (p.get("tag", "") if isinstance(p, dict) else str(p)))
        if t_str:
          targets.append(t_str)
    elif event is not None:
      info_prompt = event.infotxt or (event.params.get("prompt", "") if isinstance(event.params, dict) else "")
      if info_prompt:
        targets.append(str(info_prompt))

    normalized: list[str] = []
    try:
      from modules.calculator.preprocessing import PreProcessor
      for t in targets:
        norm = PreProcessor.normalize_tag(t)
        if norm is not None:
          if isinstance(norm, list):
            for nt in norm:
              if nt and nt not in normalized:
                normalized.append(nt)
          elif isinstance(norm, str):
            if norm and norm not in normalized:
              normalized.append(norm)
    except Exception:
      for t in targets:
        if isinstance(t, str):
          for pt in t.split(","):
            clean = pt.strip().lower()
            if clean and clean not in normalized:
              normalized.append(clean)
    return normalized

  @classmethod
  def extract_inferred_tags(cls, event: Optional[OnGenerationEndedEvent] = None, raw_inferred: Optional[dict[str, float]] = None) -> dict[str, float]:
    """Tagger検出結果からタグと信頼度スコアを抽出して正規化"""
    inferred: dict[str, float] = {}
    if raw_inferred is not None:
      return {str(k): float(v) for k, v in raw_inferred.items()}
    if event is not None and getattr(event, "booru_out", None) is not None:
      booru = event.booru_out
      scores = (getattr(booru, "tags", []) or []) + (getattr(booru, "characters", []) or [])
      try:
        from modules.calculator.preprocessing import PreProcessor
        for s in scores:
          t_str = getattr(s, "tag", s[0] if isinstance(s, (tuple, list)) and len(s) > 0 else (s.get("tag", "") if isinstance(s, dict) else str(s)))
          sc_val = getattr(s, "score", s[1] if isinstance(s, (tuple, list)) and len(s) > 1 else (s.get("score", 0.0) if isinstance(s, dict) else 0.0))
          norm = PreProcessor.normalize_tag(t_str)
          if norm is not None:
            if isinstance(norm, list):
              for nt in norm:
                if nt:
                  inferred[nt] = float(sc_val)
            elif isinstance(norm, str) and norm:
              inferred[norm] = float(sc_val)
          elif t_str:
            inferred[t_str.strip().lower()] = float(sc_val)
      except Exception:
        for s in scores:
          t_str = getattr(s, "tag", s[0] if isinstance(s, (tuple, list)) and len(s) > 0 else (s.get("tag", "") if isinstance(s, dict) else str(s)))
          sc_val = getattr(s, "score", s[1] if isinstance(s, (tuple, list)) and len(s) > 1 else (s.get("score", 0.0) if isinstance(s, dict) else 0.0))
          if t_str:
            inferred[t_str.strip().lower()] = float(sc_val)
    return inferred

  @classmethod
  def extract_mismatch_data(cls, event: Optional[OnGenerationEndedEvent] = None, prompt_tags: Optional[list[str]] = None, inferred_tags: Optional[dict[str, float]] = None, raw_mismatch: Optional[dict[str, list[str]]] = None) -> dict[str, list[str]]:
    """LostとGhostのミスマッチデータを計算または抽出"""
    lost_list: list[str] = []
    ghost_list: list[str] = []
    if raw_mismatch is not None and isinstance(raw_mismatch, dict):
      lost_list = raw_mismatch.get("Lost", raw_mismatch.get("lost", [])) or []
      ghost_list = raw_mismatch.get("Ghost", raw_mismatch.get("ghost", [])) or []
      return {
        "Lost": lost_list,
        "Ghost": ghost_list,
        "lost": lost_list,
        "ghost": ghost_list,
      }

    if event is not None and getattr(event, "lost_tags", None) is not None:
      for p in event.lost_tags:
        t_str = getattr(p, "tag", p[0] if isinstance(p, (tuple, list)) and len(p) > 0 else (p.get("tag", "") if isinstance(p, dict) else str(p)))
        if t_str and t_str not in lost_list:
          lost_list.append(t_str)
    else:
      threshold = 0.5
      if event is not None and getattr(event, "booru_out", None) is not None:
        threshold = getattr(event.booru_out, "threshold", 0.5) or 0.5
      for t in (prompt_tags or []):
        if t not in (inferred_tags or {}) or (inferred_tags or {}).get(t, 0.0) < threshold:
          if t not in lost_list:
            lost_list.append(t)

    if event is not None and getattr(event, "ghost_tags", None) is not None:
      for p in event.ghost_tags:
        t_str = getattr(p, "tag", p[0] if isinstance(p, (tuple, list)) and len(p) > 0 else (p.get("tag", "") if isinstance(p, dict) else str(p)))
        if t_str and t_str not in ghost_list:
          ghost_list.append(t_str)
    else:
      threshold = 0.5
      if event is not None and getattr(event, "booru_out", None) is not None:
        threshold = getattr(event.booru_out, "threshold", 0.5) or 0.5
      input_set = set(prompt_tags or [])
      for t, sc in (inferred_tags or {}).items():
        if sc >= threshold and t not in input_set:
          if t not in ghost_list:
            ghost_list.append(t)

    return {
      "Lost": lost_list,
      "Ghost": ghost_list,
      "lost": lost_list,
      "ghost": ghost_list,
    }

  @classmethod
  def create_generation_record(
    cls,
    event: Optional[OnGenerationEndedEvent] = None,
    id: Optional[str] = None,
    timestamp: Optional[float | int] = None,
    user_action: Optional[str] = None,
    prompt_tags: Optional[list[str]] = None,
    inferred_tags: Optional[dict[str, float]] = None,
    mismatch_data: Optional[dict[str, list[str]]] = None,
    info_text: Optional[str] = None,
    param: Optional[str] = None,
  ) -> GenerationLogRecord:
    """生成ログのPydanticモデルを作成して返す"""
    record_id = id or (str(event.luuid) if event and getattr(event, "luuid", None) else uuid.uuid4().hex)
    record_ts = float(timestamp if timestamp is not None else (event.ts if event and getattr(event, "ts", None) is not None else time.time()))

    if user_action is not None:
      record_action = user_action
    else:
      # TODO(#0): User Action field is placeholder as Keep for user evaluation / Discard for skip flag
      end_type = getattr(event, "end_type", "complete") if event else "complete"
      rate_val = getattr(event, "rate", "undefined") if event else "undefined"
      if end_type in ("interrupt", "booru_interrupt") or rate_val in ("bad", "worst"):
        record_action = "Discard"
      else:
        record_action = "Keep"

    norm_prompt_tags = prompt_tags if prompt_tags is not None else cls.extract_normalized_tags(event)
    norm_inferred_tags = inferred_tags if inferred_tags is not None else cls.extract_inferred_tags(event)
    calc_mismatch = mismatch_data if mismatch_data is not None else cls.extract_mismatch_data(event, norm_prompt_tags, norm_inferred_tags)
    record_info = info_text if info_text is not None else (getattr(event, "infotxt", "") if event else "")

    if param is not None:
      record_param = param
    elif event is not None:
      raw_param = getattr(event, "pem_params", None) or getattr(event, "params", None) or {}
      record_param = raw_param if isinstance(raw_param, str) else json.dumps(raw_param, ensure_ascii=False)
    else:
      record_param = "{}"

    return GenerationLogRecord(
      id=record_id,
      timestamp=record_ts,
      user_action=record_action,
      prompt_tags=norm_prompt_tags,
      inferred_tags=norm_inferred_tags,
      mismatch_data=calc_mismatch,
      info_text=record_info,
      param=record_param,
    )

  @classmethod
  def save_generation_record(cls, record: GenerationLogRecord) -> None:
    """生成ログを /logs/generation_records.jsonl に保存"""
    logs_dir = cls.get_logs_dir()
    jsonl_path = os.path.join(logs_dir, "generation_records.jsonl")
    data_dict = record.model_dump() if hasattr(record, "model_dump") else record.dict()
    os.makedirs(os.path.dirname(jsonl_path), exist_ok=True)
    if not os.path.exists(jsonl_path):
      with open(jsonl_path, "w", encoding="utf-8") as f:
        pass
    try:
      from modules.utils import jsonl
      jsonl.append(data_dict, jsonl_path, ensure_ascii=False, encoding="utf-8")
    except Exception:
      with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data_dict, ensure_ascii=False) + "\n")

  @classmethod
  def update_tag_stats(cls, record: GenerationLogRecord) -> None:
    """IOベースで全ログ結果からタグ統計マスタを集計・更新し保存"""
    lost_set = set(record.mismatch_data.get("Lost", record.mismatch_data.get("lost", [])) or [])
    prompt_set = set(record.prompt_tags)

    for tag in prompt_set:
      fp = cls.get_tag_stats_path(tag)
      stats: Optional[TagStatsMaster] = None
      if os.path.exists(fp):
        try:
          with open(fp, "r", encoding="utf-8") as f:
            stats = TagStatsMaster(**json.load(f))
        except Exception:
          stats = None
      if stats is None:
        stats = TagStatsMaster(tag_name=tag)

      stats.usage_count += 1
      is_detected = (tag in record.inferred_tags) and (tag not in lost_set)
      if is_detected:
        stats.detection_count += 1
      if record.user_action == "Keep":
        stats.keep_count += 1

      stats.detection_rate = round((stats.detection_count / stats.usage_count) * 100.0, 2)
      stats.keep_rate = round((stats.keep_count / stats.usage_count) * 100.0, 2)

      for other_tag in prompt_set:
        if other_tag != tag:
          stats.co_occurrence[other_tag] = stats.co_occurrence.get(other_tag, 0) + 1
          if is_detected:
            stats.co_detected[other_tag] = stats.co_detected.get(other_tag, 0) + 1

      sorted_co = dict(sorted(stats.co_occurrence.items(), key=lambda item: item[1], reverse=True)[:100])
      stats.co_occurrence = sorted_co
      stats.co_detected = {k: v for k, v in stats.co_detected.items() if k in stats.co_occurrence}

      conflicts: list[str] = []
      for co_tag, co_count in stats.co_occurrence.items():
        co_det_rate = (stats.co_detected.get(co_tag, 0) / co_count) * 100.0
        if co_count >= 2 and co_det_rate < stats.detection_rate:
          conflicts.append(co_tag)
      stats.conflicts = conflicts

      try:
        data_dump = stats.model_dump() if hasattr(stats, "model_dump") else stats.dict()
        with open(fp, "w", encoding="utf-8") as f:
          json.dump(data_dump, f, ensure_ascii=False, indent=2)
      except Exception:
        pass

    for inferred_tag in record.inferred_tags.keys():
      if inferred_tag not in prompt_set:
        fp = cls.get_tag_stats_path(inferred_tag)
        if not os.path.exists(fp):
          stats = TagStatsMaster(tag_name=inferred_tag)
          try:
            data_dump = stats.model_dump() if hasattr(stats, "model_dump") else stats.dict()
            with open(fp, "w", encoding="utf-8") as f:
              json.dump(data_dump, f, ensure_ascii=False, indent=2)
          except Exception:
            pass

  @classmethod
  async def on_generation_ended(cls, event: OnGenerationEndedEvent) -> None:
    """イベントリスナーから呼び出されるログ保存処理のメインエントリーポイント"""
    cls.process_event(event)

  @classmethod
  def process_event(cls, event: OnGenerationEndedEvent) -> GenerationLogRecord:
    """イベントを処理してレコードを作成し、AおよびBを更新・保存して返す"""
    record = cls.create_generation_record(event)
    cls.save_generation_record(record)
    cls.update_tag_stats(record)
    return record


from modules.event import Callback
onGenerationEnded.put_callback(Callback(OutputLogger.on_generation_ended))
