# 设计资产提取指南

> 本文件由 prd-reverse-writer 技能在提取 UI/CSS 设计资产时加载。
> 提供从各类前端技术栈中提取设计 token 的具体方法。

## 提取策略

### 优先级

按以下优先级查找设计 token 的定义位置：

1. **全局主题文件**（最高优先级）
   - `tailwind.config.js` / `tailwind.config.ts`
   - `theme.ts` / `theme.tsx` / `design-tokens.ts`
   - `variables.css` / `tokens.css` / `globals.css`
   - `styled-components` 的 ThemeProvider
   - `antd` / `element-plus` 的主题覆盖配置

2. **组件库配置**
   - `antd` 的 ConfigProvider token
   - `chakra-ui` 的 theme 对象
   - `MUI` 的 createTheme 配置
   - `vuetify` 的 theme 定义

3. **CSS 文件扫描**
   - 全局 CSS 变量（`--color-*`、`--font-*`、`--spacing-*`）
   - SCSS/Less 变量（`$color-*`、`@color-*`）
   - CSS-in-JS 的 theme 对象

4. **组件内联样式**（最低优先级，仅在前 3 层无信息时使用）
   - 从组件的 className 和 style 推断

### 色彩提取

**Tailwind CSS**：
```
读取 tailwind.config.js → theme.extend.colors
提取格式：{ name: hex_value }
```

**CSS 变量**：
```
搜索 --color-* 或 --*-color-* 的 :root 定义
提取格式：{ variable_name: hex_value }
```

**Ant Design / MUI 等**：
```
搜索 theme 覆盖配置中的 colorPrimary / palette 定义
提取实际色值
```

**提取时注意**：
- 区分亮色/暗色模式（如有 dark mode）
- 记录色值的语义角色（primary、success、warning、error）而非仅记录色值本身
- 如果色值引用了 CSS 变量（如 `var(--primary)`），追溯到变量的实际值

### 字体提取

关注以下信息：
- font-family（主字体、备选字体链）
- font-size 层级（h1-h6、body、caption、button）
- font-weight 使用情况
- line-height 规范

**提取位置**：
- Tailwind: `theme.fontSize` 和 `theme.fontFamily`
- CSS: `font-size`、`font-family` 在 `:root` 或 `body` 上的定义
- 组件库主题: `typography` 相关配置

### 间距提取

**Tailwind CSS**：
```
默认 spacing scale（0, px, 0.5, 1, 1.5, 2, ...）
检查 theme.extend.spacing 是否有自定义
```

**CSS 变量**：
```
搜索 --spacing-* 或 --space-* 定义
```

**提取时注意**：
- 记录基础单元（如 4px 或 8px）
- 记录常用的间距组合（如 padding: 16px 24px）

### 组件清单提取

**统计方法**：
1. 扫描所有 import 语句，统计组件导入频率
2. 区分来源：自定义组件 vs 第三方库组件
3. 按使用频率排序，取 Top 20

**自定义组件额外信息**：
- 文件路径
- 是否有 Storybook story（如有，说明是设计规范组件）
- Props 接口定义（TypeScript 的 interface/type）

### 动效提取

搜索以下关键词：
- `transition` CSS 属性
- `animation` / `@keyframes`
- `framer-motion` 的 motion 组件
- `react-spring` 的配置
- Tailwind 的 `transition-*` 和 `duration-*` 类

提取格式：
```
{
  场景描述: "...",
  时长: "200ms",
  缓动函数: "ease-in-out",
  属性: "transform, opacity",
  代码位置: "src/components/Modal.tsx:45"
}
```

## 提取结果验证

提取完成后，做以下快速验证：
1. 色值是否都是合法的 HEX/RGB 值？
2. 字号是否合理（不小于 10px，不大于 72px）？
3. 间距是否遵循某个基础单元的倍数？
4. 组件清单中是否有重复项（同一组件不同命名）？

如果发现问题，在报告中标注"（待验证）"。
