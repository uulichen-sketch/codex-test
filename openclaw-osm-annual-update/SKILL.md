---
name: openclaw-osm-annual-update
description: Parameterized OSM regional annual update analytics with full local outputs (changesets, feature edits, road-length metrics, and Mapbox bbox map). Use when analyzing a city/administrative region (e.g., Macau) for a target year and you need reproducible boundary resolution, resumable data collection, summary stats, and report-ready artifacts.
---

# OpenClaw Skill: OSM 区域年度更新统计（工具化 + 深内容下沉）

将重复、易出错的步骤优先通过 `scripts/` 工具化执行；将长文档与指标定义放在 `references/`，避免每次任务重复展开，降低 token 消耗。

## 输入参数

- `region_query`（如 `Macau`）
- `year`（如 `2025`）
- `timezone`（默认 `UTC`）
- `osm_api_base`（默认 `https://api.openstreetmap.org`）
- `nominatim_base`（默认 `https://nominatim.openstreetmap.org`）
- `overpass_base`（可选）
- `mapbox_token_env`（默认 `MAPBOX_ACCESS_TOKEN`）
- `mapbox_style`（默认 `mapbox/streets-v12`）
- `image_size`（默认 `1000x700`）
- `granularity`（默认 `month`）

## 快速执行（推荐）

优先运行一体化脚本：

```bash
python openclaw-osm-annual-update/scripts/run_pipeline.py \
  --region-query "Macau" \
  --year 2025 \
  --out-dir outputs
```

该脚本会：
1. 解析行政区候选与边界，写入 `meta/region.json`
2. 生成并保存 Mapbox bbox 叠加图 `figures/bbox_map.png`（若 token 可用）
3. 生成 `summary.json` 与 `monthly.csv` 骨架
4. 预建全量目录与日志文件

## 分步执行（按需）

如需精细控制，可调用子脚本：

1. 解析行政区与 bbox：
```bash
python openclaw-osm-annual-update/scripts/resolve_region.py \
  --region-query "Macau" --year 2025 --out-dir outputs
```

2. 生成 bbox 叠加图：
```bash
python openclaw-osm-annual-update/scripts/render_bbox_map.py \
  --region-json outputs/Macau/2025/meta/region.json \
  --out-png outputs/Macau/2025/figures/bbox_map.png
```

## 输出结构

固定输出到：`outputs/<region>/<year>/`

- `meta/region.json`
- `meta/capabilities.xml`（后续采集层可补）
- `raw/changesets.csv`
- `raw/changeset_download/`
- `stats/summary.json`
- `stats/monthly.csv`
- `figures/bbox_map.png`
- `logs/run.log`

## 实施约束

- 行政区解析必须保留候选列表与最终选择依据
- bbox 必须执行“服务返回 vs 几何自算”校验
- 统计口径必须写入 `summary.json`（含局限与风险）
- 若 Mapbox token 不可用，记录错误并继续产出其余文件

## 深度内容位置

详细指标定义、质量口径、实施细则，请按需加载：
- `references/metric_definitions.md`
- `references/data_collection_plan.md`
- `references/limitations_and_quality.md`

仅在需要解释/扩展时读取 reference，默认优先执行脚本并引用结果文件。
