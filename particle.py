from point import Point
import random

class Particle:
	
	vision_radius = 50; #Radio de vision

	def __init__(self, coord_x = 0, coord_y = 0, direction = -1):
		self.curr_coord = Point(coord_x, coord_y)
		self.prev_coord = self.curr_coord
		self.fitness = 1000000	#Mejor solucion (angulo direccion) encontrada en los caminos de las particulas en su radio
		self.bi_solution = 1000000	#Mejor solucion (angulo direccion) encontrada en su camino
		if (direction == -1):
			self.direction = random.randint(0, 360)
