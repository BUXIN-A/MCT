from core import I18N
from core import logger

from utils import check
from utils import base

from ui import theme
from nicegui import ui
import os
import json5
import uuid
from functools import partial

PROJECT_DIR = 'data/tools/resource/projects'

def get_project_list():
    l = os.listdir(PROJECT_DIR)
    logger.info(f'获取资源包工具项目 "{l}"')
    return l
def ask_create_project():
    with ui.dialog().props('persistent') as dialog, ui.card().style('width: 50%'):
        ui.label(text=I18N('tool.resource.create_project')).classes('text-h4')
        project_name = ui.input(label=I18N('tool.resource.project.name'), placeholder='New').style('width: 100%')
        project_description = ui.input(label=I18N('tool.resource.project.description'), placeholder='This is a minecraft resource pack').style('width: 100%')
        with ui.row(wrap=False).style('width: 100%'):
            min_format_num = ui.input(label=I18N('tool.resource.project.min_format'),validation={I18N('tool.resource.project.tip_num'): lambda value: check.is_number(value)}).style('width: 100%')
            with ui.dropdown_button(I18N('tool.resource.project.format.default')).style('width: 30%'):
                for v in base.FORMAT_MAP.values():
                    ui.item(v, on_click=partial(min_format_num.set_value, base.FORMAT_MAP_REVERSE.get(v)))
        with ui.row(wrap=False).style('width: 100%'):
            max_format_num = ui.input(label=I18N('tool.resource.project.max_format'),validation={I18N('tool.resource.project.tip_num'): lambda value: check.is_number(value)}).style('width: 100%')
            with ui.dropdown_button(I18N('tool.resource.project.format.default')).style('width: 30%'):
                for v in base.FORMAT_MAP.values():
                    ui.item(v, on_click=partial(max_format_num.set_value, base.FORMAT_MAP_REVERSE.get(v)))
        with ui.row():
            ui.button(text=I18N('tool.resource.ok'), on_click=lambda:create_project(dialog, project_name.value, project_description.value, min_format_num.value, max_format_num.value))
            ui.button(text=I18N('tool.resource.cancle'), on_click=lambda:dialog.close())
    dialog.open()
def create_project(dialog, name, description, min_format_num, max_format_num):
    dialog.close()
    logger.info('创建新项目')
    if description == "": description="This is a Resource Pack"
    if not check.is_number(min_format_num): min_format_num = 0
    if not check.is_number(max_format_num): max_format_num = 9999
    if name == '':
        logger.debug('项目未命名，采用随机命名')
        name = uuid.uuid1()
        os.makedirs(f'{PROJECT_DIR}/{name}')
        with open(f'{PROJECT_DIR}/{name}/pack.mcmeta', 'w') as infomation:
            content = ('{{\n"pack": {{\n"description": "{0}",\n"pack_format": 9999,\n"supported_formats": [{1}, {2}],\n"min_format": {1},\n"max_format": {2}\n}}\n}}'.format(description, min_format_num, max_format_num))
            infomation.write(content)
    elif name in get_project_list():
        logger.debug('已存在项目')
        ui.notify(message='已存在项目')
    else:
        os.makedirs(f'{PROJECT_DIR}/{name}')
        with open(f'{PROJECT_DIR}/{name}/pack.mcmeta', 'w') as infomation:
            content = ('{{\n"pack": {{\n"description": "{0}",\n"pack_format": 9999,\n"supported_formats": [{1}, {2}],\n"min_format": {1},\n"max_format": {2}\n}}\n}}'.format(description, min_format_num, max_format_num))
            infomation.write(content)
def delete_project():
    ...

@ui.page('/tools/resource/{project_name}')
def project_editor_page(project_name: str):
    logger.info(f"注册页面 {project_name}")
    page = ToolResourcePage()
    page.editor_show(project_name)

class ToolResourcePage:
    """资源包工具页"""
    def __init__(self):
        self.ID = "tool.resource"
        get_project_list()

    def show(self):
        with theme.frame(I18N('tool.resource.title')):
            ui.label(I18N('tool.resource.title')).classes('text-h4')
            with ui.row():
                ui.button(text=I18N('tool.resource.create_project'), on_click=ask_create_project)
                ui.button(text=I18N('tool.resource.delete_project'), on_click=delete_project)
            with ui.card().style('width: 100%; height: calc(95vh - 250px)'):
                with ui.column().classes('items-center flex-1 min-h-0 overflow-y-auto').style('width: 100%'):
                    for card_name in get_project_list():
                        with open(f'{PROJECT_DIR}/{card_name}/pack.mcmeta', "r", encoding="utf-8") as f:
                            content = json5.load(f)
                        with ui.card().style('width: 95%; height: 125px').classes('cursor-pointer transition hover:scale-101 duration-300').on('click', lambda name=card_name: ui.navigate.to(f'/tools/resource/{name}')):
                            with ui.row(wrap=False).classes('items-start h-full'):
                                ui.image('assets/images/resource.png').classes('w-24 h-24')
                                with ui.column().classes('justify-start items-start h-full'):
                                    ui.label(card_name).classes('text-h6')
                                    ui.label(content['pack']['description']).classes('text-p1')

    def editor_show(self, project_name):
        with theme.frame(project_name):
            ui.label(f'正在编辑项目：{project_name}').classes('text-h4')
            pass