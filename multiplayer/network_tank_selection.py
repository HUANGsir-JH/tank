"""
多人游戏坦克选择视图

为多人游戏提供坦克选择界面，支持主机和客户端的坦克选择
"""

import arcade
from typing import Optional, Dict, Any
import sys
import os

# 添加父目录到路径以导入tank_selection
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tank_selection import TankOption, PLAYER_IMAGE_PATH_GREEN, PLAYER_IMAGE_PATH_DESERT, PLAYER_IMAGE_PATH_BLUE, PLAYER_IMAGE_PATH_GREY


# 如果constants模块不存在，使用默认值
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720


class NetworkTankSelectionView(arcade.View):
    """多人游戏坦克选择视图"""

    def __init__(self, is_host: bool = True, room_name: str = "", host_ip: str = "", host_port: int = 12346):
        super().__init__()
        self.is_host = is_host
        self.room_name = room_name
        self.host_ip = host_ip
        self.host_port = host_port

        # 坦克选择相关
        self.tank_sprites = arcade.SpriteList()
        self.tank_options = []
        self.selected_tank = None

        # 网络状态
        self.ready_to_start = False
        self.other_players_ready = False

    def setup(self):
        """设置坦克选择界面"""
        # 创建坦克选项（复用单人游戏的逻辑）
        center_y = SCREEN_HEIGHT / 2
        start_x = SCREEN_WIDTH / 2 - 300  # 居中显示
        padding = 150

        self.tank_options = [
            TankOption(PLAYER_IMAGE_PATH_GREEN, "绿色坦克", start_x, center_y, 0.1),
            TankOption(PLAYER_IMAGE_PATH_DESERT, "黄色坦克", start_x + padding, center_y, 0.11),
            TankOption(PLAYER_IMAGE_PATH_BLUE, "蓝色坦克", start_x + 2 * padding, center_y, 0.1),
            TankOption(PLAYER_IMAGE_PATH_GREY, "灰色坦克", start_x + 3 * padding, center_y, 0.1)
        ]

        # 将坦克精灵添加到列表
        for option in self.tank_options:
            self.tank_sprites.append(option.sprite)

        # 默认选择第一个坦克
        self.selected_tank = self.tank_options[0]
        self.selected_tank.selected = True
        self.selected_tank.player = 1

    def on_show_view(self):
        """显示视图时的设置"""
        arcade.set_background_color(arcade.color.LIGHT_BLUE)
        self.setup()

    def on_draw(self):
        """绘制视图"""
        self.clear()

        # 绘制标题
        title = "选择你的坦克 - 多人游戏"
        if self.is_host:
            title += " (主机)"
        else:
            title += " (客户端)"

        arcade.draw_text(
            title,
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT - 100,
            arcade.color.BLACK,
            font_size=36,
            anchor_x="center"
        )

        # 绘制房间信息
        if self.is_host:
            room_info = f"房间: {self.room_name}"
        else:
            room_info = f"连接到: {self.host_ip}:{self.host_port}"

        arcade.draw_text(
            room_info,
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT - 150,
            arcade.color.DARK_BLUE,
            font_size=18,
            anchor_x="center"
        )

        # 绘制所有坦克精灵
        self.tank_sprites.draw()

        # 绘制每个坦克选项的附加元素
        for option in self.tank_options:
            option.draw()

        # 绘制操作说明
        arcade.draw_text(
            "使用 A 和 D 键选择坦克",
            SCREEN_WIDTH / 2,
            200,
            arcade.color.BLACK,
            font_size=18,
            anchor_x="center"
        )

        # 绘制准备状态
        if self.ready_to_start:
            arcade.draw_text(
                "已准备！等待其他玩家...",
                SCREEN_WIDTH / 2,
                150,
                arcade.color.GREEN,
                font_size=20,
                anchor_x="center",
                bold=True
            )
        else:
            arcade.draw_text(
                "按 SPACE 准备开始游戏",
                SCREEN_WIDTH / 2,
                150,
                arcade.color.ORANGE_RED,
                font_size=20,
                anchor_x="center",
                bold=True
            )

        # 绘制返回提示
        arcade.draw_text(
            "按 ESC 返回",
            SCREEN_WIDTH / 2,
            100,
            arcade.color.GRAY,
            font_size=16,
            anchor_x="center"
        )

    def on_key_press(self, key, modifiers):
        """处理按键事件"""
        if key == arcade.key.ESCAPE:
            # 返回房间浏览或主机视图
            if self.is_host:
                from .network_views import NetworkHostView
                host_view = NetworkHostView()
                if host_view.start_hosting(self.room_name):
                    self.window.show_view(host_view)
                else:
                    from .network_views import RoomBrowserView
                    browser_view = RoomBrowserView()
                    self.window.show_view(browser_view)
            else:
                from .network_views import RoomBrowserView
                browser_view = RoomBrowserView()
                self.window.show_view(browser_view)

        elif key == arcade.key.A:
            # 向左选择坦克
            self._change_tank_selection(-1)

        elif key == arcade.key.D:
            # 向右选择坦克
            self._change_tank_selection(1)

        elif key == arcade.key.SPACE:
            # 准备开始游戏
            self._toggle_ready()

    def _change_tank_selection(self, direction: int):
        """改变坦克选择"""
        if not self.selected_tank:
            return

        # 找到当前选择的索引
        current_index = self.tank_options.index(self.selected_tank)
        new_index = (current_index + direction) % len(self.tank_options)

        # 取消当前选择
        self.selected_tank.selected = False
        self.selected_tank.player = None

        # 设置新选择
        self.selected_tank = self.tank_options[new_index]
        self.selected_tank.selected = True
        self.selected_tank.player = 1

    def _toggle_ready(self):
        """切换准备状态"""
        self.ready_to_start = not self.ready_to_start

        if self.ready_to_start:
            # 发送坦克选择信息到网络
            tank_info = {
                "image_path": self.selected_tank.image_path,
                "tank_type": self._get_tank_type(self.selected_tank.image_path)
            }

            if self.is_host:
                self._start_host_game(tank_info)
            else:
                self._send_client_ready(tank_info)

    def _get_tank_type(self, image_path: str) -> str:
        """根据图片路径获取坦克类型"""
        if 'green' in image_path.lower():
            return "green"
        elif 'desert' in image_path.lower() or 'yellow' in image_path.lower():
            return "yellow"
        elif 'blue' in image_path.lower():
            return "blue"
        elif 'grey' in image_path.lower():
            return "grey"
        return "green"

    def _start_host_game(self, tank_info: Dict[str, Any]):
        """主机开始游戏"""
        from .network_views import NetworkHostView

        # 创建主机视图并传递坦克信息
        host_view = NetworkHostView()
        host_view.host_tank_info = tank_info

        if host_view.start_hosting(self.room_name):
            self.window.show_view(host_view)
        else:
            print("启动主机失败")
            self.ready_to_start = False

    def _send_client_ready(self, tank_info: Dict[str, Any]):
        """客户端发送准备信息"""
        from .network_views import NetworkClientView

        # 创建客户端视图并传递坦克信息
        client_view = NetworkClientView()
        client_view.client_tank_info = tank_info

        if client_view.connect_to_room(self.host_ip, self.host_port, "Player"):
            self.window.show_view(client_view)
        else:
            print("连接到主机失败")
            self.ready_to_start = False
