import argparse
from typing import *

import shared


class ArgParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="parser")

    def add(
            self,
            args: List[str],
            arg_type: Any = bool,
            required: bool = True,
            default: Any = None,
            help: str = ""
    ):
        args = [x.lower() for x in args]
        if isinstance(arg_type, bool) or arg_type == bool:
            self.parser.add_argument(
                *args, action="store_true",
                help=help, default=False
            )
            return

        self.parser.add_argument(
            *args, type=arg_type, default=default,
            required=required, help=help
        )
        return

    def parse(self):
        return self.parser.parse_args()

def parse_args():
    parser = ArgParser()

    # 引数追加
    parser.add(
        ["--noLM", "-nolm"], arg_type=bool
    )
    parser.add(
        ["--no_bert"], arg_type=bool
    )
    parser.add(
        ["--no_fasttext"], arg_type=bool
    )
    parser.add(
        ["--no_gensim"], arg_type=bool
    )
    parser.add(
        ["--no_booru"], arg_type=bool
    )
    parser.add(
        ["--luna_theme"], arg_type=bool
    )
    parser.add(
        ["--half_booru"], arg_type=bool
    )
    parser.add(
        ["--ignore_cuda"], arg_type=bool
    )
    parser.add(
        ["--nojsk"], arg_type=bool
    )
    parser.add(
        ["--nogpt2"], arg_type=bool
    )
    parser.add(
        ["--high_vram"], arg_type=bool
    )
    parser.add(
        ["--cpu"], arg_type=bool
    )

    args = parser.parse()
    shared.args = args