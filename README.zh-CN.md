# BlenderLorama

<img src="./logo.png" width="50%" alt="Blender-Aseprite Bridge Logo">

[简体中文](README.zh-CN.md) | [English](README.md)

## 概述

Blender Pixel Sync 是一个实时同步工具，连接 Blender 和 Pixelorama，为像素艺术工作流提供无缝衔接。该项目包含两个组件：Blender 插件和 Pixelorama 扩展，通过 WebSocket 进行实时数据同步。

## 主要功能

### Blender 插件 (`blender-part/`)
- **WebSocket 服务器**：用于数据同步的实时通信服务器
- **像素完美 UV 展开**：专门为像素艺术设计的 UV 展开算法
- **纹理管理**：自动纹理检测、加载和管理
- **UV 导出/导入**：将 UV 布局导出到 Pixelorama 并导入修改后的版本
- **图像状态监控**：实时监控 Blender 中的图像变化
- **世界网格工具**：专为像素艺术工作流设计的网格设置
- **棋盘纹理生成**：创建用于纹理测试的棋盘图案

### Pixelorama 扩展 (`blender-lorama/`)
- **WebSocket 客户端**：连接到 Blender 的 WebSocket 服务器
- **UV 叠加层**：在 Pixelorama 中显示 Blender UV 布局的视觉叠加
- **纹理导出**：将修改后的纹理导出回 Blender
- **同步面板**：管理同步设置的用户界面
- **实时更新**：当 Blender 中纹理发生变化时进行实时更新

## 安装

### Blender 插件安装

1. 下载或克隆此仓库
2. 在 Blender 中，转到 `编辑 > 偏好设置 > 插件`
3. 点击"安装..."并导航到 `blender-part` 目录
4. 选择文件夹（不是单个文件）进行安装
5. 启用"Pixelorama Sync"插件

### Pixelorama 扩展安装

1. 打开 Pixelorama
2. 转到 `扩展 > 管理扩展`
3. 点击"从文件导入"并导航到 `blender-lorama/src/Extensions/BlenderPixelorama` 目录
4. 选择 `extension.json` 文件
5. 启用"BlenderPixelorama"扩展

## 使用方法

### 设置工作流

1. **启动 Blender 服务器**：
   - 在 Blender 中打开图像编辑器
   - 转到"Pixelorama Sync"面板（图像编辑器 > UI 面板 > Pixelorama Sync）
   - 点击"启动服务器"开始 WebSocket 服务器

2. **从 Pixelorama 连接**：
   - 在 Pixelorama 中，Blender Pixel Sync 面板将作为新标签页出现
   - 扩展将自动尝试连接到 Blender
   - 连接状态将显示在面板中

3. **准备模型**：
   - 在 Blender 中创建或导入 3D 模型
   - 应用材质和 UV 展开
   - 使用像素完美展开工具获得最佳效果

### 处理纹理

1. **导出 UV 布局**：
   - 在 Blender 中选择对象
   - 使用 UV 工具将布局导出到 Pixelorama
   - UV 布局将作为叠加层出现在 Pixelorama 中

2. **创建/编辑纹理**：
   - 在 Pixelorama 中设计像素艺术纹理
   - 使用 UV 叠加层作为精确放置的指南
   - 网格设置确保像素完美对齐

3. **同步更改**：
   - Pixelorama 中的更改可以导出回 Blender
   - Blender 将自动更新纹理
   - 实时同步保持两个应用程序同步

### 推荐工作流

1. **模型设置**：
   - 在 Blender 中创建低多边形模型
   - 使用"设置世界网格"工具进行适当的像素艺术缩放
   - 根据像素密度要求设置网格细分

2. **UV 展开**：
   - 使用"像素完美展开"获得干净的、像素对齐的 UV
   - 或使用"展开到网格"进行基于网格的 UV 布局
   - 在 UV 编辑器中检查 UV 的正确对齐

3. **纹理创建**：
   - 将 UV 布局导出到 Pixelorama
   - 遵循 UV 指南创建像素艺术纹理
   
4. **最终集成**：
   - 将纹理导出回 Blender
   - 应用到模型并在 3D 视图中测试
   - 根据需要在任一应用程序中进行调整

