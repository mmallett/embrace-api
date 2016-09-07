#!/usr/bin/env python
# Michael Saunby. April 2013
#
# Notes.
# pexpect uses regular expression so characters that have special meaning
# in regular expressions, e.g. [ and ] must be escaped with a backslash.
#
#   Copyright 2013 Michael Saunby
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

# MAC: 
#20:73:7A:15:13:DE
import filters
import matplotlib.pyplot as plot
import pexpect
import sys
import time
import httplib
import json
import numpy as np
import subprocess
import socket

import math
import operator

import MathUtil
import kalman

# Global functions/retrieve start time --------------------------------------
current_milli_time = lambda: int(round(time.time() * 1000))
start_time = 0.0
elapsed_time = lambda: float ("{0:.4f}".format( (float(current_milli_time()) - float(start_time))/1000 ) )


# Wiced sense class
class wicedsense:

  # frequency of data
  delta_t = .0125 # in seconds (preset to 12.5 ms)
  # total duration
  endtime = 5.0 # in seconds
  garbageiterations = 10

  inittime = 0 
  starttimer = 0 # wait for garbageiterations before the timer starts

  calibrate = False
  calibrateMagnet = False
  accelCal = [0.0, 0.0, 0.0]
  gyroCal = [0.0, 0.0, 0.0]
  magCal = [0,0, 0,0, 0,0]

  vx = 0.0
  ax = []
  dx = 0.0
  # y
  vy = 0.0
  ay = []
  dy = 0.0
  # z
  vz = 0.0
  az = []
  dz = 0.0

  gyroX = []
  gyroY = []
  gyroZ = []

  magX = []
  magY = []
  magZ = []

  magnitude = []
  timestamp = []

  def pushToCloud(self, frames, gyrodata, accel):
    #print frames[1]
    connection = httplib.HTTPSConnection("api.parse.com", 443)
    connection.connect()
    connection.request('PUT', '/1/classes/Putt/12fz4AHTDK', json.dumps({
       "frames": frames,
       "gyro": gyrodata,
       "accel": accel
     }), {
       "X-Parse-Application-Id": "iAFEw9XwderX692l0DGIwoDDHcLTGMGtcBFbgMqb",
       "X-Parse-REST-API-Key": "I0xfoOS0nDqaHxfSBTgLNMuXGtsStl7zO0XZVDZX",
       "Content-Type": "application/json"
     })  

  # Init function to connect to wiced sense using mac address
  # Blue tooth address is obtained from blescan.py 
  def __init__( self, bluetooth_adr, calibrate, calibrateMagnet):
    self.con = pexpect.spawn('gatttool -b ' + bluetooth_adr + ' --interactive')
    #self.con.logfile = sys.stdout
    self.con.expect('\[LE\]>', timeout=600)
    print "Preparing to connect. You might need to press the side button..."
    self.con.sendline('connect')
    # test for success of connect
    self.con.expect('Connection successful.*\[LE\]>')
    print "Connection successful"
    self.calibrate = calibrate
    self.calibrateMagnet = calibrateMagnet
    self.cb = {}
    return

  # Function to write a value to a particular handle  
  def char_write_cmd( self, handle, value ):
    cmd = 'char-write-req 0x%02x 0%x' % (handle, value)
    #print cmd
    self.con.sendline( cmd )
    return

  def writeToFile(self, filename, text):
    file = open(filename, 'w')
    file.write(text)
    file.close

  def readFromFile(self, filename):
    file = open(filename, 'r')
    return file.read()

    # Notification handle = 0x002b 
  def notification_loop( self ):
    if(self.calibrate == False):
      calText = self.readFromFile("calibration.txt")
      calArray = calText.split(",")
      self.gyroCal = calArray[0:3]
      self.accelCal = calArray[3:]
      calText = self.readFromFile("magnetCalibration.txt")
      self.magCal = calText.split(",")
      print self.gyroCal
      print self.accelCal
      print self.magCal
      total = math.ceil( self.endtime/self.delta_t )

    # LOOP UNTIL TIME EXPIRES
    else:
      total = math.ceil(30.0 / self.delta_t)
      print "set time to 30s for calibration"
      
    iters = 0    
    while total > iters:
      try:
        pnum = self.con.expect('Notification handle = .*? \r', timeout=4)
        
        # wait for the BT to settle -> wait for program to cycle through garbage iterations
        if self.starttimer == 1:
          iters += 1

      except pexpect.TIMEOUT:
        print "TIMEOUT exception!"
        break

      try:
        if pnum==0:
          after = self.con.after
          hxstr = after.split()[3:]
          handle = long(float.fromhex(hxstr[0]))
          self.cb[handle]([long(float.fromhex(n)) for n in hxstr[2:]])
        else:
          print "pnum not equal to 0"

      except Exception,e:
        print str(e)
        '''else:
          print "TIMEOUT!!"
          pass'''
      


    # After the while loop has broken...
    gyroAvg = [0, 0, 0]
    accelAvg = [0, 0, 0]
    if(self.calibrate == True):
      calText = ""
      if(self.calibrateMagnet == True):
        xOff = -(max(self.magX) + min(self.magX)) / 2
        yOff = -(max(self.magY) + min(self.magY)) / 2
        zOff = -(max(self.magZ) + min(self.magZ)) / 2
        calText += str(xOff) + "," + str(yOff) + "," + str(zOff)
        print calText
        self.writeToFile("magnetCalibration.txt", calText)
      else:
        calText = ""
        gyroAvg[0] = math.fsum(self.gyroX) / len(self.gyroX)
        gyroAvg[1] = math.fsum(self.gyroY) / len(self.gyroY)
        gyroAvg[2] = math.fsum(self.gyroZ) / len(self.gyroZ)
        accelAvg[0] =math.fsum(self.ax) / len(self.ax)
        accelAvg[1] = math.fsum(self.ay) / len(self.ay)
        accelAvg[2] = math.fsum(self.az) / len(self.az)
        calText += str(0 - gyroAvg[0]) + "," + str(0 - gyroAvg[1]) + "," + str(0 - gyroAvg[2]) + ","
        calText += str(0 - accelAvg[0]) + "," + str(0 - accelAvg[1]) + "," + str(8192 - accelAvg[2])
        self.writeToFile("calibration.txt", calText)
    
    else:
      # FILTER OUT INITIAL ACCELERATION VALUES --------------
      thresh = 9.9 # accel treshold must be exceeded to indicate putt has begun (m/s^2)
      axnew = []   # new acceleration list in the x direction
      aynew = []   # ... y direction
      aznew = []   # ... z direction
      accelNew = []
      gyroXnew = []
      gyroYnew = []
      gyroZnew = []
      magnew = []
    
      for x in range(len(self.magnitude)):
        print self.magnitude[x]
        #if self.magnitude[x] > thresh:
        if True:
          print "PUTTING................."
          axnew = self.ax[x:]
          aynew = self.ay[x:]
          aznew = self.az[x:]
          magnew = self.magnitude[x:]
          gyroXnew = self.gyroX[x:]
          gyroYnew = self.gyroY[x:]
          gyroZnew = self.gyroZ[x:]
          #self.magX = self.magX[x:]
          #self.magY = self.magY[x:]
          #self.magZ = self.magZ[x:]
          break

      # ========================
      # GET DISPLACEMENT FRAMES
      # ========================
      
      for x in range(len(axnew)):
        accelNew.append([axnew[x], aynew[x], aznew[x], magnew[x]])

      roll = []
      pitch = []
      yaw = []
      roll.append(MathUtil.roll(axnew[0], aynew[0], aznew[0]))
      pitch.append(MathUtil.pitch(axnew[0], aynew[0], aznew[0]))
      #yaw.append(MathUtil.yaw(roll[0], pitch[0], self.magX[0], self.magY[0], self.magZ[0])) 
      for x in range(1, len(axnew)):
        roll.append(MathUtil.roll(axnew[x], aynew[x], aznew[x]))
        pitch.append(MathUtil.pitch(axnew[x], aynew[x], aznew[x]))
        #yaw.append(MathUtil.yaw(roll[x], pitch[x], self.magX[x], self.magY[x], self.magZ[x]))
        

      # OUTPUT TO SCREEN ------------------
      '''
      print "axnew:"
      for x in range(0,len(axnew)): print axnew[x]
      print

      print "axnew length"
      print len(axnew)
      print

      print "xyzframes (frame indicates the x displacement in meters at a given time):"
      for x in range(0,len(xyzframes)): print xyzframes[x]
      print
      
      print "total duration (in s) "
      print (float(len(axnew)))*delta_t
      print

      print "total samples"
      print int (len(axnew)) + 1 # add one for time 0
      print

      '''
     
      #Kalman filtering
      gyrodata = []
      kalmanX = kalman.Kalman(roll[0])
      kalmanY = kalman.Kalman(pitch[0])
      
      gyrodata.append([roll[0], pitch[0], 0.0])
      zAngle = [0.0]
      xAngle = [0.0]
      yAngle = [0.0]
      time = [0.0]
      data = [0.0]
      angle = [0.0]
      for x in range(1, len(gyroXnew)):
        time.append(time[-1] + self.delta_t)
        data.append(MathUtil.getAngle(gyroZnew[x], self.delta_t))
        xAngle.append(xAngle[-1] + MathUtil.getAngle(gyroXnew[x], self.delta_t))
        yAngle.append(yAngle[-1] + MathUtil.getAngle(gyroYnew[x], self.delta_t))
        zAngle.append(zAngle[-1] + data[-1])
        gyrodata.append([kalmanX.updateAngle(roll[x], gyroXnew[x], self.delta_t), 
                        kalmanY.updateAngle(pitch[x], gyroYnew[x], self.delta_t), 
                        zAngle[x] ])
        
      accelRot = MathUtil.rotateAcceleration([axnew, aynew, aznew], [[i[0] for i in gyrodata[:]], [i[1] for i in gyrodata[:]], [i[2] for i in gyrodata[:]]])

      #displacement calculations
      xframes = [MathUtil.displacement(self.dx,self.vx,accelRot[0][0], self.delta_t)[0]]
      yframes = [MathUtil.displacement(self.dy,self.vy,accelRot[1][0], self.delta_t)[0]]
      zframes = [MathUtil.displacement(self.dz,self.vz,accelRot[2][0], self.delta_t)[0]]
      xyzframes = [[xframes[-1], yframes[-1], zframes[-1]]]
      for x in range(1, len(gyroXnew)):
        self.dx,self.vx = MathUtil.displacement(self.dx,self.vx,accelRot[0][x], self.delta_t)
        xframes.append( float(xframes[-1] + self.dx)  )
        self.dy,self.vy = MathUtil.displacement(self.dy,self.vy,accelRot[1][x], self.delta_t)
        yframes.append( float(yframes[-1] + self.dy)  )
        self.dz,self.vz = MathUtil.displacement(self.dz,self.vz,accelRot[2][x], self.delta_t)
        zframes.append( float(zframes[-1] + self.dz)  )
        xyzframes.append( [xframes[-1], yframes[-1], zframes[-1]] )
        accelNew[x] = [accelRot[0][x], accelRot[1][x], accelRot[2][x], accelNew[x][3]]
       


      # =======================
      # PUSH FRAMES TO PARSE
      # =======================
      self.pushToCloud(xyzframes, gyrodata, accelNew)
      
     
    self.resetVars()  

 
  def resetVars(self):
    self.inittime = 0 
    self.starttimer = 0 # wait for garbageiterations before the timer starts
    self.accelCal = [0.0, 0.0, 0.0]
    self.gyroCal = [0.0, 0.0, 0.0]
    self.magCal = [0,0, 0,0, 0,0]
    self.vx = 0.0
    self.ax = []
    self.dx = 0.0
    # y
    self.vy = 0.0
    self.ay = []
    self.dy = 0.0
    # z
    self.vz = 0.0
    self.az = []
    self.dz = 0.0

    self.gyroX = []
    self.gyroY = []
    self.gyroZ = []

    self.magX = []
    self.magY = []
    self.magZ = []

    self.magnitude = []
    self.timestamp = []


  def register_cb( self, handle, fn ):
    self.cb[handle]=fn
    return


  def dataCallback(self, v):
    global start_time
    # clear first ten recordings because BT timing needs to settle
    # garbageiterations = 10
    if self.inittime > self.garbageiterations-1:

      if self.starttimer == 0:
        self.starttimer = 1

      else: # the garbage iterations have passed
        if len(self.timestamp) == 0:
          start_time = current_milli_time()
          self.timestamp.append(elapsed_time())
          print "Python timestamp (in s): " + str(self.timestamp[-1])
        else:
          self.timestamp.append( elapsed_time() )
          print "Python timestamp (in s): " + str(self.timestamp[-1])

        bytelen = len(v) # v is the handle data

        vx1 = int( str(v[2]*256 + v[1]) )
        vy1 = int( str(v[4]*256 + v[3]) )
        vz1 = int( str(v[6]*256 + v[5]) )
        gx1 = int( str(v[8]*256 + v[7]) )
        gy1 = int( str(v[10]*256 + v[9]) )
        gz1 = int( str(v[12]*256 + v[11]) )

        if(self.calibrateMagnet == True):
          (Mxyz, Mmag) = MathUtil.convertData(mx1, my1, mz1, 1.0)
          self.magX.append(Mxyz[0])
          self.magY.append(Mxyz[1])
          self.magZ.append(Mxyz[2])
        elif(self.calibrate == True):
            (Gxyz, Gmag) = MathUtil.convertData(gx1, gy1, gz1, 1.0) # FS = 500dps
            (Axyz, Amag) = MathUtil.convertData( vx1,vy1,vz1, 1.0)#(8192.0/9.80665))
            self.gyroX.append(Gxyz[0])
            self.gyroY.append(Gxyz[1])
            self.gyroZ.append(Gxyz[2])
            self.ax.append( Axyz[0] )
            self.ay.append( Axyz[1] )
            self.az.append( Axyz[2] )
            print str(Gxyz[0]) +", "+str(Gxyz[1])+", "+str(Gxyz[2]) + ", " + "{0:.5f}".format(Axyz[0]) + ", " + "{0:.5f}".format(Axyz[1]) + ", " + "{0:.5f}".format(Axyz[2])
        else:
          (Gxyz, Gmag) = MathUtil.convertData(gx1 + int(float(self.gyroCal[0])), gy1 + int(float(self.gyroCal[1])), gz1 + int(float(self.gyroCal[2])), 1.0/.00762939)
          (Axyz, Amag) = MathUtil.convertData(vx1 + int(float(self.accelCal[0])), vy1 + int(float(self.accelCal[1])), vz1 + int(float(self.accelCal[2])), 16384.0/9.80665)
          #(Mxyz, Mmag) = MathUtil.convertData(mx1 + int(float(self.magCal[0])), my1 + int(float(self.magCal[1])), mz1 + int(float(self.magCal[2])), 16384.0)
                    
          print str(Gxyz[0]) +", "+str(Gxyz[1])+", "+str(Gxyz[2]) + ", " + "{0:.5f}".format(Axyz[0]) + ", " + "{0:.5f}".format(Axyz[1]) + ", " + "{0:.5f}".format(Axyz[2])# + ", " + "{0:.5f}".format(Mxyz[0]) + ", " + "{0:.5f}".format(Mxyz[1]) + ", " + "{0:.5f}".format(Mxyz[2])

          self.gyroX.append(Gxyz[0])
          self.gyroY.append(Gxyz[1])
          self.gyroZ.append(Gxyz[2])

         # self.magX.append(Mxyz[0])
         # self.magY.append(Mxyz[1])
         # self.magZ.append(Mxyz[2])

          self.magnitude.append( Amag )

          self.ax.append( Axyz[0] )
          self.ay.append( Axyz[1] )
          self.az.append( Axyz[2] )
   
    else:
      self.inittime += 1  # increment 10 times before evaluating values      

