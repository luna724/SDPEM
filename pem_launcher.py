import argparse
from typing import *
import shared
import lunapy_module_importer


def argparser() -> Tuple[argparse.Namespace, List[str]]:
  parser = argparse.ArgumentParser("lunapy_sdpem")
  
  parser.add_argument("--pem-ui_ip", type=str, help="ui's IP", default=None)
  parser.add_argument("--pem-ui_port", type=int, help="ui's port", default=None)
  parser.add_argument("--testui", action="store_true", default=False)
  parser.add_argument("--test_mode", type=str, default="ce")
  
  return parser.parse_known_args()

def launch():
  shared.args, unknown_args = argparser()
  for a in unknown_args:
    print(f"[PEM]: Got unknown argument: {a}")
  lunapy_module_importer.Importer = lunapy_module_importer.moduleImporter("pem")

  if shared.args.testui:
    import test_mode
    test_mode.main(shared.args.test_mode)
  
  import webui
  webui.launch("pem")()

if __name__  == "__main__":
  launch()