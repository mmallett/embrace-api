import boto3
from boto3.dynamodb.conditions import Attr
import time
import hashlib
import random
import math
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
from sklearn import svm
from sklearn import cross_validation
from operator import itemgetter

class DynamoDB:

    TABLE = 'brace'

    def __init__(self):
        self.dynamo = boto3.resource('dynamodb')

        self.table = None
        try:
            print 'connecting to DynamoDB'
            self.table = self.dynamo.create_table(
                TableName=self.TABLE,
                KeySchema=[
                    {
                        'AttributeName': 'key',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'key',
                        'AttributeType': 'S'
                    }

                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )

            # Wait until the table exists.
            self.table.meta.client.get_waiter('table_exists').wait(TableName=self.TABLE)
            print '   done'
        except Exception as e:
            print '   table exists, using existing table'
            self.table = self.dynamo.Table(self.TABLE)


    def put(self, data):
        data['time'] = str(time.time())
        self.table.put_item(
            Item=data
        )

    def batch_put(self, data):
        with self.table.batch_writer() as batch:
            for item in data:
                item['key'] = hashlib.md5(item['time'] + str(random.random())).hexdigest()
                batch.put_item(Item=item)

    def list(self):
        return self.table.scan()['Items']
    
    def pullit(self,ID):
        client = boto3.client('dynamodb')
        paginator = client.get_paginator("scan")
        x = [];
        for p in paginator.paginate(
                TableName = 'brace', 
                FilterExpression='label = :mylabel',
                ExpressionAttributeValues={':mylabel' : {'S':ID}}):
            x.append(p['Items'])
        return x
    
def process(data):
    Adata = []
    Bdata = []
    for i in data:
        if i['device'] == '20:73:6A:17:19:A2':
            Adata.append([[int(i['gyro_x']), int(i['gyro_y']), int(i['gyro_z'])],[int(i['accel_x']), int(i['accel_y']), int(i['accel_z'])],int(i['time'])])
        else:
            Bdata.append([[int(i['gyro_x']), int(i['gyro_y']), int(i['gyro_z'])],[int(i['accel_x']), int(i['accel_y']), int(i['accel_z'])],int(i['time'])])
    setlen = min(len(Adata), len(Bdata))
    Adata = Adata[0:setlen]
    Bdata = Bdata[0:setlen]
    return Adata, Bdata

def processNew(data):
    Adata = []
    Bdata = []
    for d in data:
        for i in d:
            if i['device']['S'] == '20:73:6A:17:19:A2':
                Adata.append([[int(i['gyro_x']['N']), int(i['gyro_y']['N']), int(i['gyro_z']['N'])],[int(i['accel_x']['N']), int(i['accel_y']['N']), int(i['accel_z']['N'])],int(i['time']['S'])])
            else:
                Bdata.append([[int(i['gyro_x']['N']), int(i['gyro_y']['N']), int(i['gyro_z']['N'])],[int(i['accel_x']['N']), int(i['accel_y']['N']), int(i['accel_z']['N'])],int(i['time']['S'])])
    setlen = min(len(Adata), len(Bdata))
    Adata = Adata[0:setlen]
    Bdata = Bdata[0:setlen]
    print len(Adata)
    return Adata, Bdata

def getacc(alisty,blisty):
    AaccX = [x[1][0] for x in alisty]
    AaccY = [x[1][1] for x in alisty]
    AaccZ = [x[1][2] for x in alisty]
    Aacc = [x[1] for x in alisty]
    BaccX = [x[1][0] for x in blisty]
    BaccY = [x[1][1] for x in blisty]
    BaccZ = [x[1][2] for x in blisty]
    Bacc = [x[1] for x in blisty]
    return AaccX, AaccY, AaccZ, Aacc, BaccX, BaccY, BaccZ, Bacc

def getgyro(alisty,blisty):  
    AgyroX = [x[0][0] for x in alisty]
    AgyroY = [x[0][1] for x in alisty]
    AgyroZ = [x[0][2] for x in alisty]
    Agyro = [x[0] for x in alisty]
    BgyroX = [x[0][0] for x in blisty]
    BgyroY = [x[0][1] for x in blisty]
    BgyroZ = [x[0][2] for x in blisty]
    Bacc = [x[0] for x in blisty]
    return AgyroX, AgyroY, AgyroZ, Agyro, BgyroX, BgyroY, BgyroZ, Bacc

def mergeDat(Accel,Gryo):
    wG = .2
    temp = []
    for i in range(0,len(Accel)):
        RxEst = ((Accel[i][0] + Gyro[i][0]*wG)/(1+wG))
        RyEst = ((Accel[i][1] + Gyro[i][1]*wG)/(1+wG))
        RzEst = ((Accel[i][2] + Gyro[i][2]*wG)/(1+wG))
        temp.append([RxEst,RyEst,RzEst])
    return temp

def plotit():
    fig = plt.figure()
    fig.suptitle('Classification Example', fontsize = 14, fontweight= 'bold')
    ax = fig.add_subplot(111)
    fig.subplots_adjust(top=0.925)
    ax.set_title('Live Experimental Data - Predicted/Actual State')

    ax.set_xlabel('Time (Minutes)',fontsize = 20)
    ax.set_ylabel('State',fontsize = 20)
    labels = ['Reclining','Horizontal','Sitting','Standing']

    line1 = ax.plot(ydata,truthdata,'r',label='Scripted Action', linewidth=2.0)
    line2 = ax.plot(ydata,testdata,'k',label='Predicted Action', linewidth=2.0)
    plt.yticks([0, 1, 2, 3], labels)
    plotXlength = max(ydata)[0]
    legend = ax.legend(loc='upper center')
    ax.axis([0, plotXlength, -0.5, 3.5])

    plt.legend()
    plt.show()
    
x = dynDB.pullit('Final_135D1')
Adata, Bdata = processNew(x)
x = dynDB.pullit('Final_H1')
Adata2, Bdata2 = processNew(x)
x = dynDB.pullit('Final_90D1')
Adata3, Bdata3 = processNew(x)
x = dynDB.pullit('Final_180D1')
Adata4, Bdata4 = processNew(x)
x = dynDB.pullit('Final_TestLive1')
AdataT, BdataT = processNew(x)

Asorted_listT = sorted(AdataT, key=itemgetter(2))
Bsorted_listT = sorted(BdataT, key=itemgetter(2))
Asorted_list = sorted(Adata, key=itemgetter(2))
Bsorted_list = sorted(Bdata, key=itemgetter(2))
Asorted_list2 = sorted(Adata2, key=itemgetter(2))
Bsorted_list2 = sorted(Bdata2, key=itemgetter(2))
Asorted_list3 = sorted(Adata3, key=itemgetter(2))
Bsorted_list3 = sorted(Bdata3, key=itemgetter(2))
Asorted_list4 = sorted(Adata4, key=itemgetter(2))
Bsorted_list4 = sorted(Bdata4, key=itemgetter(2))

import warnings
warnings.filterwarnings('ignore')
count = 0
for i in range(1001,2000):
    wp = clf.predict(comb[i])
    if (wp == [0]):
        count = count+1
    wp = clf.predict(comb2[i])
    if (wp == [1]):
        count = count+1
    wp = clf.predict(comb3[i])
    if (wp == [2]):
        count = count+1
    wp = clf.predict(comb4[i])
    if (wp == [3]):
        count = count+1
print count

comb = []
for i in range(0,(len(Aacc))):
    comb.append(sum([Aacc[i],Bacc[i]],[]))
comb2 = []
for i in range(0,(len(Aacc2))):
    comb2.append(sum([Aacc2[i],Bacc2[i]],[]))
comb3 = []
for i in range(0,(len(Aacc3))):
    comb3.append(sum([Aacc3[i],Bacc3[i]],[]))
comb4 = []
for i in range(0,(len(Aacc4))):
    comb4.append(sum([Aacc4[i],Bacc4[i]],[]))
combT = []
for i in range(0,(len(AaccT))):
    combT.append(sum([AaccT[i],BaccT[i]],[]))
    
combPlot = []
for i in range(0,(len(AaccT))):
    Ra = math.sqrt((AaccXT[i]**2)+(AaccYT[i]**2)+(AaccZT[i]**2))
    Rb = math.sqrt((BaccXT[i]**2)+(BaccYT[i]**2)+(BaccZT[i]**2))
    combPlot.append([Ra, Rb])
bigM = max(max(combPlot))
lilM = min(min(combPlot))

ya = [0]*1000#len()
yb = [1]*1000#len(Aacc)
yc = [2]*1000#len(Aacc)
yd = [3]*1000#len(Aacc)
useD = comb[0:1000]+comb2[0:1000]+comb3[0:1000]+comb4[0:1000]
useY = ya+yb+yc+yd
len(useY)
clf = svm.LinearSVC()
clf.fit(useD, useY)

ya = [0]*2000#len()
yb = [1]*2000#len(Aacc)
yc = [2]*2000#len(Aacc)
yd = [3]*2000#len(Aacc)
useY = ya+yb+yc+yd
useCV = comb[0:2000]+comb2[0:2000]+comb3[0:2000]+comb4[0:2000]
X_train, X_test, y_train, y_test = cross_validation.train_test_split(useCV,useY, test_size=0.4, random_state=0)

clf = svm.SVC(kernel='linear').fit(X_train, y_train)
clf.score(X_test, y_test) 

count = 1
fig = plt.figure()
left, width = .25, .5
bottom, height = .25, .5
right = left + width
top = bottom + height
labels = ['Sensor 1-X','Sensor 1-Y','Sensor 1-Z','Sensor 2-X','Sensor 2-Y','Sensor 2-Z']
#ax = fig.add_subplot(1,1,1)
#ax.xaxis.set_visible(False)
#ax.yaxis.set_visible(False)
#plt.suptitle('Test')su
#fig.set_visible('False')
fig.suptitle('Scatter-Plot Matrix of Accelerometer Data', fontsize=40)
for i in range(0,6):
    for j in range(0,6):
        if (i == j):
            ax = fig.add_subplot(6,6,count)
            ax.xaxis.set_visible(False)
            ax.yaxis.set_visible(False)
            ax.text(0.5*(left+right), 0.5*(bottom+top), labels[i],
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=27, color='k',
                transform=ax.transAxes)
            #ax.text(3,,labels[i],fontsize = 20)
            ax.axis([0, 0, 1, 1])
            count = count+1
        else:
            print count
            temp = np.asarray(useD)
            temp = temp[:,[j,i]]
            X = temp
            ax = fig.add_subplot(6,6,count)
            ax.xaxis.set_visible(False)
            ax.yaxis.set_visible(False)
            ax.scatter(X[:,0],X[:,1],c=y)
            count = count +1
#plt.title('Test')
plt.show()
