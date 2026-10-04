#!/usr/bin/env python3
###########################################################################
# Prorgammed by: Sophia Castellarin                                       #
# Thursday, August 30, 2012                                               #
# Program Desciption: A text adventure game                               #
#                                                                         #
# Refactored: the story dialog, item checks, party checks, combat and     #
# world logic now live in the `game` package; this file is only the       #
# entry point.  All narrative text is unchanged.                          #
###########################################################################
import readline

from game.engine import main
from game.story import HOW_TO_PLAY, NOT_UNDERSTOOD, WELCOME

print(WELCOME)
opt = input()
if opt == 'start':
    main()
elif opt == 'how to play':
    print(HOW_TO_PLAY)
    if input() == 'start':
        main()
else:
    print(NOT_UNDERSTOOD)
