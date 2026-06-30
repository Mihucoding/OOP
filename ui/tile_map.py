import os
import random
from functools import lru_cache

import pygame
from perlin_noise import PerlinNoise


TILE_SIZE = 32
CHUNK_SIZE = 16
SCALE = 0.03
OCTAVES = 6
DEFAULT_SEED = 1337
MAP_SEED = DEFAULT_SEED

PROP_SPAWN_CHANCE = 0.09

CHUNK_RENDER_DISTANCE = 2
CHUNK_PRELOAD_DISTANCE = 2
CHUNK_IMMEDIATE_DISTANCE = 1
CHUNKS_PER_FRAME = 2

noise_gen = PerlinNoise(octaves=OCTAVES, seed=DEFAULT_SEED)


def set_map_seed(seed: int) -> None:
    global noise_gen, MAP_SEED
    MAP_SEED = seed
    noise_gen = PerlinNoise(octaves=OCTAVES, seed=seed)
    get_tile_id.cache_clear()
    seeded_random.cache_clear()


@lru_cache(maxsize=None)
def get_tile_id(global_x, global_y):
    return 2


@lru_cache(maxsize=None)
def seeded_random(global_x, global_y, salt):
    return random.Random(f"{global_x}_{global_y}_{MAP_SEED}_{salt}").random()


def get_grass_bitmask(global_x, global_y):
    north = get_tile_id(global_x, global_y - 1) == 2
    east = get_tile_id(global_x + 1, global_y) == 2
    south = get_tile_id(global_x, global_y + 1) == 2
    west = get_tile_id(global_x - 1, global_y) == 2
    bitmask = 0
    if north:
        bitmask |= 1
    if east:
        bitmask |= 2
    if south:
        bitmask |= 4
    if west:
        bitmask |= 8
    return bitmask


def get_grass_tile(resources, global_x, global_y):
    north_west = get_tile_id(global_x - 1, global_y - 1) == 2
    north_east = get_tile_id(global_x + 1, global_y - 1) == 2
    south_west = get_tile_id(global_x - 1, global_y + 1) == 2
    south_east = get_tile_id(global_x + 1, global_y + 1) == 2

    bitmask = get_grass_bitmask(global_x, global_y)

    if bitmask == 15:
        missing = []
        if not north_west:
            missing.append("top_left")
        if not north_east:
            missing.append("top_right")
        if not south_west:
            missing.append("bottom_left")
        if not south_east:
            missing.append("bottom_right")

        if len(missing) == 1:
            return resources.grass_inner_corners[missing[0]]
        return resources.tiles["grass_base"]

    return resources.grass_autotile.get(bitmask, resources.tiles["grass_base"])


