import arcade
import math # <--- 添加 math 模块导入
from tank_sprites import Tank, PLAYER_IMAGE_PATH_GREEN # PLAYER_SCALE 将在GameView中定义或作为参数传入Tank

# --- 常量 ---
# 根据用户反馈调整窗口大小，使其更接近参考图的比例
SCREEN_WIDTH = 760  # 例如 19个格子 * 40像素/格子
SCREEN_HEIGHT = 600 # 例如 15个格子 * 40像素/格子
# SCREEN_TITLE 在主程序中定义

# 调整后的坦克缩放和墙壁厚度
NEW_PLAYER_SCALE = 0.65 # 调整坦克大小
WALL_THICKNESS = 10    # 墙壁改薄

class MainMenu(arcade.View):
    """ 主菜单视图 """
    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        arcade.draw_text("坦克动荡", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 100,
                         arcade.color.WHITE, font_size=50, anchor_x="center")
        # arcade.draw_text("点击开始游戏 (任意键)", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
        #                  arcade.color.WHITE, font_size=20, anchor_x="center") # 移除此行
        arcade.draw_text("按 M 查看游戏模式", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, #调整位置
                            arcade.color.WHITE, font_size=20, anchor_x="center")
        arcade.draw_text("按 Q 退出", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50, #调整位置
                            arcade.color.WHITE, font_size=20, anchor_x="center")

    # 移除 on_mouse_press 方法，彻底取消点击开始游戏
    # def on_mouse_press(self, _x, _y, _button, _modifiers):
    #     """ 当鼠标点击时, 默认进入玩家vs电脑模式 """
    #     game_view = GameView(mode="pvc") # 默认模式
    #     self.window.show_view(game_view)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.Q:
            arcade.exit()
        elif key == arcade.key.M:
            mode_view = ModeSelectView()
            self.window.show_view(mode_view)
        # 其他按键无响应


