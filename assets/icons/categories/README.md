# Category Icons 分类图标说明

## 图标放置位置
所有AI模型分类的图标文件应放在此目录中：
```
D:\Code\快报填写程序\assets\icons\categories\
```

## 图标文件命名规则

根据模型的 `category` 字段，图标文件名应与category对应：

| 分类名称 | 文件名 | 示例模型 |
|---------|--------|---------|
| deepseek-ai | `deepseek-ai.png` | DeepSeek V3 |
| Qwen | `qwen.png` | Qwen2.5-7B-Instruct |
| BAAI | `baai.png` | bge-large-zh-v1.5 |
| Gemini | `gemini.png` | Gemini 2.5 Pro |
| GPT-4 | `gpt-4.png` | GPT-4 Turbo |
| GPT-3.5 | `gpt-3.5.png` | GPT-3.5 Turbo |
| 通用对话 | `通用对话.png` | 通用对话模型 |
| 默认图标 | `default.png` | (所有未指定的) |

## 图标规格要求

- **格式**: PNG (推荐) 或 JPG
- **尺寸**: 24×24 像素（建议使用更大的图片，程序会自动缩放）
- **背景**: 透明背景（PNG格式）
- **分辨率**: 至少 72 DPI
- **建议尺寸**: 48×48、64×64、128×128 像素（高分辨率设备显示更清晰）

## 使用示例

### 在模型配置中指定分类
```json
{
  "id": "deepseek-v3",
  "name": "DeepSeek V3",
  "category": "deepseek-ai",  // ← 对应文件名 deepseek-ai.png
  ...
}
```

### 程序自动加载路径
程序会按以下顺序查找图标：
1. `assets/icons/categories/{category字段值}.png` - 例如: `assets/icons/categories/deepseek-ai.png`
2. `assets/icons/categories/default.png` - 如果指定的图标不存在，使用默认图标
3. 灰色占位符 - 如果连default.png都不存在，显示纯色占位符

## 当前状态

✅ 目录已创建: `D:\Code\快报填写程序\assets\icons\categories\`
⏸️ 需要手动添加图标文件（见上述命名规则）

---

**最后更新**: 2025-10-06
