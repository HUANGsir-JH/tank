"""
网络游戏视图

实现多人游戏的用户界面，包括房间浏览、主机视图、客户端视图等
"""

import arcade
import threading
import math
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
        """加入选中的房间 - 进入坦克选择"""
        if not self.available_rooms:
            return

        room_list = list(self.available_rooms.values())
        if 0 <= self.selected_room_index < len(room_list):
            selected_room = room_list[self.selected_room_index]

            # 进入坦克选择界面
            from .network_tank_selection import NetworkTankSelectionView
            tank_selection_view = NetworkTankSelectionView(
                is_host=False,
                host_ip=selected_room.host_ip,
                host_port=12346
            )
            self.window.show_view(tank_selection_view)

    def _create_room_with_name(self, room_name: str):
        """使用指定名称创建房间 - 进入坦克选择"""
        from .network_tank_selection import NetworkTankSelectionView
        tank_selection_view = NetworkTankSelectionView(is_host=True, room_name=room_name)
        self.window.show_view(tank_selection_view)

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

        # 坦克选择信息
        self.host_tank_info = None  # 主机坦克信息
        self.client_tank_info = {}  # 客户端坦克信息 {client_id: tank_info}

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

        # 传递坦克选择信息
        player1_tank_image = None
        player2_tank_image = None

        if self.host_tank_info:
            player1_tank_image = self.host_tank_info.get("image_path")

        # 获取第一个客户端的坦克信息
        if self.client_tank_info:
            first_client_info = list(self.client_tank_info.values())[0]
            player2_tank_image = first_client_info.get("image_path")

        self.game_view = GameView(
            mode="network_host",
            player1_tank_image=player1_tank_image,
            player2_tank_image=player2_tank_image
        )
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

        # 坦克状态 - 优化数据大小
        for tank in self.game_view.player_list:
            # 简化坦克图片信息，只传递类型而不是完整路径
            tank_image_file = getattr(tank, 'tank_image_file', '')
            tank_type = "green"  # 默认
            if tank_image_file:
                if 'green' in tank_image_file.lower():
                    tank_type = "green"
                elif 'desert' in tank_image_file.lower() or 'yellow' in tank_image_file.lower():
                    tank_type = "yellow"
                elif 'blue' in tank_image_file.lower():
                    tank_type = "blue"
                elif 'grey' in tank_image_file.lower():
                    tank_type = "grey"

            tank_data = {
                "id": getattr(tank, 'player_id', 'unknown'),
                "pos": [round(tank.center_x, 1), round(tank.center_y, 1)],  # 减少精度
                "ang": round(tank.angle, 1),
                "hp": tank.health,
                "type": tank_type
            }
            tanks.append(tank_data)

        # 子弹状态 - 优化数据大小
        for i, bullet in enumerate(self.game_view.bullet_list):
            bullet_data = {
                "id": i,  # 使用索引而不是内存地址
                "pos": [round(bullet.center_x, 1), round(bullet.center_y, 1)],
                "ang": round(bullet.angle, 1),
                "own": getattr(bullet.owner, 'player_id', 'unk') if bullet.owner else 'unk'
            }
            bullets.append(bullet_data)

        # 回合信息 - 优化数据大小
        round_info = {
            "sc": [self.game_view.player1_score, self.game_view.player2_score],
            "ro": self.game_view.round_over,
            "go": max(self.game_view.player1_score, self.game_view.player2_score) >= self.game_view.max_score
        }

        return {
            "tanks": tanks,
            "bullets": bullets,
            "round_info": round_info
        }


