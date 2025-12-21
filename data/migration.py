# data/migration.py

import aiosqlite
from typing import Dict, Callable, Awaitable
from astrbot.api import logger
from ..config_manager import ConfigManager

LATEST_DB_VERSION = 10  # 版本号提升 - 清理废弃字段

MIGRATION_TASKS: Dict[int, Callable[[aiosqlite.Connection, ConfigManager], Awaitable[None]]] = {}

def migration(version: int):
    """注册数据库迁移任务的装饰器"""
    def decorator(func: Callable[[aiosqlite.Connection, ConfigManager], Awaitable[None]]):
        MIGRATION_TASKS[version] = func
        return func
    return decorator

class MigrationManager:
    """数据库迁移管理器"""

    def __init__(self, conn: aiosqlite.Connection, config_manager: ConfigManager):
        self.conn = conn
        self.config_manager = config_manager

    async def migrate(self):
        await self.conn.execute("PRAGMA foreign_keys = ON")
        async with self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='db_info'") as cursor:
            if await cursor.fetchone() is None:
                logger.info("未检测到数据库版本，将进行全新安装...")
                await self.conn.execute("BEGIN")
                # 使用最新的建表函数
                await _create_all_tables_v2(self.conn)
                await self.conn.execute("INSERT INTO db_info (version) VALUES (?)", (LATEST_DB_VERSION,))
                await self.conn.commit()
                logger.info(f"数据库已初始化到最新版本: v{LATEST_DB_VERSION}")
                return

        async with self.conn.execute("SELECT version FROM db_info") as cursor:
            row = await cursor.fetchone()
            current_version = row[0] if row else 0

        logger.info(f"当前数据库版本: v{current_version}, 最新版本: v{LATEST_DB_VERSION}")
        if current_version < LATEST_DB_VERSION:
            logger.info("检测到数据库需要升级...")
            for version in sorted(MIGRATION_TASKS.keys()):
                if current_version < version:
                    logger.info(f"正在执行数据库升级: v{current_version} -> v{version} ...")
                    await self.conn.execute("BEGIN")
                    try:
                        await MIGRATION_TASKS[version](self.conn, self.config_manager)
                        await self.conn.execute("UPDATE db_info SET version = ?", (version,))
                        await self.conn.commit()
                        current_version = version
                        logger.info(f"数据库升级成功: v{version}")
                    except Exception as e:
                        await self.conn.rollback()
                        logger.error(f"数据库升级失败: v{version}. 错误: {str(e)}")
                        raise
            logger.info(f"数据库已升级到最新版本: v{LATEST_DB_VERSION}")
        else:
            logger.info("数据库已是最新版本，无需升级。")

async def _create_all_tables_v1(conn: aiosqlite.Connection):
    """创建所有表 - v1，只保留玩家基础信息"""

    # 数据库版本信息表
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS db_info (
            version INTEGER NOT NULL
        )
    """)

    # 玩家表 - 只保留基础属性
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id TEXT PRIMARY KEY,
            level_index INTEGER NOT NULL DEFAULT 0,
            spiritual_root TEXT NOT NULL DEFAULT '未知',
            experience INTEGER NOT NULL DEFAULT 0,
            gold INTEGER NOT NULL DEFAULT 0,
            state TEXT NOT NULL DEFAULT '空闲',
            hp INTEGER NOT NULL DEFAULT 100,
            max_hp INTEGER NOT NULL DEFAULT 100,
            attack INTEGER NOT NULL DEFAULT 10,
            defense INTEGER NOT NULL DEFAULT 5,
            spiritual_power INTEGER NOT NULL DEFAULT 50,
            mental_power INTEGER NOT NULL DEFAULT 50
        )
    """)

    # 创建索引
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_player_level ON players(level_index)")

    logger.info("数据库表已创建完成（v1）")

