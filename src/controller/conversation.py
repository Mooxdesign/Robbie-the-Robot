from modules.conversation import ConversationModule

class ConversationController:
    def __init__(self, debug=False):
        self.conversation = ConversationModule(debug=debug)

    def chat(self, text):
        return self.conversation.chat(text)

    def cleanup(self):
        self.conversation.cleanup()
