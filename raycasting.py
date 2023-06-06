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
        # Limpiamos la lista de objetos a renderizar
        self.objects_to_render = []

        # Obtenemos los calculos realizados para cada rayo en el raycasting
        for valores_ray_casting in self.ray_casting_result:
            indice_rayo, distancia_rayo, altura_proyectada, texture, offset = valores_ray_casting

            # Evitamos que la altura proyectada sea mayor que la altura de la pantalla
            # ya que esto haria que la altura tendiera a infinito, y por lo tanto los 
            # frames por segundo bajaran considerablemente.
            if altura_proyectada < HEIGHT:
                # Generamos la subsurface de la textura que corresponde a la seccion de la pared
                # que corresponde al rayo. Para ello tenemos en cuenta el offset, que nos indica
                # en que parte de la textura se encuentra el rayo. Usamos la variable SCALE para
                # indicar el tamaño de la seccion de la textura que corresponde al rayo.
                wall_column = self.textures[texture].subsurface(
                    offset * (TEXTURE_SIZE - SCALE), 0, SCALE, TEXTURE_SIZE
                )
                # posteriormente escalamos la seccion de la textura para que tenga la altura de la
                # proyeccion de la pared en la pantalla.
                wall_column = pg.transform.scale(wall_column, (int(SCALE), int(altura_proyectada)))
                # Por ultimo calculamos la posicion de la seccion de la textura en la pantalla.
                wall_pos = (indice_rayo * SCALE, HALF_HEIGHT - altura_proyectada // 2)
            else:
                # Si la altura proyectada es mayor que la altura de la pantalla, significa que el
                # jugador esta muy cerca de la pared.
                texture_height = TEXTURE_SIZE * HEIGHT / altura_proyectada
                wall_column = self.textures[texture].subsurface(
                    offset * (TEXTURE_SIZE - SCALE), HALF_TEXTURE_SIZE - texture_height // 2,
                    SCALE, texture_height
                )
                wall_column = pg.transform.scale(wall_column, (int(SCALE), int(HEIGHT)))
                wall_pos = (indice_rayo * SCALE, 0)

            # Añadimos a la lista de objetos a renderizar la seccion de la textura y su posicion
            self.objects_to_render.append((distancia_rayo, wall_column, wall_pos))

    def ray_cast(self):
        # Limpiamos la lista de objetos a renderizar
        self.ray_casting_result = []
        
        x_jugador, y_jugador = self.game.player.pos
        x_map, y_map = self.game.player.map_pos

        # Inicializamos las texturas a renderizar por si no se choca con ninguna pared
        texture_vert, texture_hor = 1, 1
         
        # Hace referencia al primer angulo de el Field of View del jugador
        # el angulo del jugador es la mitad del field of view, por lo que restarle
        # la mitad del field of view nos da el primer angulo del field of view.
        # El 0.0001 es para evitar dividir entre 0.
        angulo_del_rayo = self.game.player.angle - HALF_FOV + 0.0001

        for indice_rayo in range(NUM_RAYS):

            # Calculamos los senos y cosenos para facilitar los calculos
            # Ademas nos dan informacion sobre la direccion del rayo
            sin_a = math.sin(angulo_del_rayo)
            cos_a = math.cos(angulo_del_rayo)

            # Empezamos hallando las intersecciones del rayo con las divisiones
            # horizontales del mapa. Si el seno es positivo significa que el rayo
            # va hacia abajo, por lo que y de la interseccion con la division horizontal
            # mas cercana es la siguiente a la posicion del mapa. Si el seno es negativo
            # significa que el rayo va hacia arriba, por lo que y de la interseccion con la
            # division horizontal mas cercana es la anterior a la posicion del mapa, osea 
            # la posicion y del mapa menos 1e-6 para entrar dentro de la anterior tile. 
            y_hor, dy = (y_map + 1, 1) if sin_a > 0 else (y_map - 1e-6, -1)

            # Mediante trigonometría hallamos la distancia horizontal entre el jugador y la
            # interseccion con la division horizontal mas cercana. Sease la hipotenusa.
            distancia_hor = (y_hor - y_jugador) / sin_a
            # Sumando a la posicion del jugador el cateto obtenemos la posicion x de la interseccion
            x_hor = x_jugador + distancia_hor * cos_a

            # El siguiente paso seria conseguir la distancia entre la primera interseccion horizontal
            # y la siguiente, al ser el mapa un grid uniforme, la distancia vertical ya la tenemos, es dy, 
            # y el angulo tambien, por lo que con trigonometría podemos hallar la distancia sin problemas.
            diferencial_intersecciones_hor = dy / sin_a
            dx = diferencial_intersecciones_hor * cos_a

            # Vamos a crear un diccionario para las paredes transparentes
            dict_transparentes = {}

            # Con estos valores ya podemos ir paso a paso comprobando si el rayo ha chocado con una pared
            # o no. Para ello vamos sumando el diferencial de las intersecciones a la posicion del jugador
            # hasta completar los pasos indicados con MAX_DEPTH.
            for _ in range(MAX_DEPTH):
                # Con esto obtendriamos un indice en dos dimensiones de la primera interseccion horizontal
                tile_hor = int(x_hor), int(y_hor)
                if tile_hor in self.game.map.world_map:
                    # Si la tile es una pared, guardamos su textura y rompemos el bucle.
                    texture_hor = self.game.map.world_map[tile_hor]
                    # comprobamos si la pared es transparente
                    if texture_hor == 5:
                        # Si es transparente, añadimos la posicion de la interseccion, la distancia y la textura
                        dict_transparentes[str(tile_hor)] = (x_hor, y_hor, distancia_hor, texture_hor, False)
                    else:
                        break
                # Si no es una pared, seguimos sumando el diferencial de las intersecciones a la posicion
                # del jugador para obtener la siguiente interseccion horizontal.
                x_hor += dx
                y_hor += dy
                distancia_hor += diferencial_intersecciones_hor

            # Ahora hacemos lo mismo pero con las intersecciones verticales.
            x_vert, dx = (x_map + 1, 1) if cos_a > 0 else (x_map - 1e-6, -1)
            distancia_ver = (x_vert - x_jugador) / cos_a
            y_vert = y_jugador + distancia_ver * sin_a
            diferencial_intersecciones_ver = dx / cos_a
            dy = diferencial_intersecciones_ver * sin_a

            for _ in range(MAX_DEPTH):
                tile_vert = int(x_vert), int(y_vert)
                if tile_vert in self.game.map.world_map:
                    texture_vert = self.game.map.world_map[tile_vert]
                    # comprobamos si la pared es transparente
                    if texture_vert == 5:
                        # Vemos que interseccion es mas cercana, la horizontal o la vertical mas detalle posteriormente
                        if str(tile_vert) in dict_transparentes:
                            if distancia_ver < dict_transparentes[str(tile_vert)][2]:
                                dict_transparentes[str(tile_vert)] = (x_vert, y_vert, distancia_ver, texture_vert, True)
                        else:
                            dict_transparentes[str(tile_vert)] = (x_vert, y_vert, distancia_ver, texture_vert, True)
                    else:
                        break
                x_vert += dx
                y_vert += dy
                distancia_ver += diferencial_intersecciones_ver

            # Una vez tenemos la distancia horizontal y vertical donde ha chocado el rayo con una pared,
            # comparamos cual de las dos es menor, y esa es la que nos interesa, ya que es la que esta mas
            # cerca del jugador.
            if distancia_ver < distancia_hor:
                distancia = distancia_ver
            else:
                distancia = distancia_hor

            # Con el paso siguiente a este ya podemos dibujar la pared en la pantalla.
            # Pero debido al uso del sistema cartesiano junto con el polar, la pared se 
            # ve con un efecto de "fishbowl", por lo que para corregirlo, hay que multiplicar
            # la distancia por el coseno del angulo del rayo
            # menos el angulo del jugador. Esto nos da la distancia corregida.
            distancia_corregida = distancia * math.cos(self.game.player.angle - angulo_del_rayo)

            # Ahora que tenemos la distancia, podemos calcular la proyeccion de la pared en la pantalla.
            # Para ello dividimos la distancia entre la distancia de la pantalla al jugador, y multiplicamos
            # por la altura de la pantalla. Esto nos da la altura de la pared en la pantalla. Teniendo en 
            # cuenta que la altura real de la pared es de 1. 
            # Siendo AlturaReal / Distancia = AlturaProyeccion / DistanciaPantalla
            # AlturaProyeccion = (AlturaReal * DistanciaPantalla) / Distancia
            # Añadimos un 0.0001 para evitar dividir entre 0.
            altura_projeccion = (1 * SCREEN_DIST) / (distancia_corregida + 0.0001)

            # Para texturizar obtenemos la textura de la colisión. Y tambien hallamos el offset en la propia
            # textura. Esto se debe a que la textura se dividira en tantas partes como rayos coliisionen con ella.
            # Por lo que el offset nos indica en que parte de la textura se encuentra el rayo. Esto es lo que da la
            # sensacion de profundidad. Para hallar el offset tenemos en cuenta los casos en los que el rayo va hacia
            # arriba o hacia abajo, y hacia la izquierda o hacia la derecha. Es por ello que miramos el signo de los
            # senos y cosenos.
            if distancia_ver < distancia_hor:
                texture = texture_vert
                y = y_vert % 1
                offset = y if cos_a > 0 else (1 - y)
            else:
                texture = texture_hor
                x = x_hor % 1
                offset = (1 - x) if sin_a > 0 else x

            # Ahora que tenemos la altura de la proyeccion y el offset, podemos dibujar la pared en la pantalla.
            # Pero de eso se encargara otra funcion, con lo que añadimos lo calculado anteriormente a una lista
            # para que la funcion de dibujado pueda acceder a ellos.
            self.ray_casting_result.append((indice_rayo, distancia_corregida, altura_projeccion, texture, offset))

            # Computamos las intersecciones con las paredes transparentes
            for key, value in dict_transparentes.items():
                distancia_corregida = value[2] * math.cos(self.game.player.angle - angulo_del_rayo)
                altura_projeccion = (1 * SCREEN_DIST) / (distancia_corregida + 0.0001)
                if value[4]:
                    y = value[1] % 1
                    offset = y if cos_a > 0 else (1 - y)
                    self.ray_casting_result.append((indice_rayo, distancia_corregida, altura_projeccion, value[3], offset))
                else:
                    x = value[0] % 1
                    offset = (1 - x) if sin_a > 0 else x
                    self.ray_casting_result.append((indice_rayo, distancia_corregida, altura_projeccion, value[3], offset))


            # Por ultimo sumamos el diferencial de los angulos de los rayos al angulo del primer rayo, para
            # obtener el angulo del siguiente rayo y continuar con el raycasting
            angulo_del_rayo += DELTA_ANGLE

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