import pygame
from pygame.locals import *
from typing import Optional
from dataclasses import dataclass, asdict, field
import ast
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent

@dataclass
class PathConfig:
    map: Path = BASE_DIR / "map.json"
    image_folder: Path = BASE_DIR / "img"
    sound_folder: Path = BASE_DIR / "sound"

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
    DEFAULT_CONFIG_JSON_PATH: Path = BASE_DIR / "config.json"

    window: WindowConfig = field(default_factory=WindowConfig)
    grid: GridConfig = field(default_factory=GridConfig)
    path: PathConfig = field(default_factory=PathConfig)

    @classmethod
    def load_from_json(cls, path: Optional[Path]=None):
        config_path = path or cls.DEFAULT_CONFIG_JSON_PATH
        if not config_path.exists():
            return cls()
        with open(config_path, "r") as f:
            data = json.load(f)
        return cls(
            window=WindowConfig(**data.get("window",{})),
            grid=GridConfig(**data.get("grid",{})),
            path=PathConfig(**data.get("path",{}))
        )
    
class AudioManager:
    
    def __init__(self, sound_path_config: Path = None):
        """
        効果音クラスの初期化。
        
        :param sound_path_config: サウンドファイルのパス
        :type sound_path_config: Optional[SoundPathConfig]
        """
        pygame.mixer.init()
        self.sound_path_config = sound_path_config
        self.nonsound = pygame.mixer.Sound(self.sound_path_config / "nosound.wav")
        self.load_sounds(self.sound_path_config, self.nonsound)

    def load_sounds(self, folder_path: Path, nonsound: Optional[pygame.mixer.Sound] = None):
        # フォルダ内の .wav を全部スキャン
        self.sounds = {}
        for file_path in folder_path.glob("*.wav"):
            name = file_path.stem  # ファイル名（拡張子なし）を取得
            try:
                sound = pygame.mixer.Sound(file_path)
            except pygame.error as e:
                print(f"サウンドの読み込みに失敗しました: {file_path}: {e}")
                sound = nonsound
            if name != "nonsound":
                self.sounds[name] = sound

    def play(self, name):
        sound = self.sounds.get(name)
        if sound:
            sound.play()
        else:
            print(f"sound not fould: {name}")

