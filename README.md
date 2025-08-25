 ==================== README.md ====================
# README.md
"""
# 文件内容提取与上传工具 - 模块化版本

## 项目结构

```
file_extractor_uploader/
├── main.py                     # 程序入口
├── requirements.txt            # 依赖文件
├── README.md                   # 说明文档
├── config/
│   ├── __init__.py
│   └── settings.py             # 配置管理
├── utils/
│   ├── __init__.py
│   └── event_bus.py           # 事件系统
├── core/
│   ├── __init__.py
│   ├── data_manager.py        # 数据管理
│   ├── file_scanner.py        # 文件扫描
│   ├── content_analyzer.py    # 内容分析  
│   ├── uploader.py            # 数据上传
│   └── crypto_utils.py        # 加密工具
├── ui/
│   ├── __init__.py
│   ├── main_window.py         # 主窗口
│   ├── components/
│   │   ├── __init__.py
│   │   ├── control_panel.py   # 控制面板
│   │   ├── progress_panel.py  # 进度面板
│   │   └── results_panel.py   # 结果面板
│   └── dialogs/
│       └── __init__.py
└── __init__.py
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行程序

```bash
python main.py
```

## 主要功能

1. **文件扫描**: 扫描指定目录下的debug文件，支持增量更新
2. **内容分析**: 使用正则表达式提取特定格式的日志内容
3. **数据管理**: 维护文件与匹配数据的映射关系，支持选择性操作
4. **数据上传**: 支持全量上传、选择性上传、失败重传
5. **3DES解密**: 支持ECB模式的3DES解密预览（需要pycryptodome）
6. **模块化架构**: 采用事件驱动的松耦合架构设计

## 架构特点

- **职责分离**: 每个模块负责单一职责
- **事件驱动**: 使用观察者模式实现模块间通信
- **异步处理**: 后台线程处理耗时操作，避免UI阻塞
- **配置集中**: 所有配置参数集中管理
- **状态管理**: 统一的数据状态管理
- **错误处理**: 完善的错误处理和用户反馈机制

## 模块说明

### 配置模块 (config/)
- `settings.py`: 集中管理所有配置参数

### 工具模块 (utils/)  
- `event_bus.py`: 实现事件总线，支持模块间松耦合通信

### 核心模块 (core/)
- `data_manager.py`: 数据状态管理，包括文件列表、匹配数据、上传状态等
- `file_scanner.py`: 文件扫描功能，支持增量检测
- `content_analyzer.py`: 内容分析，使用多种正则模式提取数据
- `uploader.py`: 数据上传功能，支持批量、重试等
- `crypto_utils.py`: 3DES解密和数据格式化工具

### 界面模块 (ui/)
- `main_window.py`: 主窗口，整合所有功能
- `components/`: UI组件
  - `control_panel.py`: 操作按钮面板
  - `progress_panel.py`: 进度显示面板
  - `results_panel.py`: 结果展示面板

## 使用说明

1. 启动程序后，首先选择要扫描的目录
2. 点击"开始扫描"扫