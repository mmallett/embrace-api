import boto3
import time

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
                        'AttributeName': 'time',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'time',
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

    def list(self):
        return self.table.scan()['Items']
