import arcade
import math # <--- 添加 math 模块导入
from tank_sprites import Tank, PLAYER_IMAGE_PATH_GREEN # PLAYER_SCALE 将在GameView中定义或作为参数传入Tank

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
        # self.enemy_list = None # TODO: 之后添加敌人
        # self.powerup_list = None # TODO: 之后添加道具

        # 物理引擎 (如果需要更复杂的碰撞)
        # self.physics_engine = None

    def start_new_round(self):
        """开始一个新回合或重置当前回合的坦克状态"""
        print("Starting new round / Resetting tanks...")
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
            if self.player_list is None: self.player_list = arcade.SpriteList()
            self.player_list.append(self.player_tank)
        else: # 如果坦克对象还在，只是重置状态
            self.player_tank.health = self.player_tank.max_health
            self.player_tank.center_x = p1_start_x
            self.player_tank.center_y = p1_start_y
            self.player_tank.angle = 0
            self.player_tank.speed = 0
            self.player_tank.angle_speed = 0
        
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
                if self.player_list is None: self.player_list = arcade.SpriteList()
                self.player_list.append(self.player2_tank)
            else:
                self.player2_tank.health = self.player2_tank.max_health
                self.player2_tank.center_x = p2_start_x
                self.player2_tank.center_y = p2_start_y
                self.player2_tank.angle = 0
                self.player2_tank.speed = 0
                self.player2_tank.angle_speed = 0
        
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
        
        current_wall_thickness = WALL_THICKNESS # 使用类常量
        wall_color = arcade.color.DARK_SLATE_GRAY

        # --- 创建地图墙壁 ---
        # 边界墙壁 - 调整为游戏区域边界
        for x_coord in range(0, SCREEN_WIDTH, current_wall_thickness): # 底部游戏区边界
            wall = arcade.SpriteSolidColor(current_wall_thickness, current_wall_thickness, wall_color)
            wall.center_x = x_coord + current_wall_thickness / 2
            wall.center_y = GAME_AREA_BOTTOM_Y + current_wall_thickness / 2
            self.wall_list.append(wall)
        for x_coord in range(0, SCREEN_WIDTH, current_wall_thickness): # 顶部游戏区边界
            wall = arcade.SpriteSolidColor(current_wall_thickness, current_wall_thickness, wall_color)
            wall.center_x = x_coord + current_wall_thickness / 2
            wall.center_y = GAME_AREA_TOP_Y - current_wall_thickness / 2
            self.wall_list.append(wall)
        # 左侧游戏区边界 (y从GAME_AREA_BOTTOM_Y到GAME_AREA_TOP_Y)
        for y_coord in range(int(GAME_AREA_BOTTOM_Y + current_wall_thickness), int(GAME_AREA_TOP_Y - current_wall_thickness), current_wall_thickness):
            wall = arcade.SpriteSolidColor(current_wall_thickness, current_wall_thickness, wall_color)
            wall.center_x = current_wall_thickness / 2
            wall.center_y = y_coord + current_wall_thickness / 2
            self.wall_list.append(wall)
        # 右侧游戏区边界
        for y_coord in range(int(GAME_AREA_BOTTOM_Y + current_wall_thickness), int(GAME_AREA_TOP_Y - current_wall_thickness), current_wall_thickness):
            wall = arcade.SpriteSolidColor(current_wall_thickness, current_wall_thickness, wall_color)
            wall.center_x = SCREEN_WIDTH - current_wall_thickness / 2
            wall.center_y = y_coord + current_wall_thickness / 2
            self.wall_list.append(wall)
        
        # 示例内部墙壁 - 确保Y坐标在GAME_AREA内
        maze_walls_data = [
            (SCREEN_WIDTH * 0.3, GAME_AREA_BOTTOM_Y + GAME_AREA_HEIGHT / 2, current_wall_thickness, GAME_AREA_HEIGHT * 0.4), 
            (SCREEN_WIDTH * 0.7, GAME_AREA_BOTTOM_Y + GAME_AREA_HEIGHT / 2, current_wall_thickness, GAME_AREA_HEIGHT * 0.4), 
            (SCREEN_WIDTH / 2, GAME_AREA_BOTTOM_Y + GAME_AREA_HEIGHT * 0.3, SCREEN_WIDTH * 0.3, current_wall_thickness),   
            (SCREEN_WIDTH / 2, GAME_AREA_BOTTOM_Y + GAME_AREA_HEIGHT * 0.7, SCREEN_WIDTH * 0.3, current_wall_thickness),   
        ]
        for x, y, w, h in maze_walls_data:
            wall = arcade.SpriteSolidColor(int(w), int(h), wall_color)
            wall.center_x = int(x)
            wall.center_y = int(y)
            self.wall_list.append(wall)
        
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
            p2_wins_x = SCREEN_WIDTH - 30 # 右对齐的X坐标
            arcade.draw_text(f"胜场: {self.player2_score}", 
                             p2_wins_x, 
                             p1_ui_y_bar + 7, # Y坐标与P1胜场对齐
                             ui_text_color, 
                             font_size=16, 
                             anchor_x="right", anchor_y="center")

            # P2 血条 (在胜场的左边)
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
                # 检查是否有最终胜利者
                if self.player1_score >= self.max_score:
                    game_over_view = GameOverView(f"玩家1 最终胜利!", self.mode)
                    self.window.show_view(game_over_view)
                elif self.mode == "pvp" and self.player2_score >= self.max_score:
                    game_over_view = GameOverView(f"玩家2 最终胜利!", self.mode)
                    self.window.show_view(game_over_view)
                else:
                    # 开始新回合
                    self.start_new_round()
            return # 回合结束，不再执行后续更新

        # 坦克移动前记录位置，用于碰撞后回退
        # 确保player_list存在才进行迭代
        if self.player_list:
            for player_obj in self.player_list:
                if player_obj: # 确保坦克对象实际存在 (即不是None)
                    player_obj.original_center_x = player_obj.center_x
                    player_obj.original_center_y = player_obj.center_y
                    player_obj.original_angle = player_obj.angle

        if self.player_list:
            self.player_list.update()
        if self.bullet_list:
            self.bullet_list.update()

        # 坦克与墙壁的碰撞检测
        if self.player_list:
            for player_obj in self.player_list:
                if not player_obj: continue 
                wall_hit_list = arcade.check_for_collision_with_list(player_obj, self.wall_list)
                if wall_hit_list:
                    player_obj.center_x = player_obj.original_center_x
                    player_obj.center_y = player_obj.original_center_y
                    player_obj.speed = 0 
                    player_obj.angle_speed = 0
                    push_amount = 1.0 
                    for wall in wall_hit_list: 
                        dx = player_obj.center_x - wall.center_x
                        dy = player_obj.center_y - wall.center_y
                        overlap_x = (player_obj.width / 2 + wall.width / 2) - abs(dx)
                        overlap_y = (player_obj.height / 2 + wall.height / 2) - abs(dy)
                        if overlap_x > 0 and overlap_y > 0: 
                            if overlap_x < overlap_y : 
                                if dx > 0: player_obj.left = wall.right + push_amount
                                else: player_obj.right = wall.left - push_amount
                            else: 
                                if dy > 0: player_obj.bottom = wall.top + push_amount
                                else: player_obj.top = wall.bottom - push_amount
                            break 

        # 移除飞出屏幕的子弹 (基于新的游戏区域)
        if self.bullet_list:
            for bullet in self.bullet_list:
                if bullet.bottom > GAME_AREA_TOP_Y or \
                   bullet.top < GAME_AREA_BOTTOM_Y or \
                   bullet.right < 0 or \
                   bullet.left > SCREEN_WIDTH:
                    bullet.remove_from_sprite_lists()
                
                hit_walls = arcade.check_for_collision_with_list(bullet, self.wall_list)
                if hit_walls:
                    prev_angle = bullet.angle
                    prev_pos = (bullet.center_x, bullet.center_y)
                    bullet.bounce_count += 1
                    if bullet.bounce_count >= bullet.max_bounces:
                        print(f"Bullet {id(bullet)} removed after {bullet.bounce_count} bounces.")
                        bullet.remove_from_sprite_lists()
                    else:
                        bullet_angle_rad = math.radians(bullet.angle)
                        bullet.center_x -= -bullet.speed * math.sin(bullet_angle_rad) / 2 
                        bullet.center_y -= bullet.speed * math.cos(bullet_angle_rad) / 2  
                        prev_angle_rad = math.radians(prev_angle)
                        vx = -bullet.speed * math.sin(prev_angle_rad)
                        vy = bullet.speed * math.cos(prev_angle_rad)
                        if abs(vx) > abs(vy):  
                            bullet.angle = (180 - prev_angle) % 360
                        else:  
                            bullet.angle = (-prev_angle) % 360
                        print(f"Bullet {id(bullet)} bounced. Pos:({prev_pos[0]:.0f},{prev_pos[1]:.0f}) Angle: {prev_angle:.1f} -> {bullet.angle:.1f}. Bounces: {bullet.bounce_count}")

        # 子弹与坦克的碰撞检测
        # 创建一个列表来存储需要移除的子弹，以避免在迭代过程中修改列表
        bullets_to_remove_after_hit = []
        if self.bullet_list and self.player_list:
            for bullet in self.bullet_list:
                if bullet in bullets_to_remove_after_hit: continue # 如果子弹已标记移除，则跳过

                hit_tanks = arcade.check_for_collision_with_list(bullet, self.player_list)
                for tank in hit_tanks:
                    if tank and bullet.owner is not tank and tank.is_alive(): # 确保坦克对象存在且存活
                        tank.take_damage(1)
                        bullets_to_remove_after_hit.append(bullet) # 标记子弹以便之后移除
                        
                        if not tank.is_alive():
                            print(f"Tank at ({tank.center_x:.0f},{tank.center_y:.0f}) destroyed!")
                            # 不立即从 self.player_list 移除，也不立即将 self.player_tank/player2_tank 设为 None
                            # 仅标记回合结束，由 start_new_round 负责重置或在 GameOverView 中处理显示
                            if not self.round_over:
                                self.round_over = True
                                self.round_over_timer = self.round_over_delay
                                if tank is self.player_tank:
                                    if self.mode == "pvp": 
                                        self.player2_score += 1
                                        print(f"P2 scores! P1: {self.player1_score}, P2: {self.player2_score}")
                                    # else: TODO: PVC 模式下电脑获胜
                                elif self.mode == "pvp" and tank is self.player2_tank:
                                    self.player1_score += 1
                                    print(f"P1 scores! P1: {self.player1_score}, P2: {self.player2_score}")
                        break # 一颗子弹只处理一次对坦克的击中
                if self.round_over: break # 如果回合已结束，停止检查其他子弹

        # 移除被标记的子弹
        for bullet in bullets_to_remove_after_hit:
            if bullet in self.bullet_list: # 再次检查，以防万一
                 bullet.remove_from_sprite_lists()


        # 坦克与坦克的碰撞检测 (仅在PVP模式且有两个存活坦克时)
        if self.mode == "pvp" and \
           self.player_tank and self.player_tank.is_alive() and \
           self.player2_tank and self.player2_tank.is_alive():
            if arcade.check_for_collision(self.player_tank, self.player2_tank):
                self.player_tank.center_x = self.player_tank.original_center_x
                self.player_tank.center_y = self.player_tank.original_center_y
                self.player_tank.speed = 0
                self.player_tank.angle_speed = 0
                self.player2_tank.center_x = self.player2_tank.original_center_x
                self.player2_tank.center_y = self.player2_tank.original_center_y
                self.player2_tank.speed = 0
                self.player2_tank.angle_speed = 0
                print("Tanks collided!")

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
