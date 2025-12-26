# handlers/boss_handlers.py
from astrbot.api.event import AstrMessageEvent
from ..managers.boss_manager import BossManager
from ..data.data_manager import DataBase

class BossHandlers:
    def __init__(self, db: DataBase, boss_mgr: BossManager):
        self.db = db
        self.boss_mgr = boss_mgr

    async def handle_boss_info(self, event: AstrMessageEvent):
        """查询世界Boss"""
        success, msg, _ = await self.boss_mgr.get_boss_info()
        yield event.plain_result(msg)

    async def handle_boss_fight(self, event: AstrMessageEvent):
        """挑战世界Boss"""
        user_id = event.get_sender_id()
        success, msg, _ = await self.boss_mgr.challenge_boss(user_id)
        yield event.plain_result(msg)
    
    # 管理员指令：生成BOSS（可选）
    async def handle_spawn_boss(self, event: AstrMessageEvent):
        """生成世界Boss (Admin)"""
        # 这里应该加权限判断，暂时略过
        success, msg, _ = await self.boss_mgr.auto_spawn_boss()
        yield event.plain_result(msg)
