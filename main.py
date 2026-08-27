# -*- coding: utf-8 -*-

"""
Akamai Country / Region Header 创建工具

固定父规则：

    SET Header(Country-Name&Country-Region-Name)

工具功能：

1. 通过 --config 读取 Akamai API / Property 配置
2. 通过 --region-mapping 指定要创建规则的国家和 Region
3. 通过 --property-version 指定要修改的 Property Version
4. 通过 --country-header 自定义 Country Header 名称
5. 通过 --region-header 自定义 Region Header 名称
6. 通过 --header-target 控制：
       request  -> Modify Outgoing Request Header
       response -> Modify Outgoing Response Header
7. 支持 --dry-run，只生成 JSON，不 PUT 到 Akamai
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pycountry

from akamai_api import AkamaiAPI
from config_loader import load_config
from generate_country_rule import create_country_rule
from generate_region_rule import create_region_rule


# ============================================================
# Windows / Linux / macOS 终端 UTF-8 输出支持
# ============================================================

def configure_console_encoding():
    """
    将标准输出 stdout 和错误输出 stderr 尽量设置为 UTF-8。

    主要解决 Windows 环境下中文输出时出现：

        UnicodeEncodeError:
        'charmap' codec can't encode characters

    GitHub Actions Windows Runner、
    Windows PowerShell、CMD 等环境默认编码可能不是 UTF-8。

    errors="replace" 可以保证极端情况下，
    程序不会因为打印中文而直接崩溃。
    """

    # --------------------------------------------------------
    # stdout
    # --------------------------------------------------------

    try:

        if hasattr(
            sys.stdout,
            "reconfigure"
        ):

            sys.stdout.reconfigure(
                encoding="utf-8",
                errors="replace"
            )

    except Exception:
        pass

    # --------------------------------------------------------
    # stderr
    # --------------------------------------------------------

    try:

        if hasattr(
            sys.stderr,
            "reconfigure"
        ):

            sys.stderr.reconfigure(
                encoding="utf-8",
                errors="replace"
            )

    except Exception:
        pass


# ============================================================
# 必须在 argparse 输出帮助之前执行
# ============================================================

configure_console_encoding()


# ============================================================
# 固定父规则名称
# ============================================================

TARGET_RULE_NAME = "SET Header(Country-Name&Country-Region-Name)"


# ============================================================
# 自定义中文 ArgumentParser
# ============================================================

class ChineseArgumentParser(argparse.ArgumentParser):
    """
    自定义 argparse。

    主要作用：

    1. 常见参数错误改为中文
    2. usage 改为“用法”
    3. options 改为“参数说明”
    """

    def format_help(self):
        """
        将 argparse 默认生成的部分英文标题替换成中文。
        """

        help_text = super().format_help()

        help_text = help_text.replace(
            "usage:",
            "用法："
        )

        help_text = help_text.replace(
            "options:",
            "参数说明："
        )

        help_text = help_text.replace(
            "optional arguments:",
            "可选参数："
        )

        help_text = help_text.replace(
            "positional arguments:",
            "位置参数："
        )

        return help_text

    def error(self, message):
        """
        参数错误时输出中文提示。

        常见情况：

        1. 缺少必填参数
        2. 参数不存在
        3. 参数值不合法
        4. integer 类型错误
        """

        chinese_message = message

        # ====================================================
        # 缺少必填参数
        # ====================================================

        required_prefix = (
            "the following arguments are required:"
        )

        if message.startswith(
            required_prefix
        ):

            missing_args = message[
                len(required_prefix):
            ].strip()

            chinese_message = (
                "缺少以下必填参数：\n\n"
                "  {}".format(
                    missing_args
                )
            )

        # ====================================================
        # 未识别参数
        # ====================================================

        elif message.startswith(
            "unrecognized arguments:"
        ):

            unknown_args = message.replace(
                "unrecognized arguments:",
                "",
                1
            ).strip()

            chinese_message = (
                "存在无法识别的参数：\n\n"
                "  {}".format(
                    unknown_args
                )
            )

        # ====================================================
        # choice 参数错误
        # ====================================================

        elif "invalid choice:" in message:

            chinese_message = (
                "参数值不正确。\n\n"
                "{}\n\n"
                "--header-target 只允许：\n"
                "  request\n"
                "  response"
            ).format(
                message
            )

        # ====================================================
        # Integer 参数错误
        # ====================================================

        elif "invalid int value:" in message:

            chinese_message = (
                "参数值必须是整数。\n\n"
                "{}\n\n"
                "例如：\n"
                "  --property-version 16"
            ).format(
                message
            )

        # ====================================================
        # 参数缺少值
        # ====================================================

        elif "expected one argument" in message:

            chinese_message = (
                "参数后面缺少对应的值。\n\n"
                "{}"
            ).format(
                message
            )

        # ====================================================
        # 输出中文错误
        # ====================================================

        print("")
        print(
            "========================================"
        )
        print(
            "参数错误"
        )
        print(
            "========================================"
        )

        print(
            chinese_message
        )

        print("")
        print(
            "请检查启动参数。"
        )

        print("")
        print(
            "查看完整帮助："
        )

        print("")
        print(
            "  akamai-header-tool --help"
        )

        print(
            "========================================"
        )
        print("")

        self.print_help()

        self.exit(
            2
        )


# ============================================================
# 命令行参数
# ============================================================

def parse_args():
    """
    解析命令行参数。

    所有参数都增加中文说明。
    """

    parser = ChineseArgumentParser(

        prog="akamai-header-tool",

        description=(
            "Akamai Header 创建工具\n"
            "\n"
            "功能：\n"
            "根据 region_mapping.json 中定义的国家和 Region，\n"
            "自动在固定父规则：\n"
            "\n"
            "  SET Header(Country-Name&Country-Region-Name)\n"
            "\n"
            "下面创建 Country / Region Header 规则。\n"
            "\n"
            "注意：\n"
            "只有 region_mapping.json 中存在的国家才会进行配置。"
        ),

        formatter_class=argparse.RawTextHelpFormatter,

        add_help=False,

        epilog=(
            "\n"
            "------------------------------------------------------------\n"
            "示例 1：测试模式，不更新 Akamai\n"
            "------------------------------------------------------------\n"
            "\n"
            "akamai-header-tool \\\n"
            "  --config ./config.py \\\n"
            "  --region-mapping ./region_mapping.json \\\n"
            "  --property-version 16 \\\n"
            "  --country-header CloudFront-Viewer-Country-Name \\\n"
            "  --region-header CloudFront-Viewer-Country-Region-Name \\\n"
            "  --header-target response \\\n"
            "  --dry-run\n"
            "\n"
            "------------------------------------------------------------\n"
            "示例 2：正式写入 Outgoing Request Header\n"
            "------------------------------------------------------------\n"
            "\n"
            "akamai-header-tool \\\n"
            "  --config ./config.py \\\n"
            "  --region-mapping ./region_mapping.json \\\n"
            "  --property-version 16 \\\n"
            "  --country-header CloudFront-Viewer-Country-Name \\\n"
            "  --region-header CloudFront-Viewer-Country-Region-Name \\\n"
            "  --header-target request\n"
        ),
    )

    # ========================================================
    # Help
    # ========================================================

    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help=(
            "显示本帮助信息并退出。"
        )
    )

    # ========================================================
    # Config
    # ========================================================

    parser.add_argument(
        "--config",
        required=True,
        metavar="配置文件",
        help=(
            "Akamai 配置文件路径。\n"
            "\n"
            "支持：\n"
            "  config.py\n"
            "  config.json\n"
            "\n"
            "配置文件必须包含：\n"
            "  AKAMAI_HOST\n"
            "  PROPERTY_ID\n"
            "  CONTRACT_ID\n"
            "  GROUP_ID\n"
            "  CLIENT_TOKEN\n"
            "  CLIENT_SECRET\n"
            "  ACCESS_TOKEN\n"
            "\n"
            "示例：\n"
            "  --config ./config.py"
        )
    )

    # ========================================================
    # Region Mapping
    # ========================================================

    parser.add_argument(
        "--region-mapping",
        required=True,
        metavar="REGION映射文件",
        help=(
            "Region Mapping JSON 文件路径。\n"
            "\n"
            "该文件决定需要创建哪些国家和 Region 规则。\n"
            "\n"
            "只有 JSON 中存在的国家才会创建 Country Rule。\n"
            "\n"
            "例如 JSON 中只有：\n"
            "  US\n"
            "  CA\n"
            "  FR\n"
            "\n"
            "则程序只会生成：\n"
            "  Country-Name-US\n"
            "  Country-Name-CA\n"
            "  Country-Name-FR\n"
            "\n"
            "示例：\n"
            "  --region-mapping ./region_mapping.json"
        )
    )

    # ========================================================
    # Property Version
    # ========================================================

    parser.add_argument(
        "--property-version",
        required=True,
        type=int,
        metavar="版本号",
        help=(
            "需要读取并修改的 Akamai Property Version。\n"
            "\n"
            "该参数不会从 config.py 中读取。\n"
            "\n"
            "例如 Property Version 为 16：\n"
            "  --property-version 16"
        )
    )

    # ========================================================
    # Country Header
    # ========================================================

    parser.add_argument(
        "--country-header",
        required=True,
        metavar="国家HEADER名称",
        help=(
            "Country Header 名称。\n"
            "\n"
            "程序会把识别到的国家名称写入该 Header。\n"
            "\n"
            "例如：\n"
            "  CloudFront-Viewer-Country-Name\n"
            "\n"
            "使用方式：\n"
            "  --country-header CloudFront-Viewer-Country-Name"
        )
    )

    # ========================================================
    # Region Header
    # ========================================================

    parser.add_argument(
        "--region-header",
        required=True,
        metavar="地区HEADER名称",
        help=(
            "Region Header 名称。\n"
            "\n"
            "程序会把识别到的 Region 名称写入该 Header。\n"
            "\n"
            "例如：\n"
            "  CloudFront-Viewer-Country-Region-Name\n"
            "\n"
            "使用方式：\n"
            "  --region-header CloudFront-Viewer-Country-Region-Name"
        )
    )

    # ========================================================
    # Header Target
    # ========================================================

    parser.add_argument(
        "--header-target",
        required=True,
        choices=(
            "request",
            "response"
        ),
        metavar="写入方向",
        help=(
            "指定 Header 写入方向。\n"
            "\n"
            "允许值：\n"
            "\n"
            "  request\n"
            "    对应：modifyOutgoingRequestHeader\n"
            "    Header 会发送给源站。\n"
            "    建议正式生产环境使用。\n"
            "\n"
            "  response\n"
            "    对应：modifyOutgoingResponseHeader\n"
            "    Header 会返回客户端。\n"
            "    适合使用 curl -I 测试。\n"
            "\n"
            "示例：\n"
            "  --header-target response"
        )
    )

    # ========================================================
    # Dry Run
    # ========================================================

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "测试模式，不执行 Akamai PUT。\n"
            "\n"
            "启用后程序仍然会：\n"
            "  1. 读取配置\n"
            "  2. 读取 Region Mapping\n"
            "  3. 生成 Country / Region Rule\n"
            "  4. GET Akamai Rule Tree\n"
            "  5. 保存原始备份\n"
            "  6. 生成新的 Rule Tree JSON\n"
            "\n"
            "但不会修改 Akamai Property。\n"
            "\n"
            "建议第一次使用时先启用。"
        )
    )

    # ========================================================
    # Backup
    # ========================================================

    parser.add_argument(
        "--backup",
        default="backup_before_update.json",
        metavar="备份文件",
        help=(
            "指定原始 Akamai Rule Tree 的备份文件路径。\n"
            "\n"
            "默认：\n"
            "  backup_before_update.json\n"
            "\n"
            "示例：\n"
            "  --backup ./backup_v16.json"
        )
    )

    # ========================================================
    # Output
    # ========================================================

    parser.add_argument(
        "--output",
        default="rule_tree_after_update.json",
        metavar="输出文件",
        help=(
            "指定新生成 Rule Tree 的 JSON 文件路径。\n"
            "\n"
            "默认：\n"
            "  rule_tree_after_update.json\n"
            "\n"
            "示例：\n"
            "  --output ./rule_tree_v16.json"
        )
    )

    return parser.parse_args()


# ============================================================
# Header Target -> Akamai Behavior
# ============================================================

def get_behavior_name(
    header_target: str
) -> str:
    """
    根据用户参数生成 Akamai Behavior 名称。

    request：
        modifyOutgoingRequestHeader

    response：
        modifyOutgoingResponseHeader
    """

    if header_target == "request":

        return (
            "modifyOutgoingRequestHeader"
        )

    return (
        "modifyOutgoingResponseHeader"
    )


# ============================================================
# CloudFront 风格 Percent-Encoding
# ============================================================

def cloudfront_encode(
    text: str
) -> str:
    """
    将非 ASCII 字符按照 UTF-8 做 Percent-Encoding。

    ASCII 字符保持原样。
    """

    if text is None:
        return ""

    text = str(
        text
    ).strip()

    result = []

    for char in text:

        if ord(char) < 128:

            result.append(
                char
            )

            continue

        utf8_bytes = char.encode(
            "utf-8"
        )

        for byte in utf8_bytes:

            result.append(
                "%{:02X}".format(
                    byte
                )
            )

    return "".join(
        result
    )


# ============================================================
# 查找目标父规则
# ============================================================

def find_target_rule(
    rule: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    递归查找固定父规则：

    SET Header(Country-Name&Country-Region-Name)

    查找时名称不区分大小写。
    """

    rule_name = str(
        rule.get(
            "name",
            ""
        )
    ).strip().lower()

    target_name = (
        TARGET_RULE_NAME
        .strip()
        .lower()
    )

    if rule_name == target_name:

        return rule

    children = rule.get(
        "children",
        []
    )

    if not isinstance(
        children,
        list
    ):

        return None

    for child in children:

        if not isinstance(
            child,
            dict
        ):

            continue

        result = find_target_rule(
            child
        )

        if result is not None:

            return result

    return None


