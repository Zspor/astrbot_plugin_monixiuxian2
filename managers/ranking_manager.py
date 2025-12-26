# managers/ranking_manager.py
"""
排行榜系统管理器 - 处理各种排行榜逻辑
"""

from typing import Tuple, List
from ..data.data_manager import DataBase
from ..managers.combat_manager import CombatManager


class RankingManager:
    """排行榜系统管理器"""
    
    def __init__(self, db: DataBase, combat_mgr: CombatManager):
        self.db = db
        self.combat_mgr = combat_mgr
    
    async def get_level_ranking(self, limit: int = 10) -> Tuple[bool, str]:
        """
        境界排行榜
        
        Args:
            limit: 显示数量
            
        Returns:
            (成功标志, 消息)
        """
        all_players = await self.db.get_all_players()
        
        if not all_players:
            return False, "❌ 暂无数据！"
        
        # 按修为排序
        sorted_players = sorted(all_players, key=lambda p: p.experience, reverse=True)[:limit]
        
        msg = "╔══════════════════════╗\n"
        msg += "║    境界排行榜    ║\n"
        msg += "╚══════════════════════╝\n\n"
        
        for idx, player in enumerate(sorted_players, 1):
            name = player.user_name if player.user_name else f"道友{player.user_id[:6]}"
            msg += f"{idx}. {name}\n"
            msg += f"   境界：Lv.{player.level_index} | 修为：{player.experience:,}\n\n"
        
        return True, msg
    
    async def get_power_ranking(self, limit: int = 10) -> Tuple[bool, str]:
        """
        战力排行榜（基于ATK）
        
        Args:
            limit: 显示数量
            
        Returns:
            (成功标志, 消息)
        """
        all_players = await self.db.get_all_players()
        
        if not all_players:
            return False, "❌ 暂无数据！"
        
        # 计算战力（ATK + HP + MP综合）
        player_power = []
        for player in all_players:
            # 如果没有战斗属性，先计算
            if player.atk == 0:
                atk = self.combat_mgr.calculate_atk(player.experience, player.atkpractice)
            else:
                atk = player.atk
            
            if player.hp == 0:
                hp, _ = self.combat_mgr.calculate_hp_mp(player.experience)
            else:
                hp = player.hp
            
            # 战力 = ATK * 10 + HP
            power = atk * 10 + hp
            player_power.append((player, power))
        
        # 按战力排序
        sorted_players = sorted(player_power, key=lambda x: x[1], reverse=True)[:limit]
        
        msg = "╔══════════════════════╗\n"
        msg += "║    战力排行榜    ║\n"
        msg += "╚══════════════════════╝\n\n"
        
        for idx, (player, power) in enumerate(sorted_players, 1):
            name = player.user_name if player.user_name else f"道友{player.user_id[:6]}"
            atk = player.atk if player.atk > 0 else self.combat_mgr.calculate_atk(player.experience, player.atkpractice)
            msg += f"{idx}. {name}\n"
            msg += f"   战力：{power:,} | ATK：{atk:,}\n\n"
        
        return True, msg
    
    async def get_wealth_ranking(self, limit: int = 10) -> Tuple[bool, str]:
        """
        财富排行榜（灵石）
        
        Args:
            limit: 显示数量
            
        Returns:
            (成功标志, 消息)
        """
        all_players = await self.db.get_all_players()
        
        if not all_players:
            return False, "❌ 暂无数据！"
        
        # 按灵石排序
        sorted_players = sorted(all_players, key=lambda p: p.gold, reverse=True)[:limit]
        
        msg = "╔══════════════════════╗\n"
        msg += "║    财富排行榜    ║\n"
        msg += "╚══════════════════════╝\n\n"
        
        for idx, player in enumerate(sorted_players, 1):
            name = player.user_name if player.user_name else f"道友{player.user_id[:6]}"
            msg += f"{idx}. {name}\n"
            msg += f"   灵石：{player.gold:,}\n\n"
        
        return True, msg
    
    async def get_sect_ranking(self, limit: int = 10) -> Tuple[bool, str]:
        """
        宗门排行榜（建设度）
        
        Args:
            limit: 显示数量
            
        Returns:
            (成功标志, 消息)
        """
        all_sects = await self.db.ext.get_all_sects()
        
        if not all_sects:
            return False, "❌ 暂无宗门数据！"
        
        # 已经按建设度排序
        top_sects = all_sects[:limit]
        
        msg = "╔══════════════════════╗\n"
        msg += "║    宗门排行榜    ║\n"
        msg += "╚══════════════════════╝\n\n"
        
        for idx, sect in enumerate(top_sects, 1):
            owner = await self.db.get_player_by_id(sect.sect_owner)
            owner_name = owner.user_name if owner and owner.user_name else "未知"
            members = await self.db.ext.get_sect_members(sect.sect_id)
            
            msg += f"{idx}. 【{sect.sect_name}】\n"
            msg += f"   宗主：{owner_name}\n"
            msg += f"   建设度：{sect.sect_scale:,} | 成员：{len(members)}人\n\n"
        
        return True, msg
    
    async def get_contribution_ranking(self, sect_id: int, limit: int = 10) -> Tuple[bool, str]:
        """
        宗门贡献度排行榜
        
        Args:
            sect_id: 宗门ID
            limit: 显示数量
            
        Returns:
            (成功标志, 消息)
        """
        sect = await self.db.ext.get_sect_by_id(sect_id)
        if not sect:
            return False, "❌ 宗门不存在！"
        
        members = await self.db.ext.get_sect_members(sect_id)
        
        if not members:
            return False, "❌ 宗门暂无成员！"
        
        # 按贡献度排序
        sorted_members = sorted(members, key=lambda p: p.sect_contribution, reverse=True)[:limit]
        
        msg = f"╔══════════════════════╗\n"
        msg += f"║ {sect.sect_name} 贡献排行 ║\n"
        msg += f"╚══════════════════════╝\n\n"
        
        for idx, member in enumerate(sorted_members, 1):
            name = member.user_name if member.user_name else f"道友{member.user_id[:6]}"
            position_name = ["宗主", "长老", "亲传", "内门", "外门"][member.sect_position]
            msg += f"{idx}. {name} ({position_name})\n"
            msg += f"   贡献度：{member.sect_contribution:,}\n\n"
        
        return True, msg
