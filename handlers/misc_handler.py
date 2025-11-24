# handlers/misc_handler.py
from astrbot.api.event import AstrMessageEvent
from ..data import DataBase

CMD_START_XIUXIAN = "我要修仙"
CMD_PLAYER_INFO = "我的信息"
CMD_START_CULTIVATION = "闭关"
CMD_END_CULTIVATION = "出关"
CMD_CHECK_IN = "签到"

__all__ = ["MiscHandler"]


class MiscHandler:
    """杂项指令处理器 - 提供帮助信息"""

    def __init__(self, db: DataBase):
        self.db = db

    async def handle_help(self, event: AstrMessageEvent):
        """显示帮助信息"""
        help_text = (
            "=== 修仙指令手册 ===\n"
            f"【{CMD_START_XIUXIAN}】 开启修仙之旅\n"
            f"【{CMD_PLAYER_INFO}】 查看角色信息\n"
            f"【{CMD_START_CULTIVATION}】 进入闭关修炼\n"
            f"【{CMD_END_CULTIVATION}】 结束闭关修炼\n"
            f"【{CMD_CHECK_IN}】 每日签到领取灵石\n"
            "==========================\n"
            "⚔️ 装备系统：\n"
            "【我的装备】 查看已装备物品\n"
            "【装备 物品名】 装备指定物品\n"
            "【卸下 装备名】 卸下指定装备\n"
            "==========================\n"
            "⚡ 突破系统：\n"
            "【突破信息】 查询下一境界、成功率与可用丹药\n"
            "【突破】 直接尝试突破\n"
            "【突破 丹药名】 使用破境丹提升成功率\n"
            "==========================\n"
            "💡 闭关说明：\n"
            "• 闭关期间每分钟可获得修为\n"
            "• 修为获取受灵根资质影响\n"
            "• 主修心法可提供修为倍率加成\n"
            "==========================\n"
            "💰 签到说明：\n"
            "• 每日可签到一次\n"
            "• 闭关状态也能签到\n"
            "==========================\n"
            "装备栏位说明：\n"
            "• 武器：提升攻击、防御\n"
            "• 防具：提升防御、精神力\n"
            "• 主修心法：提升修为倍率、灵气上限\n"
            "• 功法（最多3个）：提升各项属性\n"
            "==========================\n"
        )
        yield event.plain_result(help_text)
