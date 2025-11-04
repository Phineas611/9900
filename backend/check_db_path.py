"""
快速检查数据库路径的脚本
在 Render Shell 中运行：python backend/check_db_path.py
"""
import os
from pathlib import Path

print("=" * 60)
print("数据库路径检查")
print("=" * 60)

# 检查环境变量
db_path_env = os.getenv("DATABASE_PATH")
print(f"\n1. 环境变量 DATABASE_PATH:")
if db_path_env:
    print(f"   ✓ 已设置: {db_path_env}")
    db_path = Path(db_path_env)
    if db_path.exists():
        size = db_path.stat().st_size
        print(f"   ✓ 文件存在，大小: {size:,} bytes")
    else:
        print(f"   ✗ 文件不存在！")
else:
    print(f"   ✗ 未设置！")
    print(f"   ⚠️  数据库将使用项目目录，会被重置！")

# 检查项目目录中的数据库
backend_dir = Path("backend")
project_db = backend_dir / "app.db"
print(f"\n2. 项目目录数据库 (backend/app.db):")
if project_db.exists():
    size = project_db.stat().st_size
    print(f"   ✓ 存在，大小: {size:,} bytes")
    print(f"   ⚠️  注意：这个路径在部署时会被重置！")
else:
    print(f"   ✗ 不存在")

# 检查 /data 目录
data_dir = Path("/data")
print(f"\n3. /data 目录:")
if data_dir.exists():
    print(f"   ✓ /data 目录存在")
    if data_dir.is_dir():
        items = list(data_dir.iterdir())
        print(f"   ✓ 是目录，包含 {len(items)} 个项目")
        for item in items[:5]:
            print(f"      - {item.name}")
    else:
        print(f"   ✗ /data 不是目录")
else:
    print(f"   ✗ /data 目录不存在")
    print(f"   ⚠️  持久化磁盘可能未正确挂载！")

# 检查实际使用的数据库路径
print(f"\n4. 代码将使用的数据库路径:")
if db_path_env:
    print(f"   {db_path_env}")
else:
    print(f"   {project_db}")
    print(f"   ⚠️  警告：未设置 DATABASE_PATH，数据会丢失！")

print("\n" + "=" * 60)
print("建议:")
if not db_path_env:
    print("⚠️  请在 Render Dashboard 设置环境变量:")
    print("   DATABASE_PATH=/data/app.db")
elif not Path(db_path_env).exists():
    print(f"⚠️  数据库文件不存在: {db_path_env}")
    print("   请确保持久化磁盘已正确挂载")
else:
    print("✓ 配置看起来正确")

