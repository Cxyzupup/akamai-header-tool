# -*- coding: utf-8 -*-
"""Region Header Rule 生成器。"""


def create_region_rule(
    region_code,
    region_name,
    header_name,
    behavior_name,
):
    """生成 Region-Name-XX 子规则。

    参数说明：

    region_code
        Akamai EdgeScape Region Code。

    region_name
        Header 中写入的 Region Name。

    header_name
        由 --region-header 参数传入。

    behavior_name
        由 --header-target 转换得到：

        request
        ->
        modifyOutgoingRequestHeader

        response
        ->
        modifyOutgoingResponseHeader
    """

    return {

        "name":
            "Region-Name-{}".format(
                region_code
            ),

        "children":
            [],

        "behaviors": [

            {
                "name":
                    behavior_name,

                "options": {

                    "action":
                        "MODIFY",

                    "standardModifyHeaderName":
                        "OTHER",

                    "newHeaderValue":
                        region_name,

                    "avoidDuplicateHeaders":
                        True,

                    "customHeaderName":
                        header_name,
                },
            }

        ],

        "criteria": [

            {
                "name":
                    "matchVariable",

                "options": {

                    "matchOperator":
                        "IS_ONE_OF",

                    "matchWildcard":
                        False,

                    "matchCaseSensitive":
                        False,

                    "variableName":
                        "PMUSER_GEO_REGION",

                    "variableValues": [
                        region_code,
                    ],
                },
            }

        ],

        "criteriaMustSatisfy":
            "all",

        "comments":
            "",
    }