# handlers/combat_handlers.py
from astrbot.api.event import AstrMessageEvent
from astrbot.api.all import *
from ..managers.combat_manager import CombatManager, CombatStats
from ..data.data_manager import DataBase

class CombatHandlers:
    def __init__(self, db: DataBase, combat_mgr: CombatManager):
        self.db = db
        self.combat_mgr = combat_mgr

    async def _get_target_id(self, event: AstrMessageEvent, arg: str) -> str:
        for component in event.message_obj.message:
            if isinstance(component, At):
                return str(component.qq)
        if arg and arg.isdigit():
            return arg
        return None

    async def _prepare_combat_stats(self, user_id: str) -> CombatStats:
        player = await self.db.get_player_by_id(user_id)
        if not player:
            return None
        
        # 确保战斗属性已计算
        if player.hp == 0 or player.mp == 0:
            # 简单计算，不带buff，实际应该调用统一的计算逻辑含buff
            hp, mp = self.combat_mgr.calculate_hp_mp(player.experience)
            atk = self.combat_mgr.calculate_atk(player.experience, player.atkpractice)
            player.hp = hp
            player.mp = mp
            player.atk = atk
            # 这里不保存回数据库，只用于临时计算？或者保存？
            # 最好是保存，避免重复计算
            await self.db.update_player(player)

        # 获取 Buff 信息 (暂时简化，不查询 database_extended 的 buff_info)
        # 如果需要精准计算，应该引入 DatabaseExtended 并查询 ImpartInfo 等
        
        return CombatStats(
            user_id=user_id,
            name=player.user_name if player.user_name else f"道友{user_id}",
            hp=player.hp,
            max_hp=player.hp, # 注意：这里当前HP可能不是满的，CombatStats的max_hp应该重新计算
            mp=player.mp,
            max_mp=player.mp, # 同上
            atk=player.atk,
            exp=player.experience
        )

    async def handle_duel(self, event: AstrMessageEvent, target: str):
        """决斗 (消耗气血)"""
        user_id = event.get_sender_id()
        target_id = await self._get_target_id(event, target)
        
        if not target_id:
            yield event.plain_result("❌ 请指定决斗目标")
            return
            
        if user_id == target_id:
            yield event.plain_result("❌ 不能和自己决斗")
            return

        # 获取双方数据
        p1_stats = await self._prepare_combat_stats(user_id)
        p2_stats = await self._prepare_combat_stats(target_id)
        
        if not p1_stats:
            yield event.plain_result("❌ 你还未踏入修仙之路")
            return
        if not p2_stats:
            yield event.plain_result("❌ 对方还未踏入修仙之路")
            return

        # 战斗
        result = self.combat_mgr.player_vs_player(p1_stats, p2_stats, combat_type=2) # 2=决斗
        
        # 结算（更新HP）
        await self.db.ext.update_player_hp_mp(user_id, result['player1_final_hp'], result['player1_final_mp'])
        await self.db.ext.update_player_hp_mp(target_id, result['player2_final_hp'], result['player2_final_mp'])
        
        # 生成战报
        log = "\n".join(result['combat_log'])
        yield event.plain_result(f"{log}")

    async def handle_spar(self, event: AstrMessageEvent, target: str):
        """切磋 (不消耗气血)"""
        user_id = event.get_sender_id()
        target_id = await self._get_target_id(event, target)
        
        if not target_id:
            yield event.plain_result("❌ 请指定切磋目标")
            return

        if user_id == target_id:
            yield event.plain_result("❌ 不能和自己切磋")
            return

        p1_stats = await self._prepare_combat_stats(user_id)
        p2_stats = await self._prepare_combat_stats(target_id)
        
        if not p1_stats or not p2_stats:
             yield event.plain_result("❌ 双方都需要踏入修仙之路")
             return

        result = self.combat_mgr.player_vs_player(p1_stats, p2_stats, combat_type=1) # 1=切磋
        
        log = "\n".join(result['combat_log'])
        yield event.plain_result(f"{log}")
