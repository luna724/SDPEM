import gradio as gr 
# gradio 4.44.1

class PatchedButton(gr.Button):
  def click(self, fn=None, inputs=None, outputs=None, **kwargs):
    if fn is None or inputs is None:
      return super().click(fn=fn, inputs=inputs, outputs=outputs, **kwargs)

    input_list = list(inputs) if isinstance(inputs, (set, list)) else [inputs]

    keyed = []
    unkeyed = []
    for i, comp in enumerate(input_list):
      eid = getattr(comp, "elem_id", None)
      if eid:
        keyed.append((i, eid))
      else:
        unkeyed.append(i)

    def wrapped_fn(*values):
      result = {eid: values[i] for i, eid in keyed}
      if unkeyed:
        result["args"] = [values[i] for i in unkeyed]
      return fn(result)

    return super().click(fn=wrapped_fn, inputs=input_list, outputs=outputs, **kwargs)