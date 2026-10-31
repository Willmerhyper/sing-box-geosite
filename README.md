# sing-box-geosite

在links.txt添加规则集，自动生成 sing-box Source Format。fork后自己添加想要转换的规则集。

仓库 Settings ----> Actions ----> General ----> Workflow permissions ----> Read and write permissions 勾选上

规则集源文件写法eg:

```json
{
  "tag": "geosite-wechat",
  "type": "remote",
  "format": "source",
  "url": "https://raw.githubusercontent.com/Toperlock/sing-box-geosite/main/wechat.json",
  "download_detour": "auto"
}
```

# 致谢（排名不分先后）

[@izumiChan16](https://github.com/izumiChan16)

[@ifaintad](https://github.com/ifaintad)

[@NobyDa](https://github.com/NobyDa)

[@blackmatrix7](https://github.com/blackmatrix7)

[@DivineEngine](https://github.com/DivineEngine)


## Anthropic / Claude 独立规则集

- 上游：[MetaCubeX/meta-rules-dat — anthropic](https://github.com/MetaCubeX/meta-rules-dat/blob/meta/geo/geosite/anthropic.yaml)
- 仅收录上游 Anthropic 分类的域名；不合并 OpenAI、其他 AI 服务或共享第三方服务域名。
- `links.txt` 已接入该源，沿用仓库 `Config Update` 工作流，每日同步并生成 Source JSON 和二进制 SRS。
- JSON：`https://raw.githubusercontent.com/Willmerhyper/sing-box-geosite/main/rule/anthropic.json`
- SRS：`https://raw.githubusercontent.com/Willmerhyper/sing-box-geosite/main/rule/anthropic.srs`

sing-box 配置示例（合并到现有 `route`，`proxy` 换成自己的出站分组名；专用规则应放在通用 AI 或兜底规则之前）：

```json
{
  "route": {
    "rule_set": [
      {
        "type": "remote",
        "tag": "geosite-anthropic",
        "format": "binary",
        "url": "https://raw.githubusercontent.com/Willmerhyper/sing-box-geosite/main/rule/anthropic.srs",
        "update_interval": "1d"
      }
    ],
    "rules": [
      { "rule_set": "geosite-anthropic", "outbound": "proxy" }
    ]
  }
}
```
