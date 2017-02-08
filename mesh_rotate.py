#!/usr/bin/env python

import pkg_resources
pkg_resources.require("klampt>=0.7.0")
import importlib
import sys
import os
import random
import string
import pydany_bb
import numpy as np
import math
from IPython import embed
from klampt.math import so3,se3
import time

from klampt import *
from klampt import vis 
from klampt.vis.glrobotprogram import *
from klampt.math import *
from klampt.model import collide
from klampt.io import resource
from klampt.sim import *
# from klampt.vis.glprogram import GLNavigationProgram    #Per il
from klampt.sim import *
import importlib
import sys
import os
import random
from klampt.math import so3, se3
import string
import pydany_bb
import numpy as np
import math
from IPython import embed
# from mvbb.graspvariation import PoseVariation
# from mvbb.TakePoses import SimulationPoses
from mvbb.draw_bbox import draw_GL_frame, draw_bbox
# from i16mc import make_object
# from dany_make_rotate_voxel import make_objectRotate
import trimesh
import csv
from stl import mesh
from mpl_toolkits import mplot3d
from matplotlib import pyplot
import pymesh
import random
# from dany_make_rotate_voxel import make_objectRotate


'''Code to create a rotate mesh. The rotation is always on Z axis'''


objects = {}
objects['ycb'] = [f for f in os.listdir('data/objects/ycb')]
objects['apc2015'] = [f for f in os.listdir('data/objects/apc2015')]
# objects['newObjdany'] = [f for f in os.listdir('data/objects/newObjdany')]
objects['princeton'] = [f for f in os.listdir('data/objects/princeton')]

Pose = {}
Pose['Pose'] = [f for f in os.listdir('3DCNN/NNSet/Pose/pose')]




class PoseVisualizer(GLNavigationProgram):
    def __init__(self, obj,world,o_T_p_r,o_T_p):
        GLNavigationProgram.__init__(self, 'PoseVisualizer')
        self.world = world
        # self.robot = robot
        self.obj = obj
        self.o_T_p_r = o_T_p_r
        self.o_T_p = o_T_p

    def display(self):
        self.world.drawGL()
        # if self.camera is None:
        R,t = self.obj.getTransform()
        bmin,bmax = self.obj.geometry().getBB()
        centerX = 0.5 * ( bmax[0] - bmin[0] ) +t[0] 
        centerY = 0.5 * ( bmax[1] - bmin[1] ) + t[1]
        centerZ = 0.5 * ( bmax[2] - bmin[2] ) + t[2]
        P = R,[centerX,centerY,centerZ]
        # print P
        draw_GL_frame(P,axis_length=0.5)
        draw_GL_frame(se3.from_homogeneous(self.o_T_p_r),axis_length=0.1)
        # draw_GL_frame(se3.from_homogeneous(self.o_T_p),axis_length=1)
        # Pc = 
        # [-0.99, 0, -0.0015, 0.0 ,1, 0, 0.0015 ,0,-0.99 ],[ 0.0, 0, 0.5]
        # Pc = [0.99, 0, -0.0015, 0.0 ,1 ,0, 0.0015, 0, 0.99], [0.0 ,0 ,1.5]
        # draw_GL_frame(Pc)


        #camera -> link = 0
        # draw_GL_frame(self.robot.link(0).getTransform())


    def idle(self):
        pass




















def Open_pose_file(object_list, vector_set):
    '''Read the poses and store it as rpy into a vector'''
    for object_name in object_list:
        # for object_set, objects_in_set in Pose.items():
            print object_name
            obj_dataset = '3DCNN/NNSet/Pose/pose/%s.csv'%(object_name)
            # embed()
            print obj_dataset
            try:
                with open(obj_dataset, 'rb') as csvfile: #open the file in read mode
                    file_reader = csv.reader(csvfile,quoting=csv.QUOTE_NONNUMERIC)
                    for row in file_reader:
                        T = row[9:]
                        # Matrix_ = so3.matrix(row)
                        pp = row[:9]
                        # embed()
                        P = np.array(se3.homogeneous((pp,T)))
                        vector_set.append(P)
                        # print row
            except:
                print "No pose in ", object_name


def Write_Poses(dataset,poses):
    '''Write the dataset'''
    f = open(dataset, 'w')
    # embed()
    # for pose in poses:
    T = se3.from_homogeneous(poses)
    # embed()
    f.write(','.join([str(v) for v in T[0]+T[1]]))
    f.write('\n')
    f.close()

