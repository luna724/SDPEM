import json

class jsoncfg:
  """LGS.misc.jsonconfig.py"""
  @staticmethod
  def read(fp:str="Filepath", encode:str="utf-8") -> dict:
    with open(fp, "r", encoding=encode) as f: return json.load(f)
  
  @staticmethod
  def write(data, fp, encode="utf-8", indent_block=2) -> None:
    with open(fp, "w", encoding=encode) as f: json.dump(data, f, indent=indent_block)
  
  @staticmethod
  def read_text(fp, encode="utf-8") -> str:
    with open(fp, "r", encoding=encode) as f: return f.read()
  
  @staticmethod
  def write_text(data, fp, encode="utf-8", overwrite=True) -> None:
    if overwrite:
      with open(fp, "w", encoding=encode) as f: f.write(data)
    else:
      with open(fp, "a", encoding=encode) as f: f.write(data)

