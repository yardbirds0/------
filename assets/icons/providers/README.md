# Provider Icons 图标说明

## 图标放置位置
所有AI服务商的图标文件应放在此目录中：
```
D:\Code\快报填写程序\assets\icons\providers\
```

## 图标文件命名规则

根据 `config/ai_models.json` 中的provider配置，图标文件名应与provider的 `icon` 字段对应：

| 服务商 | 文件名 | Provider ID |
|--------|--------|-------------|
| Google | `google.png` | google |
| OpenAI | `openai.png` | openai |
| 硅基流动 | `siliconflow.png` | siliconflow |
| Anthropic | `anthropic.png` | anthropic |
| 豆包 | `doubao.png` | doubao |
| 默认图标 | `default.png` | (所有未指定的) |

## 图标规格要求

- **格式**: PNG (推荐) 或 JPG
- **尺寸**: 24×24 像素（建议使用更大的图片，程序会自动缩放）
- **背景**: 透明背景（PNG格式）
- **分辨率**: 至少 72 DPI
- **建议尺寸**: 48×48、64×64、128×128 像素（高分辨率设备显示更清晰）

## 使用示例

### 在 ai_models.json 中配置
```json
{
  "id": "google",
  "name": "Google",
  "icon": "google.png",  // ← 对应文件名
  ...
}
```

### 程序自动加载路径
程序会按以下顺序查找图标：
1. `assets/icons/providers/{icon字段值}` - 例如: `assets/icons/providers/google.png`
2. `assets/icons/providers/default.png` - 如果指定的图标不存在，使用默认图标
3. 灰色占位符 - 如果连default.png都不存在，显示纯色占位符

## 准备图标文件

### 方法1: 使用官方Logo
访问各服务商官网下载官方Logo：
- Google AI: https://ai.google.dev/
- OpenAI: https://platform.openai.com/
- 硅基流动: https://siliconflow.cn/
- Anthropic: https://www.anthropic.com/
- 豆包: https://www.volcengine.com/product/doubao

### 方法2: 在线图标库
- Iconify: https://icon-sets.iconify.design/
- Flaticon: https://www.flaticon.com/
- Icons8: https://icons8.com/

### 方法3: 自己设计
使用Figma、Sketch、Photoshop等工具设计24×24px的图标

## 注意事项

1. **文件权限**: 确保图标文件可读
2. **文件编码**: 使用标准PNG/JPG格式
3. **命名规则**: 严格按照ai_models.json中的icon字段命名
4. **大小写**: Windows文件系统不区分大小写，但建议使用小写
5. **缓存**: 修改图标后重启程序才能看到效果

## 当前状态

✅ 目录已创建: `D:\Code\快报填写程序\assets\icons\providers\`
⏸️ 需要手动添加图标文件（见上述命名规则）

---

**最后更新**: 2025-10-06
