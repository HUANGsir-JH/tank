**客户端无法与主机正常连接**
在客户端按下enter进入房间后，界面就一直显示“连接中”，但是主机正常，也可以进行tank选择和游戏开始
但是一旦主机按下space开始游戏，客户端就会直接断开连接。

以下是终端输出：  
- **客户端**
  ```bash
  选择了 多人联机 模式
  房间发现已启动，监听端口 12345
  成功连接到主机 172.20.10.8:12346 (玩家ID: client_a9bf56c9)
  已连接，玩家ID: client_a9bf56c9
  房间发现已停止
  Starting new round / Resetting tanks...
  客户端游戏视图初始化完成
  主机坦克图片: D:\VSTank\tank\tank-img\green_tank.png
  客户端坦克图片: D:\VSTank\tank\tank-img\blue_tank.png
  连接丢失: host_shutdown
  连接断开: host_shutdown
  房间发现已启动，监听端口 12345
  ```
- **主机**
  ```bash
  选择了 多人联机 模式
  房间发现已启动，监听端口 12345
  开始广播房间: cc
  游戏主机已启动: cc (端口 12346)
  房间发现已停止
  玩家 Player (client_a9bf56c9) 加入游戏
  玩家加入: Player
  开始坦克选择阶段
  房间广播已停止
  游戏主机已停止
  所有玩家已准备完成，开始游戏！
  Starting new round / Resetting tanks...
  游戏开始! 主机坦克: C:\Users\Lenovo\Desktop\code\learning\tank\tank-img\green_tank.png, 客户端坦克: C:\Users\Lenovo\Desktop\code\learning\tank\tank-img\blue_tank.png
  房间广播已停止
  游戏主机已停止
  ```