# Limitations and Quality Notes

## 必须说明的局限
1. changeset bbox 命中不等于要素全部在行政区内（可能跨界）
2. `changes_count` 非独立要素数
3. 道路长度依赖节点完整性，缺失会低估
4. Nominatim/Overpass 结果受服务状态影响，需保存 `osm_type/osm_id` 与元信息保证可复现

## 质量字段建议（summary.quality）
- `truncation_windows`: 命中上限并被二分的窗口
- `bbox_cross_border_risk_note`
- `api_errors`
- `retries`
- `partial_failures`

## 容错建议
- 429/5xx 指数退避
- 断点续跑（已下载 osc 不重复）
- node 坐标本地缓存（kv/sqlite）
