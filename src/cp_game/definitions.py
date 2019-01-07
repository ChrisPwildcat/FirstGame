class Room(object):

    def __init__(self, x=0, y=0, description='', contains='', exits=None):

        self.x = x
        self.y = y
        self.description = description
        self.contains = contains
        if exits is None:
            self.exits = ['north','south','east','west']
        else:
            self.exits = exits

class Items(object):

    def __init__(self, name='', observe=''):
        self.name = name
        self.observe = observe

class SpecialItem(Items):

    def full_text(self):
        return "{} - {}".format(self.name, self.observe)
