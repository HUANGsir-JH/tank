import arcade
import math
import os
import pymunk # <--- 添加Pymunk导入

# --- 常量 ---
SCREEN_WIDTH = 1280 
SCREEN_HEIGHT = 720 # 同上

PLAYER_MOVEMENT_SPEED = 5
PLAYER_TURN_SPEED = 5  # 度/帧
PLAYER_SCALE = 0.8  # 坦克图片的缩放比例

# 坦克图片路径 - 注意：这个路径是相对于调用此模块的文件的，或者使用绝对路径/更灵活的资源管理
# 为了简单起见，我们假设图片在相对于项目根目录的 tank-img 文件夹下
# 在 main.py 中导入时，需要确保路径的正确性

# 获取 tank_sprites.py 文件所在的目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PLAYER_IMAGE_PATH_GREEN = os.path.join(BASE_DIR, "tank-img", "tanks_tankGreen1.png")
PLAYER_IMAGE_PATH_DESERT = os.path.join(BASE_DIR, "tank-img", "tanks_tankDesert1.png")
PlAYER_IMAGE_PATH_BLUE = os.path.join(BASE_DIR, "tank-img", "tanks_tankNavy1.png")
PLAYER_IMAGE_PATH_GREY = os.path.join(BASE_DIR, "tank-img", "tanks_tankGrey1.png")
# 示例：玩家2或敌人坦克