# ============================================================
# 加载 Region Mapping
# ============================================================

def load_region_mapping(
    mapping_path: str
) -> Dict[str, List[Dict[str, str]]]:
    """
    读取外部 region_mapping.json。

    国家配置范围完全由该文件决定。
    """

    region_mapping_file = Path(
        mapping_path
    ).expanduser().resolve()

    if not region_mapping_file.exists():

        raise FileNotFoundError(
            "没有找到 Region Mapping 文件：\n"
            "{}".format(
                region_mapping_file
            )
        )

    with region_mapping_file.open(
        "r",
        encoding="utf-8"
    ) as file:

        mapping = json.load(
            file
        )

    if not isinstance(
        mapping,
        dict
    ):

        raise ValueError(
            "region_mapping.json 最外层必须是 JSON 对象。"
        )

    normalized_mapping: Dict[
        str,
        List[Dict[str, str]]
    ] = {}

    total_regions = 0

    for country_code, regions in mapping.items():

        normalized_country_code = str(
            country_code
        ).strip().upper()

        if not normalized_country_code:

            raise ValueError(
                "region_mapping.json 中存在空的国家代码。"
            )

        if not isinstance(
            regions,
            list
        ):

            raise ValueError(
                "{} 对应的 Region 数据必须是数组。".format(
                    normalized_country_code
                )
            )

        normalized_regions: List[
            Dict[str, str]
        ] = []

        for region in regions:

            if not isinstance(
                region,
                dict
            ):

                raise ValueError(
                    "{} 中存在无效 Region：{}".format(
                        normalized_country_code,
                        region
                    )
                )

            region_code = str(
                region.get(
                    "code",
                    ""
                )
            ).strip()

            region_name = str(
                region.get(
                    "name",
                    ""
                )
            ).strip()

            if not region_code:

                raise ValueError(
                    "{} 中存在缺少 code 的 Region：{}".format(
                        normalized_country_code,
                        region
                    )
                )

            if not region_name:

                raise ValueError(
                    "{} 中存在缺少 name 的 Region：{}".format(
                        normalized_country_code,
                        region
                    )
                )

            normalized_regions.append(
                {
                    "code":
                        region_code,

                    "name":
                        region_name
                }
            )

            total_regions += 1

        normalized_mapping[
            normalized_country_code
        ] = normalized_regions

    print("")
    print(
        "========================================"
    )
    print(
        "Region Mapping 信息"
    )
    print(
        "========================================"
    )

    print(
        "Region Mapping 文件："
    )

    print(
        "  {}".format(
            region_mapping_file
        )
    )

    print("")

    print(
        "配置国家数量：{}".format(
            len(
                normalized_mapping
            )
        )
    )

    print(
        "Region 记录数量：{}".format(
            total_regions
        )
    )

    print(
        "========================================"
    )

    return normalized_mapping


