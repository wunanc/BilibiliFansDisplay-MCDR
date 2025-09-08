# -*- coding: utf-8 -*-
"""
Bilibili Follower Display Plugin for MCDR
Version: 3.3.1
Author: 通义千问/小豆(DeepSeek/呜楠二改)
功能：通过假人显示B站UP主粉丝数，支持多MID/多显示板/API调用
配置文件：bfanconfig.json
{
    "log_enabled": true,
    "auto_start": false,
    "update_interval": 30,
    "displays": [
        {
            "name": "main",
            "mid": "114514",
            "open_api": true,
            "digit_look_at": {
                "0": "-2464 197 -947",
                "1": "-2463 197 -947",
                "2": "-2462 197 -946",
                "3": "-2462 197 -945",
                "4": "-2462 197 -944",
                "5": "-2463 197 -943",
                "6": "-2464 197 -943",
                "7": "-2465 197 -943",
                "8": "-2466 197 -944",
                "9": "-2466 197 -945"
            },
            "reset_pos": "-2466 196 -947",
            "spawn_pos": "-2464 198 -945",
            "delay_between_commands": 1.0
        }
    ]
}
"""

import requests
import threading
import json
import os
from mcdreforged.api.all import *

# 插件元数据
PLUGIN_METADATA = {
    'id': 'follower_display',
    'version': '3.3.1',
    'name': 'Bilibili Follower Display',
    'description': '在游戏内通过假人显示B站粉丝数，支持多MID/多显示板/API调用',
    'author': '通义千问/小豆(DeepSeek/呜楠二改)'
}

# 默认配置
config = {
    'log_enabled': True,       # 是否启用详细日志
    'auto_start': False,         # 服务器启动时是否自动开启定时更新
    'update_interval': 60,      # 自动更新间隔（不可用）
    'displays': [              # 显示板配置列表
        {
            'name': 'main',    # 显示板名称
            'mid': '114514',   # 该显示板对应的B站MID
            'open_api': True,  # 是否开放API供其他插件调用
            'digit_look_at': { # 数字朝向坐标 这些是告示牌的位置
                '0': '-2464 197 -947',
                '1': '-2463 197 -947',
                '2': '-2462 197 -946',
                '3': '-2462 197 -945',
                '4': '-2462 197 -944',
                '5': '-2463 197 -943',
                '6': '-2464 197 -943',
                '7': '-2465 197 -943',
                '8': '-2466 197 -944',
                '9': '-2466 197 -945'
            },
            'reset_pos': '-2466 197 -947',  # 复位位置
            'spawn_pos': '-2464 198 -945',  # 假人生成位置
            'delay_between_commands': 1.0   # 每个动作间隔（秒）
        }
    ]
}

# 缓存文件名
CACHE_FILE = 'fan_cache.json'

# 全局变量
update_timer = None
server_inst = None  # 保存 MCDR server 实例
plugin_instances = {}  # 存储插件实例供API调用
is_updating = False  # 标记是否正在更新
current_update_index = 0  # 当前更新的显示板索引
scheduler_running = False  # 标记定时任务是否正在运行

# ===== 工具函数 =====

def log_info(msg):
    """输出 INFO 日志"""
    if server_inst and config['log_enabled']:
        server_inst.logger.info(f"[Bilibili] {msg}")

def log_debug(msg):
    """输出 DEBUG 日志"""
    if server_inst and config['log_enabled']:
        server_inst.logger.debug(f"[Bilibili] {msg}")

def get_follower_count(mid):
    """获取B站粉丝数"""
    url = f"https://api.bilibili.com/x/web-interface/card?mid={mid}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.json() if response.status_code == 200 else {'code': -1}
    except Exception as e:
        log_info(f"请求失败: {e}")
        return {'code': -1}

def save_cache(fans_count, display_name='main'):
    """保存粉丝数到缓存文件"""
    path = os.path.join(server_inst.get_data_folder(), CACHE_FILE)
    try:
        # 读取现有缓存
        cache_data = {}
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
        
        # 更新指定显示板的缓存
        cache_data[display_name] = int(fans_count)
        
        # 写回文件
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log_info(f"缓存保存失败: {e}")

def load_cache(display_name='main'):
    """从缓存文件读取粉丝数"""
    path = os.path.join(server_inst.get_data_folder(), CACHE_FILE)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            return cache_data.get(display_name, None)
    except:
        return None

