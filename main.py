from klampt import *
#Klampt v0.6.x
#from klampt import visualization as vis
# from klampt import resource
#from klampt import robotcollide as collide
#from klampt.simulation import *
#from klampt.glrobotprogram import *
#Klampt v0.7.x
from klampt import vis 
from klampt.vis.glrobotprogram import *	#Per il simulatore
# from klampt.math import *
from klampt.model import collide
# from klampt.io import resource
from klampt.sim import *
# # from moving_base_control import *
import importlib
# import os
# import time
import sys
import os
import random
# import grasp_chose
#import an object dataset
from klampt.math import so3
import string
import pydany_bb
import numpy as np
from IPython import embed

#Declare all variables
world = WorldModel()
dataset = sys.argv[1] #which dataset will be use

objects_set2 = {}
objects_set2['primo'] = [f for f in os.listdir('primo/ycb')]

index = random.randint(0,len(objects_set2[dataset])-1)

try:
	objectName = sys.argv[2]
except IndexError:
	# index = random.randint(0,len(objects_set2[dataset])-1)
	objectName = objects_set2[dataset][index]




print("objectName"), objectName
# set di oggetti
object_template_fn = 'object_template.obj'	
objects_set = {
	# 'primo':['primo/ycb//%s/meshes/tsdf_mesh.stl','primo/ycb/%s/meshes/poisson_mesh.stl']
	'primo':['primo/ycb/%s/meshes/poisson_mesh.stl'] #non considero la compenetrazione
	# 'secondo' : ['secondo/%n/poisson_mesh.stl']

	# 'ycb':['data/objects/ycb/%s/meshes/tsdf_mesh.stl','data/objects/ycb/%s/meshes/poisson_mesh.stl'],
	# 'apc2015':['data/objects/apc2015/%s/textured_meshes/optimized_tsdf_textured_mesh.ply']
}	

# objects_set2 = {}
# objects_set2['primo'] = [f for f in os.listdir('primo')]
	# 'secondo' : ['secondo/%n/poisson_mesh.stl']

	# 'ycb':['data/objects/ycb/%s/meshes/tsdf_mesh.stl','data/objects/ycb/%s/meshes/poisson_mesh.stl'],
	# 'apc2015':['data/objects/apc2015/%s/textured_meshes/optimized_tsdf_textured_mesh.ply']

print("objects_set2[dataset]"), objects_set2[dataset]
print("objects_set2 "),objects_set2[dataset][index]

world.loadElement("terrains/plane.env")	#file che richiama la mesh del piano


moving_base_template_fn = 'moving_base_template.rob'
robotname = "reflex_col"
robot_files = {
	'reflex_col':'reflex_col.rob'
}


#declare all functions

# function that import object like rigid object
def import_object():
	for pattern in objects_set[dataset]:
		# name = objects_set2[dataset][objectName]
		objfile = pattern%(objectName,)	#prendo il nome e il percorso di objectname
		print("objfile"),objfile
		objmass = 0.05 #object_masses[object_set].get('mass',0.05) #definisco la massa
		f = open(object_template_fn,'r') #apro il file 3d lo utilizzo come template per creare un file di mesh + massa
		patternfile = ''.join(f.readlines())	#leggi dentro f e unisci con '' (f= [a,b] pattern 'a' 'b')
		f.close() #lo chiudo
		f2 = open("temp_object.obj",'w')	#creo se nn esiste o apro un file in scrittura
		f2.write(patternfile % (objfile,objmass))	#scrivo mesh dell'oggetto e la massa
		f2.close() #chiuso
		# f2 = open("temp_object.txt",'w')	#creo se nn esiste o apro un file in scrittura
		# f2.write(pattern % (objfile,objmass))	#scrivo mesh dell'oggetto e la massa
		# f2.close() #chiuso
		nobjs = world.numRigidObjects() #numero di oggetti
		if world.loadElement('temp_object.obj') < 0 :
			print("no load")	#check se -1 load fallito
			continue
		assert nobjs < world.numRigidObjects(),"Hmm... the object didn't load, but loadElement didn't return -1?"
		obj = world.rigidObject(world.numRigidObjects()-1)
		obj.setTransform(*se3.identity())
		bmin,bmax = obj.geometry().getBB()	#return axix-aligned della boundig box dell'oggetto (in pratica fornisce la posizione ossia la dimensione)
		T = obj.getTransform()	#prendo la trasformazione
		spacing = 0.005 #altezza da cui cade?? 
		T = (T[0],vectorops.add(T[1],(-(bmin[0]+bmax[0])*0.5,-(bmin[1]+bmax[1])*0.5,-bmin[2]+spacing)))
		obj.setTransform(*T)	#trasformazione
		obj.appearance().setColor(0.2,0.5,0.7,1.0)	#colore
		obj.setName(objectName)	#do nome
		# print("****dove e' l'oggetto"), obj.getTransform()
		# print("****dove e' l'oggetto"), T[1][0]
	return obj

