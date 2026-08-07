# 开发引导
如果你是贡献值|开发者，请看以下项目说明
## 项目结构及功能
```
============================================================================
├── assets
    ├── icons # 存放项目图标
    ├── images # 存放项目图片资源
    └── locales # 本地多语言
        ├── en_us.json (3.61 KB)
        └── zh_cn.json (3.41 KB)
├── core # 代码核心库，存放常用库
    ├── plugin # 插件系统库
        ├── register
            ├── __init__.py (105.00 B)
            ├── filter.py (575.00 B)
            └── handler.py (949.00 B)
        ├── __init__.py (43.00 B)
        └── plugin.py (14.69 KB)
    ├── __init__.py (324.00 B)
    ├── config.py (1.38 KB) # 配置文件库
    ├── locales.py (1.05 KB)  # 本地多语言库
    └── logging.py (2.89 KB)  # 日志库
├── data  # 数据文件夹，存放项目数据
    ├── plugins
        ├── BUXIN-A # 模板插件
            └── plugin_template
                ├── locales
                    └── zh_cn.json (73.00 B)
                ├── PluginGuide.md (5.66 KB)
                ├── logo.png (3.54 KB)
                ├── main.py (788.00 B)
                └── metadata.yaml (244.00 B)
        └── MCT # 内置插件
            └── builtin_plugins
                ├── locales
                    └── zh_cn.json (76.00 B)
                ├── logo.png (3.54 KB)
                ├── main.py (553.00 B)
                └── metadata.yaml (233.00 B)
    ├── tools # 存放工具数据
        └── resource
            ├── projects
            └── config.json (0.00 B)
    ├── config.json (146.00 B) # 项目配置
    └── plugins_config.json (25.00 B) # 插件配置
├── logs # 日志文件夹
├── ui
    ├── pages # 页面开发
        ├── tool
    ├── __init__.py (0.00 B)
    ├── app.py (1.25 KB)
    ├── menu.py (1.39 KB)
    └── theme.py (1006.00 B)
├── utils # 工具库，一般存放各个页面专属功能
├── .gitignore (50.00 B)
├── LICENSE (16.70 KB)
├── README.md (372.00 B) # 项目说明
├── guide.md (0.00 B) # 引导说明
├── main.py (1.01 KB) # 程序入口
├── requirements.txt (32.00 B) # 第三方库
└── update.md (363.00 B) # 更新说明
============================================================================
```