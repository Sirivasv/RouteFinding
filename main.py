import PIL.ImageDraw, PIL.Image, PIL.ImageShow, PIL.ImageTk
from particle import Particle
from point import Point
from Tkinter import *
import random
import math

#Numero de Iteraciones General
NI = 300

#Contador de Iteraciones dados (Esto es para pythonTK pero se puede solo poner el for y ya)
NI_CONT = 1

#Numero de pasos por particula por Iteracion
NS = 50

#Contador de PASOS dados (Esto es para pythonTK pero se puede solo poner el for y ya)
NS_CONT = 0 

#Tiempo en milisegundos para cada iteracion
ITERATION_MS = 5

#Longitud de cada Paso
ST_LEN = 20.0

#Radio de particula
PA_R = 10

#Radio de Zona Segura (Solo para propositos de graficacion en Python)
SZ_R = 50

#Mejor Fitness 
BF = -1

#Probabilidad de Mutacion D:! VALOR DE 0 a 100
MUTATIONRATE = 20

#Cantidad de particulas
MANYP = 10

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
	draw.ellipse((coords.coord_x - SZ_R, coords.coord_y - SZ_R, coords.coord_x + SZ_R, coords.coord_y + SZ_R), (0, 255, 0)) #circulo SEGURO centro en coords

def printSingleParticle(part): #Dibujar la particula, recibe una particula
	global draw
	coords = part.curr_coord
	color = (0, 0, 255)
	if (part.hitWall):
		color = (255, 0, 0)
	draw.ellipse((coords.coord_x - PA_R, coords.coord_y - PA_R, coords.coord_x + PA_R, coords.coord_y + PA_R), color) #circulo centro en coords

def printParticles(parts): #Dibuja el arreglo de particulas
	for particle in particles:
		printSingleParticle(particle) 

def newPoint(point, direction): #Determina la siguiente posicion de la particula segun su angulo de direccion
	return Point(point.coord_x + math.cos(direction) * ST_LEN, point.coord_y + math.sin(direction) * ST_LEN) 

def getDistance(p1, p2): #determina la distancia entre dos puntos
	return math.sqrt(((p1.coord_x - p2.coord_x) * (p1.coord_x - p2.coord_x)) + ((p1.coord_y - p2.coord_y) * (p1.coord_y - p2.coord_y)))

def getFitness(particle):
	temp = particle.prev_coord												#guardar la posicion anterior
	particle.prev_coord = particle.curr_coord								#determinar que la posicion actual ahora es la previa
	particle.curr_coord = newPoint(particle.curr_coord, particle.directions[particle.curr_step]) #determinar nueva posicion
	fitness_value = 1.0 / getDistance(safe_zone, particle.curr_coord)		#determinar la distancia a la zona segura
	particle.curr_step += 1
	fitness_value *= fitness_value
	fitness_value *= 3.0											#Hacer un buen valor mucho mejor
	if (intersectWithWalls(particle.curr_coord, particle.prev_coord) or (particle.hitWall)):		#si intersecta con las paredes su valor fitness sera mucho menor
		fitness_value *= 1.0
		particle.hitWall = 1
		particle.curr_coord = temp
	return fitness_value

def moveParticlesOneStep():
	global BF
	for p in particles:
		p.fitness = getFitness(p) #determinar fitness	
		if p.fitness > BF: #determinar si es la mejor vista en todo el swarm
			BF = p.fitness

def printThings():
	printSafeZone(safe_zone) #Draw Circle for Safezone 
	printWalls() #Draw Walls
	particles = moveParticlesOneStep() #mover el arreglo de particulas
	printParticles(particles) #Draw Particles

#Punto de inicio
def getRandomStartZone():
	while (True):
		pos_particle = Particle(random.randint(200, 600), random.randint(150, 550), NS)
		if (not intersectWithWalls(pos_particle.curr_coord, pos_particle.curr_coord)):
			return Point(pos_particle.curr_coord.coord_x, pos_particle.curr_coord.coord_y)

start_zone = getRandomStartZone() 

#Inicializar Particulas
particles = []
for i in xrange(MANYP):
	particles.append(Particle(start_zone.coord_x, start_zone.coord_y, NS))

im = PIL.Image.new("RGB", (800,600), (255, 255, 255)) #Define Image
draw = PIL.ImageDraw.Draw(im) #Draw image



def crossover(mom, dad): 
	childDirections = [];
	crossover = int(random.randint(0, NS));
	#Take "half" from one and "half" from the other
	for i in xrange(NS):
		if (i > crossover):
			childDirections.append(mom.directions[i]);
		else:
			childDirections.append(dad.directions[i]);
	child = Particle(start_zone.coord_x, start_zone.coord_y, NS)
	child.directions = childDirections
	return child

def mutate(child):
	for i in xrange(NS):
		if (random.randint(1, 100) < MUTATIONRATE):
			child.directions[i] = random.randint(0, 360)
	return child;

#Nueva Generacion de particulas
def getNewGeneration():
	global NS, particles, BF
	nparticles = []		#Nuevo set de particulas
	matingPool = []		#La ruleta para las probabilidades
	print "******************************"
	for i in xrange(MANYP):
		nparticles.append(Particle(start_zone.coord_x, start_zone.coord_y, NS))
		fitnessNormal = particles[i].fitness / BF
		tickets_number = max(int(fitnessNormal * 100), 1) #SE multiplica de manera arbitraria
		print "Fit: {0} FitN: {1} TN: {2}".format(particles[i].fitness, fitnessNormal, tickets_number)
		for j in xrange(tickets_number):
			matingPool.append(particles[i])

	matingPoolLen = len(matingPool)
	for i in xrange(MANYP):
		# Sping the wheel of fortune to pick two parents
		m = int(random.randint(0, matingPoolLen - 1))
		d = int(random.randint(0, matingPoolLen - 1))
		mom = matingPool[m];
		dad = matingPool[d];
		child = crossover(mom, dad);
		#Mutate their genes
		child = mutate(child)
		nparticles[i] = child
	BF = -1.0
	particles = nparticles

def process():
	global im, imm, contador, draw, NS_CONT, NS, NI, NI_CONT
	im = PIL.Image.new("RGB", (800,600), (255, 255, 255)) #Define Image
	draw = PIL.ImageDraw.Draw(im) #Draw image
	
	printThings()
	
	imagename = "Photo.png".format()
	im.save(imagename)
	imm = PIL.ImageTk.PhotoImage(file = './'+imagename)

	##
	##caGrid.destroy()
	##caGrid = Canvas(root, width = 800, height = 600, background = "gray") #Inicializar Canvas
	##caGrid.grid() #Posicionar el canvas
	##

	caGrid.delete("all")	
	caGrid.create_image(400, 300, image=imm)
	caGrid.update_idletasks()
	
	NS_CONT += 1
	if (NS_CONT < NS):
		root.after(ITERATION_MS, process)
	else:
		if (NI_CONT < NI):
			NI_CONT += 1
			particles = getNewGeneration()
			NS_CONT = 0
			root.after(ITERATION_MS, process)	

process()

root.mainloop()