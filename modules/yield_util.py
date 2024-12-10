class yielding_util:
    def __init__(self, header: str = "", session_max: int = 12):
        self.header = header
        self.session_message = ""
        self.max_line = session_max

    def __call__(self, *args: str, end="\n"):
        text = self.header + "".join(args)
        print(text)

        self.session_message += text + end
        while len(self.session_message.split("\n")) > self.max_line:
            self.session_message = "\n".join(self.session_message.split("\n")[1:])

        return self.session_message

    def clear(self):
        self.session_message = ""

def new_yield(header: str = "", max_line: int = 12) -> yielding_util:
    return yielding_util(header, max_line)