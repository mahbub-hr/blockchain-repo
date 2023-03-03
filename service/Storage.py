class Storage:
    def __init__(self):
        self.resource_path = "resources/"


    def create_ngrok_log_file(self):
        f = open(self.resource_path + "ngrok.log", 'w')
        self.ngrok_log_file = f
        return f
