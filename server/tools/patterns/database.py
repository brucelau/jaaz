"""
Pattern database for air-mold design.
移植自 PneumatCraft/src/patterns/database.py
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
import json


@dataclass
class StylePattern:
    """风格 Pattern"""
    colors: list[str] = field(default_factory=list)
    composition: list[str] = field(default_factory=list)
    lighting: list[str] = field(default_factory=list)
    description: str = ""
    keywords: list[str] = field(default_factory=list)


@dataclass
class ProductPattern:
    """产品 Pattern"""
    structure: list[str] = field(default_factory=list)
    material: list[str] = field(default_factory=list)
    details: list[str] = field(default_factory=list)
    composition: list[str] = field(default_factory=list)
    description: str = ""
    keywords: list[str] = field(default_factory=list)


@dataclass
class ColorPattern:
    """颜色 Pattern"""
    palette: list[str] = field(default_factory=list)
    matching: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class PatternDatabase:
    """Pattern 数据库"""
    styles: Dict[str, StylePattern] = field(default_factory=dict)
    products: Dict[str, ProductPattern] = field(default_factory=dict)
    colors: Dict[str, ColorPattern] = field(default_factory=dict)
    photography: Dict[str, Any] = field(default_factory=dict)
    materials: Dict[str, Any] = field(default_factory=dict)
    lighting: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, path: Path) -> "PatternDatabase":
        """从 JSON 文件加载"""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        styles = {
            name: StylePattern(**values)
            for name, values in data.get("styles", {}).items()
        }

        products = {
            name: ProductPattern(**values)
            for name, values in data.get("products", {}).items()
        }

        colors = {
            name: ColorPattern(**values)
            for name, values in data.get("colors", {}).items()
        }

        return cls(
            styles=styles,
            products=products,
            colors=colors,
            photography=data.get("photography", {}),
            materials=data.get("materials", {}),
            lighting=data.get("lighting", {}),
        )


_default_db: Optional[PatternDatabase] = None


def get_pattern_database() -> PatternDatabase:
    """获取默认 Pattern 数据库"""
    global _default_db
    if _default_db is None:
        default_path = Path(__file__).parent / "design_patterns.json"
        _default_db = PatternDatabase.from_json(default_path)
    return _default_db


def load_pattern_database(path: Optional[Path] = None) -> PatternDatabase:
    """加载指定路径的 Pattern 数据库"""
    if path is None:
        return get_pattern_database()
    return PatternDatabase.from_json(path)