import base64
import io

import requests
import os

from PIL import Image

from jsonutil import JsonUtilities
from modules.chrome_drivers import ChromeDriverUtil


class TwitterPostApi:
    def __init__(self):
        self.token_pth = os.path.join(os.getcwd(), "secrets/x_token.json")
        self.driverUtil = ChromeDriverUtil("TwitterPoster")

        self.file = JsonUtilities(self.token_pth)
        self.token = self.file.read()

        self.ENDPOINT = "https://x.com/i/api/graphql/5radHM13Uo_czv5X3nnYNw/CreateTweet"
        self.headers = {
            "Host": "x.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) lunarclient/3.3.1-ow Chrome/126.0.6478.234 Electron/31.7.3 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "ja",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/json",
            "Referer": "https://x.com/home",
            "x-twitter-auth-type": "OAuth2Session",
            "x-csrf-token": None,
            "x-twitter-client-language": "ja",
            "x-twitter-active-user": "yes",
            "x-client-transaction-id": None,
            "Origin": "https://x.com",
            "DNT": "1",
            "Sec-GPC": "1",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Authorization": None,
            "Connection": "keep-alive",
            "Cookie": None,
        }

        self.payload = {
            "variables": {
                "tweet_text": None,  # ポストする内容
                "dark_request": False,
                "media": {
                    "media_entities": [

                    ],
                    "possibly_sensitive": None
                },
                "semantic_annotation_ids": [],
                "disallowed_reply_options": None,
            },
            "features": {
                "premium_content_api_read_enabled": False,
                "communities_web_enable_tweet_community_results_fetch": True,
                "c9s_tweet_anatomy_moderator_badge_enabled": True,
                "responsive_web_grok_analyze_button_fetch_trends_enabled": False,
                "responsive_web_grok_analyze_post_followups_enabled": True,
                "responsive_web_grok_share_attachment_enabled": True,
                "responsive_web_edit_tweet_api_enabled": True,
                "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
                "view_counts_everywhere_api_enabled": True,
                "longform_notetweets_consumption_enabled": True,
                "responsive_web_twitter_article_tweet_consumption_enabled": True,
                "tweet_awards_web_tipping_enabled": False,
                "creator_subscriptions_quote_tweet_preview_enabled": False,
                "longform_notetweets_rich_text_read_enabled": True,
                "longform_notetweets_inline_media_enabled": True,
                "profile_label_improvements_pcf_label_in_post_enabled": False,
                "rweb_tipjar_consumption_enabled": True,
                "responsive_web_graphql_exclude_directive_enabled": True,
                "verified_phone_label_enabled": False,
                "articles_preview_enabled": True,
                "rweb_video_timestamps_enabled": True,
                "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                "freedom_of_speech_not_reach_fetch_enabled": True,
                "standardized_nudges_misinfo": True,
                "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
                "responsive_web_graphql_timeline_navigation_enabled": True,
                "responsive_web_enhance_cards_enabled": False,
            },
            "queryId": "5radHM13Uo_czv5X3nnYNw",
        }

        self.media_entry_headers = {
            "Host": "upload.x.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) lunarclient/3.3.1-ow Chrome/126.0.6478.234 Electron/31.7.3 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/json",
            "Referer": "https://x.com/",
            "x-twitter-auth-type": "OAuth2Session",
            "x-csrf-token": None,
            "x-twitter-client-language": "ja",
            "x-twitter-active-user": "yes",
            "x-client-transaction-id": None,
            "Origin": "https://x.com",
            "DNT": "1",
            "Sec-GPC": "1",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Authorization": None,
            "Connection": "keep-alive",
            "Cookie": None,
        }

        self.MEDIA_ENDPOINT = "https://upload.x.com/i/media/upload.json?command=INIT&total_bytes={byte}&media_type=image%2Fpng&media_category=tweet_image"
        self.media_entry_payload = {
            'media_data': None
        }

    def rebuild_headers(
            self,
    ):
        self.headers["x-csrf-token"] = self.token["token"]
        self.headers["x-client-transaction-id"] = self.token["client_id"]
        self.headers["Authorization"] = f"Bearer {self.token['bearer_access_token']}"
        self.headers["Cookie"] = self.token["cookie"]

        self.media_entry_headers["x-csrf-token"] = self.token["token"]
        self.media_entry_headers["x-client-transaction-id"] = self.token["media_entry"]["client_id"]
        self.media_entry_headers["Authorization"] = f"Bearer {self.token['bearer_access_token']}"
        self.media_entry_headers["Cookie"] = self.token["media_entry"]["cookie"]
        return

    def rebuild_payload(
            self,
            tweet_text: str,
            possibly_sensitive: bool = False
    ) -> dict:
        """
        payload の事前処理を行う
        :param tweet_text:
        :param possibly_sensitive:
        :return:
        """
        self.payload["variables"]["tweet_text"] = tweet_text # type: ignore
        self.payload["variables"]["media"]["possibly_sensitive"] = possibly_sensitive # type: ignore

        payload = self.payload.copy()
        return payload

    def send_image_to_uploader(
            self, media: Image.Image,
    ) -> str:
        """
        :return: アップロード後のID
        """
        self.rebuild_headers()
        payload = self.media_entry_payload
        ENDPOINT = self.MEDIA_ENDPOINT.format(byte=len(media.tobytes()))

        buffer = io.BytesIO()
        media.save(buffer, format="PNG")
        buffered_media = buffer.getvalue()
        payload["files"] = base64.b64decode( # type: ignore
            buffered_media
        )
        response = requests.post(
            ENDPOINT,
            headers=self.headers,
            data=payload,
            allow_redirects=False
        )
        response.raise_for_status()

        if response.is_redirect:
            print("Redirected to: ", response.headers["Location"])

        print("Media upload response: ", response.text)
        response = response.json()
        return response.get("media_id_string", None)

    def POST(
            self,
            tweet_text: str,
            sensitive_content: bool = False,
            media_entries: list[Image.Image] = []
    ):
        self.rebuild_headers()
        payload = self.rebuild_payload(tweet_text, sensitive_content)

        # 画像がある場合、それらをアップロードしIDをツイートに含める
        media_ids = []
        for media in media_entries:
            media_id = self.send_image_to_uploader(media)
            if media_id is not None:
                media_ids.append(media_id)
        payload["variables"]["media"]["media_entities"] = [
            {"media_id": media_id, "tagged_users": []}
            for media_id in media_ids
            if media_id is not None
        ]

        response = requests.post(
            self.ENDPOINT,
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        print(response.text)
        return

    def _ENUMELATE_POST_FROM_JSK(
            self,
            fps, tweet_text, tmp_ep = None
    ):
        images = [
            Image.open(fp)
            for fp in fps
        ]

        if tmp_ep is not None:
            self.MEDIA_ENDPOINT = tmp_ep
        self.POST(tweet_text, media_entries=images)
        return