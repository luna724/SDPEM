from typing import Literal, Optional, TypedDict

from logger import debug

class BooruRating(TypedDict):
  general: float
  sensitive: float
  questionable: float
  explicit: float

def get_rating(
  rating: BooruRating,
  ignore_questionable: bool = False,
) -> tuple[Literal["general", "sensitive", "questionable", "explicit", "?"], float, Optional[tuple[str, float]]]:
  rate = max(rating, key=rating.get, default="?")
  if rate == "?":
    return rate, rating.get(rate, 0.0)
  
  if ignore_questionable and rate == "questionable":
    r = rating.copy()
    qt = r.pop("questionable")
    rate, thres, _ = get_rating(r, False)
    debug(f"Ignored questionable rating: (questionable({qt}) -> {rate}({thres}))")
    return rate, thres, ("questionable", qt)
  
  return rate, rating.get(rate, 0.0), None

