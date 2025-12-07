# 项目概览
- 目的：AstrBot 插件“文字修仙”（模拟修仙），提供文字版修仙养成玩法（角色、境界、闭关、装备、突破、商店等）。
- 技术栈：Python 3.8+、AstrBot 框架、aiosqlite（SQLite 异步）、async/await；dataclass 数据模型；JSON 配置驱动。
- 主要架构：入口层 main.py（注册插件、命令路由与白名单）；handlers 层（player/equipment/breakthrough/pill/shop/misc）；core 层（CultivationManager 等业务算法）；data 层（DataBase + MigrationManager 处理 SQLite 与版本升级）；config 层（level/items/weapons/pills/bosses/tags 等配置 JSON）。
- 数据库：SQLite，迁移版本最新 LATEST_DB_VERSION=8，装饰器方式注册 MIGRATION_TASKS，缺表时自动创建并写入 db_info。
- 关键模型：models.py 的 Player/Item 使用 @dataclass；支持装备栏（武器、防具、心法/功法），灵根与属性累加。
- 插件元信息：metadata.yaml（name=模拟修仙，version=v1.0.0dev，repo=https://github.com/linjianyan0229/astrbot_plugin_monixiuxian）。
- 游戏指令：见 README（修仙帮助/我要修仙/闭关/出关/签到/装备/突破/商店等）。