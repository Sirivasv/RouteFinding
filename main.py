import PIL.ImageDraw, PIL.Image, PIL.ImageShow, PIL.ImageTk
from particle import Particle
from point import Point
from Tkinter import *
import random
import math

#Valores de Influencia
c1 = 0.4
c2 = 0.8

#Inicializar mejores globales
gbest = 0
ngbest = gbest

#Zona segura 
safe_zone = Point(400, 100)

#Inicializar paredes
walls = []
walls.append((Point(200, 150), Point(350, 150))) #Lado Superior
walls.append((Point(450, 150), Point(600, 150))) #Lado Superior
walls.append((Point(200, 150), Point(200, 550))) #Lado Izquierdp
walls.append((Point(200, 550), Point(600, 550))) #Lado Inferior
walls.append((Point(600, 150), Point(600, 550))) #Lado Derecho
walls.append((Point(200, 350), Point(300, 350))) #Obstaculo Izquierdo
walls.append((Point(420, 250), Point(600, 250))) #Obstaculo Derecho

root = Tk() #Inicializar Ventana
root.geometry('{}x{}'.format(800, 600)) #Inicializar Ventana

caGrid = Canvas(root, width = 800, height = 600, background = "gray") #Inicializar Canvas
caGrid.grid() #Posicionar el canvas

###################################################################
#																  #
#																  #
#	Comienza Definicion de Intereseccion de Segmentos			  #
#   referencia de Geeks4Geeks     								  #
#																  #
###################################################################

def onSegment(p, q, r): #Three Points
	if (q.coord_x <= max(p.coord_x, r.coord_x) and q.coord_x >= min(p.coord_x, r.coord_x) and q.coord_y <= max(p.coord_y, r.coord_y) and q.coord_y >= min(p.coord_y, r.coord_y)):
		return True
	return False

# To find orientation of ordered triplet (p, q, r).
# The function returns following values
# 0 --> p, q and r are colinear
# 1 --> Clockwise
# 2 --> Counterclockwise
def orientation(p, q, r): #Three Points
	val = (q.coord_y - p.coord_y) * (r.coord_x - q.coord_x) - (q.coord_x - p.coord_x) * (r.coord_y - q.coord_y)
	if (val == 0): #colinear
		return 0
	return 1 if (val > 0) else 2 #clock or counterclock wise

def doIntersect(p1, q1, p2, q2): #Two segments (4 Points)
	# Find the four orientations needed for general and
	# special cases
	o1 = orientation(p1, q1, p2)
	o2 = orientation(p1, q1, q2)
	o3 = orientation(p2, q2, p1)
	o4 = orientation(p2, q2, q1)

	#General case
	if (o1 != o2 and o3 != o4):
		return True

	#Special Cases
	#p1, q1 and p2 are colinear and p2 lies on segment p1q1
	if (o1 == 0 and onSegment(p1, p2, q1)):
		return True
	#p1, q1 and p2 are colinear and q2 lies on segment p1q1
	if (o2 == 0 and onSegment(p1, q2, q1)):
		return True
	#p2, q2 and p1 are colinear and p1 lies on segment p2q2
	if (o3 == 0 and onSegment(p2, p1, q2)):
		return True
	#p2, q2 and q1 are colinear and q1 lies on segment p2q2
	if (o4 == 0 and onSegment(p2, q1, q2)):
		return True
	return False #Doesn't fall in any of the above cases

###################################################################
#																  #
#																  #
#	Termina Definicion de Intereseccion de Segmentos			  #
#   referencia de Geeks4Geeks     								  #
#																  #
###################################################################

def intersectWithWalls(p1, p2): #Ver si el segmento actual(2 puntos) intersecta con alguna pared
	for wall in walls:
		if (doIntersect(p1, p2, wall[0], wall[1])):
			return True
	return False

def printWalls(): #Dibujar las paredes definidas en el arreglo de paredes
	global draw
	for wall in walls:
		draw.line((wall[0].coord_x, wall[0].coord_y, wall[1].coord_x, wall[1].coord_y), (0, 0, 0), width = 10)

