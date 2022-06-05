'''
fixture here has a specific meaning. It means that mechanism to put the DUT in place for testing. In a CRC sense its responsibility
is to make the DUT mechanically ready. This is obvious from the minimal functions it needs to implement
'''
class Fixture(object):
    '''this is a dummy fixture implmentation.
    real fixtures dont' need to necessarily inherit from this class but they should implment the same functions
    '''
    def __init__(self):
        self.is_open = False
        self.is_close = True
        self.is_engaged = False
        self.is_disengaged = False

    #These should be a non-blocking calls if it takes a while. Client should use the is_XXX for the status
    def open(self):
        #in a real implementation, on_open may not be called here because we don't want open() to be a blocking call
        self.on_open()
        self.is_open = True
        self.is_engaged = False
        self.is_disengaged = False
        self.is_close = False
        return True
    def close(self):
        self.on_close()
        self.is_close = True
        self.is_engaged = False
        self.is_disengaged = False
        self.is_open = False
        return
    def engage(self):
        self.on_engage()
        self.is_engaged = True
        self.is_disengaged = False
        self.is_close = True
        self.is_open = False
        return
    def disengage(self):
        self.on_disengage()
        self.is_engaged = False
        self.is_disengaged = True
        self.is_close = False
        self.is_open = True
        return

    def is_open(self):
        return True

    def is_close(self):
        return True
    def is_engaged(self):
        return
    def is_disengaged(self):
        return True

    listeners = []
    #the fixture implment these events. Implement the listener interface
    #and add yourself to the listener list if you want to subscriber to the events
    def on_open(self):
        for listener in self.listeners:
            listener.on_open()
    def on_close(self):
        for listener in self.listeners:
            listener.on_close()
    def on_engage(self):
        for listener in self.listeners:
            listener.on_engage()
    def on_disengage(self):
        for listener in self.listeners:
            listener.on_disengage()