@migration(2)
async def _migrate_to_v2(conn: aiosqlite.Connection, config_manager: ConfigManager):
    """迁移到v2 - 新属性系统（灵修/体修）"""
    logger.info("开始迁移到v2：新属性系统")

    # 删除旧表并创建新表
    await conn.execute("DROP TABLE IF EXISTS players")
    await _create_all_tables_v2(conn)

    logger.info("v2迁移完成：新属性系统")

@migration(3)
async def _migrate_to_v3(conn: aiosqlite.Connection, config_manager: ConfigManager):
    """迁移到v3 - 添加闭关系统"""
    logger.info("开始迁移到v3：添加闭关系统")

    # 添加 cultivation_start_time 字段
    await conn.execute("ALTER TABLE players ADD COLUMN cultivation_start_time INTEGER NOT NULL DEFAULT 0")

    logger.info("v3迁移完成：闭关系统")

@migration(4)
async def _migrate_to_v4(conn: aiosqlite.Connection, config_manager: ConfigManager):
    """迁移到v4 - 添加签到系统"""
    logger.info("开始迁移到v4：添加签到系统")

    # 添加 last_check_in_date 字段
    await conn.execute("ALTER TABLE players ADD COLUMN last_check_in_date TEXT NOT NULL DEFAULT ''")

    logger.info("v4迁移完成：签到系统")

@migration(5)
async def _migrate_to_v5(conn: aiosqlite.Connection, config_manager: ConfigManager):
    """迁移到v5 - 添加装备系统"""
    logger.info("开始迁移到v5：添加装备系统")

    # 添加装备栏字段
    await conn.execute("ALTER TABLE players ADD COLUMN weapon TEXT NOT NULL DEFAULT ''")
    await conn.execute("ALTER TABLE players ADD COLUMN armor TEXT NOT NULL DEFAULT ''")
    await conn.execute("ALTER TABLE players ADD COLUMN main_technique TEXT NOT NULL DEFAULT ''")
    await conn.execute("ALTER TABLE players ADD COLUMN techniques TEXT NOT NULL DEFAULT '[]'")

    # 添加灵气容量字段
    await conn.execute("ALTER TABLE players ADD COLUMN max_spiritual_qi INTEGER NOT NULL DEFAULT 1000")

    logger.info("v5迁移完成：装备系统")

@migration(6)
async def _migrate_to_v6(conn: aiosqlite.Connection, config_manager: ConfigManager):
    """迁移到v6 - 添加丹药系统"""
    logger.info("开始迁移到v6：添加丹药系统")

    # 添加丹药系统相关字段
    await conn.execute("ALTER TABLE players ADD COLUMN active_pill_effects TEXT NOT NULL DEFAULT '[]'")
    await conn.execute("ALTER TABLE players ADD COLUMN permanent_pill_gains TEXT NOT NULL DEFAULT '{}'")
    await conn.execute("ALTER TABLE players ADD COLUMN has_resurrection_pill INTEGER NOT NULL DEFAULT 0")
    await conn.execute("ALTER TABLE players ADD COLUMN pills_inventory TEXT NOT NULL DEFAULT '{}'")

    logger.info("v6迁移完成：丹药系统")

@migration(7)
async def _migrate_to_v7(conn: aiosqlite.Connection, config_manager: ConfigManager):
    """迁移到v7 - 丹药系统扩展字段"""
    logger.info("开始迁移到v7：丹药系统扩展字段")

    await conn.execute("ALTER TABLE players ADD COLUMN has_debuff_shield INTEGER NOT NULL DEFAULT 0")

    logger.info("v7迁移完成：新增定魂丹护盾字段")

