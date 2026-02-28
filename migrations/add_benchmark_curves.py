"""
添加 benchmark_curves 字段到 backtest_results 表

运行此脚本添加新字段：
    python migrations/add_benchmark_curves.py
"""

import sqlite3
from pathlib import Path


def add_benchmark_curves_column():
    """添加 benchmark_curves 列"""
    db_path = Path(__file__).parent.parent / "q_alpha.db"

    if not db_path.exists():
        print(f"数据库文件不存在: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(backtest_results)")
        columns = [col[1] for col in cursor.fetchall()]

        if "benchmark_curves" in columns:
            print("benchmark_curves 列已存在，无需添加")
        else:
            # 添加列
            cursor.execute(
                "ALTER TABLE backtest_results ADD COLUMN benchmark_curves TEXT"
            )
            conn.commit()
            print("成功添加 benchmark_curves 列")

    except Exception as e:
        print(f"添加列失败: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    add_benchmark_curves_column()
