"""Fighting.  Returns the outcome ("win", "lose" or "run") instead of
killing the process with quit(), so the engine decides what happens next:
a loss ends the game, a win or escape returns to normal play."""
from game import items

WIN = "win"
LOSE = "lose"
RUN = "run"


def fight(state, io, rng):
    # Player stats: attack (a), defence (d) and health (hp).
    you_a = 5.0
    you_d = 7.0
    # Main player's friend
    fred_a = 9.0
    fred_d = 5.0
    fred_hp = 10.0
    # Zombie one
    zomb_a_one = 5.0
    zomb_d_one = 4.0
    zomb_hp_one = 7.0
    # Zombie two
    zomb_d_two = 6.0
    zomb_hp_two = 7.0

    # Determines if there are any weapons/ powerups
    if items.check_items(state, 'foam nunchuks'):
        you_a += 1.5
        you_d += 0.5
    if items.check_items(state, 'stick'):
        you_a += 3.0
        you_d += 1.0
    if items.check_items(state, 'pillow'):
        you_a += 0.5
        you_d += 2.0

    num_zomb = rng.randint(1, 2)    # Determines the number of zombies
    turn = 0
    fighting = True
    io.say("watch out, there are " + str(num_zomb) + " zombies!")

    while fighting:
        turn += 1
        go = turn % 2

        # If the number of zombies is less than three this will set the hp of the other zombies to zero
        if num_zomb == 1:
            zomb_hp_two = 0

        # When you kill the zombie(s)
        if zomb_hp_one <= 0 and zomb_hp_two <= 0:
            io.say("you defeted the brain sucker")
            return WIN
        # When the zombie(s) kills you: signal game over instead of quitting
        if state.you_hp <= 0:
            io.say("FAILed, no banana bread for you")
            state.game_over = True
            return LOSE

        if go == 1:    # Players turn
            super_att = rng.randint(1, 7)  # Determines the strength of att
            if super_att == 1:
                you_a = 15.0
            elif super_att == 2:
                you_a = 10.0
            elif super_att == 3:
                you_a = 30.0
            elif super_att == 4:
                you_a = 1.0
            else:
                you_a = 5.0

            # Recives input from the user regarding attack
            opt = io.ask("do you wish to attack\n")
            if opt == 'yes':
                # Recives input from the user regarding which zombie to attack
                dev = io.ask("which zombie would you like to attack\n")
                if dev == "1":
                    hit = you_a / zomb_d_one
                    zomb_hp_one -= hit
                    io.say("zombie 1 has " + str(int(zomb_hp_one)) + " hp left")
                elif dev == "2":
                    hit = you_a / zomb_d_two
                    zomb_hp_two -= hit
                    io.say("zombie 2 has " + str(int(zomb_hp_two)) + " hp left")
                else:
                    io.say("invalid input -> looks like you loose your turn")
            elif opt == 'no':
                io.say("you do not attack")
            # If the user chooses to not fight there is a on in five chance that they will be able to run away
            elif opt == 'run':
                r = rng.randint(0, 5)
                if r == 0:
                    io.say("you got away")
                    return RUN
                else:
                    io.say("son of very poop face, the zombies caught up to you")
            else:
                io.say("Invalid input.  I'm just going to take that as a no.")

        else:          # Computer turn
            att = rng.randint(1, 5)        # Determines if zombie attacks
            super_att = rng.randint(1, 3)  # Determines the strength of att
            if super_att == 1:
                zomb_a_one = 20.0
            elif super_att == 2:
                zomb_a_one = 2.0
            else:
                zomb_a_one = 6.0

            # Zombie attacks
            if att in (1, 2, 3):
                hit = zomb_a_one / you_d
                state.you_hp -= hit
                io.say("\nA zombie attacked and you have " + str(int(state.you_hp)) + " hp left")
            # Zombie does not attack
            else:
                io.say("\nThe zombie missed")
