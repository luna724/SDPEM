from dataclasses import dataclass
import pandas as pd
import base64
from io import BytesIO
from modules.utils.prompt import Prompt

@dataclass
class PromptScore:
  tag: str
  score: float
  
  def __str__(self):
    return self.tag

class Scores:
  @staticmethod
  def compact(scores: list['PromptScore']) -> str:
    df = pd.DataFrame([{"tag": s.tag, "score": s.score} for s in scores]).sort_values(by="tag")
    buf = BytesIO()
    df.to_parquet(buf, index=False, compression='zstd', engine="pyarrow")
    return base64.b85encode(buf.getvalue()).decode('utf-8')

  @staticmethod
  def expand(compacted: str | bytes) -> list['PromptScore']:
    if isinstance(compacted, str):
      compacted = compacted.encode('utf-8')
    decoded = base64.b85decode(compacted)
    buf = BytesIO(decoded)
    df = pd.read_parquet(buf, engine="pyarrow")
    return [PromptScore(tag=t, score=s) for t, s in zip(df['tag'], df['score'])]

  @staticmethod
  def from_dict(data: dict[str, float]) -> list['PromptScore']:
    return [PromptScore(tag=t, score=float(s)) for t, s in data.items()]


@dataclass
class BooruResult:
  tags: list[PromptScore]
  characters: list[PromptScore]
  rating: list[PromptScore]
  threshold: float


class Booru:
  SEP = "0x1E" 
  
  @staticmethod
  def create(
    tags: dict, characters: dict, rating: dict, threshold: float
  ) -> BooruResult:
    return BooruResult(
      tags=[PromptScore(tag=t, score=float(s)) for t, s in tags.items()],
      characters=[PromptScore(tag=c, score=float(s)) for c, s in characters.items()],
      rating=[PromptScore(tag=r, score=float(s)) for r, s in rating.items()],
      threshold=float(threshold)
    )
  
  @staticmethod
  def compact(booru: BooruResult) -> str:
    data = {
      "tag": [{"tag": t.tag, "score": t.score} for t in booru.tags],
      "c": [{"tag": c.tag, "score": c.score} for c in booru.characters],
      "r": [{"tag": r.tag, "score": r.score} for r in booru.rating],
      "t": int(booru.threshold*100, 16),
    }
    df_tags = pd.DataFrame(data['tag']).sort_values(by="tag")
    df_characters = pd.DataFrame(data['c']).sort_values(by="tag")
    df_rating = pd.DataFrame(data['r']).sort_values(by="tag")
    
    buf = BytesIO()
    encoded = ""
    df_tags.to_parquet(buf, index=False, compression='zstd', engine="pyarrow")
    encoded += base64.b85encode(buf.getvalue()).decode('utf-8') + Booru.SEP
    buf.seek(0)
    buf.truncate(0)
    df_characters.to_parquet(buf, index=False, compression='zstd', engine="pyarrow")
    encoded += base64.b85encode(buf.getvalue()).decode('utf-8') + Booru.SEP
    buf.seek(0)
    buf.truncate(0)
    df_rating.to_parquet(buf, index=False, compression='zstd', engine="pyarrow")
    encoded += base64.b85encode(buf.getvalue()).decode('utf-8') + Booru.SEP
    buf.close()
    encoded += str(data['t'])
    
    return encoded
  
  @staticmethod
  def expand(compacted: str | bytes) -> BooruResult:
    if isinstance(compacted, bytes):
      compacted = compacted.decode('utf-8')
    
    parts = compacted.split(Booru.SEP)
    
    # tags
    decoded_tags = base64.b85decode(parts[0].encode('utf-8'))
    buf_tags = BytesIO(decoded_tags)
    df_tags = pd.read_parquet(buf_tags, engine="pyarrow")
    tags = [PromptScore(tag=t, score=s) for t, s in zip(df_tags['tag'], df_tags['score'])]
    
    # characters
    decoded_chars = base64.b85decode(parts[1].encode('utf-8'))
    buf_chars = BytesIO(decoded_chars)
    df_characters = pd.read_parquet(buf_chars, engine="pyarrow")
    characters = [PromptScore(tag=t, score=s) for t, s in zip(df_characters['tag'], df_characters['score'])]
    
    # rating
    decoded_rating = base64.b85decode(parts[2].encode('utf-8'))
    buf_rating = BytesIO(decoded_rating)
    df_rating = pd.read_parquet(buf_rating, engine="pyarrow")
    rating = [PromptScore(tag=t, score=s) for t, s in zip(df_rating['tag'], df_rating['score'])]
    
    # threshold
    threshold = int(parts[3]) / 100.0
    
    return BooruResult(tags=tags, characters=characters, rating=rating, threshold=threshold)