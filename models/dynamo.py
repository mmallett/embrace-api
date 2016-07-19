import boto3
import time
import hashlib
import random

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
