# handlers/adventure_handlers.py
from astrbot.api.event import AstrMessageEvent
from ..managers.adventure_manager import AdventureManager
from ..data.data_manager import DataBase

class AdventureHandlers:
    def __init__(self, db: DataBase, adv_mgr: AdventureManager):
        self.db = db
        self.adv_mgr = adv_mgr

    async def handle_start_adventure(self, event: AstrMessageEvent, type_: str = "medium"):
        """开始历练"""
        user_id = event.get_sender_id()
        success, msg = await self.adv_mgr.start_adventure(user_id, type_)
        yield event.plain_result(msg)

    async def handle_complete_adventure(self, event: AstrMessageEvent):
        """完成历练"""
        user_id = event.get_sender_id()
        success, msg, _ = await self.adv_mgr.finish_adventure(user_id)
        yield event.plain_result(msg)
    
    async def handle_adventure_status(self, event: AstrMessageEvent):
        """历练状态"""
        user_id = event.get_sender_id()
        success, msg = await self.adv_mgr.check_adventure_status(user_id)
        yield event.plain_result(msg)
