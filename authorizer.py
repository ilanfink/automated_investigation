import json
import os

ip_key = os.environ['ip_key']

def bnsecAuthorizer(event, context):
   if (event['headers']['authorization'] == ip_key):
       response = {
           "isAuthorized": True
       }
       return response
   else:
        response = {
            "isAuthorized": False
        }
        return response