@migration(8)
async def _migrate_to_v8(conn: aiosqlite.Connection, config_manager: ConfigManager):
    """迁移到v8 - 添加商店系统"""
    logger.info("开始迁移到v8：添加商店系统")

    # 创建商店表
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS shop (
            shop_id TEXT PRIMARY KEY,
            last_refresh_time INTEGER NOT NULL DEFAULT 0,
            current_items TEXT NOT NULL DEFAULT '[]'
        )
    """)

    # 插入全局商店数据
    await conn.execute("""
        INSERT OR IGNORE INTO shop (shop_id, last_refresh_time, current_items)
        VALUES ('global', 0, '[]')
    """)

    logger.info("v8迁移完成：商店系统")

@migration(9)
async def _migrate_to_v9(conn: aiosqlite.Connection, config_manager: ConfigManager):
    """迁移到v9 - 添加体修气血系统"""
    logger.info("开始迁移到v9：添加体修气血系统")

    # 添加气血字段
    await conn.execute("ALTER TABLE players ADD COLUMN blood_qi INTEGER NOT NULL DEFAULT 0")
    await conn.execute("ALTER TABLE players ADD COLUMN max_blood_qi INTEGER NOT NULL DEFAULT 0")

    logger.info("v9迁移完成：体修气血系统")

@migration(10)
async def _migrate_to_v10(conn: aiosqlite.Connection, config_manager: ConfigManager):
    """迁移到v10 - 清理废弃字段（equipment_inventory等）"""
    logger.info("开始迁移到v10：清理废弃字段")

    # 获取当前表结构
    async with conn.execute("PRAGMA table_info(players)") as cursor:
        columns = {row[1] for row in await cursor.fetchall()}

    # 定义需要保留的字段（与 Player 模型一致）
    valid_columns = {
        'user_id', 'level_index', 'spiritual_root', 'cultivation_type', 'lifespan',
        'experience', 'gold', 'state', 'cultivation_start_time', 'last_check_in_date',
        'spiritual_qi', 'max_spiritual_qi', 'blood_qi', 'max_blood_qi',
        'magic_damage', 'physical_damage', 'magic_defense', 'physical_defense', 'mental_power',
        'weapon', 'armor', 'main_technique', 'techniques',
        'active_pill_effects', 'permanent_pill_gains', 'has_resurrection_pill', 'has_debuff_shield', 'pills_inventory'
    }

    # 找出需要删除的废弃字段
    deprecated_columns = columns - valid_columns
    if deprecated_columns:
        logger.info(f"发现废弃字段: {deprecated_columns}，将进行清理...")

        # 使用正确的表重建方式（保留约束）
        columns_to_keep = columns & valid_columns
        columns_str = ', '.join(columns_to_keep)

        # 1. 创建新表（带完整约束）
        await conn.execute("""
            CREATE TABLE players_new (
                user_id TEXT PRIMARY KEY,
                level_index INTEGER NOT NULL DEFAULT 0,
                spiritual_root TEXT NOT NULL DEFAULT '未知',
                cultivation_type TEXT NOT NULL DEFAULT '灵修',
                lifespan INTEGER NOT NULL DEFAULT 100,
                experience INTEGER NOT NULL DEFAULT 0,
                gold INTEGER NOT NULL DEFAULT 0,
                state TEXT NOT NULL DEFAULT '空闲',
                cultivation_start_time INTEGER NOT NULL DEFAULT 0,
                last_check_in_date TEXT NOT NULL DEFAULT '',
                spiritual_qi INTEGER NOT NULL DEFAULT 100,
                max_spiritual_qi INTEGER NOT NULL DEFAULT 1000,
                blood_qi INTEGER NOT NULL DEFAULT 0,
                max_blood_qi INTEGER NOT NULL DEFAULT 0,
                magic_damage INTEGER NOT NULL DEFAULT 10,
                physical_damage INTEGER NOT NULL DEFAULT 10,
                magic_defense INTEGER NOT NULL DEFAULT 5,
                physical_defense INTEGER NOT NULL DEFAULT 5,
                mental_power INTEGER NOT NULL DEFAULT 100,
                weapon TEXT NOT NULL DEFAULT '',
                armor TEXT NOT NULL DEFAULT '',
                main_technique TEXT NOT NULL DEFAULT '',
                techniques TEXT NOT NULL DEFAULT '[]',
                active_pill_effects TEXT NOT NULL DEFAULT '[]',
                permanent_pill_gains TEXT NOT NULL DEFAULT '{}',
                has_resurrection_pill INTEGER NOT NULL DEFAULT 0,
                has_debuff_shield INTEGER NOT NULL DEFAULT 0,
                pills_inventory TEXT NOT NULL DEFAULT '{}'
            )
        """)

        # 2. 复制数据
        await conn.execute(f"""
            INSERT INTO players_new ({columns_str})
            SELECT {columns_str} FROM players
        """)

        # 3. 删除旧表
        await conn.execute("DROP TABLE players")

        # 4. 重命名新表
        await conn.execute("ALTER TABLE players_new RENAME TO players")

        # 5. 重建索引
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_player_level ON players(level_index)")

        logger.info(f"已清理废弃字段: {deprecated_columns}")
    else:
        logger.info("没有发现废弃字段，跳过清理")

    logger.info("v10迁移完成：清理废弃字段")


async def _create_all_tables_v2(conn: aiosqlite.Connection):
    """创建所有表 - v2版本，新属性系统（灵修/体修）"""

    # 数据库版本信息表
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS db_info (
            version INTEGER NOT NULL
        )
    """)

    # 玩家表 - 新属性系统
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id TEXT PRIMARY KEY,
            level_index INTEGER NOT NULL DEFAULT 0,
            spiritual_root TEXT NOT NULL DEFAULT '未知',
            cultivation_type TEXT NOT NULL DEFAULT '灵修',
            lifespan INTEGER NOT NULL DEFAULT 100,
            experience INTEGER NOT NULL DEFAULT 0,
            gold INTEGER NOT NULL DEFAULT 0,
            state TEXT NOT NULL DEFAULT '空闲',
            cultivation_start_time INTEGER NOT NULL DEFAULT 0,
            last_check_in_date TEXT NOT NULL DEFAULT '',
            spiritual_qi INTEGER NOT NULL DEFAULT 100,
            max_spiritual_qi INTEGER NOT NULL DEFAULT 1000,
            blood_qi INTEGER NOT NULL DEFAULT 0,
            max_blood_qi INTEGER NOT NULL DEFAULT 0,
            magic_damage INTEGER NOT NULL DEFAULT 10,
            physical_damage INTEGER NOT NULL DEFAULT 10,
            magic_defense INTEGER NOT NULL DEFAULT 5,
            physical_defense INTEGER NOT NULL DEFAULT 5,
            mental_power INTEGER NOT NULL DEFAULT 100,
            weapon TEXT NOT NULL DEFAULT '',
            armor TEXT NOT NULL DEFAULT '',
            main_technique TEXT NOT NULL DEFAULT '',
            techniques TEXT NOT NULL DEFAULT '[]',
            active_pill_effects TEXT NOT NULL DEFAULT '[]',
            permanent_pill_gains TEXT NOT NULL DEFAULT '{}',
            has_resurrection_pill INTEGER NOT NULL DEFAULT 0,
            has_debuff_shield INTEGER NOT NULL DEFAULT 0,
            pills_inventory TEXT NOT NULL DEFAULT '{}'
        )
    """)

    # 创建索引
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_player_level ON players(level_index)")

    # 创建商店表
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS shop (
            shop_id TEXT PRIMARY KEY,
            last_refresh_time INTEGER NOT NULL DEFAULT 0,
            current_items TEXT NOT NULL DEFAULT '[]'
        )
    """)

    # 插入全局商店数据
    await conn.execute("""
        INSERT OR IGNORE INTO shop (shop_id, last_refresh_time, current_items)
        VALUES ('global', 0, '[]')
    """)

    logger.info("数据库表已创建完成（v2 - 新属性系统）")
