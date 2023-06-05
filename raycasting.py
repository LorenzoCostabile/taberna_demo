import pygame as pg
import math
from settings import *

class RayCasting:
    def __init__(self, game):
        self.game = game
        self.ray_casting_result = []
        self.objects_to_render = []
        self.textures = self.game.object_renderer.wall_textures

    def get_objects_to_render(self):
        self.objects_to_render = []
        for ray, values, in enumerate(self.ray_casting_result):
            depth, proj_height, texture, offset = values

            if proj_height < HEIGHT:
                wall_column = self.textures[texture].subsurface(
                    offset * (TEXTURE_SIZE - SCALE), 0, SCALE, TEXTURE_SIZE
                )

                wall_column = pg.transform.scale(wall_column, (int(SCALE), int(proj_height)))
                wall_pos = (ray * SCALE, HALF_HEIGHT - proj_height // 2)
            else:
                texture_height = TEXTURE_SIZE * HEIGHT / proj_height
                wall_column = self.textures[texture].subsurface(
                    offset * (TEXTURE_SIZE - SCALE), HALF_TEXTURE_SIZE - texture_height // 2,
                    SCALE, texture_height
                )
                wall_column = pg.transform.scale(wall_column, (int(SCALE), int(HEIGHT)))
                wall_pos = (ray * SCALE, 0)

            self.objects_to_render.append((depth, wall_column, wall_pos))

    def ray_cast(self):
        self.ray_casting_result = []
        
        ox, oy = self.game.player.pos
        x_map, y_map = self.game.player.map_pos

        texture_vert, texture_hor = 1, 1

        ray_angle = self.game.player.angle - HALF_FOV + 0.0001
        for ray in range(NUM_RAYS):
            sin_a = math.sin(ray_angle)
            cos_a = math.cos(ray_angle)

            # horizontals
            y_hor, dy = (y_map + 1, 1) if sin_a > 0 else (y_map - 1e-6, -1)

            depth_hor = (y_hor - oy) / sin_a
            x_hor = ox + depth_hor * cos_a

            delta_depth = dy / sin_a
            dx = delta_depth * cos_a

            transparent_horizontal_wall = None
            for i in range(MAX_DEPTH):
                tile_hor = int(x_hor), int(y_hor)
                if tile_hor in self.game.map.world_map:
                    texture_hor = self.game.map.world_map[tile_hor]
                    if texture_hor != 5:  # 5 is the value for transparent walls
                        break
                    else:
                        # Store transparent wall information (depth, texture, position) for later rendering
                        transparent_horizontal_wall = (depth_hor, texture_hor, x_hor, y_hor)
                x_hor += dx
                y_hor += dy
                depth_hor += delta_depth

            # verticals
            x_vert, dx = (x_map + 1, 1) if cos_a > 0 else (x_map - 1e-6, -1)

            depth_vert = (x_vert - ox) / cos_a
            y_vert = oy + depth_vert * sin_a

            delta_depth = dx / cos_a
            dy = delta_depth * sin_a

            transparent_vertical_wall = None
            for i in range(MAX_DEPTH):
                tile_vert = int(x_vert), int(y_vert)
                if tile_vert in self.game.map.world_map:
                    texture_vert = self.game.map.world_map[tile_vert]
                    if texture_vert != 5:  # 5 is the value for transparent walls
                        break
                    else:
                        # Store transparent wall information (depth, texture, position) for later rendering
                        transparent_vertical_wall = [depth_vert, texture_vert, x_vert, y_vert]
                x_vert += dx
                y_vert += dy
                depth_vert += delta_depth

            if depth_vert < depth_hor:
                depth, texture = depth_vert, texture_vert
                y_vert %= 1
                offset = y_vert if cos_a > 0 else (1 - y_vert)
            else:
                depth, texture = depth_hor, texture_hor
                x_hor %= 1
                offset = (1 - x_hor) if sin_a > 0 else x_hor

            # remove fishbowl effect
            depth *= math.cos(self.game.player.angle - ray_angle)

            # projection
            proj_height = SCREEN_DIST / (depth + 0.0001)

            # draw Walls
            #color = [255 / (1 + depth ** 5 * 0.00002)] * 3
            #pg.draw.rect(self.game.screen, color,
            #             (ray * SCALE, HALF_HEIGHT - proj_height // 2, SCALE, proj_height))

            #draw for debug
            # pg.draw.line(self.game.screen, 'yellow', (100 * ox, 100 * oy),
                        # (100 * ox + 100 * depth * cos_a, 100 * oy + 100 * depth * sin_a), 2)

            self.ray_casting_result.append((depth, proj_height, texture, offset))
            if transparent_horizontal_wall is not None and transparent_vertical_wall is not None:
                if transparent_horizontal_wall[0] > transparent_vertical_wall[0]:
                    depth, proj_height, texture, offset = self.calculate_values(list(transparent_vertical_wall), 3, cos_a, True, self.game.player.angle)
                    self.ray_casting_result.append((depth, proj_height, texture, offset))
                else:
                    depth, proj_height, texture, offset = self.calculate_values(list(transparent_horizontal_wall), 2, sin_a, False, self.game.player.angle)
                    self.ray_casting_result.append((depth, proj_height, texture, offset))

            elif transparent_horizontal_wall is not None:
                depth, proj_height, texture, offset = self.calculate_values(list(transparent_horizontal_wall), 2, sin_a, False, self.game.player.angle)
                self.ray_casting_result.append((depth, proj_height, texture, offset))

            elif transparent_vertical_wall is not None:
                depth, proj_height, texture, offset = self.calculate_values(list(transparent_vertical_wall), 3, cos_a, True, self.game.player.angle)
                self.ray_casting_result.append((depth, proj_height, texture, offset))

            ray_angle += DELTA_ANGLE

    def calculate_values(self, wall_info, offset_index, value, is_vertical, ray_angle):
        depth, texture = wall_info[0], wall_info[1]
        wall_info[offset_index] %= 1
        if is_vertical:
            offset = wall_info[offset_index] if value > 0 else (1 - wall_info[offset_index])
        else:
            offset = (1 - wall_info[offset_index]) if value > 0 else wall_info[offset_index]
        depth *= math.cos(self.game.player.angle - ray_angle)
        proj_height = SCREEN_DIST / (depth + 0.0001)
        return depth, proj_height, texture, offset


    def update(self):
        self.ray_cast()
        self.get_objects_to_render()