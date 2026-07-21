import csv
import os
import random
import xml.etree.ElementTree as ET
from io import StringIO

import pygame


TILED_FLIP_MASK = 0xE0000000
DEFAULT_MAP_FILE = os.path.join("assets", "map", "TS.tmx")
TINY_SWORDS_TILESET_DIR = os.path.join(
    "assets", "map", "Tiny Swords (Free Pack)", "Terrain", "Tileset")
TINY_SWORDS_TERRAIN_DIR = os.path.join(
    "assets", "map", "Tiny Swords (Free Pack)", "Terrain")

WATER_GID = 55
TERRAIN_TILESET_LAST_GID = 54
PROP_SPAWN_CHANCE = 0.012
ROCK_SPAWN_CHANCE = 0.020
FOAM_FRAME_MS = 95
TREE_FRAME_MS = 140


def _segment_vs_rect(x1: float, y1: float, x2: float, y2: float, rect):
    """Slab test đoạn thẳng (x1,y1)->(x2,y2) vs 1 pygame.Rect. Trả về
    (t, normal_x, normal_y) tại điểm cắt GẦN (x1,y1) nhất trong đoạn
    (t trong [0,1]), hoặc None nếu không cắt. Normal luôn trục X hoặc Y
    (±1, 0) hay (0, ±1) — dùng để phản xạ vector vận tốc/hướng bay."""
    dx = x2 - x1
    dy = y2 - y1
    t_near, t_far = 0.0, 1.0
    nx, ny = 0.0, 0.0

    for axis, (origin, delta, lo, hi) in enumerate((
        (x1, dx, rect.left, rect.right),
        (y1, dy, rect.top, rect.bottom),
    )):
        if delta == 0:
            if origin < lo or origin > hi:
                return None
            continue
        t1 = (lo - origin) / delta
        t2 = (hi - origin) / delta
        face_sign = -1.0
        if t1 > t2:
            t1, t2 = t2, t1
            face_sign = 1.0
        if t1 > t_near:
            t_near = t1
            nx, ny = (face_sign, 0.0) if axis == 0 else (0.0, face_sign)
        if t2 < t_far:
            t_far = t2
        if t_near > t_far:
            return None

    if t_near < 0.0 or t_near > 1.0 or (nx == 0.0 and ny == 0.0):
        return None
    return t_near, nx, ny


