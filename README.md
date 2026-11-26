# sing-box-geosite

在links.txt添加规则集，自动生成 sing-box Source Format。fork后自己添加想要转换的规则集。

只写 URL 时，输出文件名仍取链接里的文件名。多行写成 `名称=URL`，或 `名称=仓库内相对路径` 时，同名来源会去重合并成一个规则集（`rule/<名称>.json` 和 `.srs`）。

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
- Claude 登录在本地配置里还会用到 `withpersona.com`、`hcaptcha.com`、`challenges.cloudflare.com`。这三条都不在上游 Anthropic 分类里；后两条还是共享基础设施。上游里的 Datadog / Sentry 只是 Anthropic 自己的具体主机，不是 `datadoghq.com` 或 `sentry.io` 这种共享后缀。仓库没有单独的本地附加规则集，所以这三条不并入 `rule/anthropic`。
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

## 国内应用直连 `cn-app-direct`

银行、支付、证券、政务、铁路和运营商应用的域名合并为一份规则集，在 sing-box 里把这些域名的 DNS 和出站都走直连。

来源：

- MetaCubeX `category-bank-cn`、`category-securities-cn`。`category-bank-cn` 不含中信子列表，另外合并 [citic.yaml](https://github.com/MetaCubeX/meta-rules-dat/blob/meta/geo/geosite/citic.yaml)。
- blackmatrix7 Clash 列表：支付宝、云闪付、工行、农行、中行、建行、招行、交行、邮储、光大、广发、平安、东方财富、政务、12306、移动、联通、电信。
- 仓库内手工列表 `source/cn-app-direct-extra.list`：微信支付（`tenpay.com`、`pay.weixin.qq.com`、`payapp.weixin.qq.com`），以及运营商地址 `113.200.56.63/32`、`117.161.2.5/32`。中信域名已由上面的 `citic.yaml` 覆盖。
- 同一份手工列表还包括畅享云 / 宁波 InterSky（`intersky.com.cn`、包名 `com.intersky.InterSkyForeignTrade`、阿里云地址 `8.136.7.91/32`）。`geoip-cn` 目前不包含 `8.136.0.0/16`，这里只收这一条 `/32`，不扩成整段。
- 阿里云中国大陆 HTTPDNS 用精确域名 `httpdns.aliyuncs.com` 和 `resolvers-cn.httpdns.aliyuncs.com`。这是共享服务，不是 InterSky 专有。不用后缀，避免把 `resolvers-hk`、`resolvers-sg`、`resolvers-us`、`resolvers-de` 一起收进来。
- 个人直连后缀 `hyperchem.vip`、`myds.me`、`medkoo.com`、`labgogo.com`、`nxonearth.com` 也写在这份手工列表里。仓库没有单独的 personal-direct 规则集。

`links.txt` 里这些行都写成 `cn-app-direct=来源`，由 `Config Update` 工作流每天和其他规则集一起重新拉取、去重并编译。

- JSON：`https://raw.githubusercontent.com/Willmerhyper/sing-box-geosite/main/rule/cn-app-direct.json`
- SRS：`https://raw.githubusercontent.com/Willmerhyper/sing-box-geosite/main/rule/cn-app-direct.srs`

sing-box 配置示例（`direct` 换成自己的直连出站；DNS 规则指向直连 DNS。这条规则应放在代理兜底之前）：

```json
{
  "dns": {
    "rules": [
      { "rule_set": "geosite-cn-app-direct", "server": "direct-dns" }
    ]
  },
  "route": {
    "rule_set": [
      {
        "type": "remote",
        "tag": "geosite-cn-app-direct",
        "format": "binary",
        "url": "https://raw.githubusercontent.com/Willmerhyper/sing-box-geosite/main/rule/cn-app-direct.srs",
        "update_interval": "1d"
      }
    ],
    "rules": [
      { "rule_set": "geosite-cn-app-direct", "outbound": "direct" }
    ]
  }
}
```

## Canva `canva`

独立规则集，避免 `canva.cn` 和 `canvasite.cn` 被放进国内直连。来源是仓库内 `source/canva.list`，不包含 `amazonaws.com`，也不包含 Affinity / Serif 域名。

正在使用的 sing-box 配置把这组规则固定到 `🇺🇸 美国`，而不是直连，也不是 `geosite-geolocation-!cn` / Proxies。`sing-box-subscribe` 的生成模板还要单独加一条路由，把本规则集发到 `🇺🇸 美国`，并且放在 `geosite-cn` 之前。本仓库不改那个模板。

`links.txt` 写成 `canva=source/canva.list`，由 `Config Update` 每天和其他规则集一起编译。

- JSON：`https://raw.githubusercontent.com/Willmerhyper/sing-box-geosite/main/rule/canva.json`
- SRS：`https://raw.githubusercontent.com/Willmerhyper/sing-box-geosite/main/rule/canva.srs`

```json
{
  "route": {
    "rule_set": [
      {
        "type": "remote",
        "tag": "geosite-canva",
        "format": "binary",
        "url": "https://raw.githubusercontent.com/Willmerhyper/sing-box-geosite/main/rule/canva.srs",
        "update_interval": "1d"
      }
    ],
    "rules": [
      { "rule_set": "geosite-canva", "outbound": "🇺🇸 美国" }
    ]
  }
}
```
