# handlers/misc_handler.py
from astrbot.api.event import AstrMessageEvent
from ..data import DataBase

__all__ = ["MiscHandler"]


class MiscHandler:
    """杂项指令处理器 - 提供帮助信息"""

    def __init__(self, db: DataBase):
        self.db = db

    async def handle_help(self, event: AstrMessageEvent):
        """显示帮助信息"""
        help_text = (
            "=== 修仙指令 (v2.3.0) ===\n"
            "\n"
            "【基础 & 修炼】\n"
            "我要修仙 [灵修/体修] | 我的信息\n"
            "签到 | 闭关 | 出关 | 改道号 <名>\n"
            "突破信息 | 突破 [丹药名]\n"
            "\n"
            "【经济 & 银行】\n"
            "银行 | 存灵石/取灵石 <数>\n"
            "领取利息 | 丹阁 | 器阁\n"
            "\n"
            "【悬赏 & 任务】\n"
            "悬赏令 | 接取悬赏 <ID>\n"
            "悬赏状态 | 完成/放弃悬赏\n"
            "\n"
            "【宗门系统】\n"
            "创建/加入/退出宗门 <名>\n"
            "我的宗门 | 宗门列表 | 宗门捐献\n"
            "\n"
            "【战斗 & 竞技】\n"
            "切磋/决斗 <@某人>\n"
            "世界Boss | 挑战Boss\n"
            "传承挑战 <@某人> | 传承排行\n"
            "境界/战力/灵石/宗门排行\n"
            "\n"
            "【历练 & 生产】\n"
            "开始历练 | 秘境列表 | 炼丹\n"
            "传承信息 (数值详情)\n"
            "================"
        )
        yield event.plain_result(help_text)
