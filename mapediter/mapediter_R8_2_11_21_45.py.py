import pygame
from pygame.locals import *
from typing import Optional
from dataclasses import dataclass, asdict, field
import ast
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent

@dataclass
class WindowConfig:
    aspect: tuple = (1920, 1200)
    title: str = "Map Editor"
    fps: int = 60

@dataclass
class GridConfig:
    grid_size: int = 20
    grid_color: tuple = (0, 0, 0)
    tempgrid_color: tuple = (255, 0, 0)
    grid_show: bool = True
    cursor_grid_color: tuple = (255,255,255)

@dataclass
class MasterConfig:
    window: WindowConfig = field(default_factory=WindowConfig)
    grid: GridConfig = field(default_factory=GridConfig)

    @classmethod
    def load_from_json(cls, path: Optional[Path]=None):
        config_path = path or Path("config.json")
        if not config_path.exists():
            return cls()
        with open(config_path, "r") as f:
            data = json.load(f)
        return cls(
            window=WindowConfig(**data.get("window",{})),
            grid=GridConfig(**data.get("grid",{})),
        )

@dataclass
class PathConfig:
    grid_list_path: Path = BASE_DIR / "mapediter" / "grid_list.txt"

@dataclass
class IMGPathConfig:
    img_root: Path = BASE_DIR / "img"
    
    floor: Path = img_root / "tile.png"
    wall: Path = img_root / "wall.png"
    floor_pool: Path = img_root / "tile_pool.png"
    wall_pool: Path = img_root / "wall_pool.png"
    water: Path = img_root / "water.png"
    notexture: Path = img_root / "notexture.png"

@dataclass
class SoundPathConfig:
    sound_root: Path = BASE_DIR / "sound"
    
    confirm: Path = sound_root / "confirm.wav"
    cancel: Path = sound_root / "cancel_V2.wav"
    load: Path = sound_root / "load.wav"
    switch: Path = sound_root / "switch.wav"
    save: Path = sound_root / "save.wav"
    nonsound: Path = sound_root / "nosound.wav"

class AudioManager:
    
    def __init__(self, sound_path_config: Optional[SoundPathConfig] = None):
        """
        効果音クラスの初期化。
        
        :param sound_path_config: サウンドファイルのパス
        :type sound_path_config: Optional[SoundPathConfig]
        """
        pygame.mixer.init()
        self.sound_path_config = sound_path_config
        self.nonsound = pygame.mixer.Sound(self.sound_path_config.nonsound)
        self.sounds = {}
        for key, value in asdict(self.sound_path_config).items():
            if not Path(value).is_file():
                continue
            if key in "nonsound":
                continue
            try:
                self.sounds[key] = pygame.mixer.Sound(value)
            except pygame.error as e:
                print(f"Failed ot load music at {value}: {e}")
                self.sounds[key] = self.nonsound

    def play(self, name):
        sound = self.sounds.get(name)
        if sound:
            sound.play()
        else:
            print(f"sound not fould: {name}")

class ImageManager:
    
    def __init__(self, img_config: Optional[IMGPathConfig] = None, size: tuple = (20, 20)):
        """
        画像管理クラスの初期化。
        
        :param img_config: 画像パス設定オブジェクト
        :type img_config: Optional[IMGPathConfig]
        :param size: 画像のサイズ (幅, 高さ)
        :type size: tuple
        """
        self.img_config = img_config or IMGPathConfig()
        self.size = size
        self.notexture_img = pygame.image.load(self.img_config.notexture).convert_alpha()
        self.notexture_img = pygame.transform.scale(self.notexture_img, self.size)
        self.imgs = [self.load_imgs(value, self.notexture_img) for key, value in asdict(self.img_config).items() if "notexture" not in key and Path(value).is_file()]
        self._image_id = 0

    def load_imgs(self, imgpath, notexture):
        try:
            img = pygame.image.load(imgpath).convert_alpha()
            img = pygame.transform.scale(img, self.size)
            return img
        except pygame.error as e:
            print(f"Failed to load image at {imgpath}: {e}")
            return notexture

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
        
    def get_image(self, id):
        """
        指定したIDの画像を取得する。
        
        :param id: 画像ID
        """
        try:
            return self.imgs[id]
        except IndexError:
            print(f"無効な画像IDです。from ImageManager.get_image:{id}")
            return self.notexture_img

    def get_alpha_image(self, id, alpha=150):
        """
        指定したIDの画像を半透明画像にして取得する。
        
        :param id: 画像ID
        :param alpha: 半透明の数値
        """
        original = self.get_image(id)
        alpha_img = original.copy()
        alpha_img.set_alpha(alpha)
        return alpha_img

