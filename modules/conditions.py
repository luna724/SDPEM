from typing import Callable
import gradio as gr 


class Condition:
  def __init__(self, name, structure: Callable):
    self.name = name
    self.structure = structure

class Conditions:
  def __init__(self):
    c = {}
    c["percentage"] = Condition("percentage", _percentage)
    
  
  def get_condition_names(self) -> list[str]:
    return list(self.conditions.keys())