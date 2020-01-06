#!/usr/bin/env python
import rospy
from dronet_perception.msg import CNN_out
from sensor_msgs.msg import Image
from std_msgs.msg import Bool, Empty
import utils
import numpy as np
import cv2
from datetime import datetime
from sympy import *
import os
import glob
from keras import backend as K

TEST_PHASE=0

class Dronet(object):
    def __init__(self,
                 json_model_path,
                 weights_path, target_size=(200, 200),
                 crop_size=(150, 150),
                 imgs_rootpath="../models"):

        self.pub = rospy.Publisher("cnn_predictions", CNN_out, queue_size=5)
        self.feedthrough_sub = rospy.Subscriber("state_change", Bool, self.callback_feedthrough, queue_size=1)
        self.land_sub = rospy.Subscriber("land", Empty, self.callback_land, queue_size=1)

        self.use_network_out = False
        self.imgs_rootpath = imgs_rootpath

        # Set keras utils
        K.set_learning_phase(TEST_PHASE)

        # Load json and create model
        model = utils.jsonToModel(json_model_path)
        # Load weights
        model.load_weights(weights_path)
        print("Loaded model from {}".format(weights_path))

        model.compile(loss='mse', optimizer='sgd')
	
        self.model = model
	
        self.target_size = target_size
	
        self.crop_size = crop_size
	print 'Process start'
	
    def callback_feedthrough(self, data):
        self.use_network_out = data.data

    def callback_land(self, data):
        self.use_network_out = False

    def run(self):

	prev=np.zeros((200,200,1))
	
	n=0
        while not rospy.is_shutdown():
            msg = CNN_out()
	    #print 'O1'
            msg.header.stamp = rospy.Time.now()
            data = None
            while data is None:
                try:
                    data = rospy.wait_for_message("camera", Image, timeout=10)
		    #print 'O2'
                except:
		    #print 'O3'
                    pass
            #print 'O4'
            '''if self.use_network_out:
                #print("Publishing commands!")
		pass
            else:
                #print("NOT Publishing commands!")
		pass'''
	    self.crop_size=(200,200)
            img = utils.callback_img(data, self.target_size, self.crop_size,
                self.imgs_rootpath, self.use_network_out,prev)


	    #print img.shape
            outs = self.model.predict_on_batch(img[None])
            steer, coll = outs[0][0], outs[1][0]
	    
	    x=int(steer*200)
	    y=int(coll*200+100)
	    print  outs,x,y
	    #f1=open("/home/tev/Desktop/Log.txt","w")
	    #f1.write(str(datetime.now())+'	'+str(steer)+'	'+str(coll)+'\n')
	    
	    n=n+1
	    img=img*4
	    img=cv2.circle(img,(x,y),10,(255,255,255),2)
	    
    
	    cv2.imshow('img',img)
	    cv2.waitKey(2)
            msg.steering_angle = steer
            msg.collision_prob = coll
            self.pub.publish(msg)
	#f1.close()
