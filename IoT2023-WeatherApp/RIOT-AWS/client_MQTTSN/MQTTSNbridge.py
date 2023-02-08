from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import MQTTSNclient
import json
import boto3

# connection to DynamoDB and access to the table EnvironmentalStationDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
dynamoTable = dynamodb.Table('WeatherData')
jsonP = ''

# clients for MQTT and MQTTS
MQTTClient = AWSIoTMQTTClient("MQTTSNbridge")
MQTTSNClient = MQTTSNclient.Client("bridge", port=1885)

class Callback:
  # function that replies a message from the MQTTSN broker to the MQTT one
  # and inserts into the database the message just arrived
  def messageArrived(self, topicName, payload, qos, retained, msgid):
      message = payload.decode("utf-8")
      jsonP = json.loads(message) 
      print(topicName, message)
      MQTTClient.publish(topicName, message, qos)
      dynamoTable.put_item(Item=jsonP)
      return True

# path that indicates the certificates position
path = "../certs/"

# configure the access with the AWS MQTT broker
MQTTClient.configureEndpoint("a3d6q5aedgtyoc-ats.iot.us-east-2.amazonaws.com", 8883)
MQTTClient.configureCredentials(path+"AmazonRootCA1.crt",
                                path+"1581-private.pem.key",
                                path+"1581-certificate.pem.crt")

# configure the MQTT broker
MQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
MQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
MQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
MQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# register the callback
MQTTSNClient.registerCallback(Callback())

# make connections to the clients
MQTTClient.connect()
MQTTSNClient.connect()

# let's ask the user which stations he wants to subscribe to
# RiotOS MQTTSN clients publish to the topic sensor/station + id
# the user will define only the id
station_ids = ""
print("Ingrese el ID de la estación, uno por uno, de las que desee suscribir...")
print("Escriba 'stop' para detener el proceso.\n")
while True:
    current_id = input("")
    if current_id == 'stop':
        break
    else:
        station_ids += current_id + " "

# subscribe to the topics choosen by the user
for id in station_ids:
    MQTTSNClient.subscribe("sensor/station" + id)
print("Suscrito a las estaciones con los ID: " + station_ids)

# cycle that wait for a command to close the program
while True:
    if input("Escriba 'quit' para salir del programa.\n")=="quit":
        break

# disconnect from the clients
MQTTSNClient.disconnect()
MQTTClient.disconnect()
