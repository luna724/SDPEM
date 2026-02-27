import gradio as gr
def upd(num: int = 1, **kw):
  return gr.update(**kw)

import traceback
from logger import warn

async def range_check(n, x):
  try:
    if n <= x:
      return upd(2)
    else:
      # max < min
      return upd(value=x), upd(value=n)
  except:
    traceback.print_exc()
    warn(f"Invalid range values: {n}, {x}")
    return upd(2)