class TiledMap:
    """Small TMX renderer for finite, orthogonal, CSV tile maps."""

    def __init__(self, map_path: str):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.map_path = map_path
        if not os.path.isabs(self.map_path):
            self.map_path = os.path.join(self.root_dir, self.map_path)
        self.map_dir = os.path.dirname(self.map_path)
        self.tilesets = []
        self.tile_cache = {}
        self.scaled_cache = {}
        self.layers = []
        self.water_tiles = set()
        self.grass_tiles = set()
        self.auto_foam = []
        self.decorations = []
        self.collision_rects = []
        self.foam_frames = []
        self.tree_sprites = []
        self.stump_sprites = []
        self.rock_sprites = []
        self.monastery_sprites = []
        self.bush_sprites = []
        self._load()

    def _load(self) -> None:
        tree = ET.parse(self.map_path)
        root = tree.getroot()
        if root.get("orientation") != "orthogonal":
            raise ValueError("Only orthogonal TMX maps are supported.")
        if root.get("infinite", "0") != "0":
            raise ValueError("Only finite TMX maps are supported.")

        self.width = int(root.get("width", "0"))
        self.height = int(root.get("height", "0"))
        self.tile_width = int(root.get("tilewidth", "0"))
        self.tile_height = int(root.get("tileheight", "0"))
        self.pixel_width = self.width * self.tile_width
        self.pixel_height = self.height * self.tile_height
        self.origin_x = -self.pixel_width / 2
        self.origin_y = -self.pixel_height / 2

        for tileset_node in root.findall("tileset"):
            tileset = self._load_tileset(tileset_node)
            self.tilesets.append(tileset)
        self.tilesets.sort(key=lambda item: item["firstgid"])

        for layer_node in root.findall("layer"):
            data_node = layer_node.find("data")
            if data_node is None or data_node.get("encoding") != "csv":
                continue
            width = int(layer_node.get("width", self.width))
            height = int(layer_node.get("height", self.height))
            gids = self._parse_csv_layer(data_node.text or "", width, height)
            self.layers.append({
                "name": layer_node.get("name", ""),
                "width": width,
                "height": height,
                "gids": gids,
                "visible": layer_node.get("visible", "1") != "0",
                "opacity": float(layer_node.get("opacity", "1")),
            })

        self._load_environment_assets()
        self._build_tile_flags()
        self._build_auto_foam()
        self._build_decorations()
        self._build_collision()

    def _load_tileset(self, tileset_node) -> dict:
        firstgid = int(tileset_node.get("firstgid", "1"))
        source = tileset_node.get("source")
        if source:
            tsx_path = os.path.normpath(os.path.join(self.map_dir, source))
            if os.path.exists(tsx_path):
                tsx_root = ET.parse(tsx_path).getroot()
                tsx_dir = os.path.dirname(tsx_path)
            else:
                tsx_root = self._fallback_tileset_root(source)
                tsx_dir = os.path.join(self.root_dir, TINY_SWORDS_TILESET_DIR)
        else:
            tsx_root = tileset_node
            tsx_dir = self.map_dir

        image_node = tsx_root.find("image")
        if image_node is None:
            raise ValueError("Tileset has no image source.")

        image_path = self._resolve_tileset_image_path(tsx_dir, image_node.get("source", ""))
        image = pygame.image.load(image_path).convert_alpha()
        tile_width = int(tsx_root.get("tilewidth", self.tile_width))
        tile_height = int(tsx_root.get("tileheight", self.tile_height))
        columns = int(tsx_root.get("columns", image.get_width() // tile_width))
        tilecount = int(tsx_root.get(
            "tilecount",
            (image.get_width() // tile_width) * (image.get_height() // tile_height),
        ))
        return {
            "firstgid": firstgid,
            "image": image,
            "tile_width": tile_width,
            "tile_height": tile_height,
            "columns": max(1, columns),
            "tilecount": tilecount,
        }

    def _resolve_tileset_image_path(self, tsx_dir: str, source: str) -> str:
        source = source.replace("/", os.sep)
        filename = os.path.basename(source)
        candidates = [
            os.path.normpath(os.path.join(tsx_dir, source)),
            os.path.normpath(os.path.join(tsx_dir, filename)),
            os.path.normpath(os.path.join(self.map_dir, filename)),
            os.path.normpath(os.path.join(self.root_dir, "assets", "map", filename)),
            os.path.normpath(os.path.join(self.root_dir, TINY_SWORDS_TILESET_DIR, filename)),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        raise FileNotFoundError(
            f"Missing tileset image {source!r}; tried: "
            + ", ".join(candidates)
        )

    def _fallback_tileset_root(self, source: str):
        filename = os.path.splitext(os.path.basename(source))[0] + ".png"
        image_path = os.path.join(self.root_dir, TINY_SWORDS_TILESET_DIR, filename)
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Missing tileset image for {source}: {image_path}")

        image = pygame.image.load(image_path)
        tilecount = (image.get_width() // self.tile_width) * (image.get_height() // self.tile_height)
        columns = image.get_width() // self.tile_width
        return ET.fromstring(
            f'<tileset tilewidth="{self.tile_width}" tileheight="{self.tile_height}" '
            f'tilecount="{tilecount}" columns="{columns}">'
            f'<image source="{filename}" width="{image.get_width()}" height="{image.get_height()}"/>'
            f'</tileset>'
        )

    def _parse_csv_layer(self, text: str, width: int, height: int) -> list[int]:
        values = []
        for row in csv.reader(StringIO(text.strip())):
            values.extend(int(item.strip()) for item in row if item.strip())
        expected = width * height
        if len(values) != expected:
            raise ValueError(f"Layer has {len(values)} tiles, expected {expected}.")
        return values

    def _load_environment_assets(self) -> None:
        terrain_dir = os.path.join(self.root_dir, TINY_SWORDS_TERRAIN_DIR)
        foam_path = os.path.join(terrain_dir, "Tileset", "Water Foam.png")
        self.foam_frames = self._slice_sheet(foam_path, 192, 192)

        trees_dir = os.path.join(terrain_dir, "Resources", "Wood", "Trees")
        tree_specs = [
            ("Tree1.png", 192, 256),
            ("Tree2.png", 192, 256),
            ("Tree3.png", 192, 192),
            ("Tree4.png", 192, 192),
        ]
        for filename, frame_w, frame_h in tree_specs:
            frames = self._slice_sheet(os.path.join(trees_dir, filename), frame_w, frame_h)
            if frames:
                # Scale cây to lên 1.4 lần
                scaled_frames = []
                for frame in frames:
                    new_w = int(frame.get_width() * 1.4)
                    new_h = int(frame.get_height() * 1.4)
                    scaled_frames.append(pygame.transform.scale(frame, (new_w, new_h)))
                self.tree_sprites.append(scaled_frames)
        for filename in ("Stump 1.png", "Stump 2.png", "Stump 3.png", "Stump 4.png"):
            frames = self._slice_sheet(os.path.join(trees_dir, filename), 192, 256)
            if frames:
                self.stump_sprites.append(frames)

        rocks_dir = os.path.join(terrain_dir, "Decorations", "Rocks")
        for filename in ("Rock1.png", "Rock2.png", "Rock3.png", "Rock4.png"):
            path = os.path.join(rocks_dir, filename)
            if os.path.exists(path):
                self.rock_sprites.append([pygame.image.load(path).convert_alpha()])

        # Load Monastery
        monastery_path = os.path.join(self.root_dir, "assets", "map", "Tiny Swords (Free Pack)", "Buildings", "Black Buildings", "Monastery.png")
        raw_mon_sprites = self._slice_sheet(monastery_path, 192, 320)
        self.monastery_sprites = []
        for frame in raw_mon_sprites:
            new_w = int(frame.get_width() * 1.5)
            new_h = int(frame.get_height() * 1.5)
            self.monastery_sprites.append(pygame.transform.scale(frame, (new_w, new_h)))

        # Load Bushes from Tiny Swords (Free Pack)
        bushes_dir = os.path.join(terrain_dir, "Decorations", "Bushes")
        self.bush_sprites = []
        for filename in ("Bushe1.png", "Bushe2.png", "Bushe3.png", "Bushe4.png"):
            path = os.path.join(bushes_dir, filename)
            frames = self._slice_sheet(path, 128, 128)
            if frames:
                self.bush_sprites.append(frames)

        # Load Water Rocks from Tiny Swords (Free Pack)
        water_rocks_dir = os.path.join(terrain_dir, "Decorations", "Rocks in the Water")
        self.water_rock_sprites = []
        for filename in ("Water Rocks_01.png", "Water Rocks_02.png", "Water Rocks_03.png", "Water Rocks_04.png"):
            path = os.path.join(water_rocks_dir, filename)
            frames = self._slice_sheet(path, 64, 64)
            if frames:
                self.water_rock_sprites.append(frames)

    def _slice_sheet(self, path: str, frame_w: int, frame_h: int) -> list[pygame.Surface]:
        if not os.path.exists(path):
            return []
        sheet = pygame.image.load(path).convert_alpha()
        frames = []
        for y in range(0, sheet.get_height() - frame_h + 1, frame_h):
            for x in range(0, sheet.get_width() - frame_w + 1, frame_w):
                frame = sheet.subsurface((x, y, frame_w, frame_h)).copy()
                if frame.get_bounding_rect().width > 0:
                    frames.append(frame)
        return frames

    def _build_tile_flags(self) -> None:
        for layer in self.layers:
            name = layer["name"]
            is_water_layer = self._is_water_layer(name)
            is_grass_layer = self._is_grass_layer(name)
            if not is_water_layer and not is_grass_layer:
                continue
            for ty in range(layer["height"]):
                row = ty * layer["width"]
                for tx in range(layer["width"]):
                    clean_gid = layer["gids"][row + tx] & ~TILED_FLIP_MASK
                    pos = (tx, ty)
                    if is_water_layer and clean_gid == WATER_GID:
                        self.water_tiles.add(pos)
                    elif is_grass_layer and 0 < clean_gid <= TERRAIN_TILESET_LAST_GID:
                        self.grass_tiles.add(pos)

    def _is_water_layer(self, name: str) -> bool:
        normalized = name.strip().lower().replace("_", " ").replace("-", " ")
        return normalized in {"water", "waterunder", "water under", "tile layer 4"}

    def _is_grass_layer(self, name: str) -> bool:
        normalized = name.strip().lower().replace("_", " ").replace("-", " ")
        return normalized in {"grass", "shoreline"}

    def _is_collision_layer(self, name: str) -> bool:
        normalized = name.strip().lower().replace("_", " ").replace("-", " ")
        return normalized in {"collision", "collisions", "blocked", "obstacle", "obstacles"}

    def _build_auto_foam(self) -> None:
        if not self.foam_frames:
            return
        for tx, ty in sorted(self.grass_tiles):
            water_under = (tx, ty) in self.water_tiles
            adjacent_water = (
                (tx, ty - 1) in self.water_tiles
                or (tx + 1, ty) in self.water_tiles
                or (tx, ty + 1) in self.water_tiles
                or (tx - 1, ty) in self.water_tiles
            )
            if not water_under and not adjacent_water:
                continue
            phase = int(self._tile_random(tx, ty, "foam_phase") * len(self.foam_frames))
            self.auto_foam.append({"x": tx, "y": ty, "frames": self.foam_frames, "phase": phase})

    def _find_island_tiles(self) -> list[tuple[int, int]]:
        # Tìm các nhóm ô cỏ kết nối với nhau (connected components)
        visited = set()
        components = []
        for tile in self.grass_tiles:
            if tile in visited:
                continue
            comp = []
            queue = [tile]
            visited.add(tile)
            while queue:
                cx, cy = queue.pop(0)
                comp.append((cx, cy))
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    neighbor = (cx + dx, cy + dy)
                    if neighbor in self.grass_tiles and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(comp)

        if not components:
            return []

        # Nhóm lớn nhất là đất liền (mainland), các nhóm nhỏ hơn là đảo (island)
        components.sort(key=len)
        if len(components) > 1:
            # Chọn nhóm cỏ nhỏ hơn nằm gần tâm bản đồ nhất làm đảo chính
            center_x = self.width // 2
            center_y = self.height // 2

            def dist_to_center(c):
                ax = sum(t[0] for t in c) / len(c)
                ay = sum(t[1] for t in c) / len(c)
                return (ax - center_x) ** 2 + (ay - center_y) ** 2

            islands = components[:-1]
            islands.sort(key=dist_to_center)
            return islands[0]

        return []

    def _build_decorations(self) -> None:
        # Tự động tìm hòn đảo trong bản đồ
        island_tiles = self._find_island_tiles()
        if island_tiles:
            xs = [t[0] for t in island_tiles]
            ys = [t[1] for t in island_tiles]
            island_cx = (min(xs) + max(xs)) // 2
            island_cy = (min(ys) + max(ys)) // 2
        else:
            island_cx = self.width // 2
            island_cy = self.height // 2

        # Loại bỏ các ô gạch xung quanh tâm đảo (bán kính 4 ô) khỏi danh sách sinh ngẫu nhiên vật thể khác
        candidates = sorted(
            pos for pos in self.grass_tiles
            if not self._near_water(*pos)
            and (abs(pos[0] - island_cx) > 4 or abs(pos[1] - island_cy) > 4)
        )
        prop_sprites = (
            [("tree", frames) for frames in self.tree_sprites]
            + [("stump", frames) for frames in self.stump_sprites]
        )
        for tx, ty in candidates:
            roll = self._tile_random(tx, ty, "decor")
            if prop_sprites and roll < PROP_SPAWN_CHANCE:
                kind, frames = self._choose_prop_sprite(prop_sprites, tx, ty, "tree")
                sprite = frames[0]
                self.decorations.append({
                    "kind": kind,
                    "frames": frames,
                    "frame_ms": TREE_FRAME_MS,
                    "phase": int(self._tile_random(tx, ty, "tree_phase") * len(frames)),
                    "x": self.origin_x + tx * self.tile_width + self.tile_width / 2 - sprite.get_width() / 2,
                    "y": self.origin_y + (ty + 1) * self.tile_height - sprite.get_height() + 8,
                    "sort_y": self.origin_y + (ty + 1) * self.tile_height,
                })
            elif self.rock_sprites and roll < PROP_SPAWN_CHANCE + ROCK_SPAWN_CHANCE:
                # Đá luôn có đúng 1 frame (xem self.rock_sprites) — không animation
                # nên khỏi cần "frame_ms"/"phase", _draw_decorations tự dùng mặc định.
                self.decorations.append({
                    "kind": "rock",
                    "frames": self._choose_sprite(self.rock_sprites, tx, ty, "rock"),
                    "x": self.origin_x + tx * self.tile_width,
                    "y": self.origin_y + ty * self.tile_height,
                    "sort_y": self.origin_y + (ty + 1) * self.tile_height,
                })

        # Đặt Monastery ở chính giữa đảo phát hiện được một cách động
        if self.monastery_sprites:
            sprite = self.monastery_sprites[0]
            mon_x = self.origin_x + island_cx * self.tile_width + self.tile_width / 2 - sprite.get_width() / 2
            mon_y = self.origin_y + (island_cy + 2) * self.tile_height - sprite.get_height()
            self.decorations.append({
                "kind": "monastery",
                "frames": self.monastery_sprites,
                "frame_ms": 999999,
                "phase": 0,
                "x": mon_x,
                "y": mon_y,
                "sort_y": self.origin_y + (island_cy + 2) * self.tile_height,
            })


        # Đặt 1-2 loại cây xung quanh đảo động theo tọa độ đảo tìm được (đảm bảo không đè nhau)
        if len(self.tree_sprites) >= 2:
            # Cây 1 ở phía sau bên trái đảo
            sprite = self.tree_sprites[0][0]
            self.decorations.append({
                "kind": "tree",
                "frames": self.tree_sprites[0],
                "frame_ms": TREE_FRAME_MS,
                "phase": 0,
                "x": self.origin_x + (island_cx - 2.5) * self.tile_width + self.tile_width / 2 - sprite.get_width() / 2,
                "y": self.origin_y + (island_cy - 1.5) * self.tile_height - sprite.get_height() + 8,
                "sort_y": self.origin_y + (island_cy - 1.5) * self.tile_height,
            })
            # Cây 2 ở phía sau bên phải đảo
            sprite = self.tree_sprites[1][0]
            self.decorations.append({
                "kind": "tree",
                "frames": self.tree_sprites[1],
                "frame_ms": TREE_FRAME_MS,
                "phase": 1,
                "x": self.origin_x + (island_cx + 2.5) * self.tile_width + self.tile_width / 2 - sprite.get_width() / 2,
                "y": self.origin_y + (island_cy - 1.5) * self.tile_height - sprite.get_height() + 8,
                "sort_y": self.origin_y + (island_cy - 1.5) * self.tile_height,
            })
            # Cây 1 ở phía trước bên phải đảo
            sprite = self.tree_sprites[0][0]
            self.decorations.append({
                "kind": "tree",
                "frames": self.tree_sprites[0],
                "frame_ms": TREE_FRAME_MS,
                "phase": 2,
                "x": self.origin_x + (island_cx + 2.5) * self.tile_width + self.tile_width / 2 - sprite.get_width() / 2,
                "y": self.origin_y + (island_cy + 3.5) * self.tile_height - sprite.get_height() + 8,
                "sort_y": self.origin_y + (island_cy + 3.5) * self.tile_height,
            })

        # Đặt 1-2 bụi cỏ xung quanh đảo động theo tọa độ đảo tìm được (đảm bảo không đè nhau)
        if len(self.bush_sprites) >= 2:
            # Bụi cỏ 1 ở phía trước bên trái
            sprite = self.bush_sprites[0][0]
            self.decorations.append({
                "kind": "bush",
                "frames": self.bush_sprites[0],
                "frame_ms": TREE_FRAME_MS,
                "phase": 0,
                "x": self.origin_x + (island_cx - 2.5) * self.tile_width + self.tile_width / 2 - sprite.get_width() / 2,
                "y": self.origin_y + (island_cy + 2.5) * self.tile_height - sprite.get_height() + 8,
                "sort_y": self.origin_y + (island_cy + 2.5) * self.tile_height,
            })
            # Bụi cỏ 2 ở sát trước bên trái
            sprite = self.bush_sprites[1][0]
            self.decorations.append({
                "kind": "bush",
                "frames": self.bush_sprites[1],
                "frame_ms": TREE_FRAME_MS,
                "phase": 1,
                "x": self.origin_x + (island_cx - 1.0) * self.tile_width + self.tile_width / 2 - sprite.get_width() / 2,
                "y": self.origin_y + (island_cy + 4.0) * self.tile_height - sprite.get_height() + 8,
                "sort_y": self.origin_y + (island_cy + 4.0) * self.tile_height,
            })
            # Bụi cỏ 1 ở sát trước bên phải
            sprite = self.bush_sprites[0][0]
            self.decorations.append({
                "kind": "bush",
                "frames": self.bush_sprites[0],
                "frame_ms": TREE_FRAME_MS,
                "phase": 2,
                "x": self.origin_x + (island_cx + 1.0) * self.tile_width + self.tile_width / 2 - sprite.get_width() / 2,
                "y": self.origin_y + (island_cy + 4.0) * self.tile_height - sprite.get_height() + 8,
                "sort_y": self.origin_y + (island_cy + 4.0) * self.tile_height,
            })

        # Đặt vài cục đá nước ngẫu nhiên trong nước
        water_only_tiles = sorted(self.water_tiles - self.grass_tiles)
        for tx, ty in water_only_tiles:
            roll = self._tile_random(tx, ty, "water_rock")
            if self.water_rock_sprites and roll < 0.018:  # Tỉ lệ sinh vừa phải
                frames = self._choose_sprite(self.water_rock_sprites, tx, ty, "wrock")
                self.decorations.append({
                    "kind": "water_rock",
                    "frames": frames,
                    "frame_ms": TREE_FRAME_MS,
                    "phase": int(self._tile_random(tx, ty, "wrock_phase") * len(frames)),
                    "x": self.origin_x + tx * self.tile_width,
                    "y": self.origin_y + ty * self.tile_height,
                    "sort_y": self.origin_y + (ty + 1) * self.tile_height,
                })

    def _build_collision(self) -> None:
        self.collision_rects = []

        for layer in self.layers:
            if not self._is_collision_layer(layer["name"]):
                continue
            for ty in range(layer["height"]):
                row = ty * layer["width"]
                for tx in range(layer["width"]):
                    clean_gid = layer["gids"][row + tx] & ~TILED_FLIP_MASK
                    if clean_gid == 0:
                        continue
                    self.collision_rects.append(pygame.Rect(
                        self.origin_x + tx * self.tile_width,
                        self.origin_y + ty * self.tile_height,
                        self.tile_width,
                        self.tile_height,
                    ))

        for tx, ty in sorted(self.water_tiles - self.grass_tiles):
            self.collision_rects.append(pygame.Rect(
                self.origin_x + tx * self.tile_width,
                self.origin_y + ty * self.tile_height,
                self.tile_width,
                self.tile_height,
            ))

        for prop in self.decorations:
            frame = prop["frames"][0]
            width = frame.get_width()
            height = frame.get_height()
            if prop.get("kind") == "tree":
                bounds = frame.get_bounding_rect()
                # Hộp va chạm nhỏ và dịch lên trên cho cây (birch tree)
                rect_w = min(int(22 * 1.4), max(int(12 * 1.4), int(bounds.width * 0.15)))
                rect_h = int(8 * 1.4)
                rect_x = prop["x"] + bounds.centerx - rect_w / 2
                rect_bottom = prop["y"] + bounds.bottom - int(24 * 1.4)
                rect_y = rect_bottom - rect_h
            elif prop.get("kind") == "stump":
                bounds = frame.get_bounding_rect()
                # Hộp va chạm nhỏ cho gốc cây cụt (stump)
                rect_w = min(24, max(14, int(bounds.width * 0.18)))
                rect_h = 10
                rect_x = prop["x"] + bounds.centerx - rect_w / 2
                rect_bottom = prop["y"] + bounds.bottom - 12
                rect_y = rect_bottom - rect_h
            elif prop.get("kind") == "rock":
                bounds = frame.get_bounding_rect()
                # Hộp va chạm thu nhỏ cho đá (rock), dịch đáy lên một chút để tránh chặn chân nhân vật
                rect_w = min(36, max(16, int(bounds.width * 0.50)))
                rect_h = min(20, max(10, int(bounds.height * 0.35)))
                rect_x = prop["x"] + bounds.centerx - rect_w / 2
                rect_bottom = prop["y"] + bounds.bottom - 6
                rect_y = rect_bottom - rect_h
            elif prop.get("kind") == "monastery":
                rect_w = int(160 * 1.5)
                rect_h = int(80 * 1.5)
                rect_x = prop["x"] + int(192 * 1.5) / 2 - rect_w / 2
                rect_bottom = prop["y"] + int(320 * 1.5) - 8
                rect_y = rect_bottom - rect_h
            elif prop.get("kind") in ("bush", "water_rock"):
                continue # Bụi cỏ và đá trong nước không cần va chạm riêng
            else:
                bounds = frame.get_bounding_rect()
                # Mặc định cho các loại vật thể khác
                rect_w = min(48, max(24, int(bounds.width * 0.75)))
                rect_h = min(34, max(18, int(bounds.height * 0.60)))
                rect_x = prop["x"] + bounds.centerx - rect_w / 2
                rect_bottom = prop["y"] + bounds.bottom
                rect_y = rect_bottom - rect_h
            self.collision_rects.append(pygame.Rect(rect_x, rect_y, rect_w, rect_h))

    def raycast_reflect(self, x1: float, y1: float, x2: float, y2: float):
        """Tìm chướng ngại vật GẦN ĐIỂM BẮT ĐẦU NHẤT mà đoạn thẳng
        (x1,y1)->(x2,y2) cắt qua (dùng cho HitAndRunModifier — đạn/tia phản
        xạ khi chạm tường). CHỈ xét self.collision_rects (cây/đá/tu viện...),
        KHÔNG xét rìa map — bay ra ngoài map thì cứ để ra, không tính là tường.
        Trả về (hit_x, hit_y, normal_x, normal_y) hoặc None nếu không cắt gì."""
        best_t = None
        best_hit = None
        for rect in self.collision_rects:
            hit = _segment_vs_rect(x1, y1, x2, y2, rect)
            if hit is None:
                continue
            t, nx, ny = hit
            if best_t is None or t < best_t:
                best_t = t
                best_hit = (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, nx, ny)
        return best_hit

    def collides_circle(self, x: float, y: float, radius: float) -> bool:
        if (
            x - radius < self.origin_x
            or y - radius < self.origin_y
            or x + radius > self.origin_x + self.pixel_width
            or y + radius > self.origin_y + self.pixel_height
        ):
            return True

        left = x - radius
        right = x + radius
        top = y - radius
        bottom = y + radius
        for rect in self.collision_rects:
            if rect.right < left or rect.left > right or rect.bottom < top or rect.top > bottom:
                continue
            closest_x = max(rect.left, min(x, rect.right))
            closest_y = max(rect.top, min(y, rect.bottom))
            dx = x - closest_x
            dy = y - closest_y
            if dx * dx + dy * dy <= radius * radius:
                return True
        return False

    def _near_water(self, tx: int, ty: int) -> bool:
        for oy in range(-1, 2):
            for ox in range(-1, 2):
                if (tx + ox, ty + oy) in self.water_tiles:
                    return True
        return False

    def _choose_sprite(self, sprites: list[list[pygame.Surface]], tx: int, ty: int, salt: str) -> list[pygame.Surface]:
        idx = int(self._tile_random(tx, ty, salt) * len(sprites)) % len(sprites)
        return sprites[idx]

    def _choose_prop_sprite(
        self,
        sprites: list[tuple[str, list[pygame.Surface]]],
        tx: int,
        ty: int,
        salt: str,
    ) -> tuple[str, list[pygame.Surface]]:
        idx = int(self._tile_random(tx, ty, salt) * len(sprites)) % len(sprites)
        return sprites[idx]

    def _tile_random(self, tx: int, ty: int, salt: str) -> float:
        return random.Random(f"{tx}_{ty}_{salt}").random()

    def _tileset_for_gid(self, gid: int) -> dict | None:
        clean_gid = gid & ~TILED_FLIP_MASK
        result = None
        for tileset in self.tilesets:
            if clean_gid >= tileset["firstgid"]:
                result = tileset
            else:
                break
        return result

    def _tile_surface(self, gid: int) -> pygame.Surface | None:
        clean_gid = gid & ~TILED_FLIP_MASK
        if clean_gid == 0:
            return None
        cached = self.tile_cache.get(gid)
        if cached is not None:
            return cached

        tileset = self._tileset_for_gid(clean_gid)
        if tileset is None:
            return None
        local_id = clean_gid - tileset["firstgid"]
        if local_id < 0 or local_id >= tileset["tilecount"]:
            return None

        col = local_id % tileset["columns"]
        row = local_id // tileset["columns"]
        rect = pygame.Rect(
            col * tileset["tile_width"],
            row * tileset["tile_height"],
            tileset["tile_width"],
            tileset["tile_height"],
        )
        tile = tileset["image"].subsurface(rect).copy()
        if tile.get_size() != (self.tile_width, self.tile_height):
            tile = pygame.transform.scale(tile, (self.tile_width, self.tile_height))
        self.tile_cache[gid] = tile
        return tile

    def _scaled_tile(self, tile: pygame.Surface, zoom: float) -> pygame.Surface:
        if zoom == 1.0:
            return tile
        zoom_key = round(zoom, 3)
        cache_key = (id(tile), zoom_key)
        cached = self.scaled_cache.get(cache_key)
        if cached is not None:
            return cached
        scaled = pygame.transform.scale(
            tile,
            (max(1, int(tile.get_width() * zoom)),
             max(1, int(tile.get_height() * zoom))),
        )
        self.scaled_cache[cache_key] = scaled
        return scaled

    def _scaled_tile_for_draw(self, tile: pygame.Surface, zoom: float) -> pygame.Surface:
        if zoom == 1.0:
            return tile

        draw_w = max(1, round(self.tile_width * zoom) + 1)
        draw_h = max(1, round(self.tile_height * zoom) + 1)
        zoom_key = round(zoom, 3)
        cache_key = (id(tile), zoom_key, draw_w, draw_h)
        cached = self.scaled_cache.get(cache_key)
        if cached is not None:
            return cached

        scaled = pygame.transform.scale(tile, (draw_w, draw_h))
        self.scaled_cache[cache_key] = scaled
        return scaled

    def _scaled_sprite(self, image: pygame.Surface, zoom: float) -> pygame.Surface:
        if zoom == 1.0:
            return image
        zoom_key = round(zoom, 3)
        cache_key = (id(image), zoom_key)
        cached = self.scaled_cache.get(cache_key)
        if cached is not None:
            return cached
        scaled = pygame.transform.scale(
            image,
            (max(1, int(image.get_width() * zoom)),
             max(1, int(image.get_height() * zoom))),
        )
        self.scaled_cache[cache_key] = scaled
        return scaled

    def _animation_frame(self, frames: list[pygame.Surface], frame_ms: int, phase: int = 0) -> pygame.Surface:
        if len(frames) == 1:
            return frames[0]
        frame_idx = (pygame.time.get_ticks() // max(1, frame_ms) + phase) % len(frames)
        return frames[frame_idx]

    def draw(self, screen, camera_x, camera_y, screen_w, screen_h, zoom=1.0):
        offset_x = screen_w / 2 - camera_x * zoom
        offset_y = screen_h / 2 - camera_y * zoom

        start_x = max(0, int((camera_x - screen_w / (2 * zoom) - self.origin_x) // self.tile_width) - 1)
        end_x = min(self.width, int((camera_x + screen_w / (2 * zoom) - self.origin_x) // self.tile_width) + 2)
        start_y = max(0, int((camera_y - screen_h / (2 * zoom) - self.origin_y) // self.tile_height) - 1)
        end_y = min(self.height, int((camera_y + screen_h / (2 * zoom) - self.origin_y) // self.tile_height) + 2)

        for layer in self.layers:
            if layer["visible"] and self._is_water_layer(layer["name"]):
                self._draw_tile_layer(screen, layer, offset_x, offset_y, start_x, end_x, start_y, end_y, zoom)

        self._draw_auto_foam(screen, offset_x, offset_y, start_x, end_x, start_y, end_y, zoom)

        for layer in self.layers:
            if (
                layer["visible"]
                and not self._is_water_layer(layer["name"])
                and not self._is_collision_layer(layer["name"])
                and layer["name"].strip().lower() != "foam"
            ):
                self._draw_tile_layer(screen, layer, offset_x, offset_y, start_x, end_x, start_y, end_y, zoom)

    def draw_decorations(
        self,
        screen,
        camera_x,
        camera_y,
        screen_w,
        screen_h,
        zoom=1.0,
        min_sort_y: float | None = None,
        max_sort_y: float | None = None,
    ) -> None:
        offset_x = screen_w / 2 - camera_x * zoom
        offset_y = screen_h / 2 - camera_y * zoom
        self._draw_decorations(
            screen,
            offset_x,
            offset_y,
            camera_x,
            camera_y,
            screen_w,
            screen_h,
            zoom,
            min_sort_y,
            max_sort_y,
        )

    def _draw_tile_layer(self, screen, layer, offset_x, offset_y, start_x, end_x, start_y, end_y, zoom) -> None:
        for ty in range(start_y, end_y):
            row_idx = ty * layer["width"]
            for tx in range(start_x, end_x):
                gid = layer["gids"][row_idx + tx]
                clean_gid = gid & ~TILED_FLIP_MASK
                if clean_gid > WATER_GID:
                    continue
                tile = self._tile_surface(gid)
                if tile is None:
                    continue
                img = self._scaled_tile_for_draw(tile, zoom)
                sx = round((self.origin_x + tx * self.tile_width) * zoom + offset_x)
                sy = round((self.origin_y + ty * self.tile_height) * zoom + offset_y)
                screen.blit(img, (sx, sy))

    def _draw_auto_foam(self, screen, offset_x, offset_y, start_x, end_x, start_y, end_y, zoom) -> None:
        for foam in self.auto_foam:
            tx = foam["x"]
            ty = foam["y"]
            if tx < start_x or tx >= end_x or ty < start_y or ty >= end_y:
                continue
            frame = self._animation_frame(foam["frames"], FOAM_FRAME_MS, foam["phase"])
            img = self._scaled_sprite(frame, zoom)
            sx = round((self.origin_x + (tx - 1) * self.tile_width) * zoom + offset_x)
            sy = round((self.origin_y + (ty - 1) * self.tile_height) * zoom + offset_y)
            screen.blit(img, (sx, sy))

    def _draw_decorations(
        self,
        screen,
        offset_x,
        offset_y,
        camera_x,
        camera_y,
        screen_w,
        screen_h,
        zoom,
        min_sort_y: float | None = None,
        max_sort_y: float | None = None,
    ) -> None:
        view_left = camera_x - screen_w / (2 * zoom) - 220
        view_right = camera_x + screen_w / (2 * zoom) + 220
        view_top = camera_y - screen_h / (2 * zoom) - 260
        view_bottom = camera_y + screen_h / (2 * zoom) + 120
        for prop in sorted(self.decorations, key=lambda item: item["sort_y"]):
            if min_sort_y is not None and prop["sort_y"] <= min_sort_y:
                continue
            if max_sort_y is not None and prop["sort_y"] > max_sort_y:
                continue
            frame = self._animation_frame(prop["frames"], prop.get("frame_ms", 1), prop.get("phase", 0))
            if prop["x"] > view_right or prop["x"] + frame.get_width() < view_left:
                continue
            if prop["y"] > view_bottom or prop["y"] + frame.get_height() < view_top:
                continue
            img = self._scaled_sprite(frame, zoom)
            sx = round(prop["x"] * zoom + offset_x)
            sy = round(prop["y"] * zoom + offset_y)
            screen.blit(img, (sx, sy))
