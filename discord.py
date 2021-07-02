import time
import requests

class Discord():
    API = "https://discord.com/api/"


    def __init__(self, token, my_id=None, cooldown=1, debug=False):
        """ Initialize secrets and cooldown between requests """
        self.token = token
        self.headers = {"Authorization": token}
        self.myself = my_id
        self.cooldown = cooldown
        self.debug = debug


    def _handle_json(self, json):
        """ Check if valid json and handles API errors """
        if 'message' in json:
            raise Exception(json)
        else:
            return json


    def _get(self, url):
        return requests.get(f'{self.API}{url}', headers=self.headers)


    def _post(self, url, data):
        if not self.debug:
            return requests.post(f'{self.API}{url}', headers=self.headers, json=data)


    def _delete(self, url):
        time.sleep(self.cooldown)
        if not self.debug:
            return requests.delete(f'{self.API}{url}', headers=self.headers)


    def _update(self, url):
        if not self.debug:
            return requests.update(f'{self.API}{url}', headers=self.headers)


    def is_message(self, msg, with_pinned=False):
        """ Check if a message is not a call and if it's pinned """
        return not msg.get('call') and (not msg['pinned'] or with_pinned)
        
        
    def is_my_message(self, msg, with_pinned=False):
        """ Check if a message is mine, not a call and if it's pinned """
        return msg['author']['id'] == self.myself and self.is_message(msg, with_pinned)


    def count_dm(self, channel_id):
        my_total = total = 0
        before = None
        while True:
            r = self._get(f'channels/{channel_id}/messages?limit=100{f"&{before=:}" if before else ""}')
            json = self._handle_json(r.json())
            total += sum((1 for msg in json if self.is_message(msg, with_pinned=True)))
            before = next((msg['id'] for msg in reversed(json)), None)
            my_total += sum((1 for msg in json if self.is_my_message(msg)))
            if before is None:
                return my_total, total


    def delete_dm(self, channel_id, before=None, keep_count=False, strike=False):
        """ Delete all not pinned messages in DM "before" message id
        Keeps the 3 last messages if no "before" submitted
        Yields nb deleted, nb total to delete and nb total each loop"""
        if not keep_count:
            self.nb_deleted = 0
            self.my_total, self.total = self.count_dm(channel_id)
            if not before:
                self.my_total -= 3

        r = self._get(f'channels/{channel_id}/messages?limit=100{f"&{before=:}" if before else ""}')
        json = self._handle_json(r.json())
        last_id = next((msg['id'] for msg in reversed(json) if msg['author']['id'] != self.myself), None)
        messages = [msg['id'] for msg in json if self.is_my_message(msg)]
        messages = messages if before or self.debug else messages[3:]
        for id in messages:
            self._delete(f'channels/{channel_id}/messages/{id}')
            self.nb_deleted += 1
            yield self.nb_deleted, self.my_total, self.total
        if not strike:
            for d, m, t in self.delete_dm(channel_id, last_id, keep_count=True, strike=not messages):
                yield d, m, t


def delete_app():
    import secret
    token = secret.TOKEN
    me = secret.MY_ID
    channel = secret.CHANNEL_ID
    d = Discord(token, me, debug=False)
    for deleted, my_total, total in d.delete_dm(channel):
        print(f'''\
Total messages in channel: {total}
Deleted: {deleted} / {my_total}
Time remaining: {d.cooldown * (my_total - deleted)}s\x1B[0K''', end='\x1B[2A\r')
    print('\n\n')

if __name__ == '__main__':
    delete_app()
