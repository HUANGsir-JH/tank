import arcade
import math
import os

# --- 常量 ---
SCREEN_WIDTH = 800 # 暂时保留，以便Tank类中的边界检查，后续可以考虑通过参数传入或从主游戏获取
SCREEN_HEIGHT = 600 # 同上

PLAYER_MOVEMENT_SPEED = 5
PLAYER_TURN_SPEED = 5  # 度/帧
PLAYER_SCALE = 0.8  # 坦克图片的缩放比例

# 坦克图片路径 - 注意：这个路径是相对于调用此模块的文件的，或者使用绝对路径/更灵活的资源管理
# 为了简单起见，我们假设图片在相对于项目根目录的 tank-img 文件夹下
# 在 main.py 中导入时，需要确保路径的正确性

# 获取 tank_sprites.py 文件所在的目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PLAYER_IMAGE_PATH_GREEN = os.path.join(BASE_DIR, "tank-img", "tanks_tankGreen1.png")
PLAYER_IMAGE_PATH_DESERT = os.path.join(BASE_DIR, "tank-img", "tanks_tankDesert1.png") # 示例：玩家2或敌人坦克


class Tank(arcade.Sprite):
    """ 坦克类 """
    def __init__(self, image_file, scale, center_x, center_y, max_speed=PLAYER_MOVEMENT_SPEED, turn_speed_degrees=PLAYER_TURN_SPEED):
        # 检查图片文件是否存在
        # os.path.exists 会相对于当前工作目录。
        # 当从 d:/VSTank/tank/ 运行 main.py 时，image_file "tank-img/tanks_tankGreen1.png" 是正确的。
        if image_file and os.path.exists(image_file):
            super().__init__(image_file, scale)
        elif image_file: # 文件路径提供了，但未找到
            print(f"警告: 坦克图片 '{image_file}' 未找到。将使用红色占位符。")
            # 使用 SpriteSolidColor 作为占位符
            super().__init__(None, scale) # SpriteSolidColor 不需要 filename
            self.texture = arcade.make_circle_texture(int(30 * scale), arcade.color.RED) # 临时代替，SpriteSolidColor用法不同
            # 正确的占位符创建方式是直接实例化一个不同类型的Sprite或在父类初始化后设置颜色
            # 为了简单，我们先用一个红色圆形纹理代替，或者在父类初始化后修改texture
            # 更佳的方式是：
            # super().__init__()
            # self.texture = arcade.make_soft_square_texture(int(50*scale), arcade.color.RED, outer_alpha=255)
            # self.scale = scale
            # self.center_x = center_x
            # self.center_y = center_y
            # 然而，SpriteSolidColor 更简单:
            # 我们将在下面正确使用 SpriteSolidColor 的逻辑
            # 此处暂时保留一个能工作的占位符逻辑，但下面会改进
            # 实际上，如果图片未找到，我们应该创建一个纯色精灵
            # 我们将调整逻辑，如果图片不存在，则不调用 super().__init__(image_file, scale)
            # 而是调用 super().__init__() 并手动设置属性或使用 SpriteSolidColor
            # 让我们简化这个逻辑：
            # 如果图片有效，则加载。否则，创建一个纯色精灵。
            # Arcade 的 Sprite 类在找不到文件时会抛出错误，所以我们必须先检查。
            pass # 下面会处理占位符
        else: # image_file 为 None
            print(f"信息: 未提供坦克图片。将使用蓝色占位符。")
            pass # 下面会处理占位符

        # 正确的初始化逻辑：
        if image_file and os.path.exists(image_file):
            super().__init__(image_file, scale)
            # 移除初始角度校正，让坦克以图片原始朝向显示 (self.angle 默认为 0)
        else:
            # 如果图片未找到或未提供，创建一个纯色方块作为占位符
            # 占位符默认朝上
            # SpriteSolidColor 的构造函数是 (width, height, color)
            # 我们需要估算坦克的尺寸
            tank_width = int(50 * scale)  # 假设坦克大致宽度
            tank_height = int(60 * scale) # 假设坦克大致高度
            placeholder_color = arcade.color.RED if image_file else arcade.color.BLUE # 如果尝试加载但失败则为红色，否则为蓝色
            
            # SpriteSolidColor 不是这样用的，它是独立的类。
            # 我们需要创建一个普通的 Sprite，然后给它一个纯色纹理。
            super().__init__(scale=scale) # 初始化空的 Sprite
            self.texture = arcade.make_soft_square_texture(tank_width, placeholder_color, outer_alpha=255)
            # 或者使用硬边矩形
            # self.texture = arcade.make_rectangle_texture(tank_width, tank_height, placeholder_color)

        self.angle = 0 # 坦克的初始角度 (0度朝上)
        self.center_x = center_x
        self.center_y = center_y
        self.speed = 0
        self.angle_speed = 0  # 角度变化速度 (如果需要平滑旋转)
        self.max_speed = max_speed
        self.turn_speed_degrees = turn_speed_degrees  # 每帧旋转的角度
        self.health = 5 # 初始生命值为5
        self.max_health = 5 # 最大生命值，用于绘制血条

    def take_damage(self, amount):
        """坦克受到伤害"""
        self.health -= amount
        if self.health < 0:
            self.health = 0
        print(f"Tank at ({self.center_x:.0f},{self.center_y:.0f}) took {amount} damage, health: {self.health}")

    def is_alive(self):
        """检查坦克是否还有生命值"""
        return self.health > 0

    def update(self, delta_time: float = 1/60): # 添加 delta_time 参数
        # 更新角度
        self.angle += self.angle_speed # angle_speed 代表每帧的旋转角度

        # 根据当前角度和速度更新位置
        angle_rad = math.radians(self.angle)
        self.center_x += -self.speed * math.sin(angle_rad)
        self.center_y += self.speed * math.cos(angle_rad)

        # 边界检查 (确保坦克在屏幕内)
        if self.left < 0:
            self.left = 0
            self.speed = 0 # 碰到边界停止
        elif self.right > SCREEN_WIDTH - 1:
            self.right = SCREEN_WIDTH - 1
            self.speed = 0 # 碰到边界停止

        if self.bottom < 0:
            self.bottom = 0
            self.speed = 0 # 碰到边界停止
        elif self.top > SCREEN_HEIGHT - 1:
            self.top = SCREEN_HEIGHT - 1
            self.speed = 0 # 碰到边界停止

    def shoot(self):
        # TODO: 实现射击逻辑
        # arcade.Texture 对象没有 'name' 属性。
        # 我们可以打印坦克的 image_file (如果提供了) 或者一个通用消息。
        # 由于 image_file 可能未在 self 中存储，我们简单打印一个通用消息。
        # print(f"Tank at ({self.center_x:.0f}, {self.center_y:.0f}) attempts to shoot with angle {self.angle:.1f}.") # 旧的打印语句
        # 返回一个子弹对象，如果可以射击的话
        # 子弹的发射角度 = 坦克的当前旋转角度 + 炮管相对于坦克逻辑前方的固定偏移角度
        # 假设坦克图片的炮管本身就指向图片的某个固定方向（例如相对于图片Y轴正向的-45度）
        # 当 tank.angle = 0 时，坦克是图片的原始朝向。
        # 我们需要定义炮管在图片中的朝向，相对于Arcade的0度（向上）。
        # 如果图片中炮管朝右斜上，用户建议偏移30度。
        # 相对于Arcade的0度向上，指向屏幕右斜上30度是 -30.0 度。
        IMAGE_BARREL_DIRECTION_OFFSET = -60.0 # 炮管在图片中的固有方向（相对于Arcade的0度向上）
        
        # actual_bullet_angle = self.angle - IMAGE_BARREL_DIRECTION_OFFSET
        actual_bullet_angle = IMAGE_BARREL_DIRECTION_OFFSET - self.angle # 这里我们需要将炮管的方向转换为子弹的发射角度
        # print(f"Tank angle: {self.angle:.1f}, Barrel offset: {IMAGE_BARREL_DIRECTION_OFFSET:.1f}, Bullet emission angle: {actual_bullet_angle:.1f}")
        bullet = Bullet(owner=self, tank_center_x=self.center_x, tank_center_y=self.center_y, actual_emission_angle_degrees=actual_bullet_angle)
        return bullet

