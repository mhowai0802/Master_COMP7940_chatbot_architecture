import requests
import configparser

from config import config

class HKBU_ChatGPT:
    def __init__(self):
        self.config = config

    def submit(self, message):
        conversation = [{"role": "user", "content": message}]
        url = (
            self.config['CHATGPT']['BASICURL'] +
            "/deployments/" +
            self.config['CHATGPT']['MODELNAME'] +
            "/chat/completions/?api-version=" +
            self.config['CHATGPT']['APIVERSION']
        )
        headers = {
            'Content-Type': 'application/json',
            'api-key': self.config['CHATGPT']['ACCESS_TOKEN']
        }
        payload = {'messages': conversation}
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            return f'Error: {response.status_code} - {response.text}'