class ImageManager:
    
    def __init__(self, iamge_folder: Path = None, size: tuple = (20, 20)):
        """
        画像管理クラスの初期化。
        
        :param iamge_folder: 画像ファイルのパス 
        :type iamge_folder: Optional[Path]
        :param size: 画像のサイズ (幅, 高さ)
        :type size: tuple
        """
        self.size = size
        self.notexture_img = pygame.image.load(iamge_folder / "notexture.png").convert_alpha()
        self.notexture_img = pygame.transform.scale(self.notexture_img, self.size)
        self.load_images(iamge_folder)
        self.img_keys = sorted(list(self.imgs.keys()))
        self._img_idx = 0

    def load_images(self, folder_path: Path, notexture_img: Optional[pygame.Surface] = None):
        # フォルダ内の .png を全部スキャン
        self.imgs = {}
        for file_path in folder_path.glob("*.png"):
            name = file_path.stem  # ファイル名（拡張子なし）を取得
            try:
                img = pygame.image.load(file_path).convert_alpha()
                img = pygame.transform.scale(img, self.size)
            except pygame.error as e:
                print(f"画像の読み込みに失敗しました: {file_path}: {e}")
                img = notexture_img if notexture_img else pygame.Surface(self.size)
            if name != "notexture":
                self.imgs[name] = img

    @property
    def img_idx(self):
        return self._img_idx
    
    @img_idx.setter
    def img_idx(self, idx):
        self._img_idx = idx
        try:
            self.imgs[self.img_keys[self._img_idx]]
        except IndexError:
            print("Invalid image index")
            self._img_idx = 0  # デフォルトに戻す

    def get_current_image(self):
        try:
            return self.imgs[self.img_keys[self._img_idx]]
        except IndexError:
            print("Invalid image index")
            return None
        
    def get_image(self, key_or_idx):
        """
        名前（str）でも、番号（int）でも画像を取れるようにする

        :param key_or_idx: 画像の名前（str）か、画像ID（int）
        """
        # 1. 数字（int）で指定された場合
        if isinstance(key_or_idx, int):
            try:
                # 数字を名前に変換してから辞書を引く
                key = list(self.imgs.keys())[key_or_idx]
                return self.imgs[key]
            except IndexError:
                print(f"無効なインデックスです: {key_or_idx}")
                return self.notexture_img

        # 2. 名前（str）で指定された場合
        else:
            return self.imgs.get(key_or_idx, self.imgs.get("notexture"))
        
    def get_alpha_image(self, idx, alpha=150):
        """
        指定したIDの画像を半透明画像にして取得する。
        
        :param idx: 画像ID
        :param alpha: 半透明の数値
        """
        original = self.get_image(idx)
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
    
    def load_grid_list(self, path: Path, img_keys: list):
        """
        マップデータ読み込み
        
        :param path: マップデータのファイルパス
        :type path: Path
        :param img_keys: 画像IDと画像名の対応リスト
        :type img_keys: list
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 名前をIndexに戻す処理
        raw_map = data["map_data"]
        self.grid_list = [[img_keys.index(tile_name) if tile_name in img_keys else 0 
                           for tile_name in row] for row in raw_map]    

    def save_grid_list(self, path: Path, img_keys: list):
        """
        マップデータ保存
        
        :param path: 保存先のファイルパス
        :type path: Path
        :param img_keys: 画像IDと画像名の対応リスト
        :type img_keys: list
        """
        # 1. 数字のリストを名前のリストに変換（翻訳）
        translated_map = []
        for row in self.grid_list:
            translated_map.append([img_keys[idx] for idx in row])

        # 2. まるごとJSONとして保存
        data = {
            "map_data": translated_map
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4) # indent=4で見やすく保存

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
            self.editer.update_grid_list()
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
            self.editer.update_grid_list()
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

    def __init__(self, 
                 config: Optional[MasterConfig] = None, 
                 path_conig: Optional[PathConfig] = None):
        """
        マップエディタのメインクラスの初期化。

        :param config: マップエディタの設定をまとめたデータクラス
        :type config: Optional[MasterConfig]
        :param path_conig: マップエディタのパス設定をまとめたデータクラス
        :type path_conig: Optional[PathConfig]
        """
        
        self.path_config = path_conig or PathConfig()
        self.config = config or MasterConfig.load_from_json()

        pygame.init()
        self.screen = self.setup_window(self.config.window.title, self.config.window.aspect)
        self.clock = pygame.time.Clock()
        self.running = True

        self.image_manager = ImageManager(iamge_folder=self.path_config.image_folder, size=(self.config.grid.grid_size, self.config.grid.grid_size))
        self.map_data = MapData(self.config.window.aspect, self.config.grid.grid_size)
        self.renderer = MapRenderer(self.screen, self.image_manager, self.config.grid)
        self.input_hundler = InputHandler(self)
        self.temp_draw_manager = TempDrawManager()
        self.pos_cal = PosCalculater()
        self.audio_manager = AudioManager(self.path_config.sound_folder)

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
        self.map_data.save_grid_list(self.path_config.map, self.image_manager.img_keys)
        self.audio_manager.play("save")

    def select_img(self, idx):
        self.image_manager.img_idx = idx
        self.audio_manager.play("switch")

    def set_startpos_temp(self, pos):
        index = self.pos_cal.pos2grid_index(pos, self.config.grid.grid_size)
        self.temp_draw_manager.start_pos = index

    def set_goalpos_temp(self, pos):
        index = self.pos_cal.pos2grid_index(pos, self.config.grid.grid_size)
        self.temp_draw_manager.goal_pos = index

    def resetpos_temp(self, sound=True):
        if sound == True and not(self.temp_draw_manager.start_pos is None or self.temp_draw_manager.goal_pos is None):
            self.audio_manager.play("cancel")
        self.temp_draw_manager.reset_pos()

    def update_grid_list(self):
        if self.temp_draw_manager.start_pos is not None and self.temp_draw_manager.goal_pos is not None:
            s_x, s_y = self.temp_draw_manager.start_pos
            g_x, g_y = self.temp_draw_manager.goal_pos
            for i in range(min(s_x, g_x), max(s_x, g_x) + 1):
                for j in range(min(s_y, g_y), max(s_y, g_y) + 1):
                    self.map_data.write_cell((i,j), self.image_manager.img_idx)
            self.audio_manager.play("confirm")

    def toggle_show_grid(self):
        self.config.grid.grid_show = not self.config.grid.grid_show

    def load_map(self):
        self.map_data.load_grid_list(self.path_config.map, self.image_manager.img_keys)
        self.audio_manager.play("load")

    def run(self):
        while self.running:
            self.input_hundler.update()
            self.screen.fill((0,0,0))
            self.renderer.render_base(self.map_data.get_current_grid_list())
            self.renderer.render_temp(self.image_manager.img_idx, self.temp_draw_manager)
            self.renderer.draw_grid()
            self.renderer.render_hover_cursor(pygame.mouse.get_pos())
            pygame.display.update()
            self.clock.tick(self.config.window.fps)

if __name__ == "__main__":
    map_editer = MapEditer(MasterConfig.load_from_json(), PathConfig())
    map_editer.run()