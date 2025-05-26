"""
网络游戏视图

实现多人游戏的用户界面，包括房间浏览、主机视图、客户端视图等
"""

import arcade
import threading
from typing import Dict, Optional, List
from .udp_discovery import RoomDiscovery, RoomInfo
from .udp_host import GameHost
from .udp_client import GameClient


class RoomBrowserView(arcade.View):
    """房间浏览视图"""

    def __init__(self):
        super().__init__()
        self.room_discovery = RoomDiscovery()
        self.available_rooms: Dict[str, RoomInfo] = {}
        self.selected_room_index = 0
        self.player_name = "Player"

        # UI状态
        self.refresh_timer = 0
        self.refresh_interval = 1.0  # 1秒刷新一次显示

        # 房间名输入状态
        self.input_mode = False  # 是否在输入房间名
        self.custom_room_name = ""  # 自定义房间名
        self.cursor_visible = True
        self.cursor_timer = 0

    def on_show_view(self):
        """显示视图时的初始化"""
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)

        # 设置房间更新回调
        self.room_discovery.set_room_update_callback(self._on_rooms_updated)

        # 开始房间发现
        self.room_discovery.start_discovery()

    def on_hide_view(self):
        """隐藏视图时的清理"""
        self.room_discovery.stop_discovery()

    def on_draw(self):
        """绘制视图"""
        self.clear()

        if self.input_mode:
            # 绘制房间名输入界面
            self._draw_room_name_input()
        else:
            # 绘制房间列表界面
            self._draw_room_list()

    def _draw_room_list(self):
        """绘制房间列表界面"""
        # 标题
        arcade.draw_text("多人游戏 - 房间列表",
                        self.window.width // 2, self.window.height - 80,
                        arcade.color.WHITE, font_size=32, anchor_x="center")

        # 操作说明
        arcade.draw_text("↑↓ 选择房间 | Enter 加入 | C 创建房间 | Esc 返回",
                        self.window.width // 2, self.window.height - 120,
                        arcade.color.LIGHT_GRAY, font_size=16, anchor_x="center")

        # 房间列表
        if self.available_rooms:
            y_start = self.window.height - 200
            room_list = list(self.available_rooms.values())

            for i, room in enumerate(room_list):
                y_pos = y_start - i * 60

                # 选中高亮
                if i == self.selected_room_index:
                    # 使用新的API绘制矩形
                    arcade.draw_lrbt_rectangle_filled(
                        50, self.window.width - 50,  # bottom, top
                        y_pos - 50, y_pos + 50,      # left, right
                        arcade.color.DARK_GRAY
                    )

                # 房间信息
                room_text = f"{room.room_name} ({room.current_players}/{room.max_players})"
                arcade.draw_text(room_text,
                               self.window.width // 2, y_pos + 10,
                               arcade.color.WHITE, font_size=18, anchor_x="center")

                # 主机IP
                arcade.draw_text(f"主机: {room.host_ip}",
                               self.window.width // 2, y_pos - 10,
                               arcade.color.WHITE, font_size=12, anchor_x="center")
        else:
            arcade.draw_text("正在搜索房间...",
                           self.window.width // 2, self.window.height // 2,
                           arcade.color.LIGHT_GRAY, font_size=20, anchor_x="center")

    def _draw_room_name_input(self):
        """绘制房间名输入界面"""
        # 标题
        arcade.draw_text("创建房间",
                        self.window.width // 2, self.window.height - 80,
                        arcade.color.WHITE, font_size=32, anchor_x="center")

        # 说明
        arcade.draw_text("请输入房间名称:",
                        self.window.width // 2, self.window.height - 150,
                        arcade.color.LIGHT_GRAY, font_size=18, anchor_x="center")

        # 输入框背景
        input_box_width = 400
        input_box_height = 50
        input_box_x = self.window.width // 2
        input_box_y = self.window.height // 2

        arcade.draw_lrbt_rectangle_filled(
            input_box_x - input_box_width // 2, input_box_x + input_box_width // 2,
            input_box_y - input_box_height // 2, input_box_y + input_box_height // 2,
            arcade.color.WHITE
        )

        # 输入框边框
        arcade.draw_lrbt_rectangle_outline(
            input_box_x - input_box_width // 2, input_box_x + input_box_width // 2,
            input_box_y - input_box_height // 2, input_box_y + input_box_height // 2,
            arcade.color.BLACK, 2
        )

        # 显示输入的文本
        display_text = self.custom_room_name
        if self.cursor_visible:
            display_text += "|"

        arcade.draw_text(display_text,
                        input_box_x, input_box_y,
                        arcade.color.BLACK, font_size=16, anchor_x="center")

        # 操作说明
        arcade.draw_text("Enter 确认创建  Esc 取消",
                        self.window.width // 2, self.window.height // 2 - 100,
                        arcade.color.LIGHT_GRAY, font_size=16, anchor_x="center")

    def on_update(self, delta_time):
        """更新逻辑"""
        self.refresh_timer += delta_time
        if self.refresh_timer >= self.refresh_interval:
            self.refresh_timer = 0
            # 触发重绘以更新房间列表显示

        # 处理光标闪烁
        if self.input_mode:
            self.cursor_timer += delta_time
            if self.cursor_timer >= 0.5:  # 每0.5秒闪烁一次
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0

    def on_key_press(self, key, modifiers):
        """处理按键事件"""
        if self.input_mode:
            # 房间名输入模式
            self._handle_input_mode_keys(key)
        else:
            # 房间列表模式
            self._handle_room_list_keys(key)

    def _handle_input_mode_keys(self, key):
        """处理输入模式的按键"""
        if key == arcade.key.ESCAPE:
            # 取消输入，返回房间列表
            self.input_mode = False
            self.custom_room_name = ""

        elif key == arcade.key.ENTER:
            # 确认创建房间
            if self.custom_room_name.strip():
                self._create_room_with_name(self.custom_room_name.strip())
            else:
                # 如果没有输入房间名，使用默认名称
                self._create_room_with_name(f"{self.player_name}的房间")

        elif key == arcade.key.BACKSPACE:
            # 删除字符
            if self.custom_room_name:
                self.custom_room_name = self.custom_room_name[:-1]

    def _handle_room_list_keys(self, key):
        """处理房间列表模式的按键"""
        if key == arcade.key.ESCAPE:
            # 返回主菜单
            from game_views import ModeSelectView
            mode_view = ModeSelectView()
            self.window.show_view(mode_view)

        elif key == arcade.key.UP:
            # 向上选择
            if self.available_rooms:
                self.selected_room_index = max(0, self.selected_room_index - 1)

        elif key == arcade.key.DOWN:
            # 向下选择
            if self.available_rooms:
                self.selected_room_index = min(
                    len(self.available_rooms) - 1,
                    self.selected_room_index + 1
                )

        elif key == arcade.key.ENTER:
            # 加入选中的房间
            self._join_selected_room()

        elif key == arcade.key.C:
            # 进入房间名输入模式
            self.input_mode = True
            self.custom_room_name = ""
            self.cursor_visible = True
            self.cursor_timer = 0

    def _on_rooms_updated(self, rooms: Dict[str, RoomInfo]):
        """房间列表更新回调"""
        self.available_rooms = rooms
        # 确保选中索引有效
        if self.selected_room_index >= len(rooms):
            self.selected_room_index = max(0, len(rooms) - 1)

    def _join_selected_room(self):
        """加入选中的房间"""
        if not self.available_rooms:
            return

        room_list = list(self.available_rooms.values())
        if 0 <= self.selected_room_index < len(room_list):
            selected_room = room_list[self.selected_room_index]

            # 创建客户端视图
            client_view = NetworkClientView()
            if client_view.connect_to_room(selected_room.host_ip, 12346, self.player_name):
                self.window.show_view(client_view)
            else:
                print("连接房间失败")

    def _create_room_with_name(self, room_name: str):
        """使用指定名称创建房间"""
        host_view = NetworkHostView()
        host_view.start_hosting(room_name)
        self.window.show_view(host_view)

    def on_text(self, text: str):
        """处理文本输入"""
        if self.input_mode:
            # 只允许输入字母、数字、中文和一些常用符号
            allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_()[]{}的房间游戏"
            if text in allowed_chars or ord(text) > 127:  # 允许中文字符
                if len(self.custom_room_name) < 20:  # 限制房间名长度
                    self.custom_room_name += text


