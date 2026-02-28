#!/usr/bin/env python3
"""
数据库初始化脚本

创建数据库表并导入初始数据。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import init_db, drop_db
from database.connection import get_db_context
from database.models import Asset, AssetType, Strategy, RebalanceType
import json


def load_assets():
    """加载预设资产数据"""
    assets_file = project_root / "database" / "seeds" / "assets.json"

    if not assets_file.exists():
        print(f"资产数据文件不存在: {assets_file}")
        return []

    with open(assets_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assets = []
    for item in data:
        asset = Asset(
            code=item["code"],
            name=item["name"],
            type=AssetType(item["type"]),
            description=item.get("description"),
        )
        assets.append(asset)

    return assets


def load_strategies():
    """加载预设策略数据"""
    strategies_file = project_root / "database" / "seeds" / "strategies.json"

    if not strategies_file.exists():
        print(f"策略数据文件不存在: {strategies_file}")
        return []

    with open(strategies_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    strategies = []
    for item in data:
        strategy = Strategy(
            name=item["name"],
            description=item.get("description"),
            allocation=item["allocation"],
            rebalance_type=RebalanceType(item.get("rebalance_type", "monthly")),
            rebalance_threshold=item.get("rebalance_threshold"),
        )
        strategies.append(strategy)

    return strategies


def init_database():
    """初始化数据库"""
    print("正在初始化数据库...")

    # 删除旧表（如果存在）
    print("删除旧表...")
    drop_db()

    # 创建新表
    print("创建新表...")
    init_db()

    # 导入初始数据
    with get_db_context() as db:
        # 导入资产
        print("导入资产数据...")
        assets = load_assets()
        for asset in assets:
            db.add(asset)
        db.commit()
        print(f"已导入 {len(assets)} 个资产")

        # 导入策略
        print("导入策略数据...")
        strategies = load_strategies()
        for strategy in strategies:
            db.add(strategy)
        db.commit()
        print(f"已导入 {len(strategies)} 个策略")

    print("数据库初始化完成!")


if __name__ == "__main__":
    init_database()
