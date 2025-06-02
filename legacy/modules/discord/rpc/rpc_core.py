from pypresence import Presence
import time

class DiscordRPC:
    def register(self):
        """ Register ALL Variables"""
        # これらはRPCの初期値に用いられる
        self.idle = {
            "state": "SD-PEM",
            "details": "Idle",
            "large_image": "tmp-icon",
            "small_image": None,
            "large_text": "Idling..",
            "small_text": "Idling.."
        }
        self.from_lora_forever_generating = {
            "state": "SD-PEM",
            "details": "Failed to get current state",
            "large_image": "tmp-icon",
            "small_image": "tmp-icon",
            "large_text": "Failed to get current state",
            "small_text": "Failed to get current state"
        }
        self.empty = {
            "state": "SD-PEM",
            "details": "",
            "large_image": "tmp-icon",
            "small_image": None,
            "large_text": "",
            "small_text": ""
        }

    def __init__(self, client_id=None):
        self.client_id = client_id if client_id is not None else None
        self.presence = Presence(self.client_id)

        self.register()
        self.presence.connect()

    def set_rpc(
            self,
            rpc_name,
            rpc_state=None,
            rpc_details=None,
            rpc_large=None,
            rpc_small=None,
            rpc_large_text=None,
            rpc_small_text=None,
    ):
        if hasattr(self, rpc_name):
            rpc_default = getattr(self, rpc_name)
        else:
            rpc_default = self.empty

        if rpc_state:
            rpc_default["state"] = rpc_state
        if rpc_details:
            rpc_default["details"] = rpc_details
        if rpc_large:
            rpc_default["large_image"] = rpc_large
        if rpc_small:
            rpc_default["small_image"] = rpc_small
        if rpc_large_text:
            rpc_default["large_text"] = rpc_large_text
        if rpc_small_text:
            rpc_default["small_text"] = rpc_small_text

        self.presence.update(
            **rpc_default,
            start=int(time.time())
        )