import os
import shutil
import shared

def setup():
  f = os.listdir("./defaults")
  for d in os.listdir("./defaults/DEF"):
    if d not in f:
      if not d.startswith("!"):
        shutil.copyfile(f"./defaults/DEF/{d}", f"./defaults/{d}")

# codex
if __name__ == "__main__":
  try:
    setup()
    print("Setup completed successfully.")
  except Exception as e:
    print(f"An error occurred during setup: {e}")
    exit(1)

  # Optionally, you can run a command after setup
  # subprocess.run(["python", "webui.py"])  # Uncomment to run webui.py after setup