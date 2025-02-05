from typing import *

class SDDefault:
    pass

class p:
    """DataObj for SDApiVariables"""

    def __init__(self, value: Any, instance: Any | List[Any], default: Any = None, range: Tuple[float] = None,
                 allow_invalidate: bool = False, dataclass: bool = False):
        """
        :param instance: その値が受け取るタイプ(またはそのリスト)を受け取る
        :param default: その値のデフォルト値
        :param range: その値が受け取れる範囲を示す (min, max)
        :param allow_invalidate: その値が型チェックに失敗したとしても、それを許可する(エラーとして扱わない)
        :param dataclass: 値はあくまで形を合わせるためにクラスに登録されていて、追加処理や安全処理を一切行わない
        """
        if not dataclass:
            allowed_instance = []
            if not isinstance(instance, list):
                allowed_instance.append(instance)
            else:
                for i in instance:
                    if isinstance(i, type): allowed_instance.append(i)

            allow_value = [False, False]  # instance, is Falsy(except boolean), range
            for i in allowed_instance:
                if isinstance(value, i):
                    allow_value[0] = True
                    break
            if not allow_value[0]:
                raise ValueError(f"Unknown override in SDApiVariables:p:init (value: {value})")

            # range check
            if range is None: range = (-1.1000002, -1.1000001)
            allow_value[1] = self.range_check(value, range[0], range[1])

            # 値が最終的に許可されるかどうか
            allow = (allow_value[0] and allow_value[1]) or allow_invalidate
            if not allow: value = default
        self._value = value
        self._range = range or (-1.1000002, -1.1000001)
        self._default = default

    @staticmethod
    def range_check(v, min, max, type_e: bool = True) -> bool:
        try:
            if min <= v <= max:
                return True
            else:
                return False
        except TypeError:
            return type_e



class SDApiVariables:
    """txt/img 2 img 用の型チェッカーを提供するクラス"""
    def __init__(self):
        self.prompt = p("", str, "")
        self.negative_prompt = p("", str, "")
        self.styles = p([], list, [])
        self.seed = p(-1, int, -1)
        self.subseed = p(-1, int, -1)
        self.subseed_strength = p(0.0, float, 0.0)
        self.seed_resize_from_h = p(-1, int, -1)
        self.seed_resize_from_w = p(-1, int, -1)
        self.sampler_name = p("Euler a", str, "Euler a")
        self.scheduler = p("Automatic", str, "Automatic")
        self.batch_size = p(1, int, 1)
        self.n_inter = p(1, int, 1)
        self.steps = p(50, int, 50)
        self.cfg_scale = p(7.0, float, 7.0)
        self.width = p(512, int, 512)
        self.height = p(512, int, 512)
        self.restore_faces = p(False, bool, False)
        self.tiling = p(False, bool, False)
        self.do_not_save_samples = p(False, bool, False)
        self.do_not_save_grid = p(False, bool, False)
        self.eta = p(0, int, 0)
        self.denoising_strength = p(0.0, float, 0.0)
        self.s_min_uncond = p(0, int, 0, dataclass=True)
        self.s_churn = p(0, int, 0, dataclass=True)
        self.s_tmax = p(0, int, 0, dataclass=True)
        self.s_tmin = p(0, int, 0, dataclass=True)
        self.s_noise = p(0, int, 0, dataclass=True)
        self.override_settings = p({}, dict, {}, allow_invalidate=True)
        self.override_settings_restore_afterwards = p(True, bool, True)
        self.refiner_checkpoint = p("", str, "")
        self.refiner_switch_at = p(0.0, float, 0.0)
        self.disable_extra_networks = p(False, bool, False)
        self.firstpass_image = p("", str, "")
        self.comments = p({}, dict, {}, allow_invalidate=True)
        self.enable_hr = p(False, bool, False)
        self.firstphase_width = p(0, int, 0)
        self.firstphase_height = p(0, int, 0)
        self.hr_scale = p(2.0, float, 2.0)
        self.hr_upscaler = p("R-ESRGAN 4x+ Anime6B", str, "R-ESRGAN 4x+ Anime6B")
        self.hr_second_pass_steps = p(0, int, 0)
        self.hr_resize_x = p(0, int, 0)
        self.hr_resize_y = p(0, int, 0)
        self.hr_checkpoint_name = p("", str, "")
        self.hr_sampler_name = p("", str, "")
        self.hr_scheduler = p("", str, "")
        self.hr_prompt = p("", str, "")
        self.hr_negative_prompt = p("", str, "")
        self.force_task_id = p("", str, "")
        self.sampler_index = p("Euler", str, "Euler")
        self.script_name = p("", str, "")
        self.script_args = p([], list, [])
        self.send_images = p(True, bool, True)
        self.save_images = p(False, bool, False)
        self.alwayson_scripts = p({}, dict, {}, allow_invalidate=True)
        self.infotext = p("", str, "")

    def __getattr__(self, item):
        return None

    def _initialize(
            self,
            **kw
    ):
        for k, v in kw:
            k = k.lower()
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                print(f"[ERROR]: Unknown argument in SDAPIVariables ({k})")

    def _make_it_dict(self) -> dict:
        """すべての値を辞書形式で返す"""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith("_")
            if not callable(v)
        }

    def __call__(self, **kwargs) -> dict:
        """すべての値を初期化、再処理しkwに渡せる辞書形式で返す
        主に api/txt2img.py の payload に対するものとして返される
        """
        if kwargs != {}:
            self._initialize(**kwargs)
        return self._make_it_dict()