class MapData:

    def __init__(self, aspect: tuple, grid_size: int):
        """
        マップデータクラスの初期化。
        
        :param aspect: ウィンドウのアスペクト比 (幅, 高さ)
        :type aspect: tuple
        :param grid_size: グリッドのサイズ
        :type grid_size: int
        """
        cols = aspect[0] // grid_size
        rows = aspect[1] // grid_size
        self.grid_list = self.make_grid_list((cols, rows))

    def make_grid_list(self, size: tuple):
        """
        マップを表すリストを作成する。
        
        :param size: マップのサイズ (列数, 行数)
        :type size: tuple
        """
        cols, rows = size
        grid_list = []
        for y in range(0, rows):
            grid_list_temp = []
            for x in range(0, cols):
                grid_list_temp.append(0)
            grid_list.append(grid_list_temp)
        return grid_list
    
    def load_grid_list(self, path: str="grid_list.txt"):
        """
        マップリストを読み込む。

        :param path: 読み込むファイルのパス
        :type path:str
        """
        try:
            with open(path, "r") as f:
                new_grid = []
                for line in f:
                    # 改行を除去して、文字列 "[0, 0, 1...]" をリスト型に変換
                    row = ast.literal_eval(line.strip())
                    new_grid.append(row)
                self.grid_list = new_grid
            print(f"Map loaded from {path}")
        except FileNotFoundError:
            print(f"File not found: {path}. Starting with empty map.")
        except Exception as e:
            print(f"Error loading map: {e}")        

    def save_grid_list(self, path: str="grid_list.txt"):
        """
        マップリストをテキストファイルに保存する。
       
        :param path: 保存先のファイルパス
        :type path: str
        """
        try:
            with open(path, "w") as f:
                for row in self.grid_list:
                    f.write(f"{row}\n")
            print("saved!")
        except FileNotFoundError:
            print(f"File not found: {path}")
        except Exception as e:
            print(f"Error saving map: {e}")

    def write_cell(self, pos: tuple, value: int):
        """
        マップリストの指定した位置に値を書き込む。
        
        :param pos: マップリスト内の位置 (x_index, y_index)
        :type pos: tuple
        :param value: 書き込む値
        :type value: int
        """
        x_index, y_index = pos
        if 0 <= x_index < len(self.grid_list[0]) and 0 <= y_index < len(self.grid_list):
            self.grid_list[y_index][x_index] = value
        else:
            print(f"無効なindexです。from MapData.write_cell: {pos}")

    def get_current_grid_list(self):
        return self.grid_list

