import re
from copy import deepcopy
from typing import Any, Callable, Iterable, Iterator, Optional, Sequence, Union

### DEPRECATED ###
def separate_prompt(prompt: str) -> list[str]:
    return [
        x.strip() 
        for x in prompt.split(",")
    ]

def combine_prompt(*prompts: list[str]) -> str:
    prompt = []
    for p in prompts:
        prompt.extend(p)
    return ", ".join(prompt)

_SPECIAL_WEIGHT_PREFIXES = ("lbw", "stop", "start")


def _normalize_piece(piece: str) -> str:
    return str(piece).strip()


def _split_prompt_piece(piece: str) -> dict[str, Union[str, bool, None]]:
    original = _normalize_piece(piece)
    has_colon = ":" in original
    prefix = ""
    suffix = ""
    inner = original

    if has_colon:
        while inner.startswith("(") and inner.endswith(")") and len(inner) > 1:
            candidate = inner[1:-1].strip()
            if ":" not in candidate:
                break
            prefix += "("
            suffix = ")" + suffix
            inner = candidate

    base, sep, weight_token = inner.rpartition(":")
    if sep == "":
        return {
            "prefix": "",
            "text": original,
            "weight": None,
            "suffix": "",
            "explicit": False,
        }

    text = base.strip()
    weight = weight_token.strip()
    return {
        "prefix": prefix,
        "text": text,
        "weight": weight,
        "suffix": suffix,
        "explicit": True,
    }


def _weight_token_to_float(token: Optional[str]) -> float:
    if token is None:
        return 1.0
    lowered = token.lower()
    if any(lowered.startswith(prefix) for prefix in _SPECIAL_WEIGHT_PREFIXES):
        return float("-inf")
    try:
        return float(lowered)
    except ValueError:
        return 1.0


def _compose_prompt_piece(components: dict[str, Union[str, bool, None]]) -> str:
    text = components.get("text", "") or ""
    weight = components.get("weight")
    prefix = components.get("prefix", "") or ""
    suffix = components.get("suffix", "") or ""

    body = text
    if weight:
        body = f"{body}:{weight}"
    return f"{prefix}{body}{suffix}"


def disweight(piece: str) -> tuple[str, float]:
    components = _split_prompt_piece(piece)
    text = components.get("text", "") or ""
    weight_val = _weight_token_to_float(components.get("weight"))
    return text, weight_val
###################