#import gripper
def import_reflex():
	f = open(moving_base_template_fn,'r')
	pattern_2 = ''.join(f.readlines())
	f.close()
	f2 = open("temp.rob",'w')
	f2.write(pattern_2 % (robot_files[robotname],robotname))
	f2.close()
	world.loadElement("temp.rob")
	robot =  world.robot(world.numRobots()-1)
	return robot

#function that moves the gripper. Devi cambiarla usando quella creata per le boundig box
def move_reflex(robot):
	q = robot.getConfig()
	q[0] = 0.05
	q[1] = 0.01
	q[2] = 0.18
	q[3] = 0 #yaw
	q[4] = 0#pitch
	q[5] = math.radians(180) #roll
	robot.setConfig(q)
	print("******* Robot dove sono **********"), robot.getConfig()

#distance between object and gripper
def RelativePosition(robot,object):
	robot_transform = robot.getConfig()
	Robot_position = [robot_transform[0], robot_transform[1],robot_transform[2]]
	object_transform = object.getTransform()
	Pos = vectorops.distance(Robot_position,object_transform[1])
	# print("Pos"), Pos
	return Pos




#make the differential 
def Differential(robot, object, Pos_prev, time):
	Pos_actual =  RelativePosition(robot,object)
	Diff = (Pos_actual - Pos_prev) / time
	# print("Derivate"), Diff
	return Diff


#check if grasp is good or not and write the object name, hand position and kindness in file.txt
def GraspValuate(diff,kindness):
	if diff > 0:
		print("No good grasp")
	else:
		print("good grasp")
		# objfile = objectName
		f = open('grasp_valuation_template.rob','r')
		pattern_2 = ''.join(f.readlines())
		f.close()
		nameFile = 'grasp_valuation_' + objectName + '.txt'
		f2 = open(nameFile ,'w')
		pos = robot.getConfig()
		f2.write(pattern_2 % (objectName,pos,kindness))
		f2.close()

#************************************************Main******************************************

robot = import_reflex()
move_reflex(robot)

obj = import_object()
tm = obj.geometry().getTriangleMesh()
n_vertices = tm.vertices.size() / 3
box = pydany_bb.Box(n_vertices)

for i in range(n_vertices):
	box.SetPoint(i, tm.vertices[3*i], tm.vertices[3*i+1], tm.vertices[3*i+2])

I = np.ones((4,4))
box.doPCA(I)


param_area = 0.95
param_volume = 9E-6
embed()
#Simulation 

#now the simulation is launched
program = GLSimulationProgram(world)
sim = program.sim

#create a hand emulator from the given robot name
module = importlib.import_module('plugins.'+robotname)
#emulator takes the robot index (0), start link index (6), and start driver index (6)
hand = module.HandEmulator(sim,0,6,6)
sim.addEmulator(0,hand)
import simple_controller
sim.setController(robot,simple_controller.make(sim,hand,program.dt))

#this code manually updates the visualization
vis.add("world",world)
vis.show()
t0 = time.time()
Pos_ = RelativePosition(robot,obj) 
kindness = 0 
Td_prev = 0
while vis.shown():
	vis.lock()
	sim.simulate(0.01)
	sim.updateWorld()
	vis.unlock()
	t1 = time.time()
	time.sleep(max(0.01-(t1-t0),0.001))
	t0 = t1	
	diff = Differential(robot, obj, Pos_,sim.getTime())
	print("getTime"), sim.getTime()
	kindness += abs(diff*(sim.getTime()-Td_prev))
	Td_prev = sim.getTime()
	print("kindness"),kindness
	if sim.getTime() > 3:
	 	print("diff"),diff
		GraspValuate(diff,kindness)
