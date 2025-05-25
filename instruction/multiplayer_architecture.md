# 多人联机架构设计文档

## 总体架构

### 1. 网络架构选择
- **采用方案**: 局域网UDP广播 + 主从模式
- **适用场景**: 同一WiFi/局域网内的朋友对战
- **优势**: 实现简单、延迟极低、无需专用服务器

### 2. 技术栈
- **网络协议**: UDP广播 + 点对点通信
- **主机端**: 现有Arcade + Pymunk + UDP服务器
- **客户端**: 轻量级输入发送 + 状态接收
- **消息格式**: JSON (简单易调试)
- **同步策略**: 主机权威 + 客户端输入转发

## 实现步骤

### 抽离网络模块到D:\VSTank\tank\multiplayer中  

### 阶段1: 基础UDP网络 (1-2天)
1. 实现UDP广播房间发现
2. 建立主机-客户端连接
3. 基础消息收发
4. 简单的连接管理

### 阶段2: 游戏数据同步 (2-3天)
1. 主机端集成现有游戏逻辑
2. 客户端输入采集和发送
3. 游戏状态广播
4. 基础的网络游戏视图

### 阶段3: 优化完善 (1天)
1. 断线检测和处理
2. 网络延迟优化
3. 错误处理和重连

## 核心组件设计

### 1. UDP网络发现组件
```python
# udp_discovery.py
class RoomDiscovery:
    def __init__(self, broadcast_port=12345):
        self.broadcast_port = broadcast_port
        self.rooms = {}
    
    def start_discovery(self):
        # 启动UDP广播监听，发现局域网内的游戏房间
        pass
    
    def advertise_room(self, room_info):
        # 广播房间信息
        pass

class GameHost:
    def __init__(self, host_port=12346):
        self.host_port = host_port
        self.clients = {}
        self.game_view = None
    
    def start_hosting(self):
        # 开启UDP服务器，等待客户端连接
        pass
    
    def broadcast_game_state(self):
        # 向所有客户端广播游戏状态
        pass
    
    def handle_client_input(self, client_id, input_data):
        # 处理客户端输入
        pass
```

### 2. 客户端组件
```python
# udp_client.py
class GameClient:
    def __init__(self):
        self.host_address = None
        self.client_socket = None
        self.player_id = None
    
    def discover_rooms(self):
        # 搜索局域网内的游戏房间
        pass
    
    def join_room(self, host_ip, host_port):
        # 连接到指定主机
        pass
    
    def send_input(self, input_data):
        # 发送输入数据到主机
        pass
    
    def receive_game_state(self):
        # 接收并处理游戏状态更新
        pass

# 轻量级游戏视图
class NetworkClientView(arcade.View):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.game_state = {}
    
    def on_key_press(self, key, modifiers):
        # 发送按键到主机而不是本地处理
        input_data = {"key": key, "action": "press"}
        self.client.send_input(input_data)
    
    def update_from_host(self, game_state):
        # 根据主机状态更新本地显示
        pass
```

