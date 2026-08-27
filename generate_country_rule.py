# -*- coding: utf-8 -*-
"""Country Header Rule 生成器。"""


def create_country_rule(
    country_code,
    country_name,
    header_name,
    behavior_name,
):
    """生成 Country-Name-XX 子规则。

    参数说明：

    country_code
        国家代码，例如：
        US / FR / DE

    country_name
        Header 中写入的国家名称。

    header_name
        由 --country-header 参数传入。

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
            "Country-Name-{}".format(
                country_code
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
                        country_name,

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
                        "IS",

                    "matchWildcard":
                        False,

                    "matchCaseSensitive":
                        False,

                    "variableName":
                        "PMUSER_GEO_COUNTRY",

                    "variableExpression":
                        country_code,
                },
            }

        ],

        "criteriaMustSatisfy":
            "all",

        "comments":
            "",
    }