# Data Collection Plan

## Layer 0: capabilities
- 抓取 OSM API capabilities，落盘 `meta/capabilities.xml`

## Layer 1: changesets list
- 请求：`/api/0.6/changesets?bbox=...&from=...&to=...&order=newest&limit=100`
- 先按月/周请求；命中上限时自动二分窗口直到 `< limit`
- 落盘 `raw/changesets.csv` 与 `stats/monthly.csv`

## Layer 2: OsmChange download
- 每个 changeset 请求 `/api/0.6/changeset/{id}/download`
- 保存 `raw/changeset_download/{id}.osc.xml`
- 解析要素动作与主题分类

## Layer 3: road length
- 从 OsmChange 选取 highway ways（create+modify）
- 批量拉 nodes 坐标 `/api/0.6/nodes?nodes=...`
- 计算 ERL_raw / ERL_unique，记录缺失节点影响

## 可选增强：Overpass
- 统计区域存量（如 highway 总长度）
- 与年度编辑强度比值形成对照
