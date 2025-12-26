# managers/bank_manager.py
"""灵石银行系统管理器"""
import time
from typing import Tuple
from ..data import DataBase
from ..models import Player

__all__ = ["BankManager"]

# 银行配置
DAILY_INTEREST_RATE = 0.001  # 每日利息 0.1%
MAX_DEPOSIT = 10000000  # 最大存款上限

class BankManager:
    """灵石银行管理器"""
    
    def __init__(self, db: DataBase):
        self.db = db
    
    async def get_bank_info(self, player: Player) -> dict:
        """获取银行账户信息
        
        Returns:
            dict: {balance, last_interest_time, pending_interest}
        """
        # 从扩展表获取银行数据
        bank_data = await self.db.ext.get_bank_account(player.user_id)
        if not bank_data:
            return {"balance": 0, "last_interest_time": 0, "pending_interest": 0}
        
        # 计算待领利息
        pending_interest = self._calculate_interest(
            bank_data["balance"], 
            bank_data["last_interest_time"]
        )
        
        return {
            "balance": bank_data["balance"],
            "last_interest_time": bank_data["last_interest_time"],
            "pending_interest": pending_interest
        }
    
    def _calculate_interest(self, balance: int, last_time: int) -> int:
        """计算待领利息"""
        if balance <= 0 or last_time <= 0:
            return 0
        
        # 计算经过的天数
        now = int(time.time())
        days_passed = (now - last_time) // 86400  # 86400 = 24 * 60 * 60
        
        if days_passed < 1:
            return 0
        
        # 复利计算：本金 * ((1 + 利率) ^ 天数 - 1)
        interest = int(balance * ((1 + DAILY_INTEREST_RATE) ** days_passed - 1))
        return interest
    
    async def deposit(self, player: Player, amount: int) -> Tuple[bool, str]:
        """存入灵石
        
        Args:
            player: 玩家
            amount: 存款金额
            
        Returns:
            (success, message)
        """
        if amount <= 0:
            return False, "存款金额必须大于0。"
        
        if player.gold < amount:
            return False, f"灵石不足！你只有 {player.gold} 灵石。"
        
        # 获取当前余额
        bank_data = await self.db.ext.get_bank_account(player.user_id)
        current_balance = bank_data["balance"] if bank_data else 0
        
        if current_balance + amount > MAX_DEPOSIT:
            return False, f"存款上限为 {MAX_DEPOSIT:,} 灵石，当前余额 {current_balance:,}。"
        
        # 扣除玩家灵石
        player.gold -= amount
        await self.db.update_player(player)
        
        # 更新银行账户
        new_balance = current_balance + amount
        await self.db.ext.update_bank_account(
            player.user_id, 
            new_balance, 
            int(time.time()) if current_balance == 0 else bank_data["last_interest_time"]
        )
        
        return True, f"成功存入 {amount:,} 灵石！\n当前余额：{new_balance:,} 灵石"
    
    async def withdraw(self, player: Player, amount: int) -> Tuple[bool, str]:
        """取出灵石
        
        Args:
            player: 玩家
            amount: 取款金额
            
        Returns:
            (success, message)
        """
        if amount <= 0:
            return False, "取款金额必须大于0。"
        
        bank_data = await self.db.ext.get_bank_account(player.user_id)
        if not bank_data or bank_data["balance"] < amount:
            current = bank_data["balance"] if bank_data else 0
            return False, f"余额不足！当前余额：{current:,} 灵石。"
        
        # 更新银行余额
        new_balance = bank_data["balance"] - amount
        await self.db.ext.update_bank_account(
            player.user_id, 
            new_balance, 
            bank_data["last_interest_time"]
        )
        
        # 增加玩家灵石
        player.gold += amount
        await self.db.update_player(player)
        
        return True, f"成功取出 {amount:,} 灵石！\n当前余额：{new_balance:,} 灵石\n当前持有：{player.gold:,} 灵石"
    
    async def claim_interest(self, player: Player) -> Tuple[bool, str]:
        """领取利息
        
        Returns:
            (success, message)
        """
        bank_data = await self.db.ext.get_bank_account(player.user_id)
        if not bank_data or bank_data["balance"] <= 0:
            return False, "你还没有存款，无法领取利息。"
        
        interest = self._calculate_interest(
            bank_data["balance"], 
            bank_data["last_interest_time"]
        )
        
        if interest <= 0:
            return False, "利息不足1灵石，请明日再来。"
        
        # 更新银行余额（利息转入本金）
        new_balance = bank_data["balance"] + interest
        await self.db.ext.update_bank_account(
            player.user_id, 
            new_balance, 
            int(time.time())  # 重置利息计算时间
        )
        
        return True, f"成功领取利息 {interest:,} 灵石！\n当前余额：{new_balance:,} 灵石"
