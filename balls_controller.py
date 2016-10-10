from klampt import *
from klampt.math import vectorops,so3,se3
from moving_base_control import *
from reflex_control import *
from klampt.io import resource
from i16mc import box_dims
from IPython import embed
import numpy as np
from copy import deepcopy

class BallsStateMachineController(object):
    """A more sophisticated controller that uses a state machine."""
    def __init__(self,sim,hand,dt):
        self.sim = sim
        self.hand = hand
        self.dt = dt
        self.sim.updateWorld()
        self.base_xform = get_moving_base_xform(self.sim.controller(0).model())
        self.state = 'wait'
        self.balls_to_move = []
        self.attempts = {}
        self.ball = None
        self.t0 = 0
        self.start_pose = None
        self.goal_pose = None
        self.p_T_h = resource.get("default_initial_soft_hand.xform", description="Initial hand transform",
                             default=se3.identity(), world=sim.world, doedit=False)

    def __call__(self,controller):
        self.sim.updateWorld()
        sim = self.sim
        xform = self.base_xform

        #controller state machine
        #print "State:",state
        t_park = 0.5
        t_lower = 0.5
        t_grasp = 1.0
        t_lift = 0.5
        t_ungrasp = 0.5
        t_wait = 2.0
        if self.state == 'wait':
            if sim.getTime() > t_wait:
                self.state = 'idle'
                print self.state

        if self.state == 'idle':
            if len(self._get_balls_to_move()) > 0:
                ball = self.balls_to_move.pop(0)
                if ball not in self.attempts:
                    self.attempts[ball] = 0
                self.attempts[ball] += 1
                self.ball = ball
                print "Attempt", self.attempts[ball]

                self.start_pose = get_moving_base_xform(self.sim.controller(0).model())
                self.goal_pose = self._get_hand_pose_for_ball(ball)
                self.t0 = sim.getTime()
                self.state = 'parking'
                print self.state

        elif self.state == 'parking':
            u = (sim.getTime() - self.t0) / t_park
            goal_pose = deepcopy(self.goal_pose)
            goal_pose[1][2] = self.start_pose[1][2] # translate and rotate, do not lower
            t = vectorops.interpolate(self.start_pose[1], goal_pose[1], np.min((u,1.0)))
            desired = (goal_pose[0], t)
            send_moving_base_xform_PID(controller, desired[0], desired[1])

            if sim.getTime() - self.t0 > t_park:
                self.start_pose = get_moving_base_xform(self.sim.controller(0).model())
                self.t0 = sim.getTime()
                self.state = 'lowering'
                print self.state

        elif self.state == 'lowering':
            u = (sim.getTime() - self.t0) / t_lower
            t = vectorops.interpolate(self.start_pose[1], self.goal_pose[1], np.min((u, 1.0)))
            desired = (self.goal_pose[0], t)
            send_moving_base_xform_PID(controller, desired[0], desired[1])

            if sim.getTime() - self.t0 > t_lower:
                self.start_pose = get_moving_base_xform(self.sim.controller(0).model())
                self.t0 = sim.getTime()
                #this is needed to stop at the current position in case there's some residual velocity
                controller.setPIDCommand(controller.getCommandedConfig(),[0.0]*len(controller.getCommandedConfig()))
                self.hand.setCommand([1.0])
                self.state = 'grasping'
                print self.state

        elif self.state == 'grasping':
            if sim.getTime() - self.t0 > t_grasp:
                self.t0 = sim.getTime()
                self.start_pose = get_moving_base_xform(self.sim.controller(0).model())
                goal_pose = deepcopy(self.goal_pose)
                goal_pose[1][2] = self.base_xform[1][2]  # translate and rotate, do not lower
                self.goal_pose = goal_pose
                self.state = 'lifting'
                print self.state

        elif self.state == 'lifting':
            u = (sim.getTime() - self.t0) / t_lift
            goal_pose = deepcopy(self.goal_pose)
            t = vectorops.interpolate(self.start_pose[1], goal_pose[1], np.min((u, 1.0)))
            desired = (goal_pose[0], t)
            send_moving_base_xform_PID(controller, desired[0], desired[1])

            if sim.getTime() - self.t0 > t_lift:
                if self._ball_lifted():
                    self.start_pose = get_moving_base_xform(self.sim.controller(0).model())
                    self.t0 = sim.getTime()
                    self.state = 'parking_for_ungrasp'
                else:
                    self.ball = None
                    self.hand.setCommand([0.0])
                    self.state = 'idle'
                    print "Failed to raise ball"
                print self.state

        elif self.state == 'parking_for_ungrasp':
            u = (sim.getTime() - self.t0) / t_park
            goal_pose = deepcopy(self.goal_pose)
            goal_pose[1][0] += 0.7  # translate to the next box
            t = vectorops.interpolate(self.start_pose[1], goal_pose[1], np.min((u, 1.0)))
            desired = (goal_pose[0], t)
            send_moving_base_xform_PID(controller, desired[0], desired[1])

            if sim.getTime() - self.t0 > t_park:
                self.t0 = sim.getTime()
                self.hand.setCommand([0.0])
                self.state = 'ungrasp'
                print self.state

        elif self.state == 'ungrasp':
            if sim.getTime() - self.t0 > t_ungrasp:
                self.state = 'idle'
                print self.state


        # need to manually call the hand emulator
        self.hand.process({}, self.dt)

    def _get_balls_to_move(self):
        w = self.sim.world
        self.balls_to_move = []
        for i in range(w.numRigidObjects()):
            o = w.rigidObject(i)

            if 'sphere' in o.getName():
                R, t = o.getTransform()
                if t[0] < box_dims[0]/2.0 - 0.005 and t[1] < box_dims[1]/2.0 - 0.005:
                    self.balls_to_move.append(o)
            self.balls_to_move = sorted(self.balls_to_move, key = lambda obj: (obj.getTransform()[1][2],
                                                                               obj.getTransform()[1][0]**2+
                                                                               obj.getTransform()[1][1]**2))
        return self.balls_to_move

    def _get_hand_pose_for_ball(self, ball):
        w_T_op = np.eye(4)
        w_T_op[2,3] = 0.11 # TODO Manuel get this value from the BB or from the algorithm
        """
        w_T_o = np.array(ball.getTransform())
        p_T_h = np.array(se3.homogeneous(self.p_T_h))
        w_T_p =  w_T_op.dot(w_T_o)
        return w_T_p.dot(p_T_h)
        """
        pose = (self.base_xform[0], ball.getTransform()[1])
        final_pose = w_T_op.dot(np.array(se3.homogeneous(pose)))
        return se3.from_homogeneous(final_pose)

    def _ball_lifted(self):
        com = se3.apply(self.ball.getTransform(), self.ball.getMass().getCom())
        xform = get_moving_base_xform(self.sim.controller(0).model())
        w_T_h = np.array(se3.homogeneous(xform))
        h_T_p = np.linalg.inv(np.array(se3.homogeneous(self.p_T_h)))
        w_T_p = w_T_h.dot(h_T_p)
        com = np.array(com)
        if np.linalg.norm(com - w_T_p[0:3,3]) > 0.1:
            return False
        return True

def make(sim,hand,dt):
    """The make() function returns a 1-argument function that takes a SimRobotController and performs whatever
    processing is needed when it is invoked."""
    return BallsStateMachineController(sim,hand,dt)