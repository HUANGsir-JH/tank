import arcade
import math 
import pymunk 
from tank_sprites import (Tank, PLAYER_IMAGE_PATH_GREEN, PLAYER_MOVEMENT_SPEED, PLAYER_TURN_SPEED,
                          COLLISION_TYPE_BULLET, COLLISION_TYPE_WALL, COLLISION_TYPE_TANK)

# --- 常量 ---
# 根据用户反馈调整窗口大小，使其更接近参考图的比例
SCREEN_WIDTH = 760  # 例如 19个格子 * 40像素/格子
SCREEN_HEIGHT = 600 # 例如 15个格子 * 40像素/格子
# SCREEN_TITLE 在主程序中定义

# UI 面板的高度
TOP_UI_PANEL_HEIGHT = 30
BOTTOM_UI_PANEL_HEIGHT = 60 # 给血条和胜场留足空间

# 游戏可玩区域的边界
GAME_AREA_BOTTOM_Y = BOTTOM_UI_PANEL_HEIGHT
GAME_AREA_TOP_Y = SCREEN_HEIGHT - TOP_UI_PANEL_HEIGHT
GAME_AREA_HEIGHT = GAME_AREA_TOP_Y - GAME_AREA_BOTTOM_Y


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
        self.player1_score = 0
        self.player2_score = 0
        self.round_over = False # 标记当前回合是否结束
        self.round_over_timer = 0.0 # 回合结束后的等待计时器
        self.round_over_delay = 2.0 # 回合结束后等待2秒开始下一回合或结束游戏
        self.max_score = 2 # 获胜需要的胜场数
        self.round_result_text = "" # 用于显示回合结束提示
        # self.enemy_list = None # TODO: 之后添加敌人
        # self.powerup_list = None # TODO: 之后添加道具

        # Pymunk物理空间
        self.space = pymunk.Space()
        self.space.gravity = (0, 0) 
        self.space.damping = 0.8    
        
        # 用于在碰撞回调后安全移除Pymunk body和Arcade sprite
        self.pymunk_bodies_to_remove_post_step = []
        self.arcade_sprites_to_remove_post_step = []

        self._setup_collision_handlers()

    def _setup_collision_handlers(self):
        """设置Pymunk碰撞处理器"""
        # 子弹 vs 墙壁
        handler_bullet_wall = self.space.add_collision_handler(COLLISION_TYPE_BULLET, COLLISION_TYPE_WALL)
        handler_bullet_wall.pre_solve = self._bullet_hit_wall_handler # pre_solve在物理计算前，允许修改碰撞属性或忽略碰撞

        # 子弹 vs 坦克
        handler_bullet_tank = self.space.add_collision_handler(COLLISION_TYPE_BULLET, COLLISION_TYPE_TANK)
        handler_bullet_tank.pre_solve = self._bullet_hit_tank_handler
    
    def _bullet_hit_wall_handler(self, arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        """Pymunk回调：子弹撞墙"""
        bullet_shape, wall_shape = arbiter.shapes
        bullet_sprite = bullet_shape.body.sprite # 我们在创建时关联了sprite

        bullet_sprite.bounce_count += 1
        if bullet_sprite.bounce_count >= bullet_sprite.max_bounces:
            print(f"Bullet {id(bullet_sprite)} to be removed after {bullet_sprite.bounce_count} bounces (hit wall).")
            if bullet_shape.body not in self.pymunk_bodies_to_remove_post_step:
                self.pymunk_bodies_to_remove_post_step.append(bullet_shape.body)
            if bullet_sprite not in self.arcade_sprites_to_remove_post_step:
                self.arcade_sprites_to_remove_post_step.append(bullet_sprite)
            return False # 阻止碰撞的物理反弹，因为子弹要消失了
        else:
            # Pymunk的 shape.elasticity 会处理反弹的物理效果。
            # 如果需要更精确的角度控制，可以在这里修改arbiter的restitution或surface_velocity
            # 但通常依赖elasticity即可。我们已经在Bullet的shape上设置了elasticity=0.9
            print(f"Bullet {id(bullet_sprite)} bounced off wall. Bounces: {bullet_sprite.bounce_count}")
            # Pymunk的弹性已处理反弹，这里返回True让物理引擎继续处理
            # 如果我们想手动计算反弹角度，可以在这里修改bullet_shape.body.velocity和angle
            # 但Pymunk的弹性通常更真实。
            # 注意：如果子弹的弹性很高，它可能会多次快速碰撞同一面墙，导致bounce_count迅速增加。
            # 可能需要一个冷却时间或者更复杂的反弹逻辑。
            # 简单的处理是让Pymunk的弹性起作用。
            pass 
        return True # 允许碰撞发生并由Pymunk处理物理反弹

    def _bullet_hit_tank_handler(self, arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        """Pymunk回调：子弹撞坦克"""
        bullet_shape, tank_shape = arbiter.shapes
        
        # 确保获取到正确的bullet和tank shape (arbiter.shapes顺序不保证)
        if bullet_shape.collision_type == COLLISION_TYPE_BULLET:
            bullet_sprite = bullet_shape.body.sprite
            tank_sprite = tank_shape.body.sprite
        else: #顺序反了
            bullet_sprite = tank_shape.body.sprite # 这实际上是bullet
            tank_sprite = bullet_shape.body.sprite # 这实际上是tank
            # 更严谨的检查：
            if not (bullet_sprite.pymunk_shape.collision_type == COLLISION_TYPE_BULLET and \
                    tank_sprite.pymunk_shape.collision_type == COLLISION_TYPE_TANK):
                print("ERROR: Collision handler shape order assumption wrong and recovery failed.")
                return False # 忽略此碰撞

        if bullet_sprite.owner is not tank_sprite and tank_sprite.is_alive():
            if not self.round_over: # 只有在回合进行中才处理伤害
                tank_sprite.take_damage(1)
                # 子弹击中坦克后消失
                if bullet_shape.body not in self.pymunk_bodies_to_remove_post_step:
                    self.pymunk_bodies_to_remove_post_step.append(bullet_shape.body)
                if bullet_sprite not in self.arcade_sprites_to_remove_post_step:
                    self.arcade_sprites_to_remove_post_step.append(bullet_sprite)

                if not tank_sprite.is_alive():
                    print(f"Tank ({tank_sprite.center_x:.0f},{tank_sprite.center_y:.0f}) destroyed by Pymunk bullet!")
                    if not self.round_over: # 再次检查，因为伤害可能导致回合结束
                        self.round_over = True
                        self.round_over_timer = self.round_over_delay
                        if tank_sprite is self.player_tank:
                            if self.mode == "pvp":
                                self.player2_score += 1
                                self.round_result_text = "玩家2 本回合胜利!"
                        elif self.mode == "pvp" and tank_sprite is self.player2_tank:
                            self.player1_score += 1
                            self.round_result_text = "玩家1 本回合胜利!"
            return False # 子弹击中坦克后应该消失，不发生物理反弹
        return False # 如果是自己的子弹或坦克已死亡，忽略碰撞的物理效果

    def start_new_round(self):
        """开始一个新回合或重置当前回合的坦克状态"""
        print("Starting new round / Resetting tanks...")
        self.round_result_text = "" # 清除上一回合的提示
        self.round_over = False
        self.round_over_timer = 0.0
        if self.bullet_list: # 确保bullet_list已初始化
            self.bullet_list.clear() # 清空所有子弹
        else:
            self.bullet_list = arcade.SpriteList()

        # 重置/创建 玩家1 坦克
        p1_start_x = WALL_THICKNESS * 3 
        p1_start_y = GAME_AREA_BOTTOM_Y + GAME_AREA_HEIGHT / 2
        if self.player_tank and self.player_tank in self.player_list: # 检查坦克是否仍在列表中
             # 如果坦克只是被标记为None但仍在列表中，先移除
            if not self.player_tank.is_alive() and self.player_tank in self.player_list:
                 self.player_list.remove(self.player_tank)
                 self.player_tank = None # 确保设为None
        
        if not self.player_tank: # 如果坦克对象不存在了（例如上一局被设为None后从列表移除）
            self.player_tank = Tank(PLAYER_IMAGE_PATH_GREEN, NEW_PLAYER_SCALE, p1_start_x, p1_start_y)
            if self.player_list is None: self.player_list = arcade.SpriteList() # 确保player_list存在
            self.player_list.append(self.player_tank)
            if self.player_tank.pymunk_body and self.player_tank.pymunk_shape: # 添加到Pymunk空间
                self.space.add(self.player_tank.pymunk_body, self.player_tank.pymunk_shape)
        else: # 如果坦克对象还在，只是重置状态
            self.player_tank.health = self.player_tank.max_health
            # 重置Pymunk body的状态
            if self.player_tank.pymunk_body:
                self.player_tank.pymunk_body.position = p1_start_x, p1_start_y
                self.player_tank.pymunk_body.angle = 0  # Pymunk角度是弧度
                self.player_tank.pymunk_body.velocity = (0, 0)
                self.player_tank.pymunk_body.angular_velocity = 0
            # 同步Arcade Sprite (虽然sync_with_pymunk_body会在on_update调用，但这里立即同步更清晰)
            self.player_tank.sync_with_pymunk_body() 
            # 旧的Sprite属性设置可以移除，因为sync会处理
            # self.player_tank.center_x = p1_start_x 
            # self.player_tank.center_y = p1_start_y
            # self.player_tank.angle = 0
            # self.player_tank.speed = 0 # 此属性已不再由Pymunk直接使用
            # self.player_tank.angle_speed = 0 # 此属性已不再由Pymunk直接使用
        
        # 重置/创建 玩家2 坦克 (仅PVP)
        if self.mode == "pvp":
            p2_start_x = SCREEN_WIDTH - (WALL_THICKNESS * 3)
            p2_start_y = GAME_AREA_BOTTOM_Y + GAME_AREA_HEIGHT / 2
            if self.player2_tank and self.player2_tank in self.player_list:
                if not self.player2_tank.is_alive() and self.player2_tank in self.player_list:
                    self.player_list.remove(self.player2_tank)
                    self.player2_tank = None

            if not self.player2_tank:
                from tank_sprites import PLAYER_IMAGE_PATH_DESERT
                self.player2_tank = Tank(PLAYER_IMAGE_PATH_DESERT, NEW_PLAYER_SCALE, p2_start_x, p2_start_y)
                if self.player_list is None: self.player_list = arcade.SpriteList() # 确保player_list存在
                self.player_list.append(self.player2_tank)
                if self.player2_tank.pymunk_body and self.player2_tank.pymunk_shape: # 添加到Pymunk空间
                    self.space.add(self.player2_tank.pymunk_body, self.player2_tank.pymunk_shape)
            else:
                self.player2_tank.health = self.player2_tank.max_health
                if self.player2_tank.pymunk_body:
                    self.player2_tank.pymunk_body.position = p2_start_x, p2_start_y
                    self.player2_tank.pymunk_body.angle = 0
                    self.player2_tank.pymunk_body.velocity = (0, 0)
                    self.player2_tank.pymunk_body.angular_velocity = 0
                self.player2_tank.sync_with_pymunk_body()
        
        # 确保player_list是最新的 (如果坦克是重新创建的)
        # 上面的逻辑已经尝试处理了player_list的更新，但更稳妥的方式可能是在setup中完全重建
        # 但由于start_new_round可能在setup之外被调用，我们需要确保player_list正确
        # 考虑到坦克可能被设为None，然后从player_list移除，这里需要确保它们被重新添加
        # 一个简化的方法是，如果坦克对象被重新创建，就确保它在player_list里
        # （上面的逻辑已经包含了这个）

    def setup(self):
        """ 设置游戏元素: 创建列表、墙壁、UI背景，然后开始第一回合 """
        self.player_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList(use_spatial_hash=True) 
        
        current_wall_thickness = WALL_THICKNESS 
        wall_color = arcade.color.DARK_SLATE_GRAY

        # --- 创建地图墙壁 (Arcade Sprites 和 Pymunk Shapes) ---
        # 边界墙壁
        # 底部
        body_bottom = pymunk.Body(body_type=pymunk.Body.STATIC)
        shape_bottom = pymunk.Segment(body_bottom, (0, GAME_AREA_BOTTOM_Y), (SCREEN_WIDTH, GAME_AREA_BOTTOM_Y), current_wall_thickness / 2)
        shape_bottom.collision_type = COLLISION_TYPE_WALL
        shape_bottom.friction = 0.8 
        shape_bottom.elasticity = 0.8 # 为墙壁设置弹性
        self.space.add(body_bottom, shape_bottom)
        for x_coord in range(0, SCREEN_WIDTH, current_wall_thickness):
            wall = arcade.SpriteSolidColor(current_wall_thickness, current_wall_thickness, wall_color)
            wall.center_x = x_coord + current_wall_thickness / 2
            wall.center_y = GAME_AREA_BOTTOM_Y + current_wall_thickness / 2 # 确保与Pymunk形状对齐
            self.wall_list.append(wall)
        # 顶部
        body_top = pymunk.Body(body_type=pymunk.Body.STATIC)
        shape_top = pymunk.Segment(body_top, (0, GAME_AREA_TOP_Y), (SCREEN_WIDTH, GAME_AREA_TOP_Y), current_wall_thickness / 2)
        shape_top.collision_type = COLLISION_TYPE_WALL
        shape_top.friction = 0.8
        shape_top.elasticity = 0.8 # 为墙壁设置弹性
        self.space.add(body_top, shape_top)
        for x_coord in range(0, SCREEN_WIDTH, current_wall_thickness):
            wall = arcade.SpriteSolidColor(current_wall_thickness, current_wall_thickness, wall_color)
            wall.center_x = x_coord + current_wall_thickness / 2
            wall.center_y = GAME_AREA_TOP_Y - current_wall_thickness / 2
            self.wall_list.append(wall)
        # 左侧
        body_left = pymunk.Body(body_type=pymunk.Body.STATIC)
        shape_left = pymunk.Segment(body_left, (0, GAME_AREA_BOTTOM_Y), (0, GAME_AREA_TOP_Y), current_wall_thickness / 2)
        shape_left.collision_type = COLLISION_TYPE_WALL
        shape_left.friction = 0.8
        shape_left.elasticity = 0.8 # 为墙壁设置弹性
        self.space.add(body_left, shape_left)
        for y_coord in range(int(GAME_AREA_BOTTOM_Y), int(GAME_AREA_TOP_Y + current_wall_thickness), current_wall_thickness): # 调整循环确保覆盖
            wall = arcade.SpriteSolidColor(current_wall_thickness, current_wall_thickness, wall_color)
            wall.center_x = current_wall_thickness / 2
            wall.center_y = y_coord + current_wall_thickness / 2
            self.wall_list.append(wall)
        # 右侧
        body_right = pymunk.Body(body_type=pymunk.Body.STATIC)
        shape_right = pymunk.Segment(body_right, (SCREEN_WIDTH, GAME_AREA_BOTTOM_Y), (SCREEN_WIDTH, GAME_AREA_TOP_Y), current_wall_thickness / 2)
        shape_right.collision_type = COLLISION_TYPE_WALL
        shape_right.friction = 0.8
        shape_right.elasticity = 0.8 # 为墙壁设置弹性
        self.space.add(body_right, shape_right)
        for y_coord in range(int(GAME_AREA_BOTTOM_Y), int(GAME_AREA_TOP_Y + current_wall_thickness), current_wall_thickness): # 调整循环确保覆盖
            wall = arcade.SpriteSolidColor(current_wall_thickness, current_wall_thickness, wall_color)
            wall.center_x = SCREEN_WIDTH - current_wall_thickness / 2
            wall.center_y = y_coord + current_wall_thickness / 2
            self.wall_list.append(wall)

        # 示例内部墙壁 - 确保Y坐标在GAME_AREA内
        # (center_x, center_y, width, height)
        maze_walls_data = [
            (SCREEN_WIDTH * 0.3, GAME_AREA_BOTTOM_Y + GAME_AREA_HEIGHT / 2, current_wall_thickness, GAME_AREA_HEIGHT * 0.4), 
            (SCREEN_WIDTH * 0.7, GAME_AREA_BOTTOM_Y + GAME_AREA_HEIGHT / 2, current_wall_thickness, GAME_AREA_HEIGHT * 0.4), 
            (SCREEN_WIDTH / 2, GAME_AREA_BOTTOM_Y + GAME_AREA_HEIGHT * 0.3, SCREEN_WIDTH * 0.3, current_wall_thickness),   
            (SCREEN_WIDTH / 2, GAME_AREA_BOTTOM_Y + GAME_AREA_HEIGHT * 0.7, SCREEN_WIDTH * 0.3, current_wall_thickness),   
        ]
        for x, y, w, h in maze_walls_data:
            wall_sprite = arcade.SpriteSolidColor(int(w), int(h), wall_color)
            wall_sprite.center_x = int(x)
            wall_sprite.center_y = int(y)
            self.wall_list.append(wall_sprite)
            
            # 创建对应的Pymunk静态形状
            # Pymunk Poly的顶点是相对于body的重心的，对于静态物体，重心就是position
            # 我们将body的position设为(0,0)，然后用绝对坐标定义Poly的顶点
            # 或者，更简单的是，将body的position设为sprite的center_x, center_y，然后Poly的顶点相对于这个中心
            half_w = w / 2
            half_h = h / 2
            points = [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]
            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            body.position = (x, y)
            shape = pymunk.Poly(body, points)
            shape.collision_type = COLLISION_TYPE_WALL
            shape.friction = 0.8
            shape.elasticity = 0.8 # 为墙壁设置弹性
            self.space.add(body, shape)
        
        # UI面板背景 (可选) - 注意：这些绘制应该在 on_draw 中，setup只负责创建对象
        # 我将暂时注释掉这里的绘制，UI面板的视觉效果可以在on_draw中实现
        # # 顶部UI面板
        # arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 
        #                                   SCREEN_HEIGHT - TOP_UI_PANEL_HEIGHT, SCREEN_HEIGHT, 
        #                                   arcade.color.LIGHT_STEEL_BLUE)
        # # 底部UI面板
        # arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 
        #                                   0, BOTTOM_UI_PANEL_HEIGHT, 
        #                                   arcade.color.LIGHT_STEEL_BLUE)

        arcade.set_background_color(arcade.color.LIGHT_GRAY) 
        self.start_new_round() # 初始化第一回合

    def on_show_view(self):
        self.setup()

    def on_draw(self):
        self.clear()
        self.wall_list.draw() # 绘制墙壁
        self.player_list.draw()
        self.bullet_list.draw() 
        # self.enemy_list.draw()
        # self.powerup_list.draw()

        # UI文字绘制
        ui_text_color = arcade.color.BLACK
        # 顶部UI
        arcade.draw_text(f"模式: {self.mode.upper()}",
                         10, SCREEN_HEIGHT - TOP_UI_PANEL_HEIGHT / 2, 
                         ui_text_color, font_size=16, anchor_y="center")
        arcade.draw_text("Esc: 返回主菜单",
                         SCREEN_WIDTH - 10, SCREEN_HEIGHT - TOP_UI_PANEL_HEIGHT / 2, 
                         ui_text_color, font_size=16, anchor_x="right", anchor_y="center")
        
        # 底部UI
        # 玩家1 UI
        p1_ui_y_text = BOTTOM_UI_PANEL_HEIGHT - 15 # 文字稍高
        p1_ui_y_bar = BOTTOM_UI_PANEL_HEIGHT - 35  # 血条稍低
        if self.player_tank and self.player_tank.is_alive(): 
            arcade.draw_text("P1", 30, p1_ui_y_text, ui_text_color, font_size=18, anchor_y="center")
            self.draw_health_bar(70, p1_ui_y_bar, self.player_tank.health, self.player_tank.max_health)
        arcade.draw_text(f"胜场: {self.player1_score}", 200, p1_ui_y_bar + 7, ui_text_color, font_size=16, anchor_y="center") # 与血条对齐

        # 玩家2 UI (仅PVP模式)
        if self.mode == "pvp":
            # P2 胜场 (最右侧)
            p2_wins_x = SCREEN_WIDTH - 10 # 调整P2胜场X坐标，更靠右
            arcade.draw_text(f"胜场: {self.player2_score}", 
                             p2_wins_x, 
                             p1_ui_y_bar + 7, # Y坐标与P1胜场对齐
                             ui_text_color, 
                             font_size=16, 
                             anchor_x="right", anchor_y="center")

            # P2 血条 (在胜场的左边)
            # 假设胜场文字大致宽度为80 (估算值，"胜场: 0" 大约4个汉字宽度 + 数字)
            # 您可以根据实际显示效果微调这个估算宽度或固定间距
            estimated_wins_text_width = 80 # 根据 "胜场: X" 调整
            health_bar_margin = 20 # 血条与胜场文字的间距
            p2_health_bar_right_x = p2_wins_x - estimated_wins_text_width - health_bar_margin
            p2_health_bar_x = p2_health_bar_right_x - 100 # bar_width 默认为100
            
            if self.player2_tank and self.player2_tank.is_alive():
                self.draw_health_bar(p2_health_bar_x, p1_ui_y_bar, self.player2_tank.health, self.player2_tank.max_health)
                
                # P2 标识 (在血条的左边)
                p2_label_margin = 10 # P2标识与血条的间距
                # 假设 "P2" 标识宽度约30-40
                # estimated_p2_label_width = 40 
                # p2_label_x = p2_health_bar_x - p2_label_margin - estimated_p2_label_width / 2 # 以中心点定位
                # 为了简单，直接给一个固定X，然后调整
                # arcade.draw_text("P2", p2_health_bar_x - p2_label_margin - 15 , p1_ui_y_text, ui_text_color, font_size=18, anchor_x="center", anchor_y="center")
                # 更精确的定位：
                p2_text_x_for_label = p2_health_bar_x - p2_label_margin 
                arcade.draw_text("P2", p2_text_x_for_label, p1_ui_y_text, ui_text_color, font_size=18, anchor_x="right", anchor_y="center")

        # 绘制回合结束提示
        if self.round_over and self.round_over_timer > 0 and self.round_result_text:
            # 半透明背景蒙层
            overlay_width = SCREEN_WIDTH * 0.7
            overlay_height = SCREEN_HEIGHT * 0.3
            overlay_center_x = SCREEN_WIDTH / 2
            overlay_center_y = SCREEN_HEIGHT / 2
            arcade.draw_lrbt_rectangle_filled(overlay_center_x - overlay_width / 2, 
                                              overlay_center_x + overlay_width / 2,
                                              overlay_center_y - overlay_height / 2,
                                              overlay_center_y + overlay_height / 2,
                                              (0, 0, 0, 150)) # 半透明黑色
            # 回合结果文字
            arcade.draw_text(self.round_result_text, 
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 
                             arcade.color.WHITE_SMOKE, font_size=30, 
                             anchor_x="center", anchor_y="center", bold=True)


    def draw_health_bar(self, x, y, current_health, max_health, bar_width=100, bar_height=15, heart_size=12):
            # 假设胜场文字大致宽度为80 (估算值，"胜场: 0" 大约4个汉字宽度 + 数字)
            # 您可以根据实际显示效果微调这个估算宽度或固定间距
            estimated_wins_text_width = 80 
            health_bar_margin = 10
            p2_health_bar_right_x = p2_wins_x - estimated_wins_text_width - health_bar_margin
            p2_health_bar_x = p2_health_bar_right_x - 100 # bar_width 默认为100
            
            if self.player2_tank and self.player2_tank.is_alive():
                self.draw_health_bar(p2_health_bar_x, p1_ui_y_bar, self.player2_tank.health, self.player2_tank.max_health)
                
                # P2 标识 (在血条的左边)
                p2_label_margin = 10
                # 假设 "P2" 标识宽度约30-40
                estimated_p2_label_width = 40 
                p2_label_x = p2_health_bar_x - p2_label_margin - estimated_p2_label_width / 2 # 以中心点定位
                # 为了简单，直接给一个固定X，然后调整
                # arcade.draw_text("P2", p2_health_bar_x - p2_label_margin - 15 , p1_ui_y_text, ui_text_color, font_size=18, anchor_x="center", anchor_y="center")
                # 更精确的定位：
                p2_text_x_for_label = p2_health_bar_x - p2_label_margin 
                arcade.draw_text("P2", p2_text_x_for_label, p1_ui_y_text, ui_text_color, font_size=18, anchor_x="right", anchor_y="center")


    def draw_health_bar(self, x, y, current_health, max_health, bar_width=100, bar_height=15, heart_size=12):
        """绘制血条，用小方块代表血量"""
        # border_color = arcade.color.BLACK
        # filled_color = arcade.color.RED
        # empty_color = arcade.color.LIGHT_GRAY

        # arcade.draw_rectangle_outline(x + bar_width / 2, y + bar_height / 2, bar_width, bar_height, border_color)
        # health_width = (current_health / max_health) * bar_width
        # if health_width > 0:
        #     arcade.draw_rectangle_filled(x + health_width / 2, y + bar_height / 2, health_width, bar_height, filled_color)

        # 使用5个小方块表示血量
        spacing = 2
        block_width = (bar_width - (max_health -1) * spacing) / max_health
        block_height = bar_height
        
        for i in range(max_health):
            block_x = x + i * (block_width + spacing) + block_width / 2
            block_y = y + block_height / 2
            color = arcade.color.RED if i < current_health else arcade.color.GRAY
            
            # 计算 lrtb 坐标
            left = block_x - block_width / 2
            right = block_x + block_width / 2
            bottom = block_y - block_height / 2
            top = block_y + block_height / 2
            
            arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, color) # Corrected: lrbt
            arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, arcade.color.BLACK, border_width=1) # Corrected: lrbt


    def on_update(self, delta_time):
        """ 游戏逻辑更新 """

        if self.round_over:
            self.round_over_timer -= delta_time
            if self.round_over_timer <= 0:
                print(f"DEBUG: Round over timer ended. P1 Score: {self.player1_score}, P2 Score: {self.player2_score}, Max Score: {self.max_score}")
                if self.player1_score >= self.max_score:
                    print("DEBUG: Player 1 wins the game! Showing GameOverView.")
                    game_over_view = GameOverView(f"玩家1 最终胜利!", self.mode)
                    self.window.show_view(game_over_view)
                elif self.mode == "pvp" and self.player2_score >= self.max_score:
                    print("DEBUG: Player 2 wins the game! Showing GameOverView.")
                    game_over_view = GameOverView(f"玩家2 最终胜利!", self.mode)
                    self.window.show_view(game_over_view)
                else:
                    print("DEBUG: No winner yet, starting new round.")
                    self.start_new_round()
            return 

        # 更新物理空间
        self.space.step(delta_time)

        # 坦克移动前记录位置的逻辑不再需要，Pymunk会处理碰撞回退
        # if self.player_list:
        #     for player_obj in self.player_list:
        #         if player_obj: 
        #             player_obj.original_center_x = player_obj.center_x
        #             player_obj.original_center_y = player_obj.center_y
        #             player_obj.original_angle = player_obj.angle

        # Arcade SpriteList的 .update() 仍然需要调用，以便执行Sprite自己的update（如果有的话）
        # 但坦克的移动现在由Pymunk控制，所以Tank.update()方法已变为空或只做同步。
        if self.player_list:
            self.player_list.update() # 调用每个Tank Sprite的update
        
        # 同步Arcade Tank Sprites到Pymunk bodies的位置和角度
        if self.player_list:
            for tank_sprite in self.player_list:
                if tank_sprite and hasattr(tank_sprite, 'sync_with_pymunk_body'):
                    tank_sprite.sync_with_pymunk_body()

        # 同步并处理子弹 (Pymunk版)
        bullets_to_remove_arcade = [] # 存储待移除的Arcade Sprite
        bodies_to_remove_pymunk = []  # 存储待移除的Pymunk Body

        if self.bullet_list:
            for bullet_sprite in self.bullet_list:
                if bullet_sprite and hasattr(bullet_sprite, 'sync_with_pymunk_body'):
                    bullet_sprite.sync_with_pymunk_body()

                # 检查飞出屏幕的子弹 (基于Pymunk body的位置)
                if bullet_sprite.pymunk_body:
                    pos = bullet_sprite.pymunk_body.position
                    if pos.y > GAME_AREA_TOP_Y + bullet_sprite.height or \
                       pos.y < GAME_AREA_BOTTOM_Y - bullet_sprite.height or \
                       pos.x < -bullet_sprite.width or \
                       pos.x > SCREEN_WIDTH + bullet_sprite.width:
                        
                        bullets_to_remove_arcade.append(bullet_sprite)
                        if bullet_sprite.pymunk_body not in bodies_to_remove_pymunk:
                             bodies_to_remove_pymunk.append(bullet_sprite.pymunk_body)

            # 移除旧的Arcade子弹碰撞检测逻辑
            # hit_walls = arcade.check_for_collision_with_list(bullet, self.wall_list) ...
            # hit_tanks = arcade.check_for_collision_with_list(bullet, self.player_list) ...
            
        # 执行移除操作 (在space.step()之后进行)
        for sprite_to_remove in self.arcade_sprites_to_remove_post_step:
            if sprite_to_remove in self.bullet_list: # 假设只移除子弹
                self.bullet_list.remove(sprite_to_remove)
            # 如果也可能移除坦克，需要检查player_list
            # elif sprite_to_remove in self.player_list:
            #     self.player_list.remove(sprite_to_remove)
            #     if sprite_to_remove is self.player_tank: self.player_tank = None
            #     elif sprite_to_remove is self.player2_tank: self.player2_tank = None
        
        for body_to_remove in self.pymunk_bodies_to_remove_post_step:
            if body_to_remove in self.space.bodies:
                 self.space.remove(body_to_remove, *body_to_remove.shapes)
        
        self.arcade_sprites_to_remove_post_step.clear()
        self.pymunk_bodies_to_remove_post_step.clear()


        # 子弹与坦克的碰撞伤害逻辑 (现在由Pymunk碰撞处理器处理)
        # 坦克与坦克的碰撞检测 (现在由Pymunk处理)
        # if self.mode == "pvp" and \
        #    self.player_tank and self.player_tank.is_alive() and \
        #    self.player2_tank and self.player2_tank.is_alive():
        #     if arcade.check_for_collision(self.player_tank, self.player2_tank):
        #         # ... (旧的碰撞回退代码) ...
        #         print("Tanks collided!")

    def on_key_press(self, key, modifiers):
        """ 处理按键按下事件 """
        if key == arcade.key.ESCAPE:
            # TODO: 可以实现暂停菜单
            main_menu_view = MainMenu() # 暂时直接返回主菜单
            self.window.show_view(main_menu_view)

        # 玩家1 (WASD) 控制 - Pymunk版
        if self.player_tank and self.player_tank.pymunk_body: # 确保坦克及其Pymunk body存在
            body = self.player_tank.pymunk_body
            # 定义坦克的移动速度和旋转速度 (这些值可能需要调整以获得好的手感)
            # PLAYER_MOVEMENT_SPEED 和 PLAYER_TURN_SPEED 来自 tank_sprites.py 或在此处定义
            # 我们需要将 PLAYER_TURN_SPEED (度/帧) 转换为 弧度/秒 给 Pymunk
            # 假设帧率为60FPS
            PYMUNK_PLAYER_MAX_SPEED = PLAYER_MOVEMENT_SPEED * 60 # 增大移动速度倍率
            PYMUNK_PLAYER_TURN_RAD_PER_SEC = math.radians(PLAYER_TURN_SPEED * 60 * 1.0) # 增大旋转速度倍率

            if key == arcade.key.W:
                # 根据当前角度计算速度向量
                vx = -PYMUNK_PLAYER_MAX_SPEED * math.sin(body.angle)
                vy = PYMUNK_PLAYER_MAX_SPEED * math.cos(body.angle)
                body.velocity = (vx, vy)
            elif key == arcade.key.S:
                vx = PYMUNK_PLAYER_MAX_SPEED * math.sin(body.angle) # 反向
                vy = -PYMUNK_PLAYER_MAX_SPEED * math.cos(body.angle) # 反向
                body.velocity = (vx, vy)
            elif key == arcade.key.A: # 逆时针 (Pymunk中正角速度是逆时针)/勿修改
                body.angular_velocity = -PYMUNK_PLAYER_TURN_RAD_PER_SEC 
            elif key == arcade.key.D: # 顺时针
                body.angular_velocity = PYMUNK_PLAYER_TURN_RAD_PER_SEC
            elif key == arcade.key.SPACE: # 玩家1射击键
                if self.player_tank and self.player_tank.pymunk_body: # 确保坦克和其body存在
                    bullet = self.player_tank.shoot()
                    if bullet:
                        self.bullet_list.append(bullet)
                        if bullet.pymunk_body and bullet.pymunk_shape:
                            self.space.add(bullet.pymunk_body, bullet.pymunk_shape)

        # 玩家2 (上下左右箭头) 控制 - Pymunk版
        if self.mode == "pvp" and self.player2_tank and self.player2_tank.pymunk_body:
            body = self.player2_tank.pymunk_body
            PYMUNK_PLAYER_MAX_SPEED = PLAYER_MOVEMENT_SPEED * 60 # 增大移动速度倍率
            PYMUNK_PLAYER_TURN_RAD_PER_SEC = math.radians(PLAYER_TURN_SPEED * 60 * 1.0) # 增大旋转速度倍率

            if key == arcade.key.UP:
                vx = -PYMUNK_PLAYER_MAX_SPEED * math.sin(body.angle)
                vy = PYMUNK_PLAYER_MAX_SPEED * math.cos(body.angle)
                body.velocity = (vx, vy)
            elif key == arcade.key.DOWN:
                vx = PYMUNK_PLAYER_MAX_SPEED * math.sin(body.angle)
                vy = -PYMUNK_PLAYER_MAX_SPEED * math.cos(body.angle)
                body.velocity = (vx, vy)
            elif key == arcade.key.LEFT: # 逆时针
                body.angular_velocity = -PYMUNK_PLAYER_TURN_RAD_PER_SEC
            elif key == arcade.key.RIGHT: # 顺时针
                body.angular_velocity = PYMUNK_PLAYER_TURN_RAD_PER_SEC
            elif key == arcade.key.ENTER or key == arcade.key.RSHIFT: 
                if self.player2_tank and self.player2_tank.pymunk_body: # 确保坦克和其body存在
                    bullet = self.player2_tank.shoot()
                    if bullet: # 确保bullet不为None
                        self.bullet_list.append(bullet)
                        if bullet.pymunk_body and bullet.pymunk_shape:
                            self.space.add(bullet.pymunk_body, bullet.pymunk_shape)


    def on_key_release(self, key, modifiers):
        """ 处理按键释放事件 - Pymunk版 """
        # 玩家1
        if self.player_tank and self.player_tank.pymunk_body:
            if key == arcade.key.W or key == arcade.key.S:
                self.player_tank.pymunk_body.velocity = (0, 0)
            elif key == arcade.key.A or key == arcade.key.D:
                self.player_tank.pymunk_body.angular_velocity = 0
        
        # 玩家2
        if self.mode == "pvp" and self.player2_tank and self.player2_tank.pymunk_body:
            if key == arcade.key.UP or key == arcade.key.DOWN:
                self.player2_tank.pymunk_body.velocity = (0, 0)
            elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
                self.player2_tank.pymunk_body.angular_velocity = 0


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
