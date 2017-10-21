from point import Point
import random

class Particle:

	def __init__(self, coord_x = 0, coord_y = 0, steps_number = 100):
		self.curr_coord = Point(coord_x, coord_y)			#Posicion Actual
		self.prev_coord = self.curr_coord					#Posicion Anterior
		self.directions = []								#Arreglo de direcciones en cada paso
		self.fitness = 0.0									#Fitness
		for i in xrange(steps_number):	
			self.directions.append(random.randint(0, 360))	#Agregar un angulo de direccion por cada paso
		self.curr_step = 0 									#En que paso esta
		self.hitWall = 0									#Flag por si choco