class NetworkHostView(arcade.View):
    """网络主机视图"""

    def __init__(self):
        super().__init__()
        self.game_host = GameHost()
        self.connected_players: List[str] = ["host"]  # 包括主机自己
        self.game_started = False

        # 游戏相关（复用现有GameView的逻辑）
        self.game_view = None

    def start_hosting(self, room_name: str) -> bool:
        """开始主机服务"""
        # 设置回调
        self.game_host.set_callbacks(
            client_join=self._on_client_join,
            client_leave=self._on_client_leave,
            input_received=self._on_input_received
        )

        return self.game_host.start_hosting(room_name)

    def on_show_view(self):
        """显示视图时的初始化"""
        arcade.set_background_color(arcade.color.DARK_GREEN)

    def on_hide_view(self):
        """隐藏视图时的清理"""
        self.game_host.stop_hosting()

    def on_draw(self):
        """绘制视图"""
        self.clear()

        if not self.game_started:
            # 等待玩家界面
            arcade.draw_text("等待玩家加入",
                           self.window.width // 2, self.window.height - 100,
                           arcade.color.WHITE, font_size=32, anchor_x="center")

            # 显示已连接的玩家
            y_pos = self.window.height - 200
            for i, player in enumerate(self.connected_players):
                arcade.draw_text(f"玩家 {i+1}: {player}",
                               self.window.width // 2, y_pos - i * 30,
                               arcade.color.WHITE, font_size=18, anchor_x="center")

            # 操作说明
            arcade.draw_text("Space 开始游戏  Esc 返回",
                           self.window.width // 2, 100,
                           arcade.color.LIGHT_GRAY, font_size=16, anchor_x="center")
        else:
            # 游戏进行中，由游戏视图处理绘制
            if self.game_view:
                self.game_view.on_draw()

    def on_key_press(self, key, modifiers):
        """处理按键事件"""
        if key == arcade.key.ESCAPE and not self.game_started:
            # 返回房间浏览
            browser_view = RoomBrowserView()
            self.window.show_view(browser_view)

        elif key == arcade.key.SPACE and not self.game_started:
            # 开始游戏
            if len(self.connected_players) >= 2:
                self._start_game()

        elif self.game_started and self.game_view:
            # 转发给游戏视图
            self.game_view.on_key_press(key, modifiers)

    def on_update(self, delta_time):
        """更新逻辑"""
        if self.game_started and self.game_view:
            self.game_view.on_update(delta_time)

            # 广播游戏状态
            game_state = self._get_game_state()
            self.game_host.broadcast_game_state(game_state)

    def _on_client_join(self, client_id: str, player_name: str):
        """客户端加入回调"""
        self.connected_players.append(f"{player_name} ({client_id})")
        print(f"玩家加入: {player_name}")

    def _on_client_leave(self, client_id: str, reason: str):
        """客户端离开回调"""
        # 从列表中移除玩家
        self.connected_players = [p for p in self.connected_players
                                if not p.endswith(f"({client_id})")]
        print(f"玩家离开: {client_id} ({reason})")

    def _on_input_received(self, client_id: str, keys_pressed: List[str], keys_released: List[str]):
        """输入接收回调"""
        if self.game_started and self.game_view:
            # 将客户端输入应用到对应的坦克
            # 这里需要根据实际游戏逻辑来实现
            pass

    def _start_game(self):
        """开始游戏"""
        # 创建网络游戏视图（基于现有GameView）
        try:
            from ..game_views import GameView
        except ImportError:
            # 如果相对导入失败，尝试绝对导入
            from game_views import GameView
        self.game_view = GameView(mode="network_host")
        self.game_view.setup()
        self.game_started = True
        print("游戏开始!")

    def _get_game_state(self) -> dict:
        """获取当前游戏状态"""
        if not self.game_view:
            return {}

        # 提取游戏状态信息
        tanks = []
        bullets = []

        # 坦克状态
        for tank in self.game_view.player_list:
            tank_data = {
                "player_id": getattr(tank, 'player_id', 'unknown'),
                "position": [tank.center_x, tank.center_y],
                "angle": tank.angle,
                "health": tank.health,
                "tank_image": getattr(tank, 'tank_image_file', '')
            }
            tanks.append(tank_data)

        # 子弹状态
        for bullet in self.game_view.bullet_list:
            bullet_data = {
                "id": id(bullet),
                "position": [bullet.center_x, bullet.center_y],
                "angle": bullet.angle,
                "owner": getattr(bullet.owner, 'player_id', 'unknown') if bullet.owner else 'unknown'
            }
            bullets.append(bullet_data)

        # 回合信息
        round_info = {
            "scores": {
                "player1": self.game_view.player1_score,
                "player2": self.game_view.player2_score
            },
            "round_over": self.game_view.round_over,
            "game_over": max(self.game_view.player1_score, self.game_view.player2_score) >= self.game_view.max_score,
            "winner": None
        }

        return {
            "tanks": tanks,
            "bullets": bullets,
            "round_info": round_info
        }


