查看完整帮助：

  akamai-header-tool --help
========================================

用法： akamai-header-tool [-h] --config 配置文件 --region-mapping REGION映射文件 --property-version 版本号 --country-header 国家HEADER名称 --region-header 地区HEADER名称 --header-target 写入方向 [--dry-run] [--backup 备份文件] [--output 输出文件]

Akamai Header 创建工具

功能：
根据 region_mapping.json 中定义的国家和 Region，
自动在固定父规则：

  SET Header(Country-Name&Country-Region-Name)

下面创建 Country / Region Header 规则。

注意：
只有 region_mapping.json 中存在的国家才会进行配置。

可选参数：
  -h, --help            显示本帮助信息并退出。
  --config 配置文件         Akamai 配置文件路径。

                        支持：
                          config.py
                          config.json

                        配置文件必须包含：
                          AKAMAI_HOST
                          PROPERTY_ID
                          CONTRACT_ID
                          GROUP_ID
                          CLIENT_TOKEN
                          CLIENT_SECRET
                          ACCESS_TOKEN

                        示例：
                          --config ./config.py
  --region-mapping REGION映射文件
                        Region Mapping JSON 文件路径。

                        该文件决定需要创建哪些国家和 Region 规则。

                        只有 JSON 中存在的国家才会创建 Country Rule。

                        例如 JSON 中只有：
                          US
                          CA
                          FR

                        则程序只会生成：
                          Country-Name-US
                          Country-Name-CA
                          Country-Name-FR

                        示例：
                          --region-mapping ./region_mapping.json
  --property-version 版本号
                        需要读取并修改的 Akamai Property Version。

                        该参数不会从 config.py 中读取。

                        例如 Property Version 为 16：
                          --property-version 16
  --country-header 国家HEADER名称
                        Country Header 名称。

                        程序会把识别到的国家名称写入该 Header。

                        例如：
                          CloudFront-Viewer-Country-Name

                        使用方式：
                          --country-header CloudFront-Viewer-Country-Name
  --region-header 地区HEADER名称
                        Region Header 名称。

                        程序会把识别到的 Region 名称写入该 Header。

                        例如：
                          CloudFront-Viewer-Country-Region-Name

                        使用方式：
                          --region-header CloudFront-Viewer-Country-Region-Name
  --header-target 写入方向  指定 Header 写入方向。

                        允许值：

                          request
                            对应：modifyOutgoingRequestHeader
                            Header 会发送给源站。
                            建议正式生产环境使用。

                          response
                            对应：modifyOutgoingResponseHeader
                            Header 会返回客户端。
                            适合使用 curl -I 测试。

                        示例：
                          --header-target response
  --dry-run             测试模式，不执行 Akamai PUT。

                        启用后程序仍然会：
                          1. 读取配置
                          2. 读取 Region Mapping
                          3. 生成 Country / Region Rule
                          4. GET Akamai Rule Tree
                          5. 保存原始备份
                          6. 生成新的 Rule Tree JSON

                        但不会修改 Akamai Property。

                        建议第一次使用时先启用。
  --backup 备份文件         指定原始 Akamai Rule Tree 的备份文件路径。

                        默认：
                          backup_before_update.json

                        示例：
                          --backup ./backup_v16.json
  --output 输出文件         指定新生成 Rule Tree 的 JSON 文件路径。

                        默认：
                          rule_tree_after_update.json

                        示例：
                          --output ./rule_tree_v16.json
