# -*- coding: utf-8 -*-
"""Akamai PAPI GET / PUT 封装。

不使用 Account Switching。
不包含 ACCOUNT_SWITCH_KEY。

配置通过 main.py 的 --config 参数从外部文件传入。
"""

import json

import requests
from akamai.edgegrid import EdgeGridAuth


class AkamaiAPI:
    """使用外部配置初始化 Akamai EdgeGrid API Session。"""

    def __init__(
        self,
        akamai_host,
        client_token,
        client_secret,
        access_token,
    ):

        self.akamai_host = str(
            akamai_host
        ).rstrip("/")

        self.session = requests.Session()

        self.session.auth = EdgeGridAuth(
            client_token=client_token,
            client_secret=client_secret,
            access_token=access_token,
        )

    # ========================================================
    # GET Rule Tree
    # ========================================================

    def get_rule_tree(
        self,
        property_id,
        version,
    ):
        """获取指定 Property Version 的 Rule Tree。"""

        url = (
            "{}/papi/v1/properties/"
            "{}/versions/{}/rules"
        ).format(
            self.akamai_host,
            property_id,
            version,
        )

        print("")
        print(
            "GET Akamai Rule Tree:"
        )

        print(url)

        response = self.session.get(
            url,
            headers={
                "Accept":
                    "application/json",
            },
            timeout=60,
        )

        print(
            "GET HTTP Status: {}".format(
                response.status_code
            )
        )

        if response.status_code >= 400:

            print("")
            print(
                "========================================"
            )

            print(
                "Akamai GET Error"
            )

            print(
                "========================================"
            )

            print(
                response.text
            )

            print(
                "========================================"
            )

            raise RuntimeError(
                "GET Rule Tree failed: HTTP {}".format(
                    response.status_code
                )
            )

        return response.json()

    # ========================================================
    # PUT Rule Tree
    # ========================================================

    def update_rule_tree(
        self,
        property_id,
        version,
        rules,
    ):
        """更新指定 Property Version 的 Rule Tree。"""

        url = (
            "{}/papi/v1/properties/"
            "{}/versions/{}/rules"
        ).format(
            self.akamai_host,
            property_id,
            version,
        )

        print("")
        print(
            "PUT Akamai Rule Tree:"
        )

        print(url)

        response = self.session.put(
            url,
            json=rules,
            headers={
                "Accept":
                    "application/json",

                "Content-Type":
                    "application/json",
            },
            timeout=120,
        )

        print(
            "PUT HTTP Status: {}".format(
                response.status_code
            )
        )

        if response.status_code >= 400:

            print("")
            print(
                "========================================"
            )

            print(
                "Akamai PUT Error"
            )

            print(
                "========================================"
            )

            print(
                response.text
            )

            print(
                "========================================"
            )

            raise RuntimeError(
                "PUT Rule Tree failed: HTTP {}".format(
                    response.status_code
                )
            )

        if not response.text.strip():

            return {
                "status":
                    response.status_code,
            }

        try:

            return response.json()

        except json.JSONDecodeError:

            return {
                "status":
                    response.status_code,

                "response":
                    response.text,
            }