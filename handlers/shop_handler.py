# handlers/shop_handler.py

import time
import re
from astrbot.api.event import AstrMessageEvent
from astrbot.api import AstrBotConfig, logger
from ..data import DataBase
from ..core import ShopManager, EquipmentManager, PillManager
from ..models import Player
from ..config_manager import ConfigManager
from .utils import player_required

__all__ = ["ShopHandler"]

class ShopHandler:
    """商店处理器"""

    def __init__(self, db: DataBase, config: AstrBotConfig, config_manager: ConfigManager):
        self.db = db
        self.config = config
        self.config_manager = config_manager
        self.shop_manager = ShopManager(config, config_manager)
        self.equipment_manager = EquipmentManager(db)
        self.pill_manager = PillManager(db, config_manager)
        access_control = self.config.get("ACCESS_CONTROL", {})
        self.shop_manager_ids = {
            str(user_id)
            for user_id in access_control.get("SHOP_MANAGERS", [])
        }

    async def _ensure_pavilion_refreshed(self, pavilion_id: str, item_getter, count: int) -> None:
        """确保阁楼已刷新"""
        last_refresh_time, current_items = await self.db.get_shop_data(pavilion_id)
        if current_items:
            updated = self.shop_manager.ensure_items_have_stock(current_items)
            if updated:
                await self.db.update_shop_data(pavilion_id, last_refresh_time, current_items)
        refresh_hours = self.config.get("PAVILION_REFRESH_HOURS", 6)
        if not current_items or self.shop_manager.should_refresh_shop(last_refresh_time, refresh_hours):
            new_items = self.shop_manager.generate_pavilion_items(item_getter, count)
            await self.db.update_shop_data(pavilion_id, int(time.time()), new_items)

    async def handle_pill_pavilion(self, event: AstrMessageEvent):
        """处理丹阁命令 - 展示丹药列表"""
        count = self.config.get("PAVILION_PILL_COUNT", 10)
        await self._ensure_pavilion_refreshed("pill_pavilion", self.shop_manager.get_pills_for_display, count)
        last_refresh, items = await self.db.get_shop_data("pill_pavilion")
        if not items:
            yield event.plain_result("丹阁暂无丹药出售。")
            return
        refresh_hours = self.config.get("PAVILION_REFRESH_HOURS", 6)
        display = self.shop_manager.format_pavilion_display("丹阁", items, refresh_hours, last_refresh)
        yield event.plain_result(display)

    async def handle_weapon_pavilion(self, event: AstrMessageEvent):
        """处理器阁命令 - 展示武器列表"""
        count = self.config.get("PAVILION_WEAPON_COUNT", 10)
        await self._ensure_pavilion_refreshed("weapon_pavilion", self.shop_manager.get_weapons_for_display, count)
        last_refresh, items = await self.db.get_shop_data("weapon_pavilion")
        if not items:
            yield event.plain_result("器阁暂无武器出售。")
            return
        refresh_hours = self.config.get("PAVILION_REFRESH_HOURS", 6)
        display = self.shop_manager.format_pavilion_display("器阁", items, refresh_hours, last_refresh)
        yield event.plain_result(display)

    async def handle_treasure_pavilion(self, event: AstrMessageEvent):
        """处理百宝阁命令 - 展示所有物品"""
        count = self.config.get("PAVILION_TREASURE_COUNT", 15)
        await self._ensure_pavilion_refreshed("treasure_pavilion", self.shop_manager.get_all_items_for_display, count)
        last_refresh, items = await self.db.get_shop_data("treasure_pavilion")
        if not items:
            yield event.plain_result("百宝阁暂无物品出售。")
            return
        refresh_hours = self.config.get("PAVILION_REFRESH_HOURS", 6)
        display = self.shop_manager.format_pavilion_display("百宝阁", items, refresh_hours, last_refresh)
        yield event.plain_result(display)

    async def _find_item_in_pavilions(self, item_name: str):
        """在所有阁楼中查找物品"""
        for pavilion_id in ["pill_pavilion", "weapon_pavilion", "treasure_pavilion"]:
            _, items = await self.db.get_shop_data(pavilion_id)
            if items:
                for item in items:
                    if item['name'] == item_name and item.get('stock', 0) > 0:
                        return pavilion_id, item
        return None, None

    @player_required
    async def handle_buy(self, player: Player, event: AstrMessageEvent, item_name: str = ""):
        """处理购买物品命令"""
        if not item_name or item_name.strip() == "":
            yield event.plain_result("请指定要购买的物品名称，例如：购买 青铜剑")
            return

        # 兼容全角空格/数字与“x10”写法
        normalized = item_name.strip().replace("　", " ")
        normalized = normalized.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
        quantity = 1
        item_part = normalized

        def parse_qty(text: str):
            text = re.sub(r"\s+", " ", text)
            m = re.match(r"^(.*?)(?:\s+(\d+)|[xX＊*]\s*(\d+))$", text)
            if m:
                part = m.group(1).strip()
                qty_str = m.group(2) or m.group(3)
                return part, max(1, int(qty_str))
            return text.strip(), 1

        item_part, quantity = parse_qty(normalized)

        # 若指令解析只传入物品名（忽略数量），尝试从原始消息再解析一次
        if quantity == 1:
            try:
                raw_msg = event.get_message_str().strip()
                if raw_msg.startswith("购买"):
                    raw_msg = raw_msg[len("购买"):].strip()
                raw_msg = raw_msg.replace("　", " ")
                raw_msg = raw_msg.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
                item_part, quantity = parse_qty(raw_msg)
            except Exception:
                pass

        item_name = item_part

        pavilion_id, target_item = await self._find_item_in_pavilions(item_name)
        if not target_item:
            yield event.plain_result(f"没有找到【{item_name}】，请检查物品名称或等待刷新。")
            return

        stock = target_item.get('stock', 0)
        if quantity > stock:
            yield event.plain_result(f"【{item_name}】库存不足，当前库存: {stock}。")
            return

        price = target_item['price']
        total_price = price * quantity
        if player.gold < total_price:
            yield event.plain_result(
                f"灵石不足！\n【{target_item['name']}】价格: {price} 灵石\n"
                f"购买数量: {quantity}\n需要灵石: {total_price}\n你的灵石: {player.gold}"
            )
            return

        item_type = target_item['type']
        result_lines = []

        parsed_item = None
        if item_type in ['weapon', 'armor', 'main_technique', 'technique']:
            if quantity > 1:
                yield event.plain_result("装备类物品一次只能购买1件。")
                return
            parsed_item = self.equipment_manager.parse_item_from_name(
                target_item['name'], self.config_manager.items_data, self.config_manager.weapons_data
            )
            if not parsed_item:
                yield event.plain_result("装备信息不存在，无法完成购买。")
                return

        reserved, _, remaining = await self.db.decrement_shop_item_stock(pavilion_id, item_name, quantity)
        if not reserved:
            yield event.plain_result(f"【{item_name}】已售罄，请等待刷新。")
            return

        try:
            if item_type in ['weapon', 'armor', 'main_technique', 'technique']:
                success, message = await self.equipment_manager.equip_item(player, parsed_item)
                if not success:
                    await self.db.increment_shop_item_stock(pavilion_id, item_name, quantity)
                    yield event.plain_result(message)
                    return
                result_lines.append(message)
            elif item_type in ['pill', 'exp_pill', 'utility_pill']:
                await self.pill_manager.add_pill_to_inventory(player, target_item['name'], count=quantity)
                result_lines.append(f"成功购买【{target_item['name']}】x{quantity}，已添加到背包。")
            else:
                await self.db.increment_shop_item_stock(pavilion_id, item_name, quantity)
                yield event.plain_result(f"未知的物品类型：{item_type}")
                return

            player.gold -= total_price
            await self.db.update_player(player)
            result_lines.append(f"花费灵石: {total_price}，剩余: {player.gold}")
            result_lines.append(f"剩余库存: {remaining}" if remaining > 0 else "该物品已售罄！")
            yield event.plain_result("\n".join(result_lines))
        except Exception as e:
            await self.db.increment_shop_item_stock(pavilion_id, item_name, quantity)
            logger.error(f"购买异常: {e}")
            raise