class NetworkClientView(arcade.View):
    """网络客户端视图 - 重构版，集成完整游戏逻辑"""

    def __init__(self):
        super().__init__()
        self.game_client = GameClient()
        self.game_state = {}
        self.connected = False

        # 客户端坦克信息
        self.client_tank_info = None

        # 完整游戏视图（复用GameView的逻辑）
        self.game_view = None
        self.game_initialized = False

        # 线程安全的状态更新队列
        self.pending_updates = []
        self.pending_disconnection = None

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
        self._initialize_game_view()

    def on_hide_view(self):
        """隐藏视图时的清理"""
        self.game_client.disconnect()

    def on_update(self, delta_time):
        """主线程更新 - 处理网络线程的回调"""
        # 处理待处理的游戏状态更新
        while self.pending_updates:
            game_state = self.pending_updates.pop(0)
            self._sync_game_state(game_state)

        # 处理断开连接
        if self.pending_disconnection:
            self.connected = False
            reason = self.pending_disconnection
            self.pending_disconnection = None

            # 在主线程中安全地切换视图
            try:
                browser_view = RoomBrowserView()
                self.window.show_view(browser_view)
            except Exception as e:
                print(f"切换视图时出错: {e}")

        # 更新游戏视图
        if self.game_view and self.connected:
            # 注意：不调用game_view.on_update，因为客户端不处理游戏逻辑
            # 只同步显示状态
            pass

    def on_draw(self):
        """绘制视图"""
        self.clear()

        if self.connected and self.game_view:
            # 使用完整游戏视图进行绘制
            self.game_view.on_draw()

            # 绘制网络状态信息
            arcade.draw_text(f"客户端 - 玩家ID: {self.game_client.get_player_id()}",
                           10, self.window.height - 30,
                           arcade.color.WHITE, font_size=16)
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
        """断开连接回调 - 线程安全"""
        print(f"连接断开: {reason}")
        # 标记需要断开连接，在主线程中处理
        self.pending_disconnection = reason

    def _on_game_state_update(self, game_state: dict):
        """游戏状态更新回调 - 线程安全"""
        # 将游戏状态更新放入队列，在主线程中处理
        self.pending_updates.append(game_state.copy())

    def _initialize_game_view(self):
        """初始化完整的游戏视图"""
        if self.game_initialized:
            return

        try:
            from game_views import GameView

            # 创建完整的游戏视图
            player1_tank_image = None
            player2_tank_image = None

            if self.client_tank_info:
                player2_tank_image = self.client_tank_info.get("image_path")

            self.game_view = GameView(
                mode="network_client",
                player1_tank_image=player1_tank_image,  # 主机坦克，稍后从网络同步
                player2_tank_image=player2_tank_image   # 客户端坦克
            )
            self.game_view.setup()
            self.game_initialized = True
            print("客户端游戏视图初始化完成")

        except Exception as e:
            print(f"初始化游戏视图失败: {e}")

    def _sync_game_state(self, game_state: dict):
        """同步服务器游戏状态到本地游戏视图"""
        if not self.game_view:
            return

        try:
            # 同步坦克状态
            tanks_data = game_state.get("tanks", [])
            if self.game_view.player_list and len(tanks_data) >= len(self.game_view.player_list):
                for i, tank in enumerate(self.game_view.player_list):
                    if i < len(tanks_data):
                        tank_data = tanks_data[i]

                        # 适配优化后的数据格式
                        if "pos" in tank_data:  # 新格式
                            tank.center_x = tank_data["pos"][0]
                            tank.center_y = tank_data["pos"][1]
                            tank.angle = tank_data["ang"]
                            tank.health = tank_data.get("hp", 5)
                        else:  # 兼容旧格式
                            tank.center_x = tank_data["position"][0]
                            tank.center_y = tank_data["position"][1]
                            tank.angle = tank_data["angle"]
                            tank.health = tank_data.get("health", 5)

                        # 同步Pymunk body位置（如果存在）
                        if hasattr(tank, 'pymunk_body') and tank.pymunk_body:
                            tank.pymunk_body.position = (tank.center_x, tank.center_y)
                            tank.pymunk_body.angle = math.radians(tank.angle + 90)  # 转换角度

            # 同步子弹状态
            bullets_data = game_state.get("bullets", [])
            # 清空现有子弹
            self.game_view.bullet_list.clear()

            # 重新创建子弹（简化处理）
            for bullet_data in bullets_data:
                try:
                    from tank_sprites import Bullet

                    # 适配优化后的数据格式
                    if "pos" in bullet_data:  # 新格式
                        bullet = Bullet(bullet_data["pos"][0], bullet_data["pos"][1], bullet_data["ang"])
                    else:  # 兼容旧格式
                        bullet = Bullet(bullet_data["position"][0], bullet_data["position"][1], bullet_data["angle"])

                    self.game_view.bullet_list.append(bullet)
                except Exception as e:
                    print(f"创建子弹失败: {e}")

            # 同步回合信息
            round_info = game_state.get("round_info", {})
            if "sc" in round_info:  # 新格式
                scores = round_info["sc"]
                if len(scores) >= 2:
                    self.game_view.player1_score = scores[0]
                    self.game_view.player2_score = scores[1]
                self.game_view.round_over = round_info.get("ro", False)
            elif "scores" in round_info:  # 兼容旧格式
                self.game_view.player1_score = round_info["scores"].get("player1", 0)
                self.game_view.player2_score = round_info["scores"].get("player2", 0)
                self.game_view.round_over = round_info.get("round_over", False)

        except Exception as e:
            print(f"同步游戏状态失败: {e}")
