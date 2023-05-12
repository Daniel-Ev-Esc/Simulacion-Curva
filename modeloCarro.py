import agentpy as ap
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns
import IPython

# Función auxiliar que convierte los vectores a unitarios
def normalize(v):
    """ Normalize a vector to length 1. """
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm

# Clase principal: Carro
class Carro(ap.Agent):


    def setup(self, id, rutaNum):

        self.id = id

        # Vectores que almacenan las velocidades y los puntos donde gira el carro a lo largo del recorrido
        velocidades = [[[0.5,0.0],[0.0,0.5],[-0.5,0.0]],[[0.5,0.0],[0.5,0.0],[0.5,0.0]],[[0.0,0.5],[0.0,0.5],[-0.5,0.0]],[[0.0,0.5],[0.0,0.5],[0.0,0.5]],[[0.0,-0.5],[0.0,-0.5],[0.0,-0.5]],[[-0.5,0.0],[-0.5,0.0],[-0.5,0.0]]]
        puntosGiro = [[(23,20),(23,27)],[(23,23),(26,23)],[(23,13),(23,27)],[(27,13),(27,17)],[(24,30),(24,25)],[(25,30),(20,30)]]

        # Variables que se utilizan para indicar si el auto actual debe actualizar el semáforo
        self.enFila = False
        self.Rojo = False

        # Variable que indica en que ruta está el carro (Candidato para regresar)
        self.rutaNum = rutaNum

        # El auto actual toma sus velocidades y puntos de giro de los vectores anteriores según su ruta
        self.velocidadesRuta = velocidades[rutaNum]
        self.puntosGiro = puntosGiro[rutaNum]

        # Variables de control del destino y la velocidad
        self.seccion = 0
        self.velocity = normalize(self.velocidadesRuta[self.seccion])

        # Variable para identificae que es un auto
        self.color = 2

    # Función que da informaciónn del espacio al agente
    def setup_pos(self, space):
        self.space = space
        self.neighbors = space.neighbors
        self.pos = space.positions[self]

    # Función que comprueba si hay un auto en la dirección a la que vá el agente
    def comprobarFrente(self,vecino):
        if ((self.velocidadesRuta[self.seccion][0] > 0.0 and vecino.pos[0] > self.pos[0]) or
            (self.velocidadesRuta[self.seccion][0] < 0.0 and vecino.pos[0] < self.pos[0]) or 
            (self.velocidadesRuta[self.seccion][1] > 0.0 and vecino.pos[1] > self.pos[1]) or
            (self.velocidadesRuta[self.seccion][1] < 0.0 and vecino.pos[1] < self.pos[1])):
            return True
        else:
            return False

    # Función que evita que el auto colisione si tiene un auto enfrente
    def evitarColision(self):
        for i in self.neighbors(self, distance = 1.2):
            if i.color == 2 and self.comprobarFrente(i):
                # Si el auto de enfrente está en la misma ruta, quiere decir que se detuvo en una fila del semáforo
                if i.rutaNum == self.rutaNum:
                    self.enFila = True # Primer condición de aprendizaje
                return True
        return False

    # Función que controla el recorrido del carro
    def cambiarSeccion(self):
        # Si llega a un punto de giro, cambia su destino al siguiente
        if(self.seccion < 2 and self.puntosGiro[self.seccion][0] == self.pos[0] and self.puntosGiro[self.seccion][1] == self.pos[1]):
            self.seccion += 1

    # Función que revisa el semáforo y el recorrido y cambia la veolcidad según la información que recibe
    def revisarSemaforo(self, semaforo):

        # Recibe su posición actual y la luz del semáforo
        pos = self.pos
        luz = semaforo.mostrarLuz()

        # Si va a colisionar cambia su velocidad a 0
        if(self.evitarColision()):
            return normalize([0.0,0.0])

        # Antes de llegar al semáforo, si la luz está en rojo o no está en su ruta y está en la posición anterior a la intersección cambia su velocidad a 0
        if(self.seccion == 0 and (luz[1] == 2 or (self.rutaNum != luz[0])) and pos[0] == semaforo.semaforoRuta[self.rutaNum][0] and pos[1] == semaforo.semaforoRuta[self.rutaNum][1]):
                self.Rojo = True # Se detuvo en un semáforo en rojo (Segunda condición de aprendizaje)
                return normalize([0.0,0.0])
        else:
            # Sinó, continua a la velocidad de su ruta
            return normalize(self.velocidadesRuta[self.seccion])

    # Función que se activa al llegar a la orilla del mapa, donde no necesita moverse más, se elimina de la simulación
    def revisarDestino(self, model, semaforo):
        
        if 0 in self.pos or 40 in self.pos:
            
            # Si se cumplen ambas funciones de aprendizaje manda los datos al semáforo para actualizar sus tiempos
            if(self.Rojo and self.enFila):
                carrosFaltantes = len(self.neighbors(self, distance=10))+1
                semaforo.actualizarRuta(self.rutaNum, carrosFaltantes)

            model.space.remove_agents(self)
            #model.agents.remove(self)
            model.agentsActive.remove(self)
    
    # Función de cambio de velocidad para modificar dirección y movimiento
    def update_velocity(self, semaforo):
        self.cambiarSeccion()  
        self.velocity = self.revisarSemaforo(semaforo)

    def update_position(self):
        self.space.move_by(self, self.velocity)

    def detenido(self):
        if self.velocity[0] == 0.0 and self.velocity[1] == 0.0:
            return 1
        return 0
    
    def mostrarSeccion(self):
        return self.seccion
    
    def mostrarNumRuta(self):
        return self.rutaNum

    def mostrarId(self):
        return self.id