class NetworkClientView(arcade.View):
    """网络客户端视图"""

    def __init__(self):
        super().__init__()
        self.game_client = GameClient()
        self.game_state = {}
        self.connected = False

        # 显示相关
        self.sprite_lists = {
            "tanks": arcade.SpriteList(),
            "bullets": arcade.SpriteList(),
            "walls": arcade.SpriteList()
        }

    def connect_to_room(self, host_ip: str, host_port: int, player_name: str) -> bool:
        """连接到房间"""
        # 设置回调
        self.game_client.set_callbacks(
            connection=self._on_connected,
            disconnection=self._on_disconnected,
            game_state=self._on_game_state_update
        )

        return self.game_client.connect_to_host(host_ip, host_port, player_name)

    def on_show_view(self):
        """显示视图时的初始化"""
        arcade.set_background_color(arcade.color.LIGHT_GRAY)

    def on_hide_view(self):
        """隐藏视图时的清理"""
        self.game_client.disconnect()

    def on_draw(self):
        """绘制视图"""
        self.clear()

        if self.connected:
            # 绘制游戏内容
            for sprite_list in self.sprite_lists.values():
                sprite_list.draw()

            # 绘制UI信息
            arcade.draw_text(f"玩家ID: {self.game_client.get_player_id()}",
                           10, self.window.height - 30,
                           arcade.color.BLACK, font_size=16)
        else:
            arcade.draw_text("连接中...",
                           self.window.width // 2, self.window.height // 2,
                           arcade.color.BLACK, font_size=24, anchor_x="center")

    def on_key_press(self, key, modifiers):
        """处理按键事件"""
        if key == arcade.key.ESCAPE:
            # 返回房间浏览
            browser_view = RoomBrowserView()
            self.window.show_view(browser_view)
        else:
            # 发送按键到服务器
            key_name = self._get_key_name(key)
            if key_name:
                self.game_client.send_key_press(key_name)

    def on_key_release(self, key, modifiers):
        """处理按键释放事件"""
        key_name = self._get_key_name(key)
        if key_name:
            self.game_client.send_key_release(key_name)

    def _get_key_name(self, key) -> Optional[str]:
        """获取按键名称"""
        key_map = {
            arcade.key.W: "W",
            arcade.key.A: "A",
            arcade.key.S: "S",
            arcade.key.D: "D",
            arcade.key.SPACE: "SPACE",
            arcade.key.UP: "UP",
            arcade.key.DOWN: "DOWN",
            arcade.key.LEFT: "LEFT",
            arcade.key.RIGHT: "RIGHT",
            arcade.key.ENTER: "ENTER"
        }
        return key_map.get(key)

    def _on_connected(self, player_id: str):
        """连接成功回调"""
        self.connected = True
        print(f"已连接，玩家ID: {player_id}")

    def _on_disconnected(self, reason: str):
        """断开连接回调"""
        self.connected = False
        print(f"连接断开: {reason}")

        # 返回房间浏览
        browser_view = RoomBrowserView()
        self.window.show_view(browser_view)

    def _on_game_state_update(self, game_state: dict):
        """游戏状态更新回调"""
        self.game_state = game_state
        self._update_sprites_from_state()

    def _update_sprites_from_state(self):
        """根据游戏状态更新精灵"""
        if not self.game_state:
            return

        # 更新坦克
        tanks_data = self.game_state.get("tanks", [])
        self.sprite_lists["tanks"].clear()

        for tank_data in tanks_data:
            # 创建坦克精灵（简化版，只用于显示）
            tank_sprite = arcade.Sprite(scale=0.08)
            tank_sprite.center_x = tank_data["position"][0]
            tank_sprite.center_y = tank_data["position"][1]
            tank_sprite.angle = tank_data["angle"]

            # 根据玩家ID设置颜色
            player_id = tank_data.get("player_id", "unknown")
            if player_id == "host":
                tank_sprite.color = arcade.color.GREEN
            else:
                tank_sprite.color = arcade.color.BLUE

            self.sprite_lists["tanks"].append(tank_sprite)

        # 更新子弹
        bullets_data = self.game_state.get("bullets", [])
        self.sprite_lists["bullets"].clear()

        for bullet_data in bullets_data:
            bullet_sprite = arcade.SpriteCircle(4, arcade.color.YELLOW)
            bullet_sprite.center_x = bullet_data["position"][0]
            bullet_sprite.center_y = bullet_data["position"][1]
            bullet_sprite.angle = bullet_data["angle"]
            self.sprite_lists["bullets"].append(bullet_sprite)