def get_display_config(display_name='main'):
    """获取指定显示板的配置"""
    for display in config['displays']:
        if display['name'] == display_name:
            return display
    # 如果找不到指定名称的显示板，返回第一个
    log_info(f"显示板 '{display_name}' 未找到，使用第一个显示板")
    return config['displays'][0] if config['displays'] else None

def display_number(server, number, display_name='main', only_changed=True, callback=None):
    """
    显示数字到假人屏幕
    :param server: server 实例
    :param number: 要显示的数字
    :param display_name: 显示板名称
    :param only_changed: 是否仅更新变化的位数
    :param callback: 显示完成后的回调函数
    """
    display_config = get_display_config(display_name)
    if not display_config:
        server.say(f"❌ 显示板 '{display_name}' 配置不存在")
        if callback:
            callback()
        return
    
    digits = [int(d) for d in str(number)][::-1]  # 逆序：个位在前
    old_digits = [int(d) for d in str(load_cache(display_name))][::-1] if only_changed and load_cache(display_name) else []
    
    max_len = max(len(digits), len(old_digits)) if only_changed else len(digits)
    
    # 构建命令序列
    commands = [
        (f"/player Fan spawn at {display_config['spawn_pos']}", "召唤假人"),
        (f"/player Fan look at {display_config['reset_pos']}", "复位朝向"),
        ("/player Fan use once", "触发复位")
    ]
    
    for i in range(max_len):
        cur = digits[i] if i < len(digits) else 0
        old = old_digits[i] if i < len(old_digits) else -1
        pos = display_config['digit_look_at'].get(str(cur), display_config['reset_pos'])
        
        if not only_changed or cur != old:
            commands.append((f"/player Fan look at {pos}", f"显示第{i+1}位: {cur}"))
            commands.append(("/player Fan use once", f"敲击第{i+1}位"))
        else:
            commands.append((f"/player Fan look at {pos}", f"跳过第{i+1}位（未变）"))
    
    commands.append(("/player Fan kill", "清理假人"))
    
    def run_cmd(index):
        if index >= len(commands):
            # 所有命令执行完成
            save_cache(number, display_name)
            if callback:
                callback()
            return
        cmd, desc = commands[index]
        server.execute(cmd)
        log_debug(f"{desc}: {cmd}")
        timer = threading.Timer(display_config['delay_between_commands'], run_cmd, [index + 1])
        timer.start()
    
    run_cmd(0)

# ===== API 功能 =====

def api_display_number(display_name, number):
    """
    API: 在其他显示板上显示指定数字
    :param display_name: 显示板名称
    :param number: 要显示的数字
    :return: 成功返回True，失败返回False和错误信息
    """
    display_config = get_display_config(display_name)
    if not display_config:
        return False, f"显示板 '{display_name}' 不存在"
    
    if not display_config.get('open_api', False):
        return False, f"显示板 '{display_name}' 未开放API"
    
    try:
        number = int(number)
        display_number(server_inst, number, display_name, only_changed=False)
        return True, f"已在显示板 '{display_name}' 上显示数字 {number}"
    except ValueError:
        return False, "数字格式错误"
    except Exception as e:
        return False, f"显示失败: {str(e)}"

# ===== 定时任务控制 =====

def update_next_display():
    """更新下一个显示板"""
    global current_update_index, is_updating
    
    # 检查是否所有显示板都已更新完成
    if current_update_index >= len(config['displays']):
        is_updating = False
        current_update_index = 0
        log_info("✅ 所有显示板更新完成")
        return
    
    # 获取当前要更新的显示板
    display = config['displays'][current_update_index]
    display_name = display['name']
    mid = display['mid']
    
    log_info(f"🔄 正在更新显示板 '{display_name}' (MID: {mid})")
    
    # 获取当前粉丝数
    old_fans = load_cache(display_name)
    data = get_follower_count(mid)
    
    if data.get('code') == 0:
        fans = data['data']['card']['fans']
        name = data['data']['card']['name']
        
        if old_fans is not None:
            server_inst.say(f"🔄 {name} ({display_name}): {old_fans:,} → {fans:,}")
        else:
            server_inst.say(f"🎨 正在显示 {name} 的粉丝数到 '{display_name}' 显示板...")
        
        # 显示数字，完成后更新下一个显示板
        display_number(
            server_inst, 
            fans, 
            display_name, 
            only_changed=(old_fans is not None),
            callback=lambda: update_next_display_callback(display_name, fans, old_fans)
        )
    else:
        server_inst.say(f"❌ 显示板 '{display_name}' 更新失败")
        # 即使失败也继续更新下一个
        current_update_index += 1
        update_next_display()

