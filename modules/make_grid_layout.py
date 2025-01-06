from itertools import islice
from PIL import ImageDraw, Image, ImageFont, ImageOps
from PIL.ImageFont import FreeTypeFont
from typing import *

class MakeGridLayout:
    @staticmethod
    def _chunk_list(lst, n):
        """itertoolsでリストをn個ずつに分割"""
        it = iter(lst)
        return [list(islice(it, n)) for _ in range((len(lst) + n - 1) // n)]

    @staticmethod
    def _adjust_font_size(draw, text, image, max_font_size) -> FreeTypeFont:
        """
        フォントサイズが画像に収まるように調整する
        引数:
          draw: ImageDraw.Draw(image) のインスタンス
          text: 描画する文字列
          image: 描画先の PIL.Image インスタンス
          max_font_size: 最大フォントサイズ(開始サイズ)
        戻り値:
          調整後の ImageFont.ImageFont インスタンス
        """
        font_size = max_font_size

        while True:
            # truetype でフォント生成
            font = ImageFont.truetype("arial", font_size)

            # (0, 0) を基準にバウンディングボックスを取得
            # textbbox は (left, top, right, bottom) を返す
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # 幅・高さともに画像内に収まるか判定
            if text_width <= image.width and text_height <= image.height:
                break

            font_size -= 1

            # フォントサイズが極端に小さくなりすぎた場合は強制終了
            if font_size <= 1:
                break

        return font

    def _make_grid_layout(
            self,
            images: list[Image.Image],
            texts: tuple[list[str], list[str]], # Xtexts, Ytexts
            y_axis: int = 1, # Yの数
            start_pos: tuple[int] = (0, 0), # 画像貼り付け位置
            accept_extend: bool = False, # 余りを追加のYに足すことを許可
            extend_y_text: str = None, # 増えたYのテキスト
    ):
        """
        XY Plot を作成する関数、画像のリストとテキストのリストを受け取り、それをXY Plot に変換する
        画像のリストとYに応じたテキストの長さ (つまり images / y_axis == len(texts[0]) と y_axis == len(texts[1]) が成り立つ)
        accept_extend が True の場合、余りを追加のYに足すことを許可する。
        False の場合は images が y_axis で割り切れることが必要。

        :param images:
        :param texts:
        :param y_axis:
        :param start_pos:
        :param accept_extend:
        :param extend_y_text:
        :return:
        """

        if accept_extend:
            if extend_y_text is None:
                raise ValueError("extend_y_text must be set when accept_extend is True")
        image_count = len(images)

        # Yの差分を計算
        image_per_x = image_count // y_axis
        remain_x = image_count % y_axis
        if remain_x != 0:
            if accept_extend:
                y_axis += 1
            else:
                raise ValueError("images must be divisible by y_axis")

        x_images = []
        max_width = max(images, key=lambda x: x.width).width
        max_height = max(images, key=lambda x: x.height).height
        x_image = self._chunk_list(images, image_per_x)
        start_x = start_pos[0]
        start_y = start_pos[1]
        # Xごとの画像リストを作成し、それらを横向きに結合、最終的に x_images に挿入
        for x in x_image:
            img = Image.new("RGB", (max_width * len(x), max_height), (255, 255, 255))
            for (i, image) in enumerate(x):
                img.paste(
                    image, (start_x+(max_width*i), start_y)
                )
            x_images.append(img)

        # x_images の個数を検証し、正しいならXY Grid を作成
        if len(x_images) != y_axis:
            raise ValueError("Something errors occurred in making X_images")

        finally_image = Image.new("RGB", (max_width * len(x_image[0]), max_height * len(x_images)), (255, 255, 255))
        for (i, x_image) in enumerate(x_images):
            finally_image.paste(
                x_image, (0, max_height*i)
            )

        # X軸のテキストを作成 -- ここから
        x_axis_text_image = Image.new("RGB", (max_width * len(x_images), max_height//3), (255, 255, 255))
        x_axis_texts = texts[0]
        for (i, text) in enumerate(x_axis_texts):
            image = Image.new(
                "RGB", (max_width, max_height//3), (255, 255, 255)
            )
            draw = ImageDraw.Draw(image)
            font_size = image.size[0]
            font = self._adjust_font_size(draw, text, image, font_size)
            draw.text((0, 0), text, font=font, fill=(0, 0, 0))
            x_axis_text_image.paste(image, (i*image.width, 0))
            # X軸のテキストを作成 -- ここまで

        # Y軸のテキストを作成 -- ここから
        y_axis_text_image = Image.new("RGB", ((max_width//3) * 2, max_height * len(x_images)), (255, 255, 255))
        y_axis_texts = texts[1]
        for (i, text) in enumerate(y_axis_texts):
            image = Image.new(
                "RGB", ((max_width//3) * 2, max_height), (255, 255, 255)
            )
            draw = ImageDraw.Draw(image)
            max_font_size = image.size[1]
            font = self._adjust_font_size(draw, text, image, max_font_size)
            draw.text((0, 0), text, font=font, fill=(0, 0, 0))
            y_axis_text_image.paste(image, (0, i*image.height))
            # Y軸のテキストを作成 -- ここまで

        # 最終的に画像を結合
        # 画像にパディングを追加
        padding_scale_x = x_axis_text_image.height
        padding_scale_y = y_axis_text_image.width
        # ボーダーは左、上、右、下の順
        padded_image = ImageOps.expand(finally_image, (padding_scale_y, padding_scale_x, 0, 0), fill=(255, 255, 255))

        # X軸のテキストをペースト
        padded_image.paste(x_axis_text_image, (padding_scale_y, 0))

        # Y軸のテキストをペースト
        padded_image.paste(y_axis_text_image, (0, padding_scale_x))
        return padded_image

    def make_image(
            self, images: List[Image.Image], texts: Tuple[List[str], List[str]], y_axis: int = 1,
    ):
        return self._make_grid_layout(images, texts, y_axis)