class MapRenderer:

    def __init__(self, screen: pygame.Surface, image_manager: ImageManager, grid_config: GridConfig):
        """
        マップ描画クラスの初期化。
        
        :param screen: 描画対象のスクリーン
        :type screen: pygame.Surface
        :param image_manager: 画像管理クラスのオブジェクト
        :type image_manager: ImageManager
        :param grid_config: グリッド設定クラスのデータクラス
        :type grid_config: GridConfig
        """
        self.screen = screen
        self.image_manager = image_manager
        self.grid_config = grid_config
        self.cal_pos = PosCalculater()

    def draw_grid(self):
        """グリッドを描画する。"""
        if self.grid_config.grid_show:
            for x in range(0, self.screen.get_width(), self.grid_config.grid_size):
                pygame.draw.line(self.screen, self.grid_config.grid_color, (x, 0), (x, self.screen.get_height()))
            for y in range(0, self.screen.get_height(), self.grid_config.grid_size):
                pygame.draw.line(self.screen, self.grid_config.grid_color, (0, y), (self.screen.get_width(), y))

    def render_base(self, map_data:list):
        """
        マップデータを基にマップを描画する。
        
        :param map_data: マップデータ (2次元リスト)
        :type map_data: list
        """
        for y_index, row in enumerate(map_data):
            for x_index, img_id in enumerate(row):
                image = self.image_manager.get_image(img_id)
                self.screen.blit(image, (x_index * self.grid_config.grid_size, y_index * self.grid_config.grid_size))

    def render_temp(self, img_id, temp_manager: "TempDrawManager"):
        """
        仮の選択範囲を描画する。
        
        :param img_id: 描画するマップの画像の種類を表すid
        :param temp_manager: 仮描画を管理しているインスタンス変数。
        :type temp_manager: "TempDrawManager"
        """
        if temp_manager.start_pos:
            self.screen.blit(self.image_manager.get_image(img_id), self.cal_pos.grid_index2pos(temp_manager.start_pos, self.grid_config.grid_size))
        if temp_manager.goal_pos:
            self.screen.blit(self.image_manager.get_image(img_id), self.cal_pos.grid_index2pos(temp_manager.goal_pos, self.grid_config.grid_size))
        if temp_manager.goal_pos and temp_manager.start_pos:
            s_x, s_y = temp_manager.start_pos
            g_x, g_y = temp_manager.goal_pos
            for i in range(min(s_x, g_x), max(s_x, g_x) + 1):
                for j in range(min(s_y, g_y), max(s_y, g_y) + 1):
                    self.screen.blit(self.image_manager.get_image(img_id), self.cal_pos.grid_index2pos((i, j), self.grid_config.grid_size))
                    pygame.draw.rect(self.screen, self.grid_config.tempgrid_color, (*self.cal_pos.grid_index2pos((i, j), self.grid_config.grid_size), self.grid_config.grid_size, self.grid_config.grid_size), 2)

    def render_hover_cursor(self, mouse_pos):
        """
        現在のカーソルが選択しているセルを強調表示する。
        
        :param mouse_pos: マウスの座標
        """
        pos = self.cal_pos.pos2pos(mouse_pos, self.grid_config.grid_size)
        pygame.draw.rect(self.screen, self.grid_config.cursor_grid_color, (*pos, self.grid_config.grid_size, self.grid_config.grid_size), 2)

class TempDrawManager:

    def __init__(self):
        self.reset_pos()

    def reset_pos(self):
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

class InputHandler:

    def __init__(self, editer: "MapEditer"):
        """
        入力処理クラスの初期化。
        
        :param editer: MapEditer自身
        :type editer: "MapEditer"
        """
        self.editer  = editer

    def update(self):
        """
        キーボードとマウスからの入力監視処理。
        """
        for event in pygame.event.get():
            if event.type == QUIT:
                self.editer.running = False
            if event.type == KEYDOWN:
                self.handle_keydown(event)
            if event.type == MOUSEBUTTONDOWN:
                self.handle_mousedown(event)

    def handle_keydown(self, event):
        """
        キーボードが押された場合の処理。
        
        :param event: 入力イベントの大本
        """
        if event.key == K_ESCAPE:
            self.editer.running = False
        if event.key == K_RETURN:
            self.editer.update_glid_list()
            self.editer.resetpos_temp(sound=False)
        if event.key == K_s:
            self.editer.save_map()
        if event.key == K_r:
            self.editer.load_map()
        if pygame.K_0 <= event.key <= pygame.K_9:
            self.editer.select_img(event.key-pygame.K_1)

    def handle_mousedown(self, event):
        """
        マウスが押された場合の処理。
        
        :param event: 入力イベントの大本
        """
        if event.button == pygame.BUTTON_LEFT:
            self.editer.set_startpos_temp(pygame.mouse.get_pos())
        if event.button == pygame.BUTTON_RIGHT:
            self.editer.set_goalpos_temp(pygame.mouse.get_pos())
        if event.button == pygame.BUTTON_X1:
            self.editer.resetpos_temp()
        if event.button == pygame.BUTTON_X2:
            self.editer.update_glid_list()
            self.editer.resetpos_temp(sound=False)
        if event.button == pygame.BUTTON_MIDDLE:
            self.editer.toggle_show_grid()

