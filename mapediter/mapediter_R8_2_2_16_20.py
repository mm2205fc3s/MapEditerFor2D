import pygame
from pygame.locals import *
from typing import Optional
from dataclasses import dataclass

@dataclass
class WindowConfig:
    title: str = "Map Editor"
    width: int = 1920
    height: int = 1200
    fps: int = 60

@dataclass
class ControlConfig:
    grid_size: int = 20  # セルのサイズ
    start_color: tuple = (0, 255, 0)  # スタート位置の色（緑）
    goal_color: tuple = (255, 0, 0)   # ゴール位置の色（赤）

@dataclass
class PathConfig:
    grid_list_path: str = "project\\real_confront_maze\\mapediter\\grid_list.txt"

class DrawMode:

    def __init__(self):
        self._start_pos = None
        self._goal_pos = None

    @property
    def start_pos(self):
        return self._start_pos
    
    @start_pos.setter
    def start_pos(self, pos):
        self._start_pos = pos

    @property
    def goal_pos(self):
        return self._goal_pos
    
    @goal_pos.setter
    def goal_pos(self, pos):
        self._goal_pos = pos

class MapEditer:
    def __init__(self, config: Optional[WindowConfig] = None, control_config: Optional[ControlConfig] = None, path_config: Optional[PathConfig] = None):
        pygame.init()
        self.config = config or WindowConfig()
        self.control_config = control_config or ControlConfig()
        self.path_config = path_config or PathConfig()
        self.screen = self.setup_window(self.config.title, (self.config.width, self.config.height))
        self.clock = pygame.time.Clock()  # FPSのコントロール作成
        self.running = True
        self.grid_list = self.make_grid_list(self.control_config.grid_size)
        self.draw_mode = DrawMode()

    def setup_window(self, title, aspect):
        """Create the pygame window using values from `self.config`."""
        screen = pygame.display.set_mode(aspect)
        pygame.display.set_caption(title)
        return screen
    
    def set_grid(self, grid_size):
        """Set up a grid on the screen with the specified grid size."""
        for x in range(0, self.config.width, grid_size):
            pygame.draw.line(self.screen, (200, 200, 200), (x, 0), (x, self.config.height))
        for y in range(0, self.config.height, grid_size):
            pygame.draw.line(self.screen, (200, 200, 200), (0, y), (self.config.width, y))

    def draw_cell(self, draw_mode: DrawMode, color: tuple = (0, 255, 0)):
        if draw_mode.start_pos:
            start_x, start_y = draw_mode.start_pos
            pygame.draw.rect(self.screen, self.control_config.start_color, (start_x * self.control_config.grid_size, start_y * self.control_config.grid_size, self.control_config.grid_size, self.control_config.grid_size))
        if draw_mode.goal_pos:
            goal_x, goal_y = draw_mode.goal_pos
            pygame.draw.rect(self.screen, self.control_config.goal_color, (goal_x * self.control_config.grid_size, goal_y * self.control_config.grid_size, self.control_config.grid_size, self.control_config.grid_size))
        if draw_mode.goal_pos and draw_mode.start_pos:
            goal_x, goal_y = draw_mode.goal_pos
            start_x, start_y = draw_mode.start_pos
            for i in range(max(start_x, goal_x), min(start_x, goal_x) - 1, -1):
                for j in range(max(start_y, goal_y), min(start_y, goal_y) - 1, -1):
                    pygame.draw.rect(self.screen, self.control_config.goal_color, (i * self.control_config.grid_size, j * self.control_config.grid_size, self.control_config.grid_size, self.control_config.grid_size))
            pygame.draw.rect(self.screen, self.control_config.goal_color, (goal_x * self.control_config.grid_size, goal_y * self.control_config.grid_size, self.control_config.grid_size, self.control_config.grid_size))

    def make_grid_list(self, grid_size):
        """Create a list of grid cell positions based on the grid size."""
        grid_list = []
        for y in range(0, self.config.height, grid_size):
            grid_list_temp = []
            for x in range(0, self.config.width, grid_size):
                grid_list_temp.append((x, y))
            grid_list.append(grid_list_temp)
        return grid_list

    def save_grid_list(self, path="grid_list.txt"):
        """Save the grid list to a text file."""
        with open(path, "w") as f:
            for row in self.grid_list:
                f.write(f"{row}\n")

    def grid_cell_from_pos(self, pos):
        x, y = pos
        grid_x = x // self.control_config.grid_size
        grid_y = y // self.control_config.grid_size
        return (grid_x, grid_y)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.running = False
                    if event.key == K_s:  # 's'キーでgrid_listを保存
                        self.save_grid_list(self.path_config.grid_list_path)
                        print(f"Grid list saved to {self.path_config.grid_list_path}")
                if event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左クリック
                        grid_x, grid_y = self.grid_cell_from_pos(event.pos)
                        print(f"Clicked on grid cell: ({grid_x}, {grid_y})")
                        self.draw_mode.start_pos = (grid_x, grid_y)
                        print(f"Start position set to: {self.draw_mode.start_pos}")
                    if event.button == 2:  # 中クリック
                        grid_x, grid_y = self.grid_cell_from_pos(event.pos)
                        print(f"Clicked on grid cell: ({grid_x}, {grid_y})")
                        self.draw_mode.goal_pos = None
                        self.draw_mode.start_pos = None
                        print("Goal and start positions cleared.")
                    if event.button == 3:  # 右クリック
                        grid_x, grid_y = self.grid_cell_from_pos(event.pos)
                        print(f"Clicked on grid cell: ({grid_x}, {grid_y})")
                        self.draw_mode.goal_pos = (grid_x, grid_y)
                        print(f"Goal position set to: {self.draw_mode.goal_pos}")
            self.screen.fill((0, 0, 0))  # 画面を黒で埋める
            self.set_grid(self.control_config.grid_size)
            self.draw_cell(self.draw_mode)  # スタートとゴールを設定された色で描画
            pygame.display.flip()  # 画面更新
            self.clock.tick(self.config.fps)  # FPSを限定する
        pygame.quit()
        
if __name__ == "__main__":
    map_editer = MapEditer()
    map_editer.run()