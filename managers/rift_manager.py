# managers/rift_manager.py
"""
秘境系统管理器 - 处理秘境探索、奖励等逻辑
"""

import random
import time
from typing import Tuple, List, Optional, Dict
from ..data.data_manager import DataBase
from ..models_extended import Rift
from ..models import Player


class RiftManager:
    """秘境系统管理器"""
    
    # 默认秘境探索时长（秒）
    DEFAULT_DURATION = 1800 
    
    def __init__(self, db: DataBase, config_manager=None):
        self.db = db
        self.config = config_manager.rift_config if config_manager else {}
        self.explore_duration = self.config.get("default_duration", self.DEFAULT_DURATION)
    
    async def list_rifts(self) -> Tuple[bool, str]:
        """
        列出所有秘境
        
        Returns:
            (成功标志, 消息)
        """
        rifts = await self.db.ext.get_all_rifts()
        
        if not rifts:
            return False, "❌ 当前没有开放的秘境！"
        
        msg = "╔══════════════════════╗\n"
        msg += "║    秘境列表    ║\n"
        msg += "╚══════════════════════╝\n\n"
        
        for rift in rifts:
            rewards_dict = rift.get_rewards()
            exp_range = rewards_dict.get("exp", [0, 0])
            gold_range = rewards_dict.get("gold", [0, 0])
            
            msg += f"【{rift.rift_name}】\n"
            msg += f"  等级要求：境界 {rift.required_level} 及以上\n"
            msg += f"  修为奖励：{exp_range[0]}-{exp_range[1]}\n"
            msg += f"  灵石奖励：{gold_range[0]}-{gold_range[1]}\n\n"
        
        msg += "使用 /explore_rift <秘境ID> 探索秘境"
        
        return True, msg
    
    async def enter_rift(
        self,
        user_id: str,
        rift_id: int
    ) -> Tuple[bool, str]:
        """
        进入秘境
        
        Args:
            user_id: 用户ID
            rift_id: 秘境ID
            
        Returns:
            (成功标志, 消息)
        """
        # 1. 检查用户
        player = await self.db.get_player_by_id(user_id)
        if not player:
            return False, "❌ 你还未踏入修仙之路！"
        
        # 2. 检查用户状态
        user_cd = await self.db.ext.get_user_cd(user_id)
        if not user_cd:
            await self.db.ext.create_user_cd(user_id)
            user_cd = await self.db.ext.get_user_cd(user_id)
        
        if user_cd.type != 0:
            return False, "❌ 你当前正忙，无法探索秘境！"
        
        # 3. 检查秘境
        rift = await self.db.ext.get_rift_by_id(rift_id)
        if not rift:
            return False, "❌ 秘境不存在！"
        
        # 4. 检查境界要求
        if player.level_index < rift.required_level:
            return False, f"❌ 探索此秘境需要达到境界等级 {rift.required_level}！"
        
        # 5. 设置探索状态
        scheduled_time = int(time.time()) + self.explore_duration
        await self.db.ext.set_user_busy(user_id, 3, scheduled_time)  # 3=探索秘境
        
        return True, f"✨ 你进入了『{rift.rift_name}』！探索需要 {self.explore_duration//60} 分钟。"
    
    async def finish_exploration(
        self,
        user_id: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        完成秘境探索
        
        Args:
            user_id: 用户ID
            
        Returns:
            (成功标志, 消息, 奖励数据)
        """
        # 1. 检查用户
        player = await self.db.get_player_by_id(user_id)
        if not player:
            return False, "❌ 你还未踏入修仙之路！", None
        
        # 2. 检查CD状态
        user_cd = await self.db.ext.get_user_cd(user_id)
        if not user_cd or user_cd.type != 3:
            return False, "❌ 你当前不在探索秘境！", None
        
        # 3. 检查时间
        current_time = int(time.time())
        if current_time < user_cd.scheduled_time:
            remaining = user_cd.scheduled_time - current_time
            minutes = remaining // 60
            return False, f"❌ 探索尚未完成！还需要 {minutes} 分钟。", None
        
        # 4. 随机生成奖励（简化版本，实际应该根据秘境配置）
        exp_reward = random.randint(1000, 5000)
        gold_reward = random.randint(500, 2000)
        
        # 随机事件
        events = [
            "你发现了一处灵泉，修为大增！",
            "你在秘境中击败了一只妖兽！",
            "你找到了一个隐藏的宝箱！",
            "你领悟了一些修炼心得。",
            "你在秘境中遇到了前辈留下的传承！"
        ]
        event = random.choice(events)
        
        # 5. 应用奖励
        player.experience += exp_reward
        player.gold += gold_reward
        await self.db.update_player(player)
        
        # 6. 清除CD
        await self.db.ext.set_user_free(user_id)
        
        msg = f"""
╔══════════════════════╗
║    探索完成    ║
╚══════════════════════╝

{event}

获得修为：+{exp_reward}
获得灵石：+{gold_reward}
        """.strip()
        
        reward_data = {
            "exp": exp_reward,
            "gold": gold_reward,
            "event": event
        }
        
        return True, msg, reward_data