class PromptPiece:
    __slots__ = (
        "raw",
        "_current",
        "_history",
        "_snapshots",
        "_components",
        "_raw_components",
        "_weight",
        "_raw_weight",
        "position",
        "_meta",
    )

    def __init__(self, piece: str):
        piece_str = str(piece)
        self.raw = piece_str
        self._current = piece_str
        self._history: list[tuple[Optional[str], str]] = []
        self._snapshots: dict[str, tuple[str, int]] = {}
        self._components = _split_prompt_piece(piece_str)
        self._raw_components = dict(self._components)
        self._weight = _weight_token_to_float(self._components.get("weight"))
        self._raw_weight = self._weight
        self.position: Optional[int] = None
        self._meta: dict[str, Any] = {}

    def __str__(self) -> str:
        return self._current

    def __repr__(self) -> str:
        return f"PromptPiece(current={self._current!r})"

    def __len__(self) -> int:
        return len(self._current)

    def __getattr__(self, name: str):
        return getattr(self._current, name)

    @property
    def value(self) -> str:
        return self._current

    @property
    def text(self) -> str:
        return self._components.get("text", "") or ""

    @property
    def has_weight(self) -> bool:
        return bool(self._components.get("explicit")) and self._components.get("weight") is not None

    @property
    def weight_token(self) -> Optional[str]:
        return self._components.get("weight")  # type: ignore[return-value]

    @property
    def weight(self) -> float:
        return self._weight

    @property
    def original_weight(self) -> float:
        return self._raw_weight

    def is_modified(self) -> bool:
        return self._current != self.raw

    def _refresh_state(self) -> None:
        self._components = _split_prompt_piece(self._current)
        self._weight = _weight_token_to_float(self._components.get("weight"))

    def set(self, value: str, *, source: Optional[str] = None, allow_duplicate: bool = False) -> str:
        value = str(value)
        if not allow_duplicate and value == self._current:
            return self._current
        self._history.append((source, self._current))
        self._current = value
        self._refresh_state()
        return self._current

    def replace(self, old: str, new: str, count: int = -1, *, source: Optional[str] = None) -> str:
        current = self._current
        updated = current.replace(old, new, count)
        if updated != current:
            self._history.append((source, current))
            self._current = updated
            self._refresh_state()
        return self._current

    def revert(self, *, to_raw: bool = False) -> str:
        if to_raw:
            self._current = self.raw
            self._history.clear()
            self._snapshots.clear()
            self._components = dict(self._raw_components)
            self._weight = self._raw_weight
            return self._current
        if self._history:
            _, previous = self._history.pop()
            self._current = previous
            self._refresh_state()
        return self._current

    def snapshot(self, label: str) -> None:
        self._snapshots[label] = (self._current, len(self._history))

    def restore(self, label: str, *, discard: bool = True) -> bool:
        snapshot = self._snapshots.get(label)
        if snapshot is None:
            return False
        text, history_len = snapshot
        self._current = text
        while len(self._history) > history_len:
            self._history.pop()
        if discard:
            self._snapshots.pop(label, None)
        self._refresh_state()
        return True

    def changed_since(self, label: str) -> bool:
        snapshot = self._snapshots.get(label)
        if snapshot is None:
            return True
        text, history_len = snapshot
        return self._current != text or len(self._history) != history_len

    def forget_snapshot(self, label: str) -> None:
        self._snapshots.pop(label, None)

    def history(self) -> list[tuple[Optional[str], str]]:
        return list(self._history)

    def set_text(self, text: str, *, source: Optional[str] = None) -> str:
        sanitized = text.strip()
        if sanitized == self._components.get("text"):
            return self._current
        new_components = dict(self._components)
        new_components["text"] = sanitized
        self._history.append((source, self._current))
        self._current = _compose_prompt_piece(new_components)
        self._refresh_state()
        return self._current

    def set_weight(self, weight: Union[float, str], *, source: Optional[str] = None) -> str:
        if isinstance(weight, str):
            weight_token = weight.strip()
            weight_value = _weight_token_to_float(weight_token)
        else:
            weight_value = float(weight)
            weight_token = f"{weight_value:g}"

        if self._components.get("weight") == weight_token:
            return self._current

        new_components = dict(self._components)
        new_components["weight"] = weight_token
        new_components["explicit"] = True
        self._history.append((source, self._current))
        self._current = _compose_prompt_piece(new_components)
        self._refresh_state()
        self._weight = weight_value
        return self._current

    def remove_weight(self, *, source: Optional[str] = None) -> str:
        if not self.has_weight:
            return self._current
        new_components = dict(self._components)
        new_components["weight"] = None
        new_components["explicit"] = False
        self._history.append((source, self._current))
        self._current = _compose_prompt_piece(new_components)
        self._refresh_state()
        return self._current

    def restore_weight(self, *, source: Optional[str] = None) -> str:
        original_weight_token = self._raw_components.get("weight")
        current_weight_token = self._components.get("weight")
        if original_weight_token == current_weight_token:
            return self._current
        if original_weight_token is None:
            return self.remove_weight(source=source)

        new_components = dict(self._components)
        new_components["weight"] = original_weight_token
        new_components["explicit"] = True
        self._history.append((source, self._current))
        self._current = _compose_prompt_piece(new_components)
        self._refresh_state()
        return self._current

    def clone(self) -> "PromptPiece":
        cloned = PromptPiece(self.raw)
        cloned._current = self._current
        cloned._components = dict(self._components)
        cloned._raw_components = dict(self._raw_components)
        cloned._weight = self._weight
        cloned._raw_weight = self._raw_weight
        cloned.position = self.position
        cloned._meta = deepcopy(self._meta)
        return cloned

    def set_meta(self, key: str, value: Any) -> None:
        self._meta[key] = value

    def get_meta(self, key: str, default: Any = None) -> Any:
        return self._meta.get(key, default)

    def ensure_meta(self, key: str, default: Any) -> Any:
        return self._meta.setdefault(key, default)

    def pop_meta(self, key: str, default: Any = None) -> Any:
        return self._meta.pop(key, default)

    def clear_meta(self) -> None:
        self._meta.clear()
    