## Blender 面板 UI

Blender 插件提供多个面板：

### 服务器面板
- **启动/停止服务器**：控制 WebSocket 服务器
- **连接状态**：显示连接的客户端和服务器状态
- **端口信息**：显示服务器连接详情

### UV 工具面板
- **像素完美展开**：像素完美精度的 UV 展开
- **展开到网格**：创建基于网格的 UV 布局
- **导出 UV**：将 UV 数据发送到 Pixelorama

### 纹理工具面板
- **检查纹理**：验证纹理尺寸和格式
- **创建棋盘**：生成棋盘图案纹理
- **重新加载纹理**：从磁盘刷新纹理

### 世界网格面板
- **设置世界网格**：为像素艺术配置 Blender 的网格
- **网格细分**：调整网格密度
- **缩放设置**：为像素工作设置适当的缩放

## 兼容性

### Blender
- **版本**：Blender 4.5.0 及更高版本
- **平台**：Windows、macOS、Linux

### Pixelorama
- **版本**：支持 Pixelorama API 版本 8
- **平台**：Windows、macOS、Linux

## 技术详情

### 通信协议
- **WebSocket**：实时双向通信
- **JSON 消息格式**：结构化数据交换
- **事件驱动**：更改时自动更新

### 支持的功能
- **图像格式**：PNG、JPG、BMP 和其他 Blender 支持的格式
- **UV 坐标**：完整的 UV 贴图同步

## 依赖项

### Blender 插件依赖项
- `websockets` 库（由插件自动安装）
- Blender 4.5.0 或更高版本
- NumPy（包含在 Blender 中）

### Pixelorama 扩展依赖项
- 支持扩展的 Pixelorama
- Godot 引擎（Pixelorama 运行时）

## 文件结构

```
blender-pixel-sync/
├── blender-part/              # Blender 插件
│   ├── __init__.py           # 插件注册
│   ├── server.py             # WebSocket 服务器
│   ├── operators.py          # Blender 操作符
│   ├── blender_integration.py # Blender 集成逻辑
│   ├── uv_extractor.py       # UV 提取和处理
│   ├── image_manager.py      # 图像和纹理管理
│   ├── texture_processor.py  # 纹理处理工具
│   ├── unwrap_tools.py       # UV 展开算法
│   ├── ui.py                 # 用户界面面板
│   ├── watch.py              # 文件监控和更改检测
│   ├── deps.py               # 依赖项管理
│   └── libs/                 # 第三方库
└── blender-lorama/           # Pixelorama 扩展
    └── src/
        └── Extensions/
            └── BlenderPixelorama/
                ├── extension.json      # 扩展元数据
                ├── Main.gd            # 主扩展脚本
                ├── Main.tscn          # 主场景
                ├── BlenderLoramaPanel.tscn # UI 面板
                ├── WebSocketClient.gd # WebSocket 客户端
                ├── uv_overlay.gd      # UV 叠加功能
                ├── blender_lorama_panel.gd # 面板逻辑
                └── texture_exporter.gd # 纹理导出
```

## 贡献

欢迎贡献！请随时提交拉取请求、报告错误或建议功能。

### 开发设置
1. 克隆仓库
2. Blender 开发：使用 Blender 的脚本环境
3. Pixelorama 开发：使用带 Pixelorama 源码的 Godot 引擎
4. 使用两个运行中的应用程序测试更改

## 许可证

本项目采用 MIT 许可证 - 请参阅 LICENSE 文件了解详情。

## 致谢

- **原作者**：Heisenshark
- **重构者**：Assistant
- **Pixelorama 扩展**：yuchenyang1994
- **UV 展开算法**：基于 Nutti 的 Magic-UV

## 支持

如需问题、疑问或支持：
1. 查看 GitHub 问题页面
2. 查看文档了解常见解决方案
3. 报告问题时提供 Blender 和 Pixelorama 版本信息

## 版本历史

### v0.1.0
- 初始版本
- 基本 WebSocket 通信
- UV 导出/导入功能
- 像素完美展开工具
- 纹理同步
- 世界网格设置工具
