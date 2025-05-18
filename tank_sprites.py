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
PLAYER_IMAGE_PATH_BLUE = os.path.join(BASE_DIR, "tank-img", "tanks_tankNavy1.png")
PLAYER_IMAGE_PATH_GREY = os.path.join(BASE_DIR, "tank-img", "tanks_tankGrey1.png")

# Pymunk碰撞类型常量
COLLISION_TYPE_BULLET = 1
COLLISION_TYPE_WALL = 2
COLLISION_TYPE_TANK = 3

class Tank(arcade.Sprite):
    """ 坦克类 """
    def __init__(self, image_file, scale, center_x, center_y, max_speed=PLAYER_MOVEMENT_SPEED, turn_speed_degrees=PLAYER_TURN_SPEED):
        # 存储图片文件路径，供后续使用
        self.tank_image_file = image_file
        
        # 检查图片文件是否存在
        if image_file and os.path.exists(image_file):
            super().__init__(image_file, scale)
        elif image_file: # 文件路径提供了，但未找到
            print(f"警告: 坦克图片 '{image_file}' 未找到。将使用红色占位符。")
            super().__init__(scale=scale) 
            tank_width = int(50 * scale)
            self.texture = arcade.make_soft_square_texture(tank_width, arcade.color.RED, outer_alpha=255)
        else: # image_file 为 None
            print(f"信息: 未提供坦克图片。将使用蓝色占位符。")
            super().__init__(scale=scale)
            tank_width = int(50 * scale)
            self.texture = arcade.make_soft_square_texture(tank_width, arcade.color.BLUE, outer_alpha=255)

        self.angle = 0 
        self.center_x = center_x
        self.center_y = center_y
        self.speed = 0
        self.angle_speed = 0
        self.max_speed = max_speed
        self.turn_speed_degrees = turn_speed_degrees
        self.health = 5 
        self.max_health = 5

        self.pymunk_body = None
        self.pymunk_shape = None
        mass = 10 
        
        if self.texture and hasattr(self.texture, 'image') and self.texture.image:
            unscaled_width = self.texture.image.width
            unscaled_height = self.texture.image.height
        elif self.texture: 
            unscaled_width = self.texture.width
            unscaled_height = self.texture.height
            if isinstance(unscaled_width, tuple): 
                unscaled_width = unscaled_width[0]
            if isinstance(unscaled_height, tuple):
                unscaled_height = unscaled_height[0]
        else: 
            unscaled_width = int(50) 
            unscaled_height = int(60)

        # print(f"DEBUG Tank Init: unscaled_width type: {type(unscaled_width)}, value: {unscaled_width}")
        # print(f"DEBUG Tank Init: unscaled_height type: {type(unscaled_height)}, value: {unscaled_height}")
        # print(f"DEBUG Tank Init: self.scale type: {type(self.scale)}, value: {self.scale}")

        try:
            calc_unscaled_width = float(unscaled_width[0] if isinstance(unscaled_width, tuple) else unscaled_width)
            calc_unscaled_height = float(unscaled_height[0] if isinstance(unscaled_height, tuple) else unscaled_height)
        except Exception as e:
            print(f"ERROR converting unscaled dimensions: {e}. Falling back to defaults.")
            calc_unscaled_width = 50.0
            calc_unscaled_height = 60.0
        
        current_scale_for_pymunk = self.scale
        if isinstance(self.scale, tuple):
            current_scale_for_pymunk = self.scale[0]
            
        half_w = calc_unscaled_width * current_scale_for_pymunk / 2
        half_h = calc_unscaled_height * current_scale_for_pymunk / 2 
        
        vertices = [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]
        moment = pymunk.moment_for_poly(mass, vertices) 

        self.pymunk_body = pymunk.Body(mass, moment)
        self.pymunk_body.position = center_x, center_y
        self.pymunk_body.angle = math.radians(self.angle) 

        self.pymunk_shape = pymunk.Poly(self.pymunk_body, vertices)
        self.pymunk_shape.elasticity = 0.01 
        self.pymunk_shape.friction = 0.9   
        self.pymunk_shape.collision_type = COLLISION_TYPE_TANK 

        self.pymunk_body.damping = 0.01 
        self.pymunk_body.angular_damping = 0.01 
        self.pymunk_body.sprite = self

    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0:
            self.health = 0
        print(f"Tank at ({self.center_x:.0f},{self.center_y:.0f}) took {amount} damage, health: {self.health}")

    def is_alive(self):
        return self.health > 0

    def update(self, delta_time: float = 1/60): 
        pass

    def sync_with_pymunk_body(self):
        if self.pymunk_body:
            self.center_x = self.pymunk_body.position.x
            self.center_y = self.pymunk_body.position.y
            self.angle = math.degrees(self.pymunk_body.angle) 
              
    def shoot(self):
        IMAGE_BARREL_DIRECTION_OFFSET = -60.0 
        actual_bullet_angle = IMAGE_BARREL_DIRECTION_OFFSET - self.angle 
        
        bullet_color = arcade.color.YELLOW_ORANGE  
        
        if hasattr(self, 'tank_image_file') and self.tank_image_file:
            path = self.tank_image_file.lower()
            if 'green' in path: bullet_color = (0, 255, 0)
            elif 'desert' in path: bullet_color = (255, 165, 0)
            elif 'grey' in path: bullet_color = (128, 128, 128)
            elif 'navy' in path: bullet_color = (0, 0, 128)
        
        # 定义子弹半径和速度
        BULLET_RADIUS = 4 # 将半径改回4 (或您期望的其他值)
        BULLET_SPEED_MAGNITUDE = 12 # 保持原来的速度值

        bullet = Bullet(radius=BULLET_RADIUS, # 传递半径
                       owner=self, 
                       tank_center_x=self.center_x, 
                       tank_center_y=self.center_y, 
                       actual_emission_angle_degrees=actual_bullet_angle, 
                       speed_magnitude=BULLET_SPEED_MAGNITUDE, # 明确传递速度大小
                       color=bullet_color)
        return bullet

