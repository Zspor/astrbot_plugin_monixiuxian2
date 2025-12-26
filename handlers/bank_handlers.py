# handlers/bank_handlers.py
"""灵石银行处理器"""
from astrbot.api.event import AstrMessageEvent
from ..data import DataBase
from ..managers.bank_manager import BankManager
from ..models import Player
from .utils import player_required

__all__ = ["BankHandlers"]

class BankHandlers:
    """灵石银行处理器"""
    
    def __init__(self, db: DataBase, bank_mgr: BankManager):
        self.db = db
        self.bank_mgr = bank_mgr
    
    @player_required
    async def handle_bank_info(self, player: Player, event: AstrMessageEvent):
        """查看银行信息"""
        info = await self.bank_mgr.get_bank_info(player)
        
        yield event.plain_result(
            "🏦 灵石银行\n"
            "━━━━━━━━━━━━━━━\n"
            f"💰 存款余额：{info['balance']:,} 灵石\n"
            f"📈 待领利息：{info['pending_interest']:,} 灵石\n"
            f"📊 日利率：0.1%（复利）\n"
            "━━━━━━━━━━━━━━━\n"
            f"💎 持有灵石：{player.gold:,}\n"
            "━━━━━━━━━━━━━━━\n"
            "💡 指令：\n"
            "  /存灵石 <数量>\n"
            "  /取灵石 <数量>\n"
            "  /领取利息"
        )
    
    @player_required
    async def handle_deposit(self, player: Player, event: AstrMessageEvent, amount: int = 0):
        """存入灵石"""
        if amount <= 0:
            yield event.plain_result("❌ 请输入存款金额，例如：/存灵石 10000")
            return
        
        success, msg = await self.bank_mgr.deposit(player, amount)
        prefix = "✅" if success else "❌"
        yield event.plain_result(f"{prefix} {msg}")
    
    @player_required
    async def handle_withdraw(self, player: Player, event: AstrMessageEvent, amount: int = 0):
        """取出灵石"""
        if amount <= 0:
            yield event.plain_result("❌ 请输入取款金额，例如：/取灵石 10000")
            return
        
        success, msg = await self.bank_mgr.withdraw(player, amount)
        prefix = "✅" if success else "❌"
        yield event.plain_result(f"{prefix} {msg}")
    
    @player_required
    async def handle_claim_interest(self, player: Player, event: AstrMessageEvent):
        """领取利息"""
        success, msg = await self.bank_mgr.claim_interest(player)
        prefix = "✅" if success else "❌"
        yield event.plain_result(f"{prefix} {msg}")
