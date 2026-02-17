import pygame
from pygame.locals import *
from typing import Optional
from dataclasses import dataclass, asdict

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

@dataclass
class IMGPathConfig:
    wall: str = "project\\real_confront_maze\\img\\wall.png"
    floor: str = "project\\real_confront_maze\\img\\tile.png"
    notexture: str = "project\\real_confront_maze\\img\\notexture.png"

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

class ImageManager:
    
    def __init__(self, img_config: Optional[IMGPathConfig] = None, size: tuple = (20, 20)):
        self.img_config = img_config or IMGPathConfig()
        self.size = size
        self.imgs = [self.load_imgs(value, self.img_config.notexture) for key, value in asdict(self.img_config).items() if "notexture" not in key]
        self._image_id = 0

    def load_imgs(self, imgpath, noneimgpath):
        try:
            img = pygame.image.load(imgpath).convert_alpha()
            img = pygame.transform.scale(img, self.size)
            return img
        except pygame.error as e:
            print(f"Failed to load image at {imgpath}: {e}")
            return pygame.image.load(noneimgpath).convert_alpha()

    @property
    def image_id(self):
        return self._image_id
    
    @image_id.setter
    def image_id(self, id):
        self._image_id = id
        try:
            self.imgs[self._image_id]
        except IndexError:
            print("Invalid image ID")
            self._image_id = 0  # デフォルトに戻す

    def get_current_image(self):
        try:
            return self.imgs[self._image_id]
        except IndexError:
            print("Invalid image ID")
            return None

class MapEditer:
    def __init__(self, config: Optional[WindowConfig] = None, control_config: Optional[ControlConfig] = None, path_config: Optional[PathConfig] = None, image_manager: Optional[ImageManager] = None):
        pygame.init()
        self.config = config or WindowConfig()
        self.control_config = control_config or ControlConfig()
        self.path_config = path_config or PathConfig()
        self.screen = self.setup_window(self.config.title, (self.config.width, self.config.height))
        self.clock = pygame.time.Clock()  # FPSのコントロール作成
        self.running = True
        self.grid_list = self.make_grid_list(self.control_config.grid_size)
        self.draw_mode = DrawMode()
        self.image_manager = image_manager or ImageManager(size=(self.control_config.grid_size, self.control_config.grid_size))

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
            self.draw_cell_image((start_x, start_y), self.image_manager.get_current_image())
        if draw_mode.goal_pos:
            goal_x, goal_y = draw_mode.goal_pos
            self.draw_cell_image((goal_x, goal_y), self.image_manager.get_current_image())
        if draw_mode.goal_pos and draw_mode.start_pos:
            goal_x, goal_y = draw_mode.goal_pos
            start_x, start_y = draw_mode.start_pos
            for i in range(max(start_x, goal_x), min(start_x, goal_x) - 1, -1):
                for j in range(max(start_y, goal_y), min(start_y, goal_y) - 1, -1):
                    self.draw_cell_image((i, j), self.image_manager.get_current_image())

    def draw_cell_image(self, pos, image):
        x, y = pos
        self.screen.blit(image, (x * self.control_config.grid_size, y * self.control_config.grid_size))

    def make_grid_list(self, grid_size):
        """Create a list of grid cell positions based on the grid size."""
        grid_list = []
        for y in range(0, self.config.height//grid_size):
            grid_list_temp = []
            for x in range(0, self.config.width//grid_size):
                grid_list_temp.append(0)
            grid_list.append(grid_list_temp)
        return grid_list

    def write_grid_list(self, grid_x, grid_y, value):
        """Write a value to the grid list at the specified grid coordinates."""
        self.grid_list[grid_y][grid_x] = value

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
                    if 49 <= event.key <= 57:  # '1'〜'9'キーで画像を選択
                        self.image_manager.image_id = event.key - 49  # '1'キーは49
                        print(f"Image ID set to: {self.image_manager.image_id+1}")
                    if event.key == K_RETURN:  # Enterキーでスタートとゴールをリセット
                        self.draw_mode.start_pos = None
                        self.draw_mode.goal_pos = None
                        print("Start and goal positions reset.")
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