class Tank(arcade.Sprite):
    """ 坦克类 """
    def __init__(self, image_file, scale, center_x, center_y, max_speed=PLAYER_MOVEMENT_SPEED, turn_speed_degrees=PLAYER_TURN_SPEED):
        # 存储图片文件路径，供后续使用
        self.tank_image_file = image_file
        
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

        # Pymunk相关属性
        self.pymunk_body = None
        self.pymunk_shape = None
        # 坦克的物理属性 (可以根据需要调整)
        mass = 10 
        # 假设坦克是矩形，计算转动惯量
        # 对于实心矩形，I = m * (width^2 + height^2) / 12
        # 我们需要坦克的实际宽度和高度（解缩放后）
        # Sprite的width/height是缩放后的，但Pymunk形状用的是未缩放的顶点，然后body的scale会影响整体
        # 或者，直接用Pymunk提供的矩形惯量计算函数
        # 暂时使用一个估算值或让Pymunk自动计算（如果形状简单）
        # Pymunk的Poly形状需要顶点列表
        
        # 获取Sprite的未缩放尺寸 (如果图片已加载)
        if self.texture and hasattr(self.texture, 'image') and self.texture.image:
            unscaled_width = self.texture.image.width
            unscaled_height = self.texture.image.height
        elif self.texture: # 如果texture存在但没有image属性或image为None，尝试直接用texture的宽高
            unscaled_width = self.texture.width
            unscaled_height = self.texture.height
            if isinstance(unscaled_width, tuple): # 防御性检查，如果还是元组
                print(f"Warning: self.texture.width is a tuple: {unscaled_width}. Using first element.")
                unscaled_width = unscaled_width[0]
            if isinstance(unscaled_height, tuple):
                print(f"Warning: self.texture.height is a tuple: {unscaled_height}. Using first element.")
                unscaled_height = unscaled_height[0]
        else: # 占位符尺寸
            unscaled_width = int(50) 
            unscaled_height = int(60)

        print(f"DEBUG Tank Init: unscaled_width type: {type(unscaled_width)}, value: {unscaled_width}")
        print(f"DEBUG Tank Init: unscaled_height type: {type(unscaled_height)}, value: {unscaled_height}")
        print(f"DEBUG Tank Init: self.scale type: {type(self.scale)}, value: {self.scale}")

        try:
            # 确保转换为数值类型进行计算
            calc_unscaled_width = float(unscaled_width[0] if isinstance(unscaled_width, tuple) else unscaled_width)
            calc_unscaled_height = float(unscaled_height[0] if isinstance(unscaled_height, tuple) else unscaled_height)
        except Exception as e:
            print(f"ERROR converting unscaled dimensions: {e}. Falling back to defaults.")
            calc_unscaled_width = 50.0
            calc_unscaled_height = 60.0
        
        current_scale_for_pymunk = self.scale
        if isinstance(self.scale, tuple):
            print(f"DEBUG Tank Init: self.scale is a tuple {self.scale}. Using self.scale[0] for Pymunk calculations.")
            current_scale_for_pymunk = self.scale[0]
            
        # Pymunk的Poly顶点是相对于body的重心的。对于坦克，重心在中心。
        half_w = calc_unscaled_width * current_scale_for_pymunk / 2
        half_h = calc_unscaled_height * current_scale_for_pymunk / 2 # 使用缩放后的半宽高创建Pymunk形状
        
        vertices = [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]
        moment = pymunk.moment_for_poly(mass, vertices) # 使用缩放后的顶点计算moment

        self.pymunk_body = pymunk.Body(mass, moment)
        self.pymunk_body.position = center_x, center_y
        self.pymunk_body.angle = math.radians(self.angle) # Pymunk使用弧度

        self.pymunk_shape = pymunk.Poly(self.pymunk_body, vertices)
        self.pymunk_shape.elasticity = 0.1 # 碰撞弹性
        self.pymunk_shape.friction = 0.8   # 摩擦力
        self.pymunk_shape.collision_type = COLLISION_TYPE_TANK # 设置坦克的碰撞类型

        # 设置阻尼以防止无限滑动
        # Pymunk的 body.damping: 值越小，阻尼越强。1.0 为无阻尼。
        # 0.1 表示每秒速度衰减到其原始值的10% (velocity_t+1 = velocity_t * damping)
        # 实际上是 velocity_new = velocity_old * pow(damping, dt)
        # 如果 damping = 0.1, dt = 1/60, pow(0.1, 1/60) approx 0.962 (每帧衰减约4%)
        # 如果 damping = 0.01, dt = 1/60, pow(0.01, 1/60) approx 0.926 (每帧衰减约7.4%)
        # 之前用的0.05，对应约0.951 (每帧衰减约5%)
        # 为了更强的停止效果，尝试一个更小的值。
        self.pymunk_body.damping = 0.01 # 尝试一个非常强的阻尼
        # 也可以设置角阻尼
        self.pymunk_body.angular_damping = 0.01 # 使旋转也快速停止

        # 将Arcade Sprite与Pymunk Body关联起来，方便之后同步
        self.pymunk_body.sprite = self


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
        # Pymunk接管后，坦克的移动和旋转主要由物理引擎控制
        # Arcade Sprite的update方法主要用于同步Pymunk body的状态到Sprite
        # 以及处理非物理的逻辑（例如动画，但坦克目前没有）

        # 实际的移动和旋转逻辑将通过在GameView中对Pymunk body施加力/速度来完成
        # 这里的 self.speed 和 self.angle_speed 将不再直接驱动Sprite移动
        # 边界检查也将由Pymunk与静态墙壁的碰撞处理

        # 同步Sprite到Pymunk body (这一步通常在GameView的on_update中，在space.step()之后进行)
        # 但如果Tank类自己有一些基于Pymunk body的逻辑，可以在这里访问
        pass
    def sync_with_pymunk_body(self):
        """将Arcade Sprite的位置和角度同步到Pymunk Body的状态"""
        if self.pymunk_body:
            self.center_x = self.pymunk_body.position.x
            self.center_y = self.pymunk_body.position.y
            self.angle = math.degrees(self.pymunk_body.angle) # Pymunk是弧度，Arcade是角度    
    def shoot(self):
        """实现射击逻辑，返回一个子弹对象"""
        IMAGE_BARREL_DIRECTION_OFFSET = -60.0 # 炮管在图片中的固有方向（相对于Arcade的0度向上）
        actual_bullet_angle = IMAGE_BARREL_DIRECTION_OFFSET - self.angle # 这里我们需要将炮管的方向转换为子弹的发射角度
        
        # 根据坦克图片类型设置不同的子弹颜色
        bullet_color = BULLET_COLOR  # 默认颜色
        
        # 使用保存的图片路径判断坦克类型
        if hasattr(self, 'tank_image_file') and self.tank_image_file:
            path = self.tank_image_file.lower()
            print(f"DEBUG: Tank image path: {path}")
            
            if 'green' in path:
                bullet_color = arcade.color.GREEN
            elif 'desert' in path:
                bullet_color = arcade.color.ORANGE
            elif 'grey' in path:
                bullet_color = arcade.color.GRAY
            elif 'navy' in path:
                bullet_color = arcade.color.BLUE
        
        bullet = Bullet(owner=self, tank_center_x=self.center_x, tank_center_y=self.center_y, actual_emission_angle_degrees=actual_bullet_angle, color=bullet_color)
        return bullet

# --- 子弹类 ---
BULLET_SPEED = 12 # 这个速度值之后会用于Pymunk body的初始速度
BULLET_WIDTH = 6 
BULLET_HEIGHT = 10 
BULLET_COLOR = arcade.color.YELLOW_ORANGE

# Pymunk碰撞类型常量 (也可以定义在game_views.py或一个专门的常量模块)
COLLISION_TYPE_BULLET = 1
COLLISION_TYPE_WALL = 2 # 假设墙壁用这个
COLLISION_TYPE_TANK = 3 # 假设坦克用这个