class Prompt:
    __slots__ = ("raw", "_pieces")

    def __init__(self, prompt: Union[str, Sequence[Union[str, PromptPiece]], "Prompt"]):
        if isinstance(prompt, Prompt):
            self.raw = prompt.raw
            self._pieces = [piece.clone() for piece in prompt._pieces]
        elif isinstance(prompt, str):
            self.raw = prompt
            parts = [p for p in separate_prompt(prompt) if p]
            self._pieces = [PromptPiece(p) for p in parts]
        elif isinstance(prompt, Sequence):
            self._pieces = []
            for item in prompt:
                if isinstance(item, PromptPiece):
                    self._pieces.append(item.clone())
                else:
                    self._pieces.append(PromptPiece(str(item)))
            self.raw = combine_prompt([str(piece) for piece in self._pieces])
        else:
            raise TypeError("prompt must be a string, a sequence of pieces, or a Prompt instance")

        self._bind_positions()

    def _bind_positions(self) -> None:
        for index, piece in enumerate(self._pieces):
            piece.position = index

    def __iter__(self) -> Iterator[PromptPiece]:
        return iter(self._pieces)

    def __len__(self) -> int:
        return len(self._pieces)

    def __getitem__(self, index: int) -> PromptPiece:
        return self._pieces[index]

    def __str__(self) -> str:
        return self.combine()

    def __repr__(self) -> str:
        return f"Prompt(pieces={self.as_list()!r})"

    def pieces(self) -> list[PromptPiece]:
        return list(self._pieces)

    def as_list(self) -> list[str]:
        return [str(piece) for piece in self._pieces]

    def combine(self) -> str:
        return combine_prompt(self.as_list())

    def append(self, piece: Union[str, PromptPiece]) -> PromptPiece:
        new_piece = piece.clone() if isinstance(piece, PromptPiece) else PromptPiece(str(piece))
        new_piece.position = len(self._pieces)
        self._pieces.append(new_piece)
        return new_piece

    def extend(self, pieces: Iterable[Union[str, PromptPiece]]) -> None:
        for piece in pieces:
            self.append(piece)

    def insert(self, index: int, piece: Union[str, PromptPiece]) -> PromptPiece:
        new_piece = piece.clone() if isinstance(piece, PromptPiece) else PromptPiece(str(piece))
        index = max(0, min(index, len(self._pieces)))
        self._pieces.insert(index, new_piece)
        self._bind_positions()
        return new_piece

    def pop(self, index: int = -1) -> PromptPiece:
        piece = self._pieces.pop(index)
        self._bind_positions()
        return piece

    def remove(self, piece: PromptPiece) -> None:
        self._pieces.remove(piece)
        self._bind_positions()

    def ensure_order(self) -> None:
        self._pieces.sort(key=lambda p: (p.position is None, p.position))
        self._bind_positions()

    def restore_original_weights(self) -> None:
        for piece in self._pieces:
            piece.restore_weight()

    def snapshot(self, label: str) -> None:
        for piece in self._pieces:
            piece.snapshot(f"{label}:{piece.position}")

    def restore(self, label: str, *, discard: bool = True) -> None:
        for piece in self._pieces:
            piece.restore(f"{label}:{piece.position}", discard=discard)

    def forget_snapshot(self, label: str) -> None:
        for piece in self._pieces:
            piece.forget_snapshot(f"{label}:{piece.position}")

    def map(
        self,
        func: Callable[[PromptPiece, int], Union[str, PromptPiece, None]],
        *,
        inplace: bool = True,
    ) -> "Prompt":
        transformed: list[PromptPiece] = []
        for index, piece in enumerate(self._pieces):
            result = func(piece, index)
            if result is None:
                continue
            if isinstance(result, PromptPiece):
                transformed.append(result.clone())
            else:
                piece.set(str(result))
                transformed.append(piece)

        if inplace:
            self._pieces = transformed
            self._bind_positions()
            return self

        cloned = Prompt(transformed)
        cloned._bind_positions()
        return cloned

    def clone(self) -> "Prompt":
        return Prompt(self)

    def filter_inplace(self, predicate: Callable[[PromptPiece], bool]) -> None:
        self._pieces = [piece for piece in self._pieces if predicate(piece)]
        self._bind_positions()

    def refill_placeholder_entries(self) -> None:
        for piece in self._pieces:
            entries = piece.get_meta("placeholder_refill")
            if not entries:
                continue
            remaining = []
            for entry in entries:
                label = entry.get("label")
                key = entry.get("key")
                if not label:
                    continue
                if key and key in piece.value:
                    piece.restore(label)
                    continue
                # Drop stale marker when placeholder output no longer present.
            if remaining:
                piece.set_meta("placeholder_refill", remaining)
            else:
                piece.pop_meta("placeholder_refill", None)