class ModeSelectView(arcade.View):
    """ 游戏模式选择视图 """
    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

    def on_draw(self):
        self.clear()
        arcade.draw_text("游戏模式", SCREEN_WIDTH / 2, SCREEN_HEIGHT - 100,
                         arcade.color.WHITE, font_size=40, anchor_x="center")

        arcade.draw_text("1. 玩家 vs 电脑", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50,
                         arcade.color.WHITE, font_size=20, anchor_x="center")
        arcade.draw_text("2. 双人对战", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                         arcade.color.WHITE, font_size=20, anchor_x="center")
        arcade.draw_text("3. 多人联机 (未实现)", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50,
                         arcade.color.LIGHT_GRAY, font_size=20, anchor_x="center")
        arcade.draw_text("按 Esc 返回主菜单", SCREEN_WIDTH / 2, 50,
                            arcade.color.WHITE, font_size=15, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            main_menu_view = MainMenu()
            self.window.show_view(main_menu_view)
        elif key == arcade.key.KEY_1:
            print("选择了 玩家 vs 电脑 模式")
            game_view = GameView(mode="pvc")
            self.window.show_view(game_view)
        elif key == arcade.key.KEY_2:
            print("选择了 双人对战 模式")
            game_view = GameView(mode="pvp")
            self.window.show_view(game_view)
        elif key == arcade.key.KEY_3:
            print("选择了 多人联机 模式 (未实现)")


class GameView(arcade.View):
    """ 游戏主视图 """
    def __init__(self, mode="pvc"):
        super().__init__()
        self.mode = mode
        self.player_tank = None # 玩家1
        self.player2_tank = None # 玩家2
        self.player_list = None # 包含所有玩家坦克
        self.bullet_list = None # 用于存放子弹
        self.wall_list = None   # 用于存放墙壁
        # self.enemy_list = None # TODO: 之后添加敌人
        # self.powerup_list = None # TODO: 之后添加道具

        # 物理引擎 (如果需要更复杂的碰撞)
        # self.physics_engine = None

    def setup(self):
        """ 设置游戏元素 """
        self.player_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList(use_spatial_hash=True) 
        
        # 使用新的缩放和墙壁厚度
        current_player_scale = NEW_PLAYER_SCALE
        current_wall_thickness = WALL_THICKNESS
        wall_color = arcade.color.DARK_SLATE_GRAY

        # 创建玩家1坦克 - 调整初始位置以避免与新墙壁重叠
        # 假设格子大小为40，坦克放在 (2, 总高/2) 的格子附近
        p1_start_x = current_wall_thickness * 2 + 20 
        p1_start_y = SCREEN_HEIGHT / 2
        self.player_tank = Tank(PLAYER_IMAGE_PATH_GREEN, current_player_scale, p1_start_x, p1_start_y)
        self.player_list.append(self.player_tank)

        # 根据游戏模式初始化其他元素
        if self.mode == "pvc":
            pass # TODO
        elif self.mode == "pvp":
            from tank_sprites import PLAYER_IMAGE_PATH_DESERT
            # 玩家2坦克初始位置 - 放在 (总宽-2, 总高/2) 的格子附近
            p2_start_x = SCREEN_WIDTH - (current_wall_thickness * 2 + 20)
            p2_start_y = SCREEN_HEIGHT / 2
            self.player2_tank = Tank(PLAYER_IMAGE_PATH_DESERT, current_player_scale, p2_start_x, p2_start_y)
            if self.player2_tank:
                self.player_list.append(self.player2_tank)
                print("玩家2坦克已创建")

        # --- 创建地图墙壁 ---
        # 边界墙壁
        for x_coord in range(0, SCREEN_WIDTH, current_wall_thickness): # 底部
            wall = arcade.SpriteSolidColor(current_wall_thickness, current_wall_thickness, wall_color)
            wall.center_x = x_coord + current_wall_thickness / 2
            wall.center_y = current_wall_thickness / 2
            self.wall_list.append(wall)
        for x_coord in range(0, SCREEN_WIDTH, current_wall_thickness): # 顶部
            wall = arcade.SpriteSolidColor(current_wall_thickness, current_wall_thickness, wall_color)
            wall.center_x = x_coord + current_wall_thickness / 2
            wall.center_y = SCREEN_HEIGHT - current_wall_thickness / 2
            self.wall_list.append(wall)
        for y_coord in range(current_wall_thickness, SCREEN_HEIGHT - current_wall_thickness, current_wall_thickness): # 左侧
            wall = arcade.SpriteSolidColor(current_wall_thickness, current_wall_thickness, wall_color)
            wall.center_x = current_wall_thickness / 2
            wall.center_y = y_coord + current_wall_thickness / 2
            self.wall_list.append(wall)
        for y_coord in range(current_wall_thickness, SCREEN_HEIGHT - current_wall_thickness, current_wall_thickness): # 右侧
            wall = arcade.SpriteSolidColor(current_wall_thickness, current_wall_thickness, wall_color)
            wall.center_x = SCREEN_WIDTH - current_wall_thickness / 2
            wall.center_y = y_coord + current_wall_thickness / 2
            self.wall_list.append(wall)
        
        # 示例内部墙壁 (根据新的SCREEN_WIDTH, SCREEN_HEIGHT, WALL_THICKNESS调整)
        # (center_x, center_y, width, height)
        # 这些墙壁现在会用 current_wall_thickness 来构建，而不是单块大墙
        # 为了简单，我还是用单块大墙，但尺寸会基于 current_wall_thickness
        maze_walls_data = [
            # (SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.75, 200, current_wall_thickness), 
            # (SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.25, 200, current_wall_thickness), 
            # (SCREEN_WIDTH * 0.25, SCREEN_HEIGHT / 2, current_wall_thickness, 300), 
            # (SCREEN_WIDTH * 0.75, SCREEN_HEIGHT / 2, current_wall_thickness, 300),
            # 更简单的几条示例墙：
            (SCREEN_WIDTH * 0.3, SCREEN_HEIGHT / 2, current_wall_thickness, SCREEN_HEIGHT * 0.4), # 左中垂直
            (SCREEN_WIDTH * 0.7, SCREEN_HEIGHT / 2, current_wall_thickness, SCREEN_HEIGHT * 0.4), # 右中垂直
            (SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.3, SCREEN_WIDTH * 0.3, current_wall_thickness),   # 中下水平
            (SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.7, SCREEN_WIDTH * 0.3, current_wall_thickness),   # 中上水平
        ]
        for x, y, w, h in maze_walls_data:
            wall = arcade.SpriteSolidColor(int(w), int(h), wall_color)
            wall.center_x = int(x)
            wall.center_y = int(y)
            self.wall_list.append(wall)

        arcade.set_background_color(arcade.color.LIGHT_GRAY) # 改个浅色背景，墙壁更突出

    def on_show_view(self):
        self.setup()

    def on_draw(self):
        self.clear()
        self.wall_list.draw() # 绘制墙壁
        self.player_list.draw()
        self.bullet_list.draw() 
        # self.enemy_list.draw()
        # self.powerup_list.draw()

        # 调整UI文字位置，避免重叠
        ui_text_color = arcade.color.BLACK
        arcade.draw_text(f"模式: {self.mode.upper()}",
                         10, SCREEN_HEIGHT - 25, ui_text_color, font_size=16)
        arcade.draw_text("Esc: 返回主菜单",
                         SCREEN_WIDTH - 150, SCREEN_HEIGHT - 25, ui_text_color, font_size=16)
        # TODO: 绘制其他UI元素 (得分, 生命值等)

    def on_update(self, delta_time):
        """ 游戏逻辑更新 """
        # 坦克移动前记录位置，用于碰撞后回退
        for player_obj in self.player_list:
            player_obj.original_center_x = player_obj.center_x
            player_obj.original_center_y = player_obj.center_y
            player_obj.original_angle = player_obj.angle # 如果旋转也需要回退

        self.player_list.update()
        self.bullet_list.update() # 更新子弹状态
        # self.enemy_list.update()
        # self.powerup_list.update() # 如果道具有动画或特殊行为

        # 坦克与墙壁的碰撞检测
        for player_obj in self.player_list:
            wall_hit_list = arcade.check_for_collision_with_list(player_obj, self.wall_list)
            if wall_hit_list:
                # 发生碰撞，将坦克移回碰撞前的位置
                # 这是一个简单的处理方式，可以防止穿墙
                player_obj.center_x = player_obj.original_center_x
                player_obj.center_y = player_obj.original_center_y
                # player_obj.angle = player_obj.original_angle # 如果旋转导致碰撞，也回退角度
                player_obj.speed = 0 # 碰撞后速度清零
                player_obj.angle_speed = 0 # 碰撞后角速度清零


        # 移除飞出屏幕的子弹
        for bullet in self.bullet_list:
            if bullet.bottom > SCREEN_HEIGHT or \
               bullet.top < 0 or \
               bullet.right < 0 or \
               bullet.left > SCREEN_WIDTH:
                bullet.remove_from_sprite_lists()
            
            # 子弹与墙壁的碰撞检测
            hit_walls = arcade.check_for_collision_with_list(bullet, self.wall_list)
            if hit_walls:
                # 记录碰撞前状态用于调试
                prev_angle = bullet.angle
                prev_pos = (bullet.center_x, bullet.center_y)

                bullet.bounce_count += 1
                if bullet.bounce_count >= bullet.max_bounces:
                    print(f"Bullet {id(bullet)} removed after {bullet.bounce_count} bounces.")
                    bullet.remove_from_sprite_lists()
                else:
                    # 尝试将子弹移回碰撞点之前一点，避免卡墙
                    # (这是一个简单的处理，更复杂情况可能需要更精确的回退)
                    bullet_angle_rad = math.radians(bullet.angle)
                    bullet.center_x -= -bullet.speed * math.sin(bullet_angle_rad) / 2 # 回退半步
                    bullet.center_y -= bullet.speed * math.cos(bullet_angle_rad) / 2  # 回退半步

                    # 基于速度方向的简化反弹逻辑
                    prev_angle_rad = math.radians(prev_angle)
                    vx = -bullet.speed * math.sin(prev_angle_rad)
                    vy = bullet.speed * math.cos(prev_angle_rad)

                    if abs(vx) > abs(vy):  # 主要撞击垂直面 (左右墙)
                        bullet.angle = (180 - prev_angle) % 360
                        print(f"Bullet {id(bullet)} bounced (H). Pos:({prev_pos[0]:.0f},{prev_pos[1]:.0f}) Angle: {prev_angle:.1f} -> {bullet.angle:.1f}. Bounces: {bullet.bounce_count}")
                    else:  # 主要撞击水平面 (上下墙)
                        bullet.angle = (-prev_angle) % 360
                        print(f"Bullet {id(bullet)} bounced (V). Pos:({prev_pos[0]:.0f},{prev_pos[1]:.0f}) Angle: {prev_angle:.1f} -> {bullet.angle:.1f}. Bounces: {bullet.bounce_count}")
                    
                    # 再次尝试将子弹移出一点，防止立即再次碰撞
                    # (这部分可能需要根据实际效果微调或使用更复杂的碰撞解决)
                    # 例如，可以根据碰撞到的墙壁的法线方向将子弹推开一个固定的小距离
                    # collided_wall = hit_walls[0]
                    # overlap_x, overlap_y = arcade.geometry.get_overlap_for_sprites(bullet, collided_wall)
                    # if overlap_x > 0 : bullet.center_x += overlap_x * (1 if bullet.center_x < collided_wall.center_x else -1)
                    # if overlap_y > 0 : bullet.center_y += overlap_y * (1 if bullet.center_y < collided_wall.center_y else -1)


        # TODO: 子弹与坦克的碰撞检测

        # 坦克与坦克的碰撞检测 (仅在PVP模式且有两个坦克时)
        if self.mode == "pvp" and self.player_tank and self.player2_tank:
            if arcade.check_for_collision(self.player_tank, self.player2_tank):
                # 简单处理：双方都退回上一步的位置
                self.player_tank.center_x = self.player_tank.original_center_x
                self.player_tank.center_y = self.player_tank.original_center_y
                self.player_tank.speed = 0
                self.player_tank.angle_speed = 0

                self.player2_tank.center_x = self.player2_tank.original_center_x
                self.player2_tank.center_y = self.player2_tank.original_center_y
                self.player2_tank.speed = 0
                self.player2_tank.angle_speed = 0
                
                print("Tanks collided!")


        # TODO: 游戏结束条件判断

    def on_key_press(self, key, modifiers):
        """ 处理按键按下事件 """
        if key == arcade.key.ESCAPE:
            # TODO: 可以实现暂停菜单
            main_menu_view = MainMenu() # 暂时直接返回主菜单
            self.window.show_view(main_menu_view)

        # 玩家1 (WASD) 控制, 不要再修改！！！
        if self.mode == "pvc" or self.mode == "pvp":
            if key == arcade.key.W:
                self.player_tank.speed = self.player_tank.max_speed
            elif key == arcade.key.S:
                self.player_tank.speed = -self.player_tank.max_speed
            elif key == arcade.key.A: # A键 -> 逆时针
                if self.player_tank:
                    self.player_tank.angle_speed = -self.player_tank.turn_speed_degrees 
            elif key == arcade.key.D: # D键 -> 顺时针
                if self.player_tank:
                    self.player_tank.angle_speed = self.player_tank.turn_speed_degrees
            elif key == arcade.key.SPACE: # 玩家1射击键
                if self.player_tank:
                    bullet = self.player_tank.shoot()
                    if bullet:
                        self.bullet_list.append(bullet)

        # 玩家2 (上下左右箭头) 控制 - 仅在双人模式下 ，不要再修改！！！
        if self.mode == "pvp" and self.player2_tank:
            if key == arcade.key.UP:
                self.player2_tank.speed = self.player2_tank.max_speed
            elif key == arcade.key.DOWN:
                self.player2_tank.speed = -self.player2_tank.max_speed
            elif key == arcade.key.LEFT: # 左箭头 -> 逆时针
                self.player2_tank.angle_speed = -self.player2_tank.turn_speed_degrees
            elif key == arcade.key.RIGHT: # 右箭头 -> 顺时针
                self.player2_tank.angle_speed = self.player2_tank.turn_speed_degrees
            elif key == arcade.key.ENTER or key == arcade.key.RSHIFT: # 玩家2射击键 (回车或右Shift)
                bullet = self.player2_tank.shoot()
                if bullet:
                    self.bullet_list.append(bullet)


    def on_key_release(self, key, modifiers):
        """ 处理按键释放事件 """
        # 玩家1
        if self.player_tank: # 确保坦克存在
            if key == arcade.key.W or key == arcade.key.S:
                self.player_tank.speed = 0
            elif key == arcade.key.A or key == arcade.key.D:
                self.player_tank.angle_speed = 0
        
        # 玩家2
        if self.mode == "pvp" and self.player2_tank:
            if key == arcade.key.UP or key == arcade.key.DOWN:
                self.player2_tank.speed = 0
            elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
                self.player2_tank.angle_speed = 0


class GameOverView(arcade.View):
    """ 游戏结束视图 """
    def __init__(self, result, last_mode="pvc"): # 添加last_mode以正确重新开始
        super().__init__()
        self.result = result
        self.last_mode = last_mode

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK_OLIVE)

    def on_draw(self):
        self.clear()
        arcade.draw_text(f"游戏结束 - {self.result}", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50,
                         arcade.color.WHITE, font_size=40, anchor_x="center")
        arcade.draw_text("按 R 重新开始", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50,
                         arcade.color.WHITE, font_size=20, anchor_x="center")
        arcade.draw_text("按 Q 退出", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100,
                         arcade.color.WHITE, font_size=20, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            game_view = GameView(mode=self.last_mode) # 使用上一次的游戏模式
            self.window.show_view(game_view)
        elif key == arcade.key.Q:
            arcade.exit()
