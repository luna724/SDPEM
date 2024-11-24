from tkinter import Tk, filedialog

def browse_file():
  root = Tk()
  root.attributes("-topmost", True)
  root.withdraw()

  filenames = filedialog.askopenfile()
  if filenames is not None:
    return filenames
  else:
    filename = "Please select file."
    root.destroy()
    return str(filename)