class Semaforo(ap.Agent):

    # Variables iniciales del semáforo
    def setup(self, semaforoRuta, tiempoRutas):
        
        self.color = 0

        # Permite accesar a los siguientes vectores
        self.rutaAct = 0

        # Vecotres que almacenan la información de la ubicación de los semáforos y los tiempos de cambio de cada ruta
        self.semaforoRuta = semaforoRuta
        self.tiempoRutas = tiempoRutas 

        # Cantidad de rutas
        self.rutas = 6        

    # Regresa la ruta y luz activa del semáforo
    def mostrarLuz(self):
        return [self.rutaAct, self.color]

    # Función de aprendizaje
    def actualizarRuta(self, numRuta, numCarros):
        tiempoRojo = 0
        
        self.tiempoRutas[numRuta][0] += numCarros

        for i in range(0,self.rutas):
            for j in range(0,self.rutas):
                if j != i:
                    tiempoRojo += self.tiempoRutas[j][0]
            if i != numRuta:
                self.tiempoRutas[i][1] = tiempoRojo
            tiempoRojo = 0
            
                

    # Función que cambia la luz del semáforo y la ruta que está activa si el tiempo alcanza el tiempo de la ruta
    def siguienteLuz(self, tiempo):
        if(tiempo >= self.tiempoRutas[self.rutaAct][self.color]):
            if(self.color == 1):
                self.color = 0
                if(self.rutaAct == self.rutas-1):
                    self.rutaAct = 0
                else:
                    self.rutaAct += 1
            else:
                self.color+= 1
            return True
        return False

