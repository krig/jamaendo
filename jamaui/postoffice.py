# message central

class PostOffice(object):
    class Client(object):
        def __init__(self):
            self.tags = {}
        def has_tag(self, tag):
            return tag in self.tags
        def notify(self, tags, data):
            for tag in tags:
                cb = self.tags.get(tag)
                if cb:
                    cb(data)
        def register(self, tag, callback):
            self.tags[tag] = callback

    def __init__(self):
        self.clients = {}

    def notify(self, tags, data):
        if not isinstance(tags, list):
            tags = [tags]
        for client in clients:
            client.notify(tags, data)

    def register(self, client_id, tag, callback):
        client = self.clients.get(client_id)
        if not client:
            client = Client()
            self.clients[client_id] = client
        client.register(tag, callback)

postoffice = PostOffice()