# ============================================================
# 生成 Country / Region Rules
# ============================================================

def build_country_rules(
    region_mapping: Dict[
        str,
        List[Dict[str, str]]
    ],
    country_header: str,
    region_header: str,
    behavior_name: str
) -> List[Dict[str, Any]]:
    """
    只根据 region_mapping.json 中存在的国家创建规则。
    """

    country_rules: List[
        Dict[str, Any]
    ] = []

    generated_region_count = 0

    encoded_country_count = 0

    encoded_region_count = 0

    country_codes = sorted(
        region_mapping.keys()
    )

    print("")
    print(
        "========================================"
    )
    print(
        "开始生成 Country / Region Rules"
    )
    print(
        "========================================"
    )

    print(
        "需要配置的国家数量：{}".format(
            len(
                country_codes
            )
        )
    )

    print("")

    for country_code in country_codes:

        country_code = str(
            country_code
        ).strip().upper()

        country = pycountry.countries.get(
            alpha_2=country_code
        )

        if country is None:

            raise ValueError(
                "region_mapping.json 中的国家代码 "
                "{} 无法在 pycountry 中找到。".format(
                    country_code
                )
            )

        original_country_name = str(
            country.name
        ).strip()

        country_name = cloudfront_encode(
            original_country_name
        )

        if (
            original_country_name
            !=
            country_name
        ):

            encoded_country_count += 1

        country_rule = create_country_rule(
            country_code=country_code,
            country_name=country_name,
            header_name=country_header,
            behavior_name=behavior_name
        )

        if "children" not in country_rule:

            country_rule[
                "children"
            ] = []

        if not isinstance(
            country_rule[
                "children"
            ],
            list
        ):

            raise ValueError(
                "Country Rule {} 的 children 不是数组。".format(
                    country_code
                )
            )

        regions = region_mapping.get(
            country_code,
            []
        )

        print(
            "{} {} -> {} 个 Region".format(
                country_code,
                original_country_name,
                len(
                    regions
                )
            )
        )

        for region in regions:

            region_code = str(
                region[
                    "code"
                ]
            ).strip()

            original_region_name = str(
                region[
                    "name"
                ]
            ).strip()

            region_name = cloudfront_encode(
                original_region_name
            )

            if (
                original_region_name
                !=
                region_name
            ):

                encoded_region_count += 1

            region_rule = create_region_rule(
                region_code=region_code,
                region_name=region_name,
                header_name=region_header,
                behavior_name=behavior_name
            )

            country_rule[
                "children"
            ].append(
                region_rule
            )

            generated_region_count += 1

        country_rules.append(
            country_rule
        )

    print("")
    print(
        "========================================"
    )
    print(
        "规则生成统计"
    )
    print(
        "========================================"
    )

    print(
        "Country Rule 数量：{}".format(
            len(
                country_rules
            )
        )
    )

    print(
        "Region Rule 数量：{}".format(
            generated_region_count
        )
    )

    print(
        "国家名称编码数量：{}".format(
            encoded_country_count
        )
    )

    print(
        "Region 名称编码数量：{}".format(
            encoded_region_count
        )
    )

    print(
        "========================================"
    )

    return country_rules


