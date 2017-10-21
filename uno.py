
funcion nuevas particulas (particulas):
	fitness = get Fitness (distancia a zona segura y si choca con algo multiplicar por un numerote)
		if fitness < p.fitness  #determinar si es la mejor vista por la particula en su camino
			p.fitness = fitness
			p.bi_solution = p.direction #mejor direccion al momento
		
		if fitness < ngbest.fitness: #determinar si es la mejor vista en todo el swarm
			ngbest = p
		
		direction = p.direction + c1 * random.random() * (p.bi_solution - p.direction) + c2 * random.random() * (gbest.direction - p.direction) #Determinar nueva direccion considerando la influencia del grupo
		p.direction = direction #cambiar la direccion
	 
	gbest = ngbest #Cambiar el mejor global

funcion dibujarParticulas():
	particulas nuevas = obtener nuevas particulas(particulas )
	dibujar particulas nuevas	

funcion Ejecutar():
	dibujar fondo
	dibujar zona segura
	
	dibujar particulas

	Repetir;
