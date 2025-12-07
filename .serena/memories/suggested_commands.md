# 常用命令（Windows PowerShell）
- 创建虚拟环境（可选）：`python -m venv .venv` 然后 `./.venv/Scripts/Activate.ps1`
- 安装依赖（仓库无 requirements.txt，需要按需）：`pip install astrbot aiosqlite`
- 本地静态检查（无专用脚本，可手动）：`python -m compileall .` 或使用 `python -m pip check`
- 运行方式：本插件需在 AstrBot 主程序中加载，放入插件目录后启动 AstrBot（如 `astrbot run`，具体以主程序命令为准）。
- 数据库位置：默认 `FILES.DATABASE_FILE` 配置为 `xiuxian_data_lite.db`，可在 AstrBot 配置中调整。