# ============================================================
# 替换 Country Rules
# ============================================================

def replace_country_rules(
    rule_tree: Dict[str, Any],
    country_rules: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    找到固定父规则：

        SET Header(Country-Name&Country-Region-Name)

    删除该父规则下现有：

        Country-Name-*

    然后添加新生成的 Country Rules。
    """

    rules_root = rule_tree.get(
        "rules"
    )

    if not isinstance(
        rules_root,
        dict
    ):

        raise ValueError(
            "PAPI 返回内容中不存在有效的 rules 对象。"
        )

    target_rule = find_target_rule(
        rules_root
    )

    if target_rule is None:

        raise RuntimeError(
            "没有找到目标父规则：\n"
            "{}".format(
                TARGET_RULE_NAME
            )
        )

    existing_children = target_rule.get(
        "children",
        []
    )

    if not isinstance(
        existing_children,
        list
    ):

        raise ValueError(
            "目标父规则的 children 不是数组。"
        )

    preserved_children: List[
        Dict[str, Any]
    ] = []

    for child in existing_children:

        if not isinstance(
            child,
            dict
        ):

            continue

        child_name = str(
            child.get(
                "name",
                ""
            )
        )

        if child_name.startswith(
            "Country-Name-"
        ):

            continue

        preserved_children.append(
            child
        )

    removed_count = (
        len(
            existing_children
        )
        -
        len(
            preserved_children
        )
    )

    target_rule[
        "children"
    ] = (
        preserved_children
        +
        country_rules
    )

    print("")
    print(
        "========================================"
    )
    print(
        "父规则更新信息"
    )
    print(
        "========================================"
    )

    print(
        "目标父规则："
    )

    print(
        "  {}".format(
            TARGET_RULE_NAME
        )
    )

    print(
        "删除旧 Country Rule：{}".format(
            removed_count
        )
    )

    print(
        "新增 Country Rule：{}".format(
            len(
                country_rules
            )
        )
    )

    print(
        "========================================"
    )

    return rule_tree


# ============================================================
# 保存 JSON
# ============================================================

def save_json(
    path: str,
    data: Dict[str, Any]
) -> Path:
    """
    将 JSON 保存到指定文件。

    如果目录不存在，会自动创建。
    """

    output_path = Path(
        path
    ).expanduser().resolve()

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    return output_path


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """
    主程序入口。
    """

    args = parse_args()

    try:

        # ====================================================
        # 1. 读取配置
        # ====================================================

        print("")
        print(
            "[1/7] 读取 Akamai 配置..."
        )

        config = load_config(
            args.config
        )

        # ====================================================
        # 2. 读取 Region Mapping
        # ====================================================

        print("")
        print(
            "[2/7] 读取 Region Mapping..."
        )

        region_mapping = load_region_mapping(
            args.region_mapping
        )

        # ====================================================
        # Header Target
        # ====================================================

        behavior_name = get_behavior_name(
            args.header_target
        )

        property_id = config[
            "PROPERTY_ID"
        ]

        # ====================================================
        # 初始化 API
        # ====================================================

        api = AkamaiAPI(

            akamai_host=config[
                "AKAMAI_HOST"
            ],

            client_token=config[
                "CLIENT_TOKEN"
            ],

            client_secret=config[
                "CLIENT_SECRET"
            ],

            access_token=config[
                "ACCESS_TOKEN"
            ]
        )

        # ====================================================
        # 当前执行信息
        # ====================================================

        print("")
        print(
            "========================================"
        )
        print(
            "Akamai Header 创建工具"
        )
        print(
            "========================================"
        )

        print(
            "Property ID：{}".format(
                property_id
            )
        )

        print(
            "Property Version：{}".format(
                args.property_version
            )
        )

        print(
            "Contract ID：{}".format(
                config[
                    "CONTRACT_ID"
                ]
            )
        )

        print(
            "Group ID：{}".format(
                config[
                    "GROUP_ID"
                ]
            )
        )

        print(
            "父规则：{}".format(
                TARGET_RULE_NAME
            )
        )

        print(
            "Country Header：{}".format(
                args.country_header
            )
        )

        print(
            "Region Header：{}".format(
                args.region_header
            )
        )

        print(
            "Header 写入方向：{}".format(
                args.header_target
            )
        )

        print(
            "Akamai Behavior：{}".format(
                behavior_name
            )
        )

        print(
            "配置国家数量：{}".format(
                len(
                    region_mapping
                )
            )
        )

        print(
            "Dry Run：{}".format(
                "是"
                if args.dry_run
                else "否"
            )
        )

        print(
            "========================================"
        )

        # ====================================================
        # 3. 生成规则
        # ====================================================

        print("")
        print(
            "[3/7] 生成 Country / Region Rules..."
        )

        country_rules = build_country_rules(

            region_mapping=region_mapping,

            country_header=args.country_header,

            region_header=args.region_header,

            behavior_name=behavior_name
        )

        # ====================================================
        # 4. GET Akamai Rule Tree
        # ====================================================

        print("")
        print(
            "[4/7] 获取 Akamai Property Rule Tree..."
        )

        rule_tree = api.get_rule_tree(
            property_id,
            args.property_version
        )

        print(
            "获取 Rule Tree 成功。"
        )

        # ====================================================
        # 5. Backup
        # ====================================================

        print("")
        print(
            "[5/7] 备份原始 Rule Tree..."
        )

        backup_path = save_json(
            args.backup,
            rule_tree
        )

        print(
            "备份文件：{}".format(
                backup_path
            )
        )

        # ====================================================
        # 6. 替换 Country Rules
        # ====================================================

        print("")
        print(
            "[6/7] 更新本地 Rule Tree..."
        )

        new_rule_tree = replace_country_rules(
            rule_tree,
            country_rules
        )

        output_path = save_json(
            args.output,
            new_rule_tree
        )

        print(
            "生成文件：{}".format(
                output_path
            )
        )

        # ====================================================
        # Dry Run
        # ====================================================

        if args.dry_run:

            print("")
            print(
                "========================================"
            )
            print(
                "DRY RUN 执行完成"
            )
            print(
                "========================================"
            )

            print(
                "本次没有执行 Akamai PUT。"
            )

            print(
                "请检查生成文件："
            )

            print(
                "  {}".format(
                    output_path
                )
            )

            print(
                "确认规则正确后，删除 --dry-run 参数重新执行。"
            )

            print(
                "========================================"
            )

            return

        # ====================================================
        # 7. PUT Akamai
        # ====================================================

        print("")
        print(
            "[7/7] 更新 Akamai Property..."
        )

        result = api.update_rule_tree(
            property_id,
            args.property_version,
            new_rule_tree
        )

        print("")
        print(
            "========================================"
        )
        print(
            "Akamai Property 更新成功"
        )
        print(
            "========================================"
        )

        print(
            json.dumps(
                result,
                indent=4,
                ensure_ascii=False
            )
        )

        print(
            "========================================"
        )

    # ========================================================
    # Ctrl+C
    # ========================================================

    except KeyboardInterrupt:

        print("")
        print(
            "========================================"
        )
        print(
            "用户取消执行。"
        )
        print(
            "========================================"
        )

        sys.exit(
            130
        )

    # ========================================================
    # 其他错误
    # ========================================================

    except Exception as error:

        print("")
        print(
            "========================================"
        )
        print(
            "执行失败"
        )
        print(
            "========================================"
        )

        print(
            str(
                error
            )
        )

        print(
            "========================================"
        )

        sys.exit(
            1
        )


# ============================================================
# 程序入口
# ============================================================

if __name__ == "__main__":
    main()
