# data/data_manager.py

import aiosqlite
from pathlib import Path
from ..models import Player

class DataBase:
    """数据库管理类，提供基础玩家操作"""

    def __init__(self, db_file: str = "xiuxian_data_lite.db"):
        self.db_path = Path(db_file)
        self.conn: aiosqlite.Connection = None

    async def connect(self):
        """连接数据库"""
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row

    async def close(self):
        """关闭数据库连接"""
        if self.conn:
            await self.conn.close()

    async def create_player(self, player: Player):
        """创建新玩家"""
        await self.conn.execute(
            """
            INSERT INTO players (
                user_id, level_index, spiritual_root, cultivation_type, lifespan,
                experience, gold, state, cultivation_start_time, last_check_in_date,
                spiritual_qi, max_spiritual_qi, magic_damage, physical_damage,
                magic_defense, physical_defense, mental_power,
                weapon, armor, main_technique, techniques
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                player.user_id,
                player.level_index,
                player.spiritual_root,
                player.cultivation_type,
                player.lifespan,
                player.experience,
                player.gold,
                player.state,
                player.cultivation_start_time,
                player.last_check_in_date,
                player.spiritual_qi,
                player.max_spiritual_qi,
                player.magic_damage,
                player.physical_damage,
                player.magic_defense,
                player.physical_defense,
                player.mental_power,
                player.weapon,
                player.armor,
                player.main_technique,
                player.techniques
            )
        )
        await self.conn.commit()

    async def get_player_by_id(self, user_id: str) -> Player:
        """根据用户ID获取玩家信息"""
        async with self.conn.execute(
            "SELECT * FROM players WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Player(**dict(row))
            return None

    async def update_player(self, player: Player):
        """更新玩家信息"""
        await self.conn.execute(
            """
            UPDATE players SET
                level_index = ?,
                spiritual_root = ?,
                cultivation_type = ?,
                lifespan = ?,
                experience = ?,
                gold = ?,
                state = ?,
                cultivation_start_time = ?,
                last_check_in_date = ?,
                spiritual_qi = ?,
                max_spiritual_qi = ?,
                magic_damage = ?,
                physical_damage = ?,
                magic_defense = ?,
                physical_defense = ?,
                mental_power = ?,
                weapon = ?,
                armor = ?,
                main_technique = ?,
                techniques = ?
            WHERE user_id = ?
            """,
            (
                player.level_index,
                player.spiritual_root,
                player.cultivation_type,
                player.lifespan,
                player.experience,
                player.gold,
                player.state,
                player.cultivation_start_time,
                player.last_check_in_date,
                player.spiritual_qi,
                player.max_spiritual_qi,
                player.magic_damage,
                player.physical_damage,
                player.magic_defense,
                player.physical_defense,
                player.mental_power,
                player.weapon,
                player.armor,
                player.main_technique,
                player.techniques,
                player.user_id
            )
        )
        await self.conn.commit()

    async def delete_player(self, user_id: str):
        """删除玩家"""
        await self.conn.execute(
            "DELETE FROM players WHERE user_id = ?",
            (user_id,)
        )
        await self.conn.commit()

    async def get_all_players(self):
        """获取所有玩家"""
        async with self.conn.execute("SELECT * FROM players") as cursor:
            rows = await cursor.fetchall()
            return [Player(**dict(row)) for row in rows]