# --- 子弹类 ---
# BULLET_SPEED, BULLET_WIDTH, BULLET_HEIGHT, BULLET_COLOR 这些全局常量不再直接被Bullet类使用
# 它们现在通过参数传递或在Tank.shoot中定义

class Bullet(arcade.SpriteCircle): # 改为继承 SpriteCircle
    """ 子弹类 """
    def __init__(self, radius, owner, tank_center_x, tank_center_y, actual_emission_angle_degrees, speed_magnitude, color):
        super().__init__(radius, color) # 使用半径和颜色初始化 SpriteCircle
        self.radius = radius # 保存半径
        # self.color = color # SpriteCircle的构造函数已处理颜色
        
        self.center_x = tank_center_x # 初始位置会基于炮口重新计算
        self.center_y = tank_center_y
        
        self.owner = owner 
        self.angle = actual_emission_angle_degrees 
        self.bounce_count = 0 
        self.max_bounces = 3  

        self.pymunk_body = None
        self.pymunk_shape = None
        mass = 0.001 
        
        # 使用圆形计算转动惯量
        moment = pymunk.moment_for_circle(mass, 0, self.radius, (0,0)) 
        
        self.pymunk_body = pymunk.Body(mass, moment)
        
        barrel_offset = 25 * PLAYER_SCALE 
        emission_angle_rad = math.radians(actual_emission_angle_degrees)
        
        self.pymunk_body.position = (
            tank_center_x - barrel_offset * math.sin(emission_angle_rad),
            tank_center_y + barrel_offset * math.cos(emission_angle_rad)
        )
        self.pymunk_body.angle = math.radians(actual_emission_angle_degrees)

        pymunk_initial_speed = speed_magnitude * 120 
        vx = -pymunk_initial_speed * math.sin(self.pymunk_body.angle) 
        vy = pymunk_initial_speed * math.cos(self.pymunk_body.angle)
        self.pymunk_body.velocity = (vx, vy)
        self.pymunk_body.damping = 1.0 

        # 创建Pymunk圆形形状
        self.pymunk_shape = pymunk.Circle(self.pymunk_body, self.radius, (0,0))
        self.pymunk_shape.friction = 0.5 
        self.pymunk_shape.elasticity = 0.9 
        self.pymunk_shape.collision_type = COLLISION_TYPE_BULLET
        self.pymunk_body.sprite = self 

        self.sync_with_pymunk_body()

    def update(self, delta_time: float = 1/60): 
        pass

    def sync_with_pymunk_body(self):
        if self.pymunk_body:
            self.center_x = self.pymunk_body.position.x
            self.center_y = self.pymunk_body.position.y
            self.angle = math.degrees(self.pymunk_body.angle) # SpriteCircle通常不旋转，但保持同步无害
