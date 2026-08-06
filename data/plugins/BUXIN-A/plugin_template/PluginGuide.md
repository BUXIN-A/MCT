# MCT 插件开发指南

## 目录结构

每个插件必须放在 `data/plugins/{作者名}/{插件名}/` 目录下，结构如下：

```
data/plugins/
  └── {作者名}/
      └── {插件名}/
          ├── main.py          # 插件入口（必须）
          ├── metadata.yaml    # 插件元数据（必须）
          ├── logo.png         # 插件图标（可选）
          └── locales/         # 插件本地化文件（可选）
              ├── zh_cn.json
              └── en_us.json
```

---

## metadata.yaml

插件元数据配置文件，必须包含以下字段：

```yaml
name: my_plugin          # 插件唯一标识名（英文，用于路由和内部引用）
display_name: 我的插件     # 显示名称
desc: 这是一个示例插件     # 插件描述
version: 1.0.0           # 版本号
author: YourName         # 作者名
repo: https://github.com/you/repo  # 仓库地址（可选）
```

---

## main.py

插件入口文件，必须定义一个 `Plugin` 类。

### 最小示例

```python
from nicegui import ui
from core.plugin.register import filter


class Plugin:
    def __init__(self, mct=None):
        self.mct = mct

    async def initialize(self):
        """插件初始化方法，应用启动时自动调用"""
        print("我的插件已初始化")

    @filter.page('my_plugin', title='我的插件')
    async def page(self):
        """插件页面，用户访问 /plugin/my_plugin 时渲染"""
        ui.label('欢迎使用我的插件')
```

---

## Plugin 类

### 构造函数 `__init__(self, mct=None)`

| 参数 | 类型 | 说明 |
|------|------|------|
| `mct` | `Any` | MCT 主程序实例引用（当前为 `None`，预留扩展） |

### `async initialize(self)`

应用启动时由插件系统自动调用。可用于执行初始化逻辑（如加载数据、注册服务等）。支持同步和异步方法。

```python
# 同步写法
def initialize(self):
    print("初始化完成")

# 异步写法
async def initialize(self):
    await some_async_task()
```

### `async page(self)`

插件页面渲染方法。使用 `@filter.page()` 装饰器注册后，访问 `/plugin/{page_id}` 时自动渲染。方法内使用 NiceGUI API 构建 UI。

```python
@filter.page('my_plugin', title='我的插件', icon='extension')
async def page(self):
    ui.label('Hello MCT!')
    ui.button('点击我', on_click=lambda: ui.notify('你点击了按钮'))
```

---

## 页面注册装饰器

### `@filter.page(page_id, title=None, icon=None)`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `page_id` | `str` | 是 | 页面唯一标识，用于路由 `/plugin/{page_id}` |
| `title` | `str` | 否 | 页面标题，显示在导航栏 |
| `icon` | `str` | 否 | 页面图标（Material Icons 名称） |

---

## 插件元数据注册装饰器（可选）

### `@initialization.register(category, name, description="", version="0.0.0")`

用于声明式注册插件元信息，提供分类管理能力。

```python
from core.plugin.register import initialization

@initialization.register(category='tool', name='my_plugin', description='我的插件', version='1.0.0')
class Plugin:
    ...
```

查询已注册插件：

```python
from core.plugin.register import initialization

# 按名称查询
info = initialization.get('my_plugin')

# 按分类查询
tools = initialization.get_by_category('tool')

# 获取所有
all_plugins = initialization.all()
```

---

## 插件本地化

在 `locales/` 目录下创建语言文件，格式为 JSON：

```json
{
    "zh_cn": {
        "my_plugin.title": "我的插件",
        "my_plugin.desc": "这是一个示例"
    }
}
```

在插件代码中使用：

```python
from core import I18N

ui.label(I18N('my_plugin.title'))
```

---

## 插件页面示例

### 带表单的页面

```python
from nicegui import ui
from core.plugin.register import filter


class Plugin:
    def __init__(self, mct=None):
        self.mct = mct

    async def initialize(self):
        print("form_plugin 初始化")

    @filter.page('form_plugin', title='表单示例')
    async def page(self):
        ui.label('用户注册').classes('text-h5')

        with ui.card().classes('w-full max-w-md'):
            name = ui.input(label='用户名')
            email = ui.input(label='邮箱')
            ui.button('提交', on_click=lambda: ui.notify(f'姓名: {name.value}, 邮箱: {email.value}'))
```

### 带异步操作的页面

```python
import asyncio
from nicegui import ui
from core.plugin.register import filter


class Plugin:
    def __init__(self, mct=None):
        self.mct = mct

    async def initialize(self):
        print("async_plugin 初始化")

    @filter.page('async_plugin', title='异步示例')
    async def page(self):
        async def fetch_data():
            ui.notify('正在加载...')
            await asyncio.sleep(2)
            ui.notify('加载完成!')

        ui.button('加载数据', on_click=fetch_data)
```

---

## 完整示例

参考项目中已有的插件：

- `data/plugins/MCT/builtin_plugins/` — 内置插件
- `data/plugins/BUXIN-A/plugin_template/` — 插件模板

---

## 注意事项

1. **插件目录命名**：作者名和插件名仅允许英文、数字和下划线
2. **page() 方法**：必须使用 `@filter.page()` 装饰器注册，否则不会被识别为页面
3. **initialize() 方法**：支持同步和异步，应用启动时自动调用
4. **NiceGUI 导入**：在 `page()` 方法内部使用 `from nicegui import ui`，避免模块加载时的循环导入
5. **异常处理**：插件初始化失败不会影响其他插件和主程序运行
6. **热重载**：修改插件代码后，NiceGUI 的 WatchFiles 会自动检测变更并重新加载
