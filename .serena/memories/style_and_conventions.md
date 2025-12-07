# 代码风格与约定
- 语言/风格：Python 异步为主（async def + yield 发送消息），dataclass 建模，类型注解较全，中文字符串与注释常见。
- 架构约定：入口 Star 类 XiuXianPlugin 负责注册命令常量、构造各 Handler/Manager，并实现白名单校验；具体业务分散在 handlers/core/data 层。
- 配置加载：ConfigManager 从插件目录下的 JSON 读取 level/items/weapons/pills 等数据，初始化在插件 __init__。
- 数据访问：DataBase 直接使用 aiosqlite，方法如 create_player/update_player/get_shop_data 等保证事务性；MigrationManager 通过 @migration 装饰器注册升级步骤，升级时 BEGIN/COMMIT/ROLLBACK 保障安全。
- 业务逻辑：Core 层计算灵根抽取、属性增量、闭关修炼收益、丹药/突破等；handlers 负责解析用户指令并 yield event.plain_result 文本。
- 命名/常量：命令关键字为中文常量（如 CMD_START_XIUXIAN="我要修仙"），装备/境界/灵根等字段保持拼音+英文混用；配置键遵循大写下划线（FILES/ACCESS_CONTROL）。
- 日志/提示：使用 astrbot.api.logger 记录，用户提示多为多行中文文本，保留表情符号与分隔线。