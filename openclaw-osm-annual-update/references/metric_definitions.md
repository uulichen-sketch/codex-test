# Metric Definitions

## Changeset / 社区贡献
- `CS`: 年度窗口内且 bbox 命中的 changeset 数
- `CHG`: 命中 changeset 的 `changes_count` 总和（非独立要素数）
- `U`: 去重贡献者 uid 数
- `AU_10cs`: 年内 changeset >= 10 的贡献者数
- `AU_500chg`: 年内 changes_count >= 500 的贡献者数
- `EDITOR`（可选）: `created_by` 聚合
- `DISC`（可选）: changeset discussion 评论指标

## 要素更新（基于 changeset download）
- `FEAT_EDIT`: N/W/R × create/modify/delete
- `FEAT_EDIT_BY_TAG`:
  - roads: `way + highway=*`
  - buildings: `building=*`
  - pois: `amenity=*|shop=*|tourism=*`
  - landuse: `landuse=*`
  - water: `waterway=*|natural=water`
  - boundaries: `boundary=*`
- `UNIQUE_FEAT`（可选）: 按 `(type,id)` 去重

## 道路长度
推荐输出两套：
1. `ERL_raw`: create+modify 且 highway=* 的 way 长度总和（不去重）
2. `ERL_unique`: 同上但按 way_id 去重
3. `NRL`（可选）: create 且 highway=* 的 way 长度总和

不默认输出：`ΔRL`（需要历史版本几何，成本高）。