# --- 子弹类 ---
BULLET_SPEED = 12
# BULLET_SCALE = 1.0 # SpriteSolidColor 不直接用 scale, 而是用width/height
BULLET_WIDTH = 6 # 子弹宽度
BULLET_HEIGHT = 10 # 子弹高度
BULLET_COLOR = arcade.color.YELLOW_ORANGE # 让子弹颜色更显眼

class Bullet(arcade.SpriteSolidColor):
    """ 子弹类 """
    def __init__(self, owner, tank_center_x, tank_center_y, actual_emission_angle_degrees, speed=BULLET_SPEED, color=BULLET_COLOR):
        # 使用固定宽高，不再依赖 scale 参数传递给 SpriteSolidColor
        super().__init__(BULLET_WIDTH, BULLET_HEIGHT, color)
        # print(f"Bullet created with angle: {actual_emission_angle_degrees:.1f}")
        
        self.owner = owner # 发射该子弹的坦克
        self.angle = actual_emission_angle_degrees # 子弹的飞行角度和视觉角度
        self.speed = speed
        self.bounce_count = 0 # 初始化反弹计数器
        self.max_bounces = 3  # 最大反弹次数

        # 计算炮口偏移量
        # barrel_offset 是从坦克中心点沿炮管方向到炮口的距离
        barrel_offset = 25 * PLAYER_SCALE 

        # 使用子弹的实际发射角度 (actual_emission_angle_degrees) 来计算偏移
        emission_angle_rad = math.radians(actual_emission_angle_degrees)
        
        # 子弹的初始位置在炮口
        # Arcade Sprite 角度0度朝上。前进方向的矢量是 (-sin(rad), cos(rad))
        self.center_x = tank_center_x - barrel_offset * math.sin(emission_angle_rad)
        self.center_y = tank_center_y + barrel_offset * math.cos(emission_angle_rad)


    def update(self, delta_time: float = 1/60): # 添加 delta_time 参数
        """ 移动子弹 """
        # 子弹的 self.angle 是其飞行和视觉角度 (0度朝上)
        angle_rad = math.radians(self.angle)
        
        # 根据Arcade Sprite的移动方式 (0度朝上时，前进是 y增加, x不变的特例)
        # dx = -speed * sin(angle_rad)
        # dy =  speed * cos(angle_rad)
        # 假设 self.speed 是 像素/帧
        self.center_x += -self.speed * math.sin(angle_rad)
        self.center_y += self.speed * math.cos(angle_rad)

        # 移除飞出屏幕的子弹 (这个逻辑应该在GameView中处理，因为它能访问bullet_list)
        # if self.bottom > SCREEN_HEIGHT or self.top < 0 or \
        #    self.right < 0 or self.left > SCREEN_WIDTH:
        #     self.remove_from_sprite_lists()

# 如果需要，可以在这里添加其他精灵类，例如 Wall, PowerUp 等
