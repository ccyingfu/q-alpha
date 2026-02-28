"""
计算工具函数
"""

from typing import Dict


def validate_allocation(allocation: Dict[str, float]) -> bool:
    """
    验证资产配置权重总和是否为 1

    Args:
        allocation: 资产配置字典

    Returns:
        是否有效
    """
    total = sum(allocation.values())
    return abs(total - 1.0) < 0.01


def normalize_allocation(allocation: Dict[str, float]) -> Dict[str, float]:
    """
    标准化资产配置权重，使总和为 1

    Args:
        allocation: 资产配置字典

    Returns:
        标准化后的配置
    """
    total = sum(allocation.values())
    if total == 0:
        return allocation

    return {k: v / total for k, v in allocation.items()}
