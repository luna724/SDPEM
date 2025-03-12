import base64
from io import BytesIO

from PIL import Image

from modules.api.adetailer import ADetailerAPI
from modules.image_param import ImageParamUtil


class ADetailer:
    def __init__(self):
        self.api = ADetailerAPI()

    @staticmethod
    def list_models():
        return [
            "None",
            "face_yolov8n.pt",
            "face_yolov8s.pt",
            "hand_yolov8n.pt",
            "person_yolov8n-seg.pt",
            "person_yolov8s-seg.pt",
            "yolov8x-worldv2.pt",
            "mediapipe_face_full",
            "mediapipe_face_short",
            "mediapipe_face_mesh",
            "mediapipe_face_mesh_eyes_only"
    ]

    def single(
        self,
        base_image: Image.Image,
        step: int,
        models: dict[str, list[str, str]] # model_name: [prompt, negtaive]
    ) -> tuple[list[Image.Image], tuple]:
        param = ImageParamUtil().parse_param(ImageParamUtil().extract_png_metadata(base_image).get("parameters", ""))[0]
        img_prompt = param["prompt"]
        img_negative = param["negative"]

        model_payload = [
            {
                "ad_model": model,
                "ad_prompt": prompt if prompt.strip() != "" else "",
                "ad_negative_prompt": negative if negative.strip() != "" else "",
            }
            for model, [prompt, negative] in models.items()
        ]
        payload = {
            "prompt": img_prompt,
            "negative_prompt": img_negative,
            "width": base_image.width,
            "height": base_image.height,
            "batch_size": 1,
            "steps": step,
            "alwayson_scripts": {
                "ADetailer": {
                    "args": [
                        True,
                        True,
                    ] + model_payload
                }
            }
        }

        # Create the generator
        generator = self.api.call(base_image, **payload)

        # Consume the generator to get the final result
        last_value = None
        try:
            # Iterate through all yielded values (ignoring them)
            while True:
                last_value = next(generator)
        except StopIteration as e:
            # The return value is stored in the exception's value
            data = e.value

        response = data[0]
        last = data[1]

        images = []
        b64_images = response.get("images", None)
        for b64_image in b64_images:
            image_byte = base64.b64decode(b64_image)
            image = Image.open(BytesIO(image_byte))
            images.append(image)
        return images, last

    def single_webui_tunnel(
        self,
        base_image: Image.Image,
        step: int,
        m1, m1p, m1n,
        m2, m2p, m2n,
        m3, m3p, m3n,
        m4, m4p, m4n,
        m5, m5p, m5n,
        m6, m6p, m6n
    ):
        i, _ = self.single(
            base_image,
            step,
            { #type: ignore
                m1: [m1p, m1n],
                m2: [m2p, m2n],
                m3: [m3p, m3n],
                m4: [m4p, m4n],
                m5: [m5p, m5n],
                m6: [m6p, m6n]
            }
        )
        return i[0]