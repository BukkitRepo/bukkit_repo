from bukkitrepo import CONFIG
import json
import requests


class Message(object):
    def __init__(self, subject, content, from_email, from_name, to_email, to_name):
        self.mandrill_send_endpoint = 'http://mandrillapp.com/api/1.0/messages/send.json'
        self.mandrill_key = CONFIG['mandrill_api_key']

        self.subject = subject
        self.content = content
        self.from_email = from_email
        self.from_name = from_name
        self.to_email = to_email
        self.to_name = to_name

    def send(self):
        payload = {
            'key': self.mandrill_key,
            'message': {
                'html': self.content,
                'subject': self.subject,
                'from_email': self.from_email,
                'from_name': self.from_name,
                'to': [
                    {
                        'email': self.to_email,
                        'name': self.to_name
                    }
                ]
            }
        }

        headers = {
            'Content-Type': 'application/json'
        }

        requests.post(self.mandrill_send_endpoint, data=json.dumps(payload), headers=headers)
