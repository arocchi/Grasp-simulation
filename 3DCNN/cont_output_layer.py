

from __future__ import division

import numpy as np

import theano
import theano.tensor as T
from IPython import embed
from dataset_Dany import Check_Metric

class ContOutputLayer(object):
	"""
	Continuous Regression Class
	"""

	def __init__(self, input, n_in,n_out, W=None, b=None):
		""" Initialize the parameters of the logistic regression

		:type input: theano.tensor.TensorType
		:param input: symbolic variable that describes the input of the
					  architecture (one minibatch)

		:type input_mask: theano.tensor.TensorType
		:param input_mask: symbolic variable that describes relevance of input

		:type n_in: int
		:param n_in: number of input units, the dimension of the space in
					 which the datapoints lie

		"""
		# start-snippet-1

		self.W = theano.shared(value=np.zeros((n_in, n_out), dtype=theano.config.floatX ), name='W', borrow=True )
		# initialize the biases b as a vector of n_out 0s
		self.b = theano.shared( value=np.zeros( n_out, dtype=theano.config.floatX ),name='b', borrow=True)

		# if W is None:
		# 	self.W = theano.shared(value=np.zeros(n_in, dtype=theano.config.floatX), name='W', borrow=True)
		# else:
		# 	assert isinstance(W, np.ndarray), 'W must be an numpy array'
		# 	self.W = theano.shared(value=W.astype(theano.config.floatX), borrow=True)

		# # initialize the biases b as a vector of n_out 0s
		# if b is None:
		# 	self.b = theano.shared(value=np.array(0, dtype=theano.config.floatX), name='b', borrow=True)
		# else:
		# 	assert isinstance(b, np.ndarray), 'b must be an numpy array'
		# 	self.b = theano.shared(value=b.astype(theano.config.floatX), borrow=True)

		self.y_pred = T.dot(input, self.W) + self.b

		# parameters of the model
		self.params = [self.W, self.b]

		# keep track of model input
		self.input = input
		# print "dentro init"
		# self.NORMA = 0
		# print "**********************************"


	def standardization(self,y,nrow):
		# for i in range()

		roll_std  = np.std(y[:,0])
		roll_mean = np.mean(y[:,0])
		pitch_std  = np.std(y[:,1])
		pitch_mean = np.mean(y[:,1])
		yaw_std  = np.std(y[:,2])
		yaw_mean = np.mean(y[:,2])

		x_std = np.std(y[:,3])
		x_mean = np.mean(y[:,3])
		y_std = np.std(y[:,4])
		y_mean = np.mean(y[:,4])
		z_std = np.std(y[:,5])
		z_mean = np.mean(y[:,5])

		std_ = [roll_std,pitch_std,yaw_std,x_std,y,z_std]
		mean_ = [roll_mean,pitch_mean,yaw_mean,x_mean,y_mean,z_mean]

		y_std = np.empty([nrow,6])
		for i in range(0,nrow):
			y_std[i,0] = (y[i,0] - std_[0])/mean_[0]
			y_std[i,1] = (y[i,1] - std_[1])/mean_[1]
			y_std[i,2] = (y[i,2] - std_[2])/mean_[2]
			y_std[i,3] = (y[i,3] - std_[3])/mean_[3]
			y_std[i,4] = (y[i,4] - std_[4])/mean_[4]
			y_std[i,5] = (y[i,5] - std_[5])/mean_[5] 



		return y_std


	def dany_error_std(self,y,nrow):
		import math
		pi = math.pi
		ORI = []
		TRA = []
		temp = []
		NORMA = 0

		y_std = standardization(y,nrow)
		yp_std = standardization(self.y_pred,nrow)

		for i in range(0,nrow):
			dx = T.min([abs(y_std[i,0]-yp_std[i,0]),(2*pi - abs(y_std[i,0]-yp_std[i,0]))])
			dy = T.min([abs(y_std[i,1]-yp_std[i,1]),(2*pi - abs(y_std[i,1]-yp_std[i,1]))])
			dz = T.min([abs(y_std[i,2]-yp_std[i,2]),(2*pi - abs(y_std[i,2]-yp_std[i,2]))])
			d_o = np.sqrt(np.add( np.add(T.pow(dx, 2),T.pow(dy, 2)),T.pow(dz, 2)))
			tx = np.array(y_std[i,3]-yp_std[i,3])
			ty = np.array(y_std[i,4]-yp_std[i,4])
			tz = np.array(y_std[i,5]-yp_std[i,5])
			t0 = np.array([tx,ty,tz])
			# embed()
			# temp.append(np.add(d_o*0.031,0.005*np.linalg.norm(t0,2)))
			# NORMA +=(np.add(d_o*0.031,0.005*np.linalg.norm(t0,2)))
			NORMA +=(np.add(d_o*0.031,0.005*np.linalg.norm(t0,2)))
			# ORI.append(d_o*0.031)
			# TRA.append(0.005*np.linalg.norm(t0,2))

		return NORMA




	def dany_error(self,y,nrow):
		import math
		pi = math.pi
		ORI = []
		TRA = []
		temp = []
		NORMA = 0

		for i in range(0,nrow):
			dx = T.min([abs(y[i,0]-self.y_pred[i,0]),(2*pi - abs(y[i,0]-self.y_pred[i,0]))])
			dy = T.min([abs(y[i,1]-self.y_pred[i,1]),(2*pi - abs(y[i,1]-self.y_pred[i,1]))])
			dz = T.min([abs(y[i,2]-self.y_pred[i,2]),(2*pi - abs(y[i,2]-self.y_pred[i,2]))])
			d_o = np.sqrt(np.add( np.add(T.pow(dx, 2),T.pow(dy, 2)),T.pow(dz, 2)))
			tx = np.array(y[i,3]-self.y_pred[i,3])
			ty = np.array(y[i,4]-self.y_pred[i,4])
			tz = np.array(y[i,5]-self.y_pred[i,5])
			t0 = np.array([tx,ty,tz])
			# embed()
			# temp.append(np.add(d_o*0.031,0.005*np.linalg.norm(t0,2)))
			# NORMA +=(np.add(d_o*0.031,0.005*np.linalg.norm(t0,2)))
			NORMA +=(np.add(d_o*0.031,0.005*np.linalg.norm(t0,2)))
			ORI.append(d_o*0.031)
			TRA.append(0.005*np.linalg.norm(t0,2))

		return NORMA,y,self.y_pred,T.cast(ORI,'float32'),T.cast(TRA,'float32')


	def Mahalanobis(self,y,nrow):

		maha= 0
		for i in range(0,nrow):
			# embed()
			o = np.array((y[i,0],y[i,1],y[i,2]))
			op= np.array((self.y_pred[i,0],self.y_pred[i,1],self.y_pred[i,2]))
			C0 = np.cov(o,op)
			Ct = np.cov(y[i,3:],self.y_pred[i,3:])


			dx = T.min([abs(y[i,0]-self.y_pred[i,0]),(2*pi - abs(y[i,0]-self.y_pred[i,0]))])
			dy = T.min([abs(y[i,1]-self.y_pred[i,1]),(2*pi - abs(y[i,1]-self.y_pred[i,1]))])
			dz = T.min([abs(y[i,2]-self.y_pred[i,2]),(2*pi - abs(y[i,2]-self.y_pred[i,2]))])
			d_o = np.sqrt(np.add( np.add(T.pow(dx, 2),T.pow(dy, 2)),T.pow(dz, 2)))
			tx = np.array(y[i,3]-self.y_pred[i,3])
			ty = np.array(y[i,4]-self.y_pred[i,4])
			tz = np.array(y[i,5]-self.y_pred[i,5])
			t0 = np.array([tx,ty,tz])

			m0 = np.sqrt((d_o.dot(C0)).dot(np.transpose(d_o)))
			mt = np.sqrt((t0.dot(C0)).dot(np.transpose(t0)))
			maha+=(m0+mt)
			# m1 = scipy.spatial.distance.mahalanobis(y[:,1],self.y_pred[:,1],np.linalg.inv(np.cov(y[:,1],self.y_pred[:,1])))
			# m2 = scipy.spatial.distance.mahalanobis(y[:,2],self.y_pred[:,2],np.linalg.inv(np.cov(y[:,2],self.y_pred[:,2])))
			# m3 = scipy.spatial.distance.mahalanobis(y[:,3:],self.y_pred[:,3:],np.linalg.inv(np.cov(y[:,3:],self.y_pred[:,3:])))

		return maha


	def cost(self, y, y_flag=None): # balanced penalization
		"""
		mean square-root error
		"""
		# check if y has same dimension of y_pred
		if y_flag is not None:
			assert y.ndim == self.y_pred.ndim and y_flag.ndim == self.y_pred.ndim, 'Dimension mismatch'
			valid_sum = T.sum(T.pow(y - self.y_pred, 2) * y_flag)
			valid_num = T.sum(y_flag)
			return valid_sum / valid_num
		else:
			assert y.ndim == self.y_pred.ndim, 'Dimension mismatch'
			a =T.mean(T.pow(y-self.y_pred, 2))
			# embed()
			return a,y,self.y_pred


	def cost2(self, y):
		diff = y - self.y_pred
		diff_skewed = T.switch(diff>0, diff*20, diff)
		# diff_skewed = T.set_subtensor(diff[diff>0], diff[diff>0]*8) # penalize underestimation, favor overestimation
		return T.mean(T.pow(diff_skewed, 2))

	def errors(self, y):
		"""
		mean square-root error
		"""
		# check if y has same dimension of y_pred
		if y.ndim != self.y_pred.ndim:
			raise TypeError(
				'y should have the same shape as self.y_pred',
				('y', y.type, 'y_pred', self.y_pred.type)
			)
		return T.mean(T.pow(y-self.y_pred, 2))

	# def negative_log_likelihood(self, y):

	# 	return -T.mean(T.log(self.p_y_given_x)[T.arange(y.shape[0]), y])