def WriteRotationObj(dataset,angle,Axis,T):
    f = open(dataset, 'w')
    f.write(str(angle))
    f.write(',')
    f.write(','.join([str(v) for v in Axis]))
    f.write(',')
    f.write(','.join([str(v) for v in T]))
    f.close()















def main(object_list):

    # world = WorldModel()
    # world.loadElement("data/terrains/plane.env")
    for object_name in object_list:
        for object_set, objects_in_set in objects.items():
            if object_name in objects_in_set:
                poses = []
                poses_rotated = []
                Open_pose_file([object_name],poses)
                # print"po

                for i, o_T_p in enumerate(poses):
                    # print i
                    # world = WorldModel()
                    # if world.numRigidObjects() > 0:
                    #     world.remove(world.rigidObject(0))
                    # print object_set
                    if object_set == 'princeton':
                        objpath = 'data/objects/princeton/%s/tsdf_mesh.off'%object_name
                        respath = 'data/objects/voxelrotate/princeton/%s/%s_rotate_%s.off'%(object_name,object_name,i)
                    elif object_set == 'apc2015':
                        objpath = 'data/objects/apc2015/%s/meshes/poisson.ply'%object_name
                        respath = 'data/objects/voxelrotate/%s/%s/%s_rotate_%s.stl'%(object_set,object_name,object_name,i)
                    # elif object_set == 'newObjdany':
                    #     objpath = 'data/objects/newObjdany/%s/tsdf_mesh.stl'%object_name
                    #     respath = 'data/objects/newObjdany/%s/%s_rotate_%s.stl'%(object_name,object_name,i)
                    else:
                        objpath = 'data/objects/%s/%s/meshes/poisson_mesh.stl'%(object_set,object_name)
                        respath = 'data/objects/voxelrotate/%s/%s/%s_rotate_%s.stl'%(object_set,object_name,object_name,i)
                    # print "qui"
                    mesh = pymesh.load_mesh(objpath)
                    axis = [0,0,1]
                    # print objpath
                    directory = 'data/objects/voxelrotate/%s/%s'%(object_set,object_name)
                    if not os.path.exists(directory):
                        os.makedirs(directory)


                    if i is 0:
                        pymesh.save_mesh(respath, mesh)
                        respose = '3DCNN/NNSet/Pose/ObjectsVariation/%s_rotate_%s.csv'%(object_name,str(i))
                        WriteRotationObj(respose,0.0,axis,[0,0,0])
                        respose = '3DCNN/NNSet/Pose/PoseVariation/%s_rotate_%s.csv'%(object_name,str(i))
                        Write_Poses(respose,o_T_p)
                        respose = '3DCNN/NNSet/Pose/ObjectsVariation/%s_rotate_%s.csv'%(object_name,str(i))
                        WriteRotationObj(respose,0.0,axis,[0,0,0])
                    else:
                         #only on z
                        theta_deg = random.randrange(-90,90)
                        if theta_deg == 0.0:
                            theta_deg = random.randrange(-90,90)

                        theta = math.radians(theta_deg)
                        ROtation_matrix = so3.matrix(so3.from_axis_angle((axis,theta)))
                        # print ROtation_matrix
                        temp_vertex = mesh.vertices.dot(np.array(ROtation_matrix).transpose())
                        mesh_new = pymesh.form_mesh(temp_vertex, mesh.faces,mesh.voxels)
                        
                        try:
                            pymesh.save_mesh(respath, mesh_new)
                        except:
                            print "Problem save mesh ", object_name, "In", object_set
                        try:
                            respose = '3DCNN/NNSet/Pose/ObjectsVariation/%s_rotate_%s.csv'%(object_name,str(i))
                            WriteRotationObj(respose,theta,axis,[0,0,0])
                        except:
                            print "Problem with write ObjectsVariation", object_name, "In", object_set
                        try:
                            # embed()
                            R = np.array(se3.homogeneous((so3.from_axis_angle((axis,theta)),[0,0,0])))
                            # print R
                            # embed()
                            poses_rotated = np.dot(R, o_T_p) #o_T_p_rotate
                            #embed()
                            respose = '3DCNN/NNSet/Pose/PoseVariation/%s_rotate_%s.csv'%(object_name,str(i))
                            Write_Poses(respose,poses_rotated)

                        except:
                            print "Problem with", object_name, "In", object_set

if __name__ == '__main__':
    all_objects = []


    for dataset in objects.values():
        for i,t in Pose.items():
            if dataset in t:
                all_objects += dataset

    try:
        nome = sys.argv[1]
        main([nome])
    except:
        main(all_objects)
