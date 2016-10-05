import pkg_resources
pkg_resources.require("klampt>=0.7.0")
from klampt import *
from klampt import vis 
from klampt.vis.glrobotprogram import *
from klampt.math import *
from klampt.model import collide
from klampt.io import resource
from klampt.sim import *
from moving_base_control import *
import importlib
import math
import os
import string
import sys
import time

from create_mvbb import MVBBVisualizer, trimesh_to_numpy, numpy_to_trimesh, compute_poses
from klampt.math import so3, se3
import pydany_bb
import numpy as np
from IPython import embed
from mvbb.graspvariation import PoseVariation
from mvbb.TakePoses import SimulationPoses
from mvbb.draw_bbox import draw_GL_frame, draw_bbox
from i16mc import make_object, make_moving_base_robot
from mvbb.CollisionCheck import CheckCollision, CollisionTestInterpolate, CollisionTestPose


objects = {}
objects['ycb'] = [f for f in os.listdir('data/objects/ycb')]
objects['apc2015'] = [f for f in os.listdir('data/objects/apc2015')]
robots = ['reflex_col', 'soft_hand', 'reflex']

object_geom_file_patterns = {
    'ycb':['data/objects/ycb/%s/meshes/tsdf_mesh.stl','data/objects/ycb/%s/meshes/poisson_mesh.stl'],
    'apc2015':['data/objects/apc2015/%s/textured_meshes/optimized_tsdf_textured_mesh.ply']
}

robot_files = {
    'reflex_col':'data/robots/reflex_col.rob',
    'soft_hand':'data/robots/soft_hand.urdf',
    'reflex':'data/robots/reflex.rob'
}

class FilteredMVBBVisualizer(MVBBVisualizer):
    def __init__(self, poses, poses_variations, boxes, world, alt_trimesh = None):
        MVBBVisualizer.__init__(self, poses, poses_variations, boxes, world, alt_trimesh)

    def display(self):
        T0 = get_moving_base_xform(self.robot)
        T0_invisible = T0
        T0_invisible[1][2] = -1
        set_moving_base_xform(self.robot,T0_invisible[0], T0_invisible[1])
        self.world.drawGL()
        set_moving_base_xform(self.robot, T0[0], T0[1])
        self.obj.drawGL()
        for pose in self.poses:
            T = se3.from_homogeneous(pose)
            if not CollisionTestPose(self.world, self.robot, self.obj, T):
                draw_GL_frame(T)
                #set_moving_base_xform(self.robot, T[0], T[1])
                #self.robot.drawGL()
            else:
                "robot collides with object at", T
                draw_GL_frame(T, color=(0.5,0.5,0.5))
        for box in self.boxes:
            draw_bbox(box.Isobox, box.T)
        set_moving_base_xform(self.robot, T0[0], T0[1])

def kdltonumpy3(R):
    npR = np.eye(3)
    for i in range(3):
        for j in range(3):
            npR[i,j] = R[i,j]
    return npR

def kdltonumpy4(F):
    npF = np.eye(4)
    npF[0:3,0:3] = kdltonumpy3(F.M)
    for i in range(3):
        npF[i,3] = F.p[i]
    return npF

def launch_mvbb_filtered(robotname, object_set, objectname):
    """Launches a very simple program that spawns an object from one of the
    databases.
    It launches a visualization of the mvbb decomposition of the object, and corresponding generated poses.
    It then spawns a hand and tries all different poses to check for collision
    """

    world = WorldModel()
    world.loadElement("data/terrains/plane.env")
    robot = make_moving_base_robot(robotname, world)
    object = make_object(object_set, objectname, world)

    R,t = object.getTransform()
    object.setTransform(R, [0, 0, 0])
    tm = object.geometry().getTriangleMesh()
    n_vertices = tm.vertices.size() / 3
    decimator = pydany_bb.MVBBDecimator()
    vertices_old, faces_old = trimesh_to_numpy(tm)
    tm_decimated = None
    if n_vertices > 2000:
        print "Object has", n_vertices, "vertices - decimating"
        decimator.decimateTriMesh(vertices_old, faces_old)
        vertices = decimator.getEigenVertices()
        faces = decimator.getEigenFaces()
        tm_decimated = numpy_to_trimesh(vertices, faces)
        print "Decimated to", vertices.shape[0], "vertices"
        poses, poses_variations, boxes = compute_poses(vertices)
    else:
        poses, poses_variations, boxes = compute_poses(object)

    w_T_o = np.eye(4)
    h_T_h2 = np.eye(4)
    if True:
        import PyKDL
        f = PyKDL.Frame()
        f.p[2] -= 0.15
        h_T_h2 = kdltonumpy4(f)


    for i in range(len(poses)):
        poses[i] = w_T_o.dot(poses[i]).dot(h_T_h2)
    """
    for i in range(len(poses_variations)):
        poses_variations[i] = w_T_o.dot(poses_variations[i]).dot(h_T_h2)
    """

    embed()
    # now the simulation is launched

    program = FilteredMVBBVisualizer(poses, poses_variations, boxes, world, tm_decimated)
    vis.setPlugin(program)
    program.reshape(800, 600)

    vis.show()

    # this code manually updates the visualization

    while vis.shown():
        time.sleep(0.01)

    vis.kill()
    return

if __name__ == '__main__':
    import random
    try:
        dataset = sys.argv[1]
    except IndexError:
        dataset = random.choice(objects.keys())

    #just plan grasping
    try:
        index = int(sys.argv[2])
        objname = objects[dataset][index]
    except IndexError:
        index = random.randint(0,len(objects[dataset])-1)
        objname = objects[dataset][index]
    except ValueError:
        objname = sys.argv[2]

    print "loading object", index, " -", objname, "-from set", dataset

    launch_mvbb_filtered("soft_hand", dataset, objname)