def update_next_display_callback(display_name, new_fans, old_fans):
    """更新完成后的回调函数"""
    global current_update_index
    # 保存新的粉丝数
    save_cache(new_fans, display_name)
    # 更新下一个显示板
    current_update_index += 1
    update_next_display()

def start_scheduled_update():
    """启动定时更新任务"""
    global update_timer, is_updating, scheduler_running
    if update_timer is not None:
        return  # 已在运行
    
    scheduler_running = True

    def task():
        global update_timer, is_updating, current_update_index, scheduler_running
        if not scheduler_running:
            return  # 如果定时任务已停止，不再执行
            
        if is_updating:
            log_info("⏱️ 跳过本次更新（上次更新仍在进行中）")
        else:
            is_updating = True
            current_update_index = 0
            log_info("⏱️ 开始顺序更新所有显示板")
            update_next_display()
        
        # 只有在定时任务仍在运行时才设置下一个定时器
        if scheduler_running:
            update_timer = threading.Timer(config['update_interval'], task)
            update_timer.start()

    update_timer = threading.Timer(config['update_interval'], task)
    update_timer.start()
    server_inst.say(f"✅ 自动更新已启动，周期 {config['update_interval']} 秒")

def stop_scheduled_update():
    """停止定时更新"""
    global update_timer, is_updating, current_update_index, scheduler_running
    scheduler_running = False
    if update_timer is not None:
        update_timer.cancel()
        update_timer = None
    is_updating = False
    current_update_index = 0
    server_inst.say("🛑 自动更新已停止")

def get_task_status():
    """获取任务状态"""
    status = "运行中" if update_timer is not None else "已停止"
    if is_updating:
        status += " (正在更新)"
    return status

# ===== 重载功能 =====

