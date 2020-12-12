import time
import requests

class Discord():
    API = "https://discord.com/api/"


    def __init__(self, token, my_id=None, cooldown=1):
        """ Initialize secrets and cooldown between requests """
        self.token = token
        self.headers = {"Authorization": token}
        self.myself = my_id
        self.cooldown = cooldown


    def _handle_json(self, json):
        """ Check if valid json and handles API errors """
        if 'message' in json:
            raise Exception(json)
        else:
            return json


    def _get(self, url):
        return requests.get(f'{self.API}{url}', headers=self.headers)


    def _post(self, url, data):
        return requests.post(f'{self.API}{url}', headers=self.headers, json=data)


    def _delete(self, url):
        time.sleep(self.cooldown)
        return requests.delete(f'{self.API}{url}', headers=self.headers)


    def _update(self, url):
        return requests.update(f'{self.API}{url}', headers=self.headers)


    def delete_dm(self, channel_id, before=None, keep_count=False, strike=False):
        """ Delete all messages in DM "before" message id
        Keeps the 3 last messages if no "before" submitted
        Yields nb_deleted and nb_total each loop"""
        if not keep_count:
            self.nb_deleted = self.total = 0

        r = self._get(f'channels/{channel_id}/messages?imit=100{f"&{before=:}" if before else ""}')
        json = self._handle_json(r.json())
        self.total += len(json)
        last_id = next((msg['id'] for msg in reversed(json) if msg['author']['id'] != self.myself), None)
        messages = [msg['id'] for msg in json if msg['author']['id'] == self.myself]
        messages = messages if before else messages[3:]
        for id in messages:
            self._delete(f'channels/{channel_id}/messages/{id}')
            self.nb_deleted += 1
            yield self.nb_deleted, self.total
        if not strike:
            for d, t in self.delete_dm(channel_id, last_id, keep_count=True, strike=not messages):
                yield d, t



if __name__ == '__main__':
    import secret
    token = secret.TOKEN
    me = secret.MY_ID
    channel = secret.CHANNEL_ID
    d = Discord(token, me)
    for _, __ in d.delete_dm(channel):
        pass