class CarModel(ap.Model):
    
    # Función que crea, agrega y posiciona los agentes en el espacio
    def generarAgentes(self):

        # Variable del número de agentes generados
        self.agentNum = 0

        # Rutas:
        # 1 A - A
        # 2 B - A
        # 3 C - A
        # 4 C - C Up
        # 5 C - C Down
        # 6 A - A
        
        # Para evitar que se generen demasiados autos en una sola ruta, se creó un arreglo que indica el máximo por ruta
        cantidadMaxRuta = [7,20,10,10,5,10]
        cantidadActualRuta = [0,0,0,0,0,0]

        # Arreglos que se van a llenar con la información aleatoria de cada agente
        numerosRuta = []
        self.posicionesIniciales = []
        id = []

        # Generar la ruta y elegir la posición inicial de cada agente
        for i in range(1,self.cantidadAgents+1):
            rutaIdx = self.random.randint(0,5)

            # Si ya se llegó al máximo de autos en esa ruta, se pasa el auto a la siguiente
            while(cantidadActualRuta[rutaIdx] == cantidadMaxRuta[rutaIdx]):
                rutaIdx += 1
                if rutaIdx > 5:
                    rutaIdx = 0

            cantidadActualRuta[rutaIdx] += 1
            id.append(i-1)
            numerosRuta.append(rutaIdx)
            self.posicionesIniciales.append(self.posiciones[rutaIdx])

        # Crear la lista de atributos con la ruta de cada agente
        numerosRutaPar = ap.AttrIter(numerosRuta)
        idAttr = ap.AttrIter(id)

        # Crear lista de agentes y de agentes activos
        # LA lista de agentes activos es la que se utilizará para llamar a las funciones de los agentes que yá se encuentren en el modelo
        self.agents = ap.AgentDList(self,self.cantidadAgents,Carro,id=idAttr,rutaNum=numerosRutaPar)
        self.agentsActive = ap.AgentDList(self)

        # Añadir el primer agente al modelo
        self.space.add_agents([self.agents[0]], [self.posicionesIniciales[0]])
        self.agentsActive.append(self.agents[0])

        # Establecer la posición del agente en el espacio
        self.agentsActive.setup_pos(self.space)

    def setup(self):
        # Inicializar el espacio
        self.batch = 1
        self.time = 0
        self.cantidadAgents = self.p.numAg
        self.space = ap.Space(self, shape=[self.p.size]*self.p.ndim)

        # Posición de parada de los semáforos
        semaforoRutasPar = [(20,20),(20,23), (23,10), (27,10),(24,35),(30,30)]

        # Variables que definen la posición inicial de cada ruta
        self.posiciones = [(1,20),(1,23),(23,1),(27,1),(25,39),(35,30)]

        # Generar agentes
        self.generarAgentes()

        # Generar semáforo
        self.agentsSem = ap.AgentDList(self,1,Semaforo, semaforoRuta=semaforoRutasPar,tiempoRutas=[[5,25],[5,25],[5,25],[5,25],[5,25],[5,25]])

        self.space.add_agents(self.agentsSem, [(-40,-40)])

    def update(self):
        # Agregar agentes uno por uno
        if self.agentNum < self.cantidadAgents-1:
            self.agentNum += 1
            self.space.add_agents([self.agents[self.agentNum]], [self.posicionesIniciales[self.agentNum]])
            self.agentsActive.append(self.agents[self.agentNum])
            
            self.agentsActive[len(self.agentsActive)-1].setup_pos(self.space)
        
    

        # Paso del tiempo y cambio de lúz del semáforo
        self.time += 1
        change = self.agentsSem[0].siguienteLuz(self.time)
        
        if(change):
            self.time = 0

        # HAcer que los agentes revisen semáforo
        self.agentsActive.update_velocity(self.agentsSem[0])

        

        # Cuando no haya carros
        if(not self.agentsActive):

            # Si es el segundo grupo termina la simulación
            if self.batch == 2:
                self.stop()
            else:
                # Si es el primero genera otra
                self.batch += 1
                self.generarAgentes()

        return[self.agents.mostrarId(),self.agents.mostrarSeccion(), self.agents.detenido(),self.agents.mostrarNumRuta(),self.agentsSem.mostrarLuz()]

    def step(self):
        self.agentsActive.update_position()
        self.agentsActive.revisarDestino(self,self.agentsSem[0])
 
    def mostrarSemaforo(self):
        return self.agentsSem[0].mostrarLuz()
    
    def mostrarRutas(self):
        return self.agentsSem.rutas

    def mostrarTiempoRutas(self):
        return self.agentsSem.tiempoRutas

    def mostrarPosicionAutos(self):
        return self.agentsActive.mostrarPosicion()