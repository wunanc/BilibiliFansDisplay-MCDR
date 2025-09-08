# Bilibili Fans Display for MCDR

[English](README.md) | **简体中文**

> 在Minecraft服务器中通过假人显示B站UP主粉丝数的MCDR插件

## 预览原作者的视频

[原作者视频链接][def]

## 预览二改后视频

[预览二改后视频链接][def1]

## 功能特点

- 显示B站UP主粉丝数量
- 支持多显示板配置
- 定时自动更新粉丝数
- 游戏内命令控制
- API接口供其他插件调用

## 安装

1. 确保已安装 [MCDReforged][mcdr] (≥2.10.0)
2. 将插件放入MCDR的`plugins`文件夹
3. 安装依赖: `pip install requests`
4. 重载插件: `!!MCDR plugin reload bilibili_fans_display`

## 使用说明

基本命令:
- `!!fan` - 查看所有显示板状态
- `!!fan display [name]` - 显示指定显示板的粉丝数
- `!!fan update [name]` - 更新指定显示板
- `!!fan mid <显示板> <mid>` - 设置显示板的B站MID
- `!!fan help` - 查看完整帮助

## 配置

插件首次运行会在`config\follower_display\bfanconfig.json`生成配置文件，可配置显示板参数和更新间隔。

## API接口

其他插件可通过以下方式调用:

```python
api = server.get_plugin_instance('bilibili_fans_display').get_plugin_api()
success, message = api.display_number('display_name', 12345)
```

## 开源协议

本项目采用 [MIT License](LICENSE)。

## 问题反馈

如有问题请在GitHub提交Issue。

[mcdr]:https://github.com/MCDReforged/MCDReforged

[mcdr-version-shield]:https://img.shields.io/badge/MCDR-2.10.0+-blue.svg

[mcdr-version-link]:https://docs.mcdreforged.com/zh-cn/latest/quick_start/index.html

[license-shield]:ttps://img.shields.io/badge/License-MIT-green.svg

[license-link]:LICENSE

[def]: https://www.bilibili.com/video/BV1vGhZzEEb8/

[def1]: https://space.bilibili.com/3461562578766467

### requirements.txt
```txt
requests>=2.25.1
mcdreforged
threading
json
os
```

## TODO
如有更多功能需求或对某个计划中的功能有兴趣，可以在 issues 中提出🚀