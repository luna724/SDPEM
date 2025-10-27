import random
import traceback
from modules.prompt_setting import setting
from modules.prompt_placeholder import placeholder
from modules.utils.character import waic
from modules.utils.lora_util import find_lora, get_tag_freq_from_lora, read_lora_name, is_lora_trigger
from modules.utils.prompt import Prompt, separate_prompt, combine_prompt

from logger import debug, warn

class PromptProcessor:
    @classmethod
    async def single_proc(cls, p: str, proc_kw: dict = {}) -> bool:
        i = cls(p)
        return len(await i.process(**proc_kw)) > 0
    
    @classmethod
    async def will_be_filtered(cls, tag: str, proc_kw: dict = {}) -> bool:
        i = cls(tag)
        res = await i.process(**proc_kw)
        debug(f"[LoraPrompt] will_be_filtered: {tag} -> {res} ({len(res)})")
        return len(res) == 0

    def __init__(self, prompt: str):
        self.prompt = Prompt(prompt)
        self.filtered = 0
        self.filtered_tags: list[str] = []
        
    def proc_blacklist(self) -> Prompt:
        blacklist = setting.obtain_blacklist()
        keep_map: dict[int, bool] = {}
        for piece in list(self.prompt):
            disweighted = piece.text
            # debug(f"[Blacklist] Checking tag: {piece.value} ({disweighted})")
            if is_lora_trigger(piece):
                debug(f"[Blacklist] Skipping LoRA trigger tag: {piece.value}")
                continue
            matched = False
            for pattern in blacklist:
                match = pattern.search(disweighted)
                if match:
                    debug(f"[Blacklist] Filtered tag: {piece.value} ({pattern.pattern})")
                    self.filtered += 1
                    self.filtered_tags.append(piece.value)
                    matched = True
                    break
            keep_map[id(piece)] = not matched

        self.prompt.filter_inplace(lambda item: keep_map.get(id(item), True))
        return self.prompt
    
    async def proc_placeholder(self) -> Prompt:
        result = await placeholder.process_prompt(self.prompt)
        if isinstance(result, Prompt):
            return result
        return Prompt(result)
    
    async def remove_character(self) -> Prompt:
        return await waic.remove_character(self.prompt)
    
    async def process(
        self,
        do_blacklist: bool = True, do_placeholder: bool = True,
        remove_character: bool = False,
        restore_placeholder_test: None = None,
    ) -> list[str]:
        if do_placeholder:
            self.prompt = await self.proc_placeholder()
        if do_blacklist:
            self.prompt = self.proc_blacklist()
            self.prompt.refill_placeholder_entries()

        self.prompt.filter_inplace(lambda piece: len(piece.value.strip()) > 0)
        if remove_character:
            self.prompt = await self.remove_character()
        return self.prompt.as_list()
    
    @staticmethod
    async def test_from_lora_rnd_prompt_available(
        test_prompt: bool = True,
        kw_p: dict = None,
        kw: dict = None
    ) -> bool:
        if kw_p is None:
            kw_p = {}
        if kw is None:
            kw = {}
        try:
            c = await PromptProcessor.gather_from_lora_rnd_prompt(**kw)
            if test_prompt:
                return len(c) > 0
        
            return True
        except Exception as e:
            traceback.print_exc()
            debug(f"[LoraPrompt] test_from_lora_rnd_prompt_available failed: {e}")
            return False
    
    @classmethod
    async def gather_from_lora_rnd_prompt(
        cls, lora_name: list[str], header: str, footer: str,
        tags: int, random_rate: float, add_lora_name: bool,
        lora_weight: str, 
        weight_multiplier: float,
        weight_multiplier_target_min: float,
        weight_multiplier_target_max: float,
        prompt_weight_chance: float,
        prompt_weight_min: float, prompt_weight_max: float,
        disallow_duplicate: bool,
        proc_kw: dict = {"remove_character": True},
        max_tries: int = 50000,
        **kw
    ) -> list[str]:
        """
        raise: ValueError tagがない場合
        raise: ValueError いくつかの数値がだめな場合
        raise: RuntimeError 50000回思考してもできなかった場合
        """
        if random_rate <= 0: raise ValueError("random_rate must be greater than 0")
        if tags <= 0: raise ValueError("tags must be greater than 0")
        if prompt_weight_min > prompt_weight_max:
            warn("prompt_weight_min is greater than prompt_weight_max, casting into equal")
            prompt_weight_min = prompt_weight_max
        if prompt_weight_chance < 0 or prompt_weight_chance > 1:
            prompt_weight_chance = max(0, min(1, prompt_weight_chance))
        
        fq = {}
        tried = 0
        for ln in lora_name:
            lora = await find_lora(ln, allow_none=True)
            if lora:
                n1, n2 = await get_tag_freq_from_lora(lora)
                fq.update(n1 | n2)
                debug(f"[Lora] Gathered tags from {ln}: {fq}")
        if len(fq) < 1: raise ValueError("No tags found in the provided LoRA(s)")
        
        res = await cls.from_frequency_like(
            fq,
            weight_multiplier,
            weight_multiplier_target_min,
            weight_multiplier_target_max,
            random_rate,
            tags, disallow_duplicate,
            prompt_weight_chance,
            prompt_weight_min, prompt_weight_max,
            max_tries=max_tries,
            proc_kw=proc_kw,
        )
        
        p = combine_prompt(res)
        if add_lora_name:
            for name in lora_name:
                n = await read_lora_name(name, allow_none=True)
                if n:
                    p = p.rstrip(", ") + f", <lora:{n}:{str(lora_weight)}>"
        c = cls(p)
        main = await c.process(**proc_kw)
        return separate_prompt(header) + main + separate_prompt(footer)
    
    @classmethod
    async def from_frequency_like(
        cls, 
        fq: dict[str, float],
        weight_multiplier: float,
        weight_multiplier_target_min: float,
        weight_multiplier_target_max: float,
        random_rate: float,
        tags: int, disallow_duplicate: bool,
        prompt_weight_chance: float,
        prompt_weight_min: float, prompt_weight_max: float,
        max_tries: int = 500000,
        proc_kw: dict = {"remove_character": True},
        finalize = False,
        header: str = "", footer: str = "",
        **kw
    ) -> list[str]:
        tried = 0
        rt = []
        for t, w in fq.items():
            mt = 1
            
            if weight_multiplier_target_min <= w <= weight_multiplier_target_max:
                mt *= weight_multiplier
            weight = (w * mt) / (100*random_rate)
            if weight > 0:
                if await cls.will_be_filtered(t, proc_kw=proc_kw):
                    debug(f"[FrequencyLike] Filtered tag from Lora: {t} ({weight})")
                    continue
                rt.append((t, weight))
            
            tried += 1
            if tried > max_tries:
                raise RuntimeError(f"Tried too many times ({max_tries}) to gather tags, aborting")
        rt = sorted(rt, key=lambda x: x[1])
        if len(rt) < tags and disallow_duplicate:
            raise ValueError(f"Not enough filtered tags found ({len(rt)} found, {tags} required)")
        
        tried = 0
        proc = True
        prompts = []
        while proc:
            prompts = []
            while len(prompts) < tags:
                for (tag, weight) in rt:
                    if len(prompts) >= tags:
                        break
                    if random.random() < weight:
                        if disallow_duplicate and tag in prompts:
                            continue
                        if random.random() < prompt_weight_chance:
                            tag = f"({tag}:{random.uniform(prompt_weight_min, prompt_weight_max):.2f})"
                        prompts.append(tag)
                    tried += 1
                    if tried > max_tries*2:
                        raise RuntimeError(f"Tried too many times to gather tags ({max_tries*2}), aborting")
            res = await cls(combine_prompt(prompts)).process(**proc_kw)
            if len(res) != tags:
                debug(f"[FrequencyLike] Re-gathering tags, got {len(res)} tags, expected {tags}")
                prompts.clear()
            else:
                proc = True
                break
        if not finalize:
            return res
        p = combine_prompt(res)
        c = cls(p)
        main = await c.process(**proc_kw)
        return separate_prompt(header.rstrip(",")) + main + separate_prompt(footer.rstrip(","))