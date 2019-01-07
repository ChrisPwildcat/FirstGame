import sys
from cp_game.definitions import Items, SpecialItem, Room

try:
    raw_input
except NameError:
    raw_input = input  # Py3 compat

EXIT_COMMANDS = ('exit', 'quit', )

lint = Items(name='lint', observe='This is a small ball of salmon colored lint.')
pretty_lint = SpecialItem(name='lint', observe='This is really pretty lint')

#print(pretty_lint.full_text())



long_description = (
    'You are standing in a oblong room with walls that curve into the floor '
    'and ceiling. There are no corners. The walls appear to be made of smooth '
    'stone. There are exits to the north, south, east, and west.'
)
StartingRoom = Room(description=long_description)
NorthRoom1= Room(y=1, exits=['south'], description='This room is identical to the room you just exited, with only one exit to the south.')
SouthRoom1= Room(y=-1, exits=['north'], description='This room is identical to the room you just exited, with only one exit to the north.')
EastRoom1= Room(x=1, contains=lint.name, exits=['west'], description='This room is identical to the room you just exited, with only one exit to the west.')
WestRoom1= Room(x=-1, exits=['east'], description='This room is identical to the room you just exited, with only one exit to the east.')

game_map = {
    (0,0):StartingRoom,
    (0,1):NorthRoom1,
    (0,-1):SouthRoom1,
    (1,0):EastRoom1,
    (-1,0):WestRoom1,
}

class Player(object):
    locationx = 0
    locationy = 0

    @property
    def location(self):
        location = game_map[(self.locationx,self.locationy)]
        return location

    def __init__(self, name):
        self.name = name.title()

    def look(self):
        print(self.location.description)
        if self.location.contains is '':
            return(None)
        else:
            print('You see the following: ')
            print(self.location.contains)

    def take(self,x):
        if self.location.contains is '':
            print('There isn\'t anything to take!')
        elif x in self.location.contains:
            print('You take {}.'.format(x))
        else:
            print('There is no {} here.'.format(x))

    def examine(self,x):
        print(lint.observe)

    def move_north(self):
        if 'north' in self.location.exits:
            self.locationy += 1
            print('You move northward.')
        else:
            print('Inconceivable!')

    def move_south(self):
        if 'south' in self.location.exits:
            self.locationy -= 1
            print('You move southward.')
        else:
            print('Inconceivable!')

    def move_east(self):
        if 'east' in self.location.exits:
            self.locationx += 1
            print('You move eastward.')
        else:
            print('Inconceivable!')

    def move_west(self):
        if 'west' in self.location.exits:
            self.locationx -= 1
            print('You move westward.')
        else:
            print('Inconceivable!')

def trim_input(value):
    """Takes any user input and trims it up for easier parsing."""
    value = value.strip()  # Cleans any whiltespace from the text
    value = value.lower()  # Make it lowercase
    return value

def run_game():
    """The main game event loop."""
    name = raw_input('Enter your name: ')
    name = trim_input(name)
    player = Player(name)
    print('Welcome to the game!')
    print('--------------------')
    print('It is nice to meet you {}!'.format(player.name))
    print('Allowed commands are:')
    print('exit - quit the game')
    print('look - see where you are')
    print('take [item] - take possession of an item')
    print('examine [item] - examine an item')
    print('move west - move westerly')
    print('move right - move easterly')
    print('move north - travel northward')
    print('move south - travel southward')
    print('mystery commands - You\'ll have to experiment to determine these!')
    print('')
    while True:
        data = raw_input('>>> ')
        data = trim_input(data)
        if data == 'move west':
            player.move_west()
        elif data == 'move east':
            player.move_east()
        elif data == 'move north':
            player.move_north()
        elif data == 'move south':
            player.move_south()
        elif data == 'look':
            player.look()
        elif data == 'exit':
            print('Goodbye {}'.format(player.name))
            sys.exit(0)
        elif data == 'think':
            print('You think very long and very hard about what you have done, you sick bastard.')
        elif 'apologize' in data:
            print('That isn\'t necessary.')
        elif 'why' in data:
            print('Because I said so.')
        elif 'take' in data:
            data = data[5:]
            player.take(data)
        elif 'examine' in data:
            data = data[8:]
            player.examine(data)
        elif 'fuck' in data:
            print('I don\'t know how to fuck!')
        else:
            print('I don\'t have a clue what "{}" means....'.format(data))

# Don't worry about this mess now, leave it as is.
if __name__ == '__main__':
    try:
        run_game()
    except KeyboardInterrupt:
        sys.stderr.write(
            u"\n\u2717 Operation canceled by user.\n"
        )
        sys.exit(1)

def main():
    try:
        run_game()
    except KeyboardInterrupt:
        sys.stderr.write(
            u"\n\u2717 Operation canceled by user.\n"
        )
        sys.exit(1)
