# core/breakthrough_manager.py

import random
from typing import Optional, Tuple
from astrbot.api import logger

from ..models import Player
from ..data import DataBase
from ..config_manager import ConfigManager


class BreakthroughManager:
    """突破管理器 - 处理境界突破相关逻辑"""

    def __init__(self, db: DataBase, config_manager: ConfigManager, config: dict):
        self.db = db
        self.config_manager = config_manager
        self.config = config

    def check_breakthrough_requirements(self, player: Player) -> Tuple[bool, str]:
        """检查玩家是否满足突破条件

        Args:
            player: 玩家对象

        Returns:
            (是否满足, 错误消息)
        """
        # 检查是否已经是最高境界
        if player.level_index >= len(self.config_manager.level_data) - 1:
            return False, "你已经达到了最高境界，无法继续突破！"

        # 获取下一境界所需修为
        next_level_index = player.level_index + 1
        next_level_data = self.config_manager.level_data[next_level_index]
        required_exp = next_level_data.get("exp_needed", 0)

        # 检查修为是否满足
        if player.experience < required_exp:
            current_level = self.config_manager.level_data[player.level_index]["level_name"]
            next_level = next_level_data["level_name"]
            return False, (
                f"修为不足！\n"
                f"当前境界：{current_level}\n"
                f"当前修为：{player.experience}\n"
                f"突破至【{next_level}】需要修为：{required_exp}"
            )

        return True, ""

    def calculate_breakthrough_success_rate(
        self,
        player: Player,
        pill_name: Optional[str] = None
    ) -> Tuple[float, str]:
        """计算突破成功率

        Args:
            player: 玩家对象
            pill_name: 使用的破境丹名称（可选）

        Returns:
            (成功率, 说明信息)
        """
        # 获取基础成功率
        next_level_index = player.level_index + 1
        next_level_data = self.config_manager.level_data[next_level_index]
        base_success_rate = next_level_data.get("success_rate", 0.5)

        info_lines = [
            f"基础成功率：{base_success_rate:.1%}"
        ]

        final_rate = base_success_rate
        max_rate = 1.0  # 默认最大100%

        # 如果使用了破境丹
        if pill_name:
            pill_data = self.config_manager.pills_data.get(pill_name)
            if pill_data and pill_data.get("subtype") == "breakthrough":
                breakthrough_bonus = pill_data.get("breakthrough_bonus", 0)
                max_rate = pill_data.get("max_success_rate", 1.0)

                # 计算加成后的成功率
                final_rate = min(base_success_rate + breakthrough_bonus, max_rate)

                info_lines.append(f"破境丹加成：+{breakthrough_bonus:.1%}")
                info_lines.append(f"最大成功率限制：{max_rate:.1%}")
            else:
                logger.warning(f"无效的破境丹：{pill_name}")

        info_lines.append(f"最终成功率：{final_rate:.1%}")
        info = "\n".join(info_lines)

        return final_rate, info

    async def execute_breakthrough(
        self,
        player: Player,
        pill_name: Optional[str] = None
    ) -> Tuple[bool, str, bool]:
        """执行突破

        Args:
            player: 玩家对象
            pill_name: 使用的破境丹名称（可选）

        Returns:
            (是否成功, 消息, 是否死亡)
        """
        # 检查突破条件
        can_breakthrough, error_msg = self.check_breakthrough_requirements(player)
        if not can_breakthrough:
            return False, error_msg, False

        # 计算成功率
        success_rate, rate_info = self.calculate_breakthrough_success_rate(player, pill_name)

        # 判定突破结果
        random_value = random.random()
        breakthrough_success = random_value < success_rate

        current_level_name = self.config_manager.level_data[player.level_index]["level_name"]
        next_level_index = player.level_index + 1
        next_level_data = self.config_manager.level_data[next_level_index]
        next_level_name = next_level_data["level_name"]

        if breakthrough_success:
            # 突破成功 - 提升境界并更新属性
            old_level_index = player.level_index
            player.level_index = next_level_index

            # 根据新旧境界的差值累加属性，避免覆盖原有数值
            current_level_data = self.config_manager.level_data[old_level_index]
            current_base_attack = current_level_data.get("base_attack", player.magic_damage)
            next_base_attack = next_level_data.get("base_attack", current_base_attack)
            attack_increase = max(0, next_base_attack - current_base_attack)

            current_base_defense = current_level_data.get("base_defense", player.magic_defense)
            next_base_defense = next_level_data.get("base_defense", current_base_defense)
            defense_increase = max(0, next_base_defense - current_base_defense)

            current_base_spiritual = current_level_data.get("base_spiritual_power", player.max_spiritual_qi)
            next_base_spiritual = next_level_data.get("base_spiritual_power", current_base_spiritual)
            spiritual_increase = max(0, next_base_spiritual - current_base_spiritual)

            current_base_mental = current_level_data.get("base_mental_power", player.mental_power)
            next_base_mental = next_level_data.get("base_mental_power", current_base_mental)
            mental_increase = max(0, next_base_mental - current_base_mental)

            player.magic_damage += attack_increase
            player.physical_damage += attack_increase
            player.magic_defense += defense_increase
            player.physical_defense += defense_increase
            player.max_spiritual_qi += spiritual_increase
            player.mental_power += mental_increase

            # 恢复满灵气
            player.spiritual_qi = player.max_spiritual_qi

            # 保存到数据库
            await self.db.update_player(player)

            success_msg = (
                f"✨ 突破成功！✨\n"
                f"━━━━━━━━━━━━━━━\n"
                f"{rate_info}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"恭喜你从【{current_level_name}】突破至【{next_level_name}】！\n"
                f"境界提升，实力大增！\n"
                f"气血上限：{player.max_spiritual_qi}\n"
                f"法伤：{player.magic_damage}\n"
                f"物伤：{player.physical_damage}\n"
                f"法防：{player.magic_defense}\n"
                f"物防：{player.physical_defense}\n"
                f"精神力：{player.mental_power}"
            )

            logger.info(
                f"玩家 {player.user_id} 突破成功：{current_level_name} -> {next_level_name}"
            )

            return True, success_msg, False

        else:
            # 突破失败 - 判断是否死亡
            death_probability_range = self.config.get("VALUES", {}).get(
                "BREAKTHROUGH_DEATH_PROBABILITY",
                [0.01, 0.1]  # 默认1%-10%死亡概率
            )

            # 随机一个死亡概率
            death_rate = random.uniform(death_probability_range[0], death_probability_range[1])
            died = random.random() < death_rate

            if died:
                # 玩家死亡 - 删除数据
                await self.db.delete_player(player.user_id)

                death_msg = (
                    f"💀 突破失败，走火入魔！💀\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"{rate_info}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"你在突破【{next_level_name}】时走火入魔，身死道消...\n"
                    f"所有修为和装备化为虚无\n"
                    f"若想重新修仙，请使用'入仙途'命令重新开始"
                )

                logger.info(
                    f"玩家 {player.user_id} 突破失败并死亡：{current_level_name} -> {next_level_name}，死亡概率 {death_rate:.2%}"
                )

                return False, death_msg, True

            else:
                # 突破失败但未死亡 - 扣除部分修为
                exp_penalty = int(player.experience * 0.1)  # 扣除10%修为
                player.experience = max(0, player.experience - exp_penalty)

                await self.db.update_player(player)

                fail_msg = (
                    f"❌ 突破失败 ❌\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"{rate_info}\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"突破【{next_level_name}】失败，但幸运地保住了性命\n"
                    f"修为受损，损失了 {exp_penalty} 点修为\n"
                    f"当前修为：{player.experience}\n"
                    f"请继续修炼，再接再厉！"
                )

                logger.info(
                    f"玩家 {player.user_id} 突破失败：{current_level_name} -> {next_level_name}，"
                    f"损失修为 {exp_penalty}"
                )

                return False, fail_msg, False
