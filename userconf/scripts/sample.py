### Disclaimer ###
# there docs are maybe changed in future versions #

#@Copilot
# Importable builtin modules, requirements.txt modules and all python files in SDPEM/ directory
# e.g.
import os
import modules.utils.jsonl as jsonl
# (not recommended to import from modules/ or webui.py directly to avoid circular imports)

# builtins
import asyncio


print(os.getcwd()) # should be SDPEM root directory

# text: process target prompt (e.g. "$EXAMPLE")
# full: full original prompt (e.g. "1girl, solo, looking at viewer, $EXAMPLE, light smile")
def do(text: str, full: str) -> str: # type-hint is optional
    return text*4 if len(text) < 5 else text

# async is supported
# sample: (func name must be "do")
async def do_async(text: str, full: str) -> str:
    await asyncio.sleep(0.1)
    return text*4 if len(text) < 5 else text

# or NoneType to avoid prompt
# sample: (func name must be "do")
def do_nonetype(text: str, full: str) -> None: 
    # This input prompt will be removed

    # If return empty string, it will appear as ", "
    # return ""
    
    return None

# If an exception is raised, the original prompt will be used
# sample: (func name must be "do")
def do_exception(text: str, full: str) -> str:
    raise Exception("Some error") # The original prompt will be used
    # return text


# If you want to use placeholder
# sample: (func name must be "do")
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from modules.prompt_placeholder import PromptReplaceRule
async def do_with_placeholder(text: str, full: str) -> str:
    ph_i: "PromptReplaceRule" = __get_self() # Do not register in script file (it will be registered automatically)

    # PromptReplaceRule methods are not guaranteed to be constant.
    # Please check if the method exists before using it.
    # Methods pair is accessible by ph_i._func_pairs
    # Do NOT call ph_i.process_prompt() (or called ph_i._func_pairs["process_prompt"]) here to avoid infinite loop.

    fn_pair = ph_i._func_pairs
    remove_rule_fn, is_coro = fn_pair.get["remove_rule"]
    if callable(remove_rule_fn):
        result = remove_rule_fn("Example Replace Rule") # remove rule by name
        
        # use is_coro or inspect.iscoroutinefunction
        if is_coro: result = await result
        
        # It will be make this rule active once per process_prompt call
    return "owo"