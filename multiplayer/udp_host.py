"""
主机端网络处理

实现游戏主机的网络功能，包括客户端连接管理、游戏状态广播等
"""

import socket
import threading
import time
import uuid
from typing import Dict, Optional, Callable, Tuple, List
from .udp_messages import UDPMessage, MessageType, MessageFactory
from .udp_discovery import RoomAdvertiser


class ClientInfo:
    """客户端信息类"""
    
    def __init__(self, client_id: str, address: Tuple[str, int], player_name: str):
        self.client_id = client_id
        self.address = address
        self.player_name = player_name
        self.last_heartbeat = time.time()
        self.connected = True
        
        # 玩家输入状态
        self.current_keys = set()
        
    def update_heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = time.time()
        
    def is_timeout(self, timeout: float = 3.0) -> bool:
        """检查是否超时"""
        return time.time() - self.last_heartbeat > timeout
        
    def update_input(self, keys_pressed: List[str], keys_released: List[str]):
        """更新输入状态"""
        for key in keys_pressed:
            self.current_keys.add(key)
        for key in keys_released:
            self.current_keys.discard(key)


class GameHost:
    """游戏主机类"""
    
    def __init__(self, host_port: int = 12346, max_players: int = 4):
        self.host_port = host_port
        self.max_players = max_players
        
        # 网络相关
        self.host_socket: Optional[socket.socket] = None
        self.running = False
        self.network_thread: Optional[threading.Thread] = None
        
        # 客户端管理
        self.clients: Dict[str, ClientInfo] = {}
        self.host_player_id = "host"
        
        # 房间广播
        self.room_advertiser = RoomAdvertiser()
        self.room_name = ""
        
        # 回调函数
        self.client_join_callback: Optional[Callable] = None
        self.client_leave_callback: Optional[Callable] = None
        self.input_received_callback: Optional[Callable] = None
        
        # 游戏状态广播
        self.game_state_callback: Optional[Callable] = None
        self.broadcast_interval = 1.0 / 30.0  # 30Hz
        self.last_broadcast_time = 0
        
    def set_callbacks(self, client_join: Callable = None, client_leave: Callable = None,
                     input_received: Callable = None, game_state: Callable = None):
        """设置回调函数"""
        if client_join:
            self.client_join_callback = client_join
        if client_leave:
            self.client_leave_callback = client_leave
        if input_received:
            self.input_received_callback = input_received
        if game_state:
            self.game_state_callback = game_state
    
    def start_hosting(self, room_name: str) -> bool:
        """开始主机服务"""
        if self.running:
            return False
            
        self.room_name = room_name
        
        try:
            # 创建UDP套接字
            self.host_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.host_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.host_socket.bind(('', self.host_port))
            self.host_socket.settimeout(0.1)  # 100ms超时
            
            self.running = True
            
            # 启动网络处理线程
            self.network_thread = threading.Thread(target=self._network_loop, daemon=True)
            self.network_thread.start()
            
            # 开始房间广播
            self.room_advertiser.start_advertising(
                room_name, self.get_current_player_count(), self.max_players
            )
            
            print(f"游戏主机已启动: {room_name} (端口 {self.host_port})")
            return True
            
        except Exception as e:
            print(f"启动游戏主机失败: {e}")
            self.stop_hosting()
            return False
    
    def stop_hosting(self):
        """停止主机服务"""
        self.running = False
        
        # 停止房间广播
        self.room_advertiser.stop_advertising()
        
        # 通知所有客户端断开连接
        for client in self.clients.values():
            self._send_to_client(client, MessageFactory.create_disconnect(
                self.host_player_id, "host_shutdown"
            ))
        
        # 关闭网络
        if self.host_socket:
            self.host_socket.close()
            self.host_socket = None
            
        if self.network_thread:
            self.network_thread.join(timeout=2.0)
            self.network_thread = None
            
        self.clients.clear()
        print("游戏主机已停止")
    
    def get_current_player_count(self) -> int:
        """获取当前玩家数量（包括主机）"""
        return 1 + len([c for c in self.clients.values() if c.connected])
    
    def get_connected_players(self) -> List[str]:
        """获取所有连接的玩家ID"""
        players = [self.host_player_id]
        players.extend([c.client_id for c in self.clients.values() if c.connected])
        return players
    
    def broadcast_game_state(self, game_state_data: dict):
        """广播游戏状态"""
        current_time = time.time()
        if current_time - self.last_broadcast_time < self.broadcast_interval:
            return
            
        message = MessageFactory.create_game_state(
            game_state_data.get("tanks", []),
            game_state_data.get("bullets", []),
            game_state_data.get("round_info", {})
        )
        
        # 发送给所有连接的客户端
        for client in self.clients.values():
            if client.connected:
                self._send_to_client(client, message)
                
        self.last_broadcast_time = current_time
    
    def get_client_input(self, client_id: str) -> set:
        """获取客户端当前输入状态"""
        if client_id in self.clients:
            return self.clients[client_id].current_keys.copy()
        return set()
    
    def _network_loop(self):
        """网络处理主循环"""
        while self.running:
            try:
                # 接收消息
                data, addr = self.host_socket.recvfrom(1024)
                self._handle_client_message(data, addr)
                
            except socket.timeout:
                # 超时是正常的，继续循环
                pass
            except Exception as e:
                if self.running:
                    print(f"网络处理错误: {e}")
            
            # 检查客户端超时
            self._check_client_timeouts()
            
            # 更新房间广播的玩家数量
            self.room_advertiser.update_player_count(self.get_current_player_count())
    
    def _handle_client_message(self, data: bytes, addr: Tuple[str, int]):
        """处理客户端消息"""
        try:
            message = UDPMessage.from_bytes(data)
            
            if message.type == MessageType.JOIN_REQUEST:
                self._handle_join_request(message, addr)
                
            elif message.type == MessageType.PLAYER_INPUT:
                self._handle_player_input(message, addr)
                
            elif message.type == MessageType.HEARTBEAT:
                self._handle_heartbeat(message, addr)
                
            elif message.type == MessageType.PLAYER_DISCONNECT:
                self._handle_disconnect(message, addr)
                
        except ValueError:
            # 忽略无效消息
            pass
    
    def _handle_join_request(self, message: UDPMessage, addr: Tuple[str, int]):
        """处理加入请求"""
        player_name = message.data.get("player_name", "Unknown Player")
        
        # 检查是否已满员
        if self.get_current_player_count() >= self.max_players:
            response = MessageFactory.create_join_response(
                False, reason="房间已满"
            )
            self._send_to_address(addr, response)
            return
        
        # 生成客户端ID
        client_id = f"client_{uuid.uuid4().hex[:8]}"
        
        # 创建客户端信息
        client_info = ClientInfo(client_id, addr, player_name)
        self.clients[client_id] = client_info
        
        # 发送成功响应
        response = MessageFactory.create_join_response(True, client_id)
        self._send_to_address(addr, response)
        
        print(f"玩家 {player_name} ({client_id}) 加入游戏")
        
        # 通知游戏逻辑
        if self.client_join_callback:
            self.client_join_callback(client_id, player_name)
    
    def _handle_player_input(self, message: UDPMessage, addr: Tuple[str, int]):
        """处理玩家输入"""
        client_id = message.player_id
        if client_id not in self.clients:
            return
            
        client = self.clients[client_id]
        client.update_heartbeat()
        
        # 更新输入状态
        keys_pressed = message.data.get("keys_pressed", [])
        keys_released = message.data.get("keys_released", [])
        client.update_input(keys_pressed, keys_released)
        
        # 通知游戏逻辑
        if self.input_received_callback:
            self.input_received_callback(client_id, keys_pressed, keys_released)
    
    def _handle_heartbeat(self, message: UDPMessage, addr: Tuple[str, int]):
        """处理心跳"""
        client_id = message.player_id
        if client_id in self.clients:
            self.clients[client_id].update_heartbeat()
    
    def _handle_disconnect(self, message: UDPMessage, addr: Tuple[str, int]):
        """处理断开连接"""
        client_id = message.player_id
        if client_id in self.clients:
            self._remove_client(client_id, "client_disconnect")
    
    def _check_client_timeouts(self):
        """检查客户端超时"""
        timeout_clients = []
        for client_id, client in self.clients.items():
            if client.connected and client.is_timeout():
                timeout_clients.append(client_id)
        
        for client_id in timeout_clients:
            self._remove_client(client_id, "timeout")
    
    def _remove_client(self, client_id: str, reason: str):
        """移除客户端"""
        if client_id in self.clients:
            client = self.clients[client_id]
            client.connected = False
            
            print(f"玩家 {client.player_name} ({client_id}) 离开游戏: {reason}")
            
            # 通知游戏逻辑
            if self.client_leave_callback:
                self.client_leave_callback(client_id, reason)
            
            # 从列表中删除
            del self.clients[client_id]
    
    def _send_to_client(self, client: ClientInfo, message: UDPMessage):
        """发送消息给客户端"""
        try:
            self.host_socket.sendto(message.to_bytes(), client.address)
        except Exception as e:
            print(f"发送消息给客户端失败: {e}")
    
    def _send_to_address(self, addr: Tuple[str, int], message: UDPMessage):
        """发送消息到指定地址"""
        try:
            self.host_socket.sendto(message.to_bytes(), addr)
        except Exception as e:
            print(f"发送消息失败: {e}")