def createServerSocket(port):
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  s.bind(("127.0.0.1", port))
  s.listen(2)
  s.setblocking(1)
  #print "connected to callback socket"
  return s

# We listen on sockets on PORTs defined above
def acceptSocketConnection(sock):
  conn, addr = sock.accept()
  putt = conn.recv(16)
  conn.close()
  print "putt: "+putt
  return putt


# main function USAGE python sense.py <mac address>
def main():
  calibrate = False
  calibrateMagnet = False
  bluetooth_adr = sys.argv[1]
  p1 = None
  
  #command line arg for calibration
  if len(sys.argv) > 2:
    if(sys.argv[2] == "true" or sys.argv[2] == "True"):
      calibrate = True
    elif(sys.argv[2] == "magnet" or sys.argv[2] == "Magnet"):
      calibrateMagnet = True
      calibrate = True
  
  #no calibration, spawn subprocess, connect to wiced sense and start notification loop
  if(calibrate == False):
    p1 = subprocess.Popen(['./callback'])
    print "created callback process"
    sock = createServerSocket(50014) 
    putt = False
    try:   
      tag = wicedsense(bluetooth_adr, calibrate, calibrateMagnet)
      tag.register_cb(0x2a,tag.dataCallback)
      putt = acceptSocketConnection(sock)
      print putt
      print "waiting for putt command"
    except Exception, e:
      print str(e)
      p1.terminate()
      return
 
    while(True):
      try:
        putt = acceptSocketConnection(sock)
        if(putt):
          tag.char_write_cmd(0x2b, 0x01)
          tag.notification_loop()
          
      except KeyboardInterrupt:
        tag.con.sendline("disconnect")
        tag.con.sendline("exit")
        sys.exit(0)
      except Exception, e:
        print str(e)
        pass
      tag.char_write_cmd(0x2b, 0x00)
    
    p1.terminate()

  else:
    try:
      tag = wicedsense(bluetooth_adr, calibrate, calibrateMagnet)
      tag.register_cb(0x2a,tag.dataCallback)
      tag.char_write_cmd(0x2b, 0x01)
      tag.notification_loop()
    except Exception, e:
      print str(e)
      pass


if __name__ == "__main__":
  main()