class Bullet(arcade.SpriteSolidColor):
    """ 子弹类 """
    def __init__(self, owner, tank_center_x, tank_center_y, actual_emission_angle_degrees, speed_magnitude=BULLET_SPEED, color=BULLET_COLOR):
        super().__init__(BULLET_WIDTH, BULLET_HEIGHT) # 使用SolidColor创建子弹
        self.color = color # 设置子弹颜色
        self.center_x = tank_center_x
        self.center_y = tank_center_y
        self.width = BULLET_WIDTH
        self.height = BULLET_HEIGHT
        
        self.owner = owner 
        self.angle = actual_emission_angle_degrees # Arcade Sprite的视觉角度
        # self.speed 不再直接用于Arcade移动，但可以保留用于Pymunk初始速度计算
        self.bounce_count = 0 
        self.max_bounces = 3  

        # Pymunk相关属性
        self.pymunk_body = None
        self.pymunk_shape = None
        mass = 0.01 # 子弹质量可以很小
        # 子弹通常用圆形碰撞体，或者一个细长的矩形
        # 使用矩形以匹配视觉
        radius = BULLET_WIDTH / 2 # 如果用圆形
        moment = pymunk.moment_for_box(mass, (BULLET_WIDTH, BULLET_HEIGHT)) # 矩形惯量
        
        self.pymunk_body = pymunk.Body(mass, moment)
        
        # 计算炮口偏移量
        # barrel_offset 是从坦克中心点沿炮管方向到炮口的距离
        barrel_offset = 25 * PLAYER_SCALE 

        # 使用子弹的实际发射角度 (actual_emission_angle_degrees) 来计算偏移
        emission_angle_rad = math.radians(actual_emission_angle_degrees)
        
        # 子弹的初始位置在炮口
        # Arcade Sprite 角度0度朝上。前进方向的矢量是 (-sin(rad), cos(rad))
        # 子弹的初始位置在炮口
        self.pymunk_body.position = (
            tank_center_x - barrel_offset * math.sin(emission_angle_rad),
            tank_center_y + barrel_offset * math.cos(emission_angle_rad)
        )
        self.pymunk_body.angle = math.radians(actual_emission_angle_degrees) # Pymunk角度

        # 设置初始速度 (将 speed_magnitude 视为 像素/帧，转换为 像素/秒)
        # 假设游戏目标帧率为60 FPS
        pymunk_initial_speed = speed_magnitude * 90 
        vx = -pymunk_initial_speed * math.sin(self.pymunk_body.angle) 
        vy = pymunk_initial_speed * math.cos(self.pymunk_body.angle)
        self.pymunk_body.velocity = (vx, vy)

        # 将子弹自身阻尼设为1.0 (无阻尼)，使其主要受空间阻尼或碰撞影响
        self.pymunk_body.damping = 1.0 


        # 创建Pymunk形状
        # 使用Poly来匹配SpriteSolidColor的矩形视觉
        half_w = BULLET_WIDTH / 2
        half_h = BULLET_HEIGHT / 2
        vertices = [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]
        self.pymunk_shape = pymunk.Poly(self.pymunk_body, vertices)
        self.pymunk_shape.friction = 0.5 
        self.pymunk_shape.elasticity = 0.7 # 子弹可以设置较高弹性用于反弹
        self.pymunk_shape.collision_type = COLLISION_TYPE_BULLET
        self.pymunk_body.sprite = self # 关联Sprite

        # 同步初始视觉位置 (虽然GameView的on_update会做，但这里确保初始帧正确)
        self.sync_with_pymunk_body()


    def update(self, delta_time: float = 1/60): 
        """ 移动子弹 - 现在由Pymunk控制，此方法主要用于同步 """
        # 子弹的移动由Pymunk物理引擎处理
        # 此方法可以保留为空，或者用于非物理的更新（例如动画，但子弹没有）
        pass

    def sync_with_pymunk_body(self):
        """将Arcade Sprite的位置和角度同步到Pymunk Body的状态"""
        if self.pymunk_body:
            self.center_x = self.pymunk_body.position.x
            self.center_y = self.pymunk_body.position.y
            self.angle = math.degrees(self.pymunk_body.angle)

        # 移除飞出屏幕的子弹 (这个逻辑应该在GameView中处理，因为它能访问bullet_list)
        # if self.bottom > SCREEN_HEIGHT or self.top < 0 or \
        #    self.right < 0 or self.left > SCREEN_WIDTH:
        #     self.remove_from_sprite_lists()

# 如果需要，可以在这里添加其他精灵类，例如 Wall, PowerUp 等
