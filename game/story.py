"""Story dialog.  Every string here is byte-for-byte the original narrative
text from textAdventure.py; only the I/O goes through the io object."""

WELCOME = "\n \n \n \nHello and welcome to the game.  It is about you!  Also about zombies.  If this is your first time playing you should type in 'how to play' so that you can learn to play the game.  If you played the game before, took a look at the code before playing or are exceptional at guessing, type in 'start' to begin."

HOW_TO_PLAY = "\n\n\n\nHOW TO PLAY:  \n\nMAIN CONTROLS:  There are several functions you can do in this game.  To move around you simply enter which way you want to go.  For example, if you want to go left, type in \"left\".  It is important to note that your movements are traked using a grid system.  You can find your position in the x or y plane at any time by inputting \"pos x\" or \"pos y\".\nTo print a map so you can know where in the world you are, input \"map\".  It will show you a map and tell you where you are.\nAs you might assume, you are carrying stuff.  To see what you are holding you can input \"check items\".  You can also drop stuff by inputting \"drop\" or check if you can pick anything up from your environment by inputting \"search\".\nIf you want to know how many health points you have, type in \"health\"   \n \nFIGHTING:  You can also fight zombies in this game.  At any one time you can fight one or two zombies but keep in mind, your friend in fat and lazy and does not help you while you fight.  First you will be told how many zombies you are fighting.  Then you can choose to fight by typeing in \"yes\" or you can choose to get away from the fight by typeing in \"run\" and \"no\" to do niether.  To choose which zombie you wish to attack, press \"1\" for zombie one, or \"2\" for zombie two.\nIf your hp is low after fighting some zombies you can eat or drink by typing in \"eat\" or \"drink\".  Remeber that you need to have food or water for you do this... unless you are a wizard then you just need to remeber aquaerupto.  \nThat is it.  Also, sometimes you can kill a zombie into negative hp.  Don't worry about that, you are just that awesome."

NOT_UNDERSTOOD = "Sorry, a zombie bit off the part of the code that was suppose to understand that.  HAAAA SHUTING DOWN."


# Introduction to the game
def d_intro(io):
    io.say("\nYou are in a basement, a bit confued.  You have just been playing video games for 47.3 hours, only pausing to dail up the pizza delivery guy to get you another extra large pizza with only cheese.  *SHPAOOSH.\n")
    io.ask()
    io.say("Dammit, there goes to super cool gaming system (play system 3.5.7).\n")
    io.ask()
    io.say("*Turn on the news \n \"...and now we bring you breaking news:  zombies have taken over the local Walemart.  Now the only safe place to hide is the island...\" *RING.")
    io.ask()
    io.say("You:\"Hello\"\n")
    io.ask()
    io.say("Fred:\"Dude, there is a zombie outbreak\"\n")
    io.ask()
    io.say("You: \"I know, what are we going to do\"\n")
    io.ask()
    io.say("Fred: \"meet me at the park across the street\"\n")
    io.ask()
    io.say("You: \"Alright\"\n")


# When you reach outside
def d_outside(io):
    io.say("\nThere is nobody outside... wait, there is someone at the park across the street... perhaps it is Fred")
    io.ask()
    io.say("Dude across the street: \"Hey, come quickly, there are zombies and when they come I won't help you\"\n")
    io.ask()


# When you get to the park
def d_park(io):
    io.say("\nFred: \"Dude, where have you been.  I've been waiting for you...\"")
    io.ask()
    io.say("\"...  lets go.  We need to get to the store house.  It is safe there.\"")
    io.say("END PART I")
