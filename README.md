# Bilibili Fans Display for MCDR

**English** | [简体中文](README.zh.md)

> An MCDR plugin that displays Bilibili UP主的粉丝数 (follower count) in Minecraft servers using armor stands

## Preview Original Author's Video

[Original Author's Video Link][def]

## Preview Modified Version Video

[Preview Modified Version Video Link][def1]

## Features

- Display Bilibili UP主 follower count
- Support for multiple display boards configuration
- Scheduled automatic follower count updates
- In-game command control
- API interface for other plugins to call

## Installation

1. Ensure [MCDReforged][mcdr] (≥2.10.0) is installed
2. Place the plugin in MCDR's `plugins` folder
3. Install dependencies: `pip install requests`
4. Reload the plugin: `!!MCDR plugin reload bilibili_fans_display`

## Usage

Basic commands:
- `!!fan` - View status of all display boards
- `!!fan display [name]` - Display follower count on specified board
- `!!fan update [name]` - Update specified display board
- `!!fan mid <board_name> <mid>` - Set Bilibili MID for a display board
- `!!fan help` - View complete help

## Configuration

On first run, the plugin will generate a configuration file at `config\follower_display\bfanconfig.json` where you can configure display board parameters and update intervals.

## API Interface

Other plugins can call this plugin using:

```python
api = server.get_plugin_instance('bilibili_fans_display').get_plugin_api()
success, message = api.display_number('display_name', 12345)
```

## License

This project is licensed under the [MIT License](LICENSE).

## Issue Reporting
Please submit any issues on GitHub.

[mcdr]: https://github.com/MCDReforged/MCDReforged
[mcdr-version-shield]: https://img.shields.io/badge/MCDR-2.10.0+-blue.svg
[mcdr-version-link]: https://docs.mcdreforged.com/zh-cn/latest/quick_start/index.html
[license-shield]: https://img.shields.io/badge/License-MIT-green.svg
[license-link]: LICENSE
[def]: https://www.bilibili.com/video/BV1vGhZzEEb8/
[def1]: https://space.bilibili.com/3461562578766467

### Dependencies.txt

```txt
requests>=2.25.1
mcdreforged
threading
json
os
```

## TODO
If you have more feature requests or are interested in a planned feature, please raise them in the issues 🚀