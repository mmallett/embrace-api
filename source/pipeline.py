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