class PosCalculater:

    def pos2grid_index(self, pos, grid_size):
        """
        画面上のx,y座標からグリッドのインデックスに変換。
        
        :param pos: 画面上のx,y座標
        :param grid_size: グリッドのサイズ
        """
        x_pos, y_pos = pos
        x_grid = x_pos//grid_size
        y_grid = y_pos//grid_size
        return (x_grid,y_grid)
    
    def grid_index2pos(self, pos, grid_size):
        """
        グリッドのインデックスから画面上のx,y座標に変換。
        
        :param pos: グリッドのインデックス
        :param grid_size: グリッドのサイズ
        """
        x_grid, y_grid = pos
        x_pos = x_grid*grid_size
        y_pos = y_grid*grid_size
        return (x_pos, y_pos)
    
    def pos2pos(self, pos, grid_size):
        index = self.pos2grid_index(pos, grid_size)
        pos = self.grid_index2pos(index, grid_size)
        return pos

class MapEditer:

    def __init__(self, config: Optional[WindowConfig] = None, 
                 grid_config: Optional[GridConfig] = None, 
                 path_config: Optional[PathConfig] = None,
                 image_path_config: Optional[IMGPathConfig] = None,
                 sound_path_config:Optional[SoundPathConfig] = None,
                 master_config: Optional[MasterConfig] = None):
        
        self.config = config or WindowConfig()
        self.grid_config = grid_config or GridConfig()
        self.path_config = path_config or PathConfig()
        self.image_path_config = image_path_config or IMGPathConfig()
        self.sound_path_config = sound_path_config or SoundPathConfig()
        self.master_config = master_config or MasterConfig()

        pygame.init()
        self.screen = self.setup_window(self.config.title, self.config.aspect)
        self.clock = pygame.time.Clock()
        self.running = True

        self.image_manager = ImageManager(img_config=self.image_path_config, size=(self.grid_config.grid_size, self.grid_config.grid_size))
        self.map_data = MapData(self.config.aspect, self.grid_config.grid_size)
        self.renderer = MapRenderer(self.screen, self.image_manager, self.grid_config)
        self.input_hundler = InputHandler(self)
        self.temp_draw_manager = TempDrawManager()
        self.pos_cal = PosCalculater()
        self.audio_manager = AudioManager(self.sound_path_config)

    def setup_window(self, title, aspect):
        """
        ウィンドウをセットアップする。
        
        :param title: ウィンドウのタイトル
        :param aspect: ウィンドウのアスペクト比 (幅, 高さ)
        """
        screen = pygame.display.set_mode(aspect)
        pygame.display.set_caption(title)
        return screen

    def save_map(self):
        self.map_data.save_grid_list(self.path_config.grid_list_path)
        self.audio_manager.play("save")

    def select_img(self, id):
        self.image_manager.image_id = id
        self.audio_manager.play("switch")

    def set_startpos_temp(self, pos):
        index = self.pos_cal.pos2grid_index(pos, self.grid_config.grid_size)
        self.temp_draw_manager.start_pos = index

    def set_goalpos_temp(self, pos):
        index = self.pos_cal.pos2grid_index(pos, self.grid_config.grid_size)
        self.temp_draw_manager.goal_pos = index

    def resetpos_temp(self, sound=True):
        if sound == True and not(self.temp_draw_manager.start_pos is None or self.temp_draw_manager.goal_pos is None):
            self.audio_manager.play("cancel")
        self.temp_draw_manager.reset_pos()

    def update_glid_list(self):
        if self.temp_draw_manager.start_pos and self.temp_draw_manager.goal_pos:
            s_x, s_y = self.temp_draw_manager.start_pos
            g_x, g_y = self.temp_draw_manager.goal_pos
            for i in range(min(s_x, g_x), max(s_x, g_x) + 1):
                for j in range(min(s_y, g_y), max(s_y, g_y) + 1):
                    self.map_data.write_cell((i,j), self.image_manager.image_id)
            self.audio_manager.play("confirm")

    def toggle_show_grid(self):
        self.grid_config.grid_show = not self.grid_config.grid_show

    def load_map(self):
        self.map_data.glid_list = self.map_data.load_grid_list(self.path_config.grid_list_path)
        self.audio_manager.play("load")

    def run(self):
        while self.running:
            self.input_hundler.update()
            self.screen.fill((0,0,0))
            self.renderer.render_base(self.map_data.get_current_grid_list())
            self.renderer.render_temp(self.image_manager.image_id, self.temp_draw_manager)
            self.renderer.draw_grid()
            self.renderer.render_hover_cursor(pygame.mouse.get_pos())
            pygame.display.update()
            self.clock.tick(self.config.fps)

if __name__ == "__main__":
    map_editer = MapEditer()
    map_editer.run()