### 3. 消息协议 (简化版)
```python
# udp_messages.py
import json
import time

class MessageType:
    ROOM_ADVERTISE = "room_advertise"    # 房间广播
    JOIN_REQUEST = "join_request"        # 加入请求
    JOIN_RESPONSE = "join_response"      # 加入响应
    PLAYER_INPUT = "player_input"        # 玩家输入
    GAME_STATE = "game_state"           # 游戏状态
    PLAYER_DISCONNECT = "disconnect"     # 玩家断线

class UDPMessage:
    def __init__(self, msg_type, data, player_id=None):
        self.type = msg_type
        self.data = data
        self.player_id = player_id
        self.timestamp = time.time()
    
    def to_bytes(self):
        msg_dict = {
            "type": self.type,
            "data": self.data,
            "player_id": self.player_id,
            "timestamp": self.timestamp
        }
        return json.dumps(msg_dict).encode('utf-8')
    
    @classmethod
    def from_bytes(cls, data):
        msg_dict = json.loads(data.decode('utf-8'))
        return cls(msg_dict["type"], msg_dict["data"], msg_dict.get("player_id"))

# 示例消息格式
ROOM_ADVERTISE_MSG = {
    "type": "room_advertise",
    "data": {
        "room_name": "Player1's Room",
        "current_players": 1,
        "max_players": 4,
        "game_mode": "pvp"
    }
}

PLAYER_INPUT_MSG = {
    "type": "player_input",
    "player_id": "client_001",
    "data": {
        "keys_pressed": ["W", "SPACE"],
        "keys_released": ["A"]
    }
}

GAME_STATE_MSG = {
    "type": "game_state",
    "data": {
        "tanks": [
            {
                "player_id": "host",
                "position": [100, 200],
                "angle": 45,
                "health": 5
            },
            {
                "player_id": "client_001", 
                "position": [300, 400],
                "angle": 90,
                "health": 3
            }
        ],
        "bullets": [
            {
                "id": "bullet_1",
                "position": [150, 250],
                "angle": 45,
                "owner": "host"
            }
        ],
        "round_info": {
            "player1_score": 1,
            "player2_score": 0,
            "round_over": False
        }
    }
}
```

## 同步策略

### 1. 主机权威模式
- 主机运行完整的游戏逻辑和物理模拟
- 客户端只发送输入，不进行游戏逻辑处理
- 主机定期(30-60Hz)向客户端广播游戏状态
- 客户端接收状态并更新显示

### 2. 输入处理流程
```
客户端: 按键 → UDP发送 → 主机
主机: 接收输入 → 应用到游戏 → 物理更新 → 广播状态
客户端: 接收状态 → 更新显示
```

### 3. 连接管理
- 心跳检测：每秒发送心跳包
- 超时处理：3秒无响应视为断线
- 自动重连：客户端断线后自动尝试重连

## 网络优化

### 1. 局域网优化
- 使用UDP减少延迟
- 广播发现减少配置复杂度
- 简化协议提高传输效率

### 2. 数据压缩
- 只传输必要的游戏状态
- 使用相对位置减少数据量
- 客户端缓存减少重复传输

### 3. 频率控制
- 输入发送: 按需发送(按键时)
- 状态广播: 30Hz (每33ms一次)
- 房间发现: 每2秒广播一次

## 部署和使用

### 开发测试
1. 确保所有设备在同一局域网
2. 关闭防火墙或开放UDP端口12345-12346
3. 一台设备创建房间(主机模式)
4. 其他设备搜索并加入房间

### 用户使用流程
1. 主机玩家: 选择"创建房间" → 等待其他玩家
2. 客户端玩家: 选择"加入房间" → 选择要加入的房间
3. 开始游戏: 主机控制游戏开始和回合管理

## 文件结构 (模块化设计)
```
tank/
├── multiplayer/          # 多人游戏模块(独立)
│   ├── __init__.py
│   ├── udp_discovery.py  # 房间发现和广播
│   ├── udp_host.py       # 主机端网络处理
│   ├── udp_client.py     # 客户端网络处理  
│   ├── udp_messages.py   # 消息协议定义
│   └── network_views.py  # 网络游戏视图
├── game_views.py         # 原有单机游戏视图
├── tank_sprites.py       # 坦克和子弹类(共用)
├── maps.py              # 地图系统(共用)
└── main.py              # 游戏入口
```

## 实现优先级

### 第一阶段 (核心功能)
1. UDP房间发现和连接
2. 基础输入发送和状态接收
3. 简单的多人游戏视图

### 第二阶段 (稳定性)
1. 断线检测和重连
2. 错误处理和异常恢复
3. 网络延迟优化

### 第三阶段 (用户体验)
1. 房间管理界面优化
2. 连接状态显示
3. 网络质量指示器