class ResourceManager:
    def __init__(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_dir = os.path.join(root_dir, "assets", "map")
        self.scaled_surface_cache = {}

        self.grass_sheet = pygame.image.load(self._asset_path("grass_tileset_16x16.png")).convert_alpha()
        self.ground_sheet = pygame.image.load(self._asset_path("Topdown RPG 32x32 - Ground Tileset 1.2.PNG")).convert_alpha()
        self.bush_sheet = pygame.image.load(self._asset_path("Topdown RPG 32x32 - Bushes 1.1.PNG")).convert_alpha()
        self.mushroom_sheet = pygame.image.load(self._asset_path("Topdown RPG 32x32 - Mushrooms.png")).convert_alpha()
        self.nature_sheet = pygame.image.load(self._asset_path("Topdown RPG 32x32 - Nature Details.png")).convert_alpha()
        self.tree_sheet = pygame.image.load(self._asset_path("Topdown RPG 32x32 - Trees 1.2.PNG")).convert_alpha()
        self.rock_sheet = pygame.image.load(self._asset_path("Topdown RPG 32x32 - Rocks 1.2.PNG")).convert_alpha()
        self.log_sheet = pygame.image.load(self._asset_path("Topdown RPG 32x32 - Tree Stumps and Logs 1.2.PNG")).convert_alpha()

        self.tiles = {}
        self.load_tiles()

    def _asset_path(self, filename):
        path = os.path.join(self.base_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing map asset: {path}")
        return path

    def load_tiles(self):
        def tile_at(col, row):
            return self.ground_sheet.subsurface((col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        def grass_at(col, row):
            row = max(0, row - 3)
            tile = self.grass_sheet.subsurface((col * 16, row * 16, 16, 16))
            return pygame.transform.scale(tile, (TILE_SIZE, TILE_SIZE))

        def add_variant(out, sheet, rect, ox, oy):
            img = sheet.subsurface(rect)
            if img.get_bounding_rect().width > 0:
                out.append({"img": img, "ox": ox, "oy": oy})

        self.tiles["dirt_base"] = self.ground_sheet.subsurface((320, 0, TILE_SIZE, TILE_SIZE))
        self.tiles["grass_base"] = grass_at(0, 3)
        self.grass_variants = [
            grass_at(0, 3),
            grass_at(0, 4),
            grass_at(0, 5),
            pygame.transform.flip(grass_at(0, 3), True, False),
            pygame.transform.flip(grass_at(0, 4), False, True),
        ]
        self.tiles["bush"] = self.bush_sheet.subsurface((0, 0, 64, 64))

        self.tree_variants = [
            {"img": self.tree_sheet.subsurface((0, 0, 96, 112)), "ox": -32, "oy": -80},
            {"img": self.tree_sheet.subsurface((96, 0, 96, 112)), "ox": -32, "oy": -80},
            {"img": self.tree_sheet.subsurface((192, 0, 96, 112)), "ox": -32, "oy": -80},
            {"img": self.tree_sheet.subsurface((288, 0, 32, 64)), "ox": 0, "oy": -48},
            {"img": self.tree_sheet.subsurface((320, 0, 32, 64)), "ox": 0, "oy": -48},
            {"img": self.tree_sheet.subsurface((352, 0, 32, 64)), "ox": 0, "oy": -48},
            {"img": self.tree_sheet.subsurface((288, 64, 64, 64)), "ox": -16, "oy": -48},
        ]
        self.rock_variants = [
            {"img": self.rock_sheet.subsurface((0, 0, 64, 64)), "ox": -16, "oy": -32},
            {"img": self.rock_sheet.subsurface((64, 0, 64, 64)), "ox": -16, "oy": -32},
            {"img": self.rock_sheet.subsurface((128, 0, 64, 32)), "ox": -16, "oy": -16},
            {"img": self.rock_sheet.subsurface((192, 0, 64, 32)), "ox": -16, "oy": -16},
            {"img": self.rock_sheet.subsurface((256, 0, 32, 32)), "ox": 0, "oy": -16},
            {"img": self.rock_sheet.subsurface((288, 0, 32, 32)), "ox": 0, "oy": -16},
            {"img": self.rock_sheet.subsurface((320, 0, 32, 32)), "ox": 0, "oy": -16},
            {"img": self.rock_sheet.subsurface((352, 0, 32, 32)), "ox": 0, "oy": -16},
        ]
        self.stump_variants = [
            {"img": self.log_sheet.subsurface((0, 0, 64, 64)), "ox": -16, "oy": -32},
            {"img": self.log_sheet.subsurface((64, 0, 64, 64)), "ox": -16, "oy": -32},
            {"img": self.log_sheet.subsurface((128, 0, 96, 32)), "ox": -32, "oy": -16},
            {"img": self.log_sheet.subsurface((224, 0, 32, 64)), "ox": 0, "oy": -32},
            {"img": self.log_sheet.subsurface((256, 0, 32, 64)), "ox": 0, "oy": -32},
            {"img": self.log_sheet.subsurface((288, 0, 32, 64)), "ox": 0, "oy": -32},
            {"img": self.log_sheet.subsurface((320, 0, 32, 64)), "ox": 0, "oy": -32},
        ]
        self.bush_variants = [
            {"img": self.bush_sheet.subsurface((0, 0, 64, 64)), "ox": -16, "oy": -32},
            {"img": self.bush_sheet.subsurface((64, 0, 64, 64)), "ox": -16, "oy": -32},
            {"img": self.bush_sheet.subsurface((128, 0, 64, 64)), "ox": -16, "oy": -32},
        ]
        self.small_rock_variants = []
        for col in range(12):
            add_variant(self.small_rock_variants, self.rock_sheet, (col * 32, 64, 32, 32), 0, 0)

        self.mushroom_variants = []
        for row in range(2):
            for col in range(12):
                add_variant(self.mushroom_variants, self.mushroom_sheet, (col * 32, row * 32, 32, 32), 0, 0)

        self.nature_variants = []
        for row in range(4):
            for col in range(12):
                add_variant(self.nature_variants, self.nature_sheet, (col * 32, row * 32, 32, 32), 0, 0)

        self.small_detail_variants = (
            self.small_rock_variants
            + self.mushroom_variants
            + self.nature_variants
        )

        self.grass_autotile = {
            1: tile_at(0, 6),
            2: tile_at(5, 6),
            4: tile_at(0, 7),
            8: tile_at(4, 6),
            5: tile_at(0, 4),
            10: tile_at(2, 4),
            3: tile_at(6, 3),
            6: tile_at(6, 2),
            9: tile_at(7, 3),
            12: tile_at(7, 2),
            7: tile_at(9, 2),
            11: tile_at(8, 2),
            13: tile_at(8, 3),
            14: tile_at(9, 3),
            15: self.tiles["grass_base"],
        }
        self.grass_inner_corners = {
            "top_left": tile_at(5, 3),
            "top_right": tile_at(4, 3),
            "bottom_left": tile_at(5, 2),
            "bottom_right": tile_at(4, 2),
        }

    def get_scaled_surface(self, surface, zoom):
        if zoom == 1.0:
            return surface
        zoom_key = round(zoom, 3)
        cache_key = (id(surface), zoom_key)
        cached = self.scaled_surface_cache.get(cache_key)
        if cached is not None:
            return cached

        scaled = pygame.transform.scale(
            surface,
            (max(1, int(surface.get_width() * zoom)),
             max(1, int(surface.get_height() * zoom))))
        self.scaled_surface_cache[cache_key] = scaled
        return scaled

class Chunk:
    def __init__(self, chunk_x, chunk_y, resources, auto_generate=True):
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.resources = resources
        self.ground_surface = pygame.Surface((CHUNK_SIZE * TILE_SIZE, CHUNK_SIZE * TILE_SIZE))
        self.stand_props_data = []
        self.scaled_ground_cache = {}
        self.generated = False
        if auto_generate:
            self.generate()

    def generate(self):
        if self.generated:
            return

        for y in range(CHUNK_SIZE):
            for x in range(CHUNK_SIZE):
                global_x = self.chunk_x * CHUNK_SIZE + x
                global_y = self.chunk_y * CHUNK_SIZE + y
                variant_idx = int(seeded_random(global_x, global_y, "grass") * len(self.resources.grass_variants))
                grass_img = self.resources.grass_variants[variant_idx]
                self.ground_surface.blit(grass_img, (x * TILE_SIZE, y * TILE_SIZE))

        for y in range(CHUNK_SIZE):
            for x in range(CHUNK_SIZE):
                global_x = self.chunk_x * CHUNK_SIZE + x
                global_y = self.chunk_y * CHUNK_SIZE + y
                rand_val = seeded_random(global_x, global_y, "stand_prop")
                px = global_x * TILE_SIZE
                py = global_y * TILE_SIZE

                if rand_val >= PROP_SPAWN_CHANCE:
                    continue

                prop_roll = seeded_random(global_x, global_y, "prop_type")
                if prop_roll < 0.82:
                    variants = self.resources.small_detail_variants
                elif prop_roll < 0.91:
                    variants = self.resources.bush_variants
                elif prop_roll < 0.95:
                    variants = self.resources.rock_variants
                elif prop_roll < 0.98:
                    variants = self.resources.stump_variants
                else:
                    variants = self.resources.tree_variants
                variant = variants[int(seeded_random(global_x, global_y, "prop_variant") * len(variants))]
                self.stand_props_data.append({
                    "img": variant["img"],
                    "x": px + variant["ox"],
                    "y": py + variant["oy"],
                })

        self.generated = True

    def get_ground_surface(self, width: int, height: int):
        if (
            width == self.ground_surface.get_width()
            and height == self.ground_surface.get_height()
        ):
            return self.ground_surface
        cache_key = (width, height)
        cached = self.scaled_ground_cache.get(cache_key)
        if cached is not None:
            return cached

        cached = pygame.transform.scale(
            self.ground_surface,
            (max(1, width), max(1, height)))
        self.scaled_ground_cache[cache_key] = cached
        return cached


class WorldMap:
    def __init__(self, seed=DEFAULT_SEED):
        set_map_seed(seed)
        self.resources = ResourceManager()
        self.chunks = {}
        self.pending_chunks = []

    def queue_chunk(self, chunk_pos, distance):
        if chunk_pos in self.chunks:
            return
        self.chunks[chunk_pos] = Chunk(chunk_pos[0], chunk_pos[1], self.resources, auto_generate=False)
        self.pending_chunks.append((distance, chunk_pos))

    def process_chunk_queue(self):
        if not self.pending_chunks:
            return
        self.pending_chunks.sort(key=lambda item: item[0])
        generated_this_frame = 0
        while self.pending_chunks and generated_this_frame < CHUNKS_PER_FRAME:
            _, chunk_pos = self.pending_chunks.pop(0)
            chunk = self.chunks.get(chunk_pos)
            if chunk is None or chunk.generated:
                continue
            chunk.generate()
            generated_this_frame += 1

    def update(self, camera_x, camera_y):
        current_chunk_x = int(camera_x // (CHUNK_SIZE * TILE_SIZE))
        current_chunk_y = int(camera_y // (CHUNK_SIZE * TILE_SIZE))
        active_chunks = set()

        for y in range(current_chunk_y - CHUNK_RENDER_DISTANCE, current_chunk_y + CHUNK_RENDER_DISTANCE + 1):
            for x in range(current_chunk_x - CHUNK_RENDER_DISTANCE, current_chunk_x + CHUNK_RENDER_DISTANCE + 1):
                chunk_pos = (x, y)
                active_chunks.add(chunk_pos)
                distance = max(abs(x - current_chunk_x), abs(y - current_chunk_y))

                if chunk_pos in self.chunks:
                    chunk = self.chunks[chunk_pos]
                    if not chunk.generated and distance <= CHUNK_IMMEDIATE_DISTANCE:
                        chunk.generate()
                    continue

                if distance <= CHUNK_IMMEDIATE_DISTANCE:
                    self.chunks[chunk_pos] = Chunk(x, y, self.resources)
                else:
                    self.queue_chunk(chunk_pos, distance)

        for key in [pos for pos in self.chunks if pos not in active_chunks]:
            del self.chunks[key]

        self.pending_chunks = [item for item in self.pending_chunks if item[1] in self.chunks]
        self.process_chunk_queue()

    def draw(self, screen, camera_x, camera_y, screen_w, screen_h, zoom=1.0):
        self.update(camera_x, camera_y)
        offset_x = screen_w // 2 - camera_x * zoom
        offset_y = screen_h // 2 - camera_y * zoom
        stand_props = []
        chunk_world_size = CHUNK_SIZE * TILE_SIZE

        for (cx, cy), chunk in self.chunks.items():
            if not chunk.generated:
                continue
            world_x = cx * chunk_world_size
            world_y = cy * chunk_world_size
            left = round(world_x * zoom + offset_x)
            top = round(world_y * zoom + offset_y)
            right = round((world_x + chunk_world_size) * zoom + offset_x)
            bottom = round((world_y + chunk_world_size) * zoom + offset_y)
            ground = chunk.get_ground_surface(right - left, bottom - top)
            screen.blit(ground, (left, top))
            stand_props.extend(chunk.stand_props_data)

        for prop in sorted(stand_props, key=lambda item: item["y"]):
            img = self.resources.get_scaled_surface(prop["img"], zoom)
            screen.blit(img, (int(prop["x"] * zoom + offset_x), int(prop["y"] * zoom + offset_y)))