def reload_config():
    """重新加载配置文件"""
    global config
    
    try:
        config_path = os.path.join(server_inst.get_data_folder(), 'bfanconfig.json')
        if os.path.isfile(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                
                # 保留当前运行状态
                was_running = (update_timer is not None)
                
                # 停止当前定时任务
                if was_running:
                    stop_scheduled_update()
                
                # 更新配置
                config.update(user_config)
                
                # 保存配置（确保完整）
                server_inst.save_config_simple(config, 'bfanconfig.json')
                
                # 如果之前定时任务在运行，重新启动
                if was_running:
                    start_scheduled_update()
                
                server_inst.say("✅ 配置已重载")
                return True
        else:
            server_inst.say("❌ 配置文件不存在")
            return False
    except Exception as e:
        server_inst.say(f"❌ 重载配置失败: {str(e)}")
        return False
    
# ===== 命令处理 =====

def on_info(server, info):
    global server_inst
    server_inst = server  # 保存实例

    # 忽略非用户输入
    if not info.is_user:
        return

    args = info.content.strip().split()
    if not args or args[0] != '!!fan':
        return

    # 日志调试
    log_debug(f"收到命令: {info.content}")

    # =============== 命令分发 ===============

    # 1. 查询所有显示板状态
    if len(args) == 1:
        display_list = []
        for display in config['displays']:
            data = get_follower_count(display['mid'])
            if data.get('code') == 0:
                fans = data['data']['card']['fans']
                name = data['data']['card']['name']
                display_list.append(f"{display['name']}: {name}({fans:,})")
            else:
                display_list.append(f"{display['name']}: 查询失败")
        
        server.say("📊 所有显示板状态:\n" + "\n".join(display_list))

    # 2. 设置显示板 MID
    elif len(args) >= 4 and args[1] == 'mid':
        display_name = args[2] if len(args) > 3 else 'main'
        new_mid = args[3] if len(args) > 3 else args[2]
        
        if not new_mid.isdigit() or len(new_mid) < 3 or len(new_mid) > 10:
            server.say("❌ 无效的 B站 MID，请输入 3~10 位数字")
            return

        display_config = get_display_config(display_name)
        if not display_config:
            server.say(f"❌ 显示板 '{display_name}' 不存在")
            return

        old_mid = display_config['mid']
        if old_mid == new_mid:
            server.say(f"ℹ {display_name} 当前已监控 MID: {old_mid}，无需更改")
            return

        display_config['mid'] = new_mid
        server.save_config_simple(config, 'bfanconfig.json')
        server.say(f"✅ 成功将 {display_name} 的 MID 从 {old_mid} 修改为 {new_mid}")
        return

    # 3. 设置API开关
    elif len(args) >= 4 and args[1] == 'api':
        display_name = args[2]
        status = args[3].lower()
        
        display_config = get_display_config(display_name)
        if not display_config:
            server.say(f"❌ 显示板 '{display_name}' 不存在")
            return
        
        if status in ['on', 'true', 'enable', '1']:
            display_config['open_api'] = True
            server.say(f"✅ 已开启 {display_name} 的API功能")
        elif status in ['off', 'false', 'disable', '0']:
            display_config['open_api'] = False
            server.say(f"✅ 已关闭 {display_name} 的API功能")
        else:
            server.say("❌ 参数错误，使用 on/off")
            return
            
        server.save_config_simple(config, 'bfanconfig.json')

    # 4. 首次显示
    elif len(args) >= 2 and args[1] == 'display':
        display_name = args[2] if len(args) > 2 else 'main'
        display_config = get_display_config(display_name)
        if not display_config:
            server.say(f"❌ 显示板 '{display_name}' 不存在")
            return
            
        data = get_follower_count(display_config['mid'])
        if data.get('code') == 0:
            fans = data['data']['card']['fans']
            name = data['data']['card']['name']
            server.say(f"🎨 正在显示 {name} 的粉丝数到 '{display_name}' 显示板...")
            display_number(server, fans, display_name, only_changed=False)
        else:
            server.say("❌ 显示失败，请检查MID或网络")

    # 5. 智能更新（仅变化位）
    elif len(args) >= 2 and args[1] == 'update':
        display_name = args[2] if len(args) > 2 else 'main'
        display_config = get_display_config(display_name)
        if not display_config:
            server.say(f"❌ 显示板 '{display_name}' 不存在")
            return
            
        old_fans = load_cache(display_name)
        if old_fans is None:
            server.say(f"⚠ 请先使用 !!fan display {display_name} 初始化显示")
            return

        data = get_follower_count(display_config['mid'])
        if data.get('code') == 0:
            fans = data['data']['card']['fans']
            name = data['data']['card']['name']
            server.say(f"🔄 {name} ({display_name}): {old_fans:,} → {fans:,}")
            display_number(server, fans, display_name, only_changed=True)
        else:
            server.say("❌ 更新失败")

    # 6. API显示数字
    elif len(args) >= 4 and args[1] == 'api' and args[2] == 'show':
        display_name = args[3]
        number = args[4] if len(args) > 4 else None
        
        if not number:
            server.say("❌ 用法: !!fan api show <显示板> <数字>")
            return
            
        success, message = api_display_number(display_name, number)
        if success:
            server.say(f"✅ {message}")
        else:
            server.say(f"❌ {message}")

    # 7. 日志开关
    elif args == ['!!fan', 'log', 'toggle']:
        config['log_enabled'] = not config['log_enabled']
        server.save_config_simple(config, 'bfanconfig.json')
        status = '开启' if config['log_enabled'] else '关闭'
        server.say(f"🔧 日志输出已 {status}")

    # 8. 显示板列表
    elif args == ['!!fan', 'displays']:
        display_list = []
        for display in config['displays']:
            api_status = "开放" if display.get('open_api', False) else "关闭"
            display_list.append(f"{display['name']} (MID: {display['mid']}, API: {api_status})")
        server.say(f"📋 可用显示板:\n" + "\n".join(display_list))

    # 9. 重载配置
    elif args == ['!!fan', 'reload']:
        if reload_config():
            server.say("✅ 插件配置已重载")
        else:
            server.say("❌ 配置重载失败")

    # 9. 定时任务控制
    elif args == ['!!fan', 'interval']:
        if get_task_status() == "运行中":
            stop_scheduled_update()
        else:
            start_scheduled_update()

    elif len(args) >= 2 and args[1] == 'interval':
        if len(args) == 2:
            server.say(f"🔄 自动更新状态: {get_task_status()}")
        elif len(args) == 3:
            cmd = args[2]
            if cmd == 'status':
                server.say(f"🔄 自动更新状态: {get_task_status()}")
            elif cmd == 'start':
                if get_task_status() == "运行中":
                    server.say("ℹ 自动更新已在运行中")
                else:
                    start_scheduled_update()
            elif cmd == 'stop':
                if get_task_status() == "已停止":
                    server.say("ℹ 自动更新已停止")
                else:
                    stop_scheduled_update()
            elif cmd.isdigit():
                interval = int(cmd)
                if interval < 5:
                    server.say("❌ 间隔不能少于5秒")
                    return
                config['update_interval'] = interval
                server.save_config_simple(config, 'bfanconfig.json')
                server.say(f"⏱️ 更新间隔已设置为 {interval} 秒")
                # 重启任务
                if update_timer is not None:
                    stop_scheduled_update()
                    start_scheduled_update()
            else:
                server.say("❌ 用法: !!fan interval <5~3600> | start | stop | status")
        else:
            server.say("❌ 用法: !!fan interval <5~3600> | start | stop | status")

    # 10. 显示帮助
    elif args == ['!!fan', 'help']:
        server.reply(info, '''
§7====== §6Bilibili 粉丝显示 §7======
§a!!fan §f- 查询所有显示板状态
§a!!fan mid <显示板> <mid> §f- 修改指定显示板的MID
§a!!fan api <显示板> <on/off> §f- 开关显示板的API功能
§a!!fan api show <显示板> <数字> §f- 在指定显示板显示数字
§a!!fan display [name] §f- 首次显示到指定显示板
§a!!fan update [name] §f- 智能更新指定显示板
§a!!fan reload §f- 重载配置文件
§a!!fan displays §f- 列出所有显示板
§a!!fan interval §f- 启/停自动更新
§a!!fan interval status §f- 查看状态
§a!!fan interval 30 §f- 设置间隔30秒
§a!!fan log toggle §f- 切换日志
§7========================§r
        '''.strip())
        server.reply(info, "§7插件版本: §a" + PLUGIN_METADATA['version'] + " §7作者: §a" + PLUGIN_METADATA['author'])

# ===== 插件生命周期 =====

def on_load(server, old_module):
    global server_inst, plugin_instances
    server_inst = server

    server.logger.info('[Bilibili] 插件正在加载...')

    # 创建数据目录
    data_folder = server.get_data_folder()
    os.makedirs(data_folder, exist_ok=True)

    # 加载配置文件
    config_path = os.path.join(data_folder, 'bfanconfig.json')
    if os.path.isfile(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                
                # 兼容旧配置文件
                if 'displays' not in user_config:
                    # 迁移旧配置到新格式
                    old_mid = user_config.get('mid', '114514')
                    user_config['displays'] = [{
                        'name': 'main',
                        'mid': old_mid,
                        'open_api': True,
                        'digit_look_at': {
                            '0': '-2464 197 -947',
                            '1': '-2463 197 -947',
                            '2': '-2462 197 -946',
                            '3': '-2462 197 -945',
                            '4': '-2462 197 -944',
                            '5': '-2463 197 -943',
                            '6': '-2464 197 -943',
                            '7': '-2465 197 -943',
                            '8': '-2466 197 -944',
                            '9': '-2466 197 -945'
                        },
                        'reset_pos': '-2466 196 -947',
                        'spawn_pos': '-2464 198 -945',
                        'delay_between_commands': 1.0
                    }]
                    # 移除旧的mid配置
                    if 'mid' in user_config:
                        del user_config['mid']
                    server.logger.info("[Bilibili] 已迁移旧配置文件到新格式")
                
                config.update(user_config)
        except Exception as e:
            server.logger.warning(f"[Bilibili] 配置文件加载失败，使用默认值: {e}")

    # 保存配置（确保完整）
    server.save_config_simple(config, 'bfanconfig.json')
    server.logger.info(f"[Bilibili] 插件加载完成，自动启动={config['auto_start']}")
    server.logger.info(f"[Bilibili] 已加载 {len(config['displays'])} 个显示板")
    
    for display in config['displays']:
        api_status = "开放" if display.get('open_api', False) else "关闭"
        server.logger.info(f"[Bilibili]   - {display['name']}: MID={display['mid']}, API={api_status}")

    # 注册帮助
    server.register_help_message('!!fan', 'B站粉丝数显示')
    server.register_help_message('!!fan help', '查看所有命令')
    
    # 注册插件实例供其他插件调用
    plugin_instances[PLUGIN_METADATA['id']] = server

    # 自动启动定时任务
    if config['auto_start']:
        start_scheduled_update()

def on_unload(server):
    """插件卸载时停止任务"""
    global plugin_instances, is_updating, current_update_index, scheduler_running
    stop_scheduled_update()
    is_updating = False
    current_update_index = 0
    scheduler_running = False
    if PLUGIN_METADATA['id'] in plugin_instances:
        del plugin_instances[PLUGIN_METADATA['id']]
    server.logger.info("[Bilibili] 插件已卸载")

# ===== API 导出 =====

def get_plugin_api():
    """返回插件API供其他插件调用"""
    return {
        'display_number': api_display_number,
        'get_display_config': get_display_config,
        'get_all_displays': lambda: config['displays']
    }