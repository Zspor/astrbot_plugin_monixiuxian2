# handlers/alchemy_handlers.py
from astrbot.api.event import AstrMessageEvent
from ..managers.alchemy_manager import AlchemyManager
from ..data.data_manager import DataBase

class AlchemyHandlers:
    def __init__(self, db: DataBase, alchemy_mgr: AlchemyManager):
        self.db = db
        self.alchemy_mgr = alchemy_mgr

    async def handle_recipes(self, event: AstrMessageEvent):
        """丹药配方"""
        user_id = event.get_sender_id()
        success, msg = await self.alchemy_mgr.get_available_recipes(user_id)
        yield event.plain_result(msg)

    async def handle_craft(self, event: AstrMessageEvent, pill_id: int):
        """炼丹"""
        user_id = event.get_sender_id()
        if not pill_id:
             yield event.plain_result("❌ 请输入丹药配方ID")
             return
        success, msg, _ = await self.alchemy_mgr.craft_pill(user_id, int(pill_id))
        yield event.plain_result(msg)