def printSafeZone(coords): #Dibujar la zona segura, recibe un punto
	global draw
	draw.ellipse((coords.coord_x - 50, coords.coord_y - 50, coords.coord_x + 50, coords.coord_y + 50), (0, 255, 0)) #circulo SEGURO centro en coords

def printSingleParticle(coords): #Dibujar la particula, recibe un punto
	global draw
	draw.ellipse((coords.coord_x - 10, coords.coord_y - 10, coords.coord_x + 10, coords.coord_y + 10), (0, 0, 255)) #circulo centro en coords

def printParticles(parts): #Dibuja el arreglo de particulas
	for particle in particles:
		printSingleParticle(particle.curr_coord) 

def newPoint(point, direction): #Determina la siguiente posicion de la particula segun su angulo de direccion
	return Point(point.coord_x + math.cos(direction) * 10.0, point.coord_y + math.sin(direction) * 10.0)

def getDistance(p1, p2): #determina la distancia entre dos puntos
	return math.sqrt(((p1.coord_x - p2.coord_x) * (p1.coord_x - p2.coord_x)) + ((p1.coord_y - p2.coord_y) * (p1.coord_y - p2.coord_y)))

def getFitness(particle):
	particle.prev_coord = particle.curr_coord #determinar que la posicion actual ahora es la previa
	particle.curr_coord = newPoint(particle.curr_coord, particle.direction) #determinar nueva posicion
	fitness_value = getDistance(safe_zone, particle.curr_coord) #determinar la distancia a la zona segura
	if (intersectWithWalls(particle.curr_coord, particle.prev_coord)): #si intersecta con las paredes su valor fitness sera mucho menor
		fitness_value *= 1000000;
	return fitness_value 

def getNewParticles():
	global gbest, ngbest
	for p in particles:
		fitness = getFitness(p) #determinar fitness
		if fitness < p.fitness: #determinar si es la mejor vista por la particula en su camino
			p.fitness = fitness
			p.bi_solution = p.direction
		
		if fitness < ngbest.fitness: #determinar si es la mejor vista en todo el swarm
			ngbest = p
		
		direction = p.direction + c1 * random.random() * (p.bi_solution - p.direction) + c2 * random.random() * (gbest.direction - p.direction) #Determinar nueva direccion considerando la influencia del grupo
		p.direction = direction #cambiar la direccion
	 
	gbest = ngbest #Cambiar el mejor global

def printThings():
	printSafeZone(safe_zone) #Draw Circle for Safezone 
	printWalls() #Draw Walls
	particles = getNewParticles() #sacar el nuevo arreglo de particulas
	printParticles(particles) #Draw Particles


particles = []
#Inicializar Particulas
SINGLE_SOURCE = 0 # Si solo se quiere un source
while (True):
	pos_particle = Particle(random.randint(200, 600), random.randint(150, 550))
	if (not intersectWithWalls(pos_particle.curr_coord, pos_particle.curr_coord)):
		if (SINGLE_SOURCE):
			for i in xrange(10):
				particles.append(Particle(pos_particle.curr_coord.coord_x, pos_particle.curr_coord.coord_y))
		else:
			particles.append(pos_particle)
	if (len(particles) == 10):
		break

gbest = particles[0]
ngbest = gbest

im = PIL.Image.new("RGB", (800,600), (255, 255, 255)) #Define Image
draw = PIL.ImageDraw.Draw(im) #Draw image

def process():
	global im, imm, contador, draw
	im = PIL.Image.new("RGB", (800,600), (255, 255, 255)) #Define Image
	draw = PIL.ImageDraw.Draw(im) #Draw image
	
	printThings()
	
	imagename = "Photo.png".format()
	im.save(imagename)
	imm = PIL.ImageTk.PhotoImage(file = './'+imagename)
	
	caGrid.delete("all")	
	caGrid.create_image(400, 300, image=imm)
	caGrid.update_idletasks()
	
	root.after(100, process)

process()
root.mainloop()