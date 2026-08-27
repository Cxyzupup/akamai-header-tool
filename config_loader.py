# -*- coding: utf-8 -*-
"""外部配置文件读取模块。

支持：

1. config.py
   推荐，保持原项目习惯。
   只读取简单字符串赋值，不执行 Python 代码。

2. config.json
   可选兼容。
"""

import ast
import json
from pathlib import Path
from typing import Dict


# ============================================================
# 配置文件必须包含的字段
# ============================================================

REQUIRED_CONFIG_KEYS = (
    "AKAMAI_HOST",
    "PROPERTY_ID",
    "CONTRACT_ID",
    "GROUP_ID",
    "CLIENT_TOKEN",
    "CLIENT_SECRET",
    "ACCESS_TOKEN",
)


# ============================================================
# 校验配置
# ============================================================

def _validate_config(
    config: Dict[str, str],
    config_path: Path,
) -> Dict[str, str]:
    """校验配置文件必须包含的字段。"""

    missing = []

    for key in REQUIRED_CONFIG_KEYS:

        value = config.get(
            key
        )

        if (
            value is None
            or
            not str(value).strip()
        ):

            missing.append(
                key
            )

    if missing:

        raise ValueError(
            "配置文件 {} 缺少必填项：{}".format(
                config_path,
                ", ".join(
                    missing
                ),
            )
        )

    normalized = {}

    for key in REQUIRED_CONFIG_KEYS:

        normalized[
            key
        ] = str(
            config[
                key
            ]
        ).strip()

    return normalized


# ============================================================
# 读取 config.py
# ============================================================

def _load_python_config(
    config_path: Path,
) -> Dict[str, str]:
    """安全读取 config.py 中的简单变量赋值。

    注意：
    不执行 config.py 中的 Python 代码。
    """

    source = config_path.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source,
        filename=str(
            config_path
        ),
    )

    config = {}

    for node in tree.body:

        if not isinstance(
            node,
            ast.Assign
        ):
            continue

        if len(
            node.targets
        ) != 1:
            continue

        target = node.targets[
            0
        ]

        if not isinstance(
            target,
            ast.Name
        ):
            continue

        key = target.id

        if key not in REQUIRED_CONFIG_KEYS:

            # 其他变量不会被工具使用。
            continue

        try:

            value = ast.literal_eval(
                node.value
            )

        except (
            ValueError,
            TypeError,
            SyntaxError,
        ):

            raise ValueError(
                "配置项 {} 必须是字符串常量。".format(
                    key
                )
            )

        config[
            key
        ] = value

    return _validate_config(
        config,
        config_path,
    )


# ============================================================
# 读取 config.json
# ============================================================

def _load_json_config(
    config_path: Path,
) -> Dict[str, str]:
    """读取 JSON 格式配置文件。"""

    with config_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        config = json.load(
            file
        )

    if not isinstance(
        config,
        dict
    ):

        raise ValueError(
            "config.json 最外层必须是 JSON 对象。"
        )

    return _validate_config(
        config,
        config_path,
    )


# ============================================================
# 对外入口
# ============================================================

def load_config(
    path: str,
) -> Dict[str, str]:
    """根据文件扩展名读取外部配置。"""

    config_path = Path(
        path
    ).expanduser().resolve()

    if not config_path.exists():

        raise FileNotFoundError(
            "没有找到配置文件：{}".format(
                config_path
            )
        )

    if (
        config_path.suffix.lower()
        ==
        ".json"
    ):

        return _load_json_config(
            config_path
        )

    # 其他扩展名默认按照 config.py 格式读取。
    return _load_python_config(
        config_path
    )