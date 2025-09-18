import re

def separate_prompt(prompt: str) -> list[str]:
    return [
        x.strip() 
        for x in prompt.split(",")
    ]

def combine_prompt(prompt: list[str]) -> str:
    return ", ".join(prompt)

def disweight(piece: str) -> tuple[str, float]:
    match = re.match(
        r"^\(?\s*(.+)\s*:(-?\d*\.?\d+|\-?\.\d+)\s*\)?$", piece.strip(),
        re.IGNORECASE
    )
    if match:
        return match.group(1).strip(), float(match.group(2))
    else:
        match = re.match(
            r"^\(?\s*(.+)\s*:(lbw|stop|start)\s*=?\s*[\w\.\-\d]+\s*\)?$", piece.strip(), re.IGNORECASE
        ) # TODO: prompt:lbw=INALL:stop=24 -> prompt:lbw=INALL になるのを直す
        if match:
            return match.group(1).strip(), float("-inf")
    return piece.strip(), 1.0
