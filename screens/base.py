class Screen:
    def __init__(self, app):
        self.app = app

    def enter(self):
        pass

    def leave(self):
        pass

    def interrupt(self):
        """A phase finished while this screen was showing."""
        pass

    def on_button(self, key, kind, now):
        pass

    def animating(self, now):
        return False

    def draw(self, now):
        pass
