# 本地文档检索

## 机制

`search_local_docs.py` 按以下顺序查找 OE 文档：

1. **环境变量** `OE_DROBOTICS_DOC_ROOT`（兼容旧名 `OE_X_SERIES_DOC_ROOT`）
   - 指向 OE Mapper 文档包根目录（如 `/opt/drobotics/oe_x5_doc`）
2. **工作区相对路径**：`.drobotics/docs/_sources/` 下的离线文档包
3. **包内文档**：`.drobotics/docs/offline-artifact-delivery.md` 等自带文档

## 设置环境变量

```bash
export OE_DROBOTICS_DOC_ROOT=/path/to/oe_x5_doc
```

## 未设置时的行为

脚本会尝试从 `.drobotics/` 目录结构中自动发现文档包。如果都找不到，返回空结果，Agent 会提示用户设置环境变量或下载文档包。
