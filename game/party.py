"""Party checks.  These read the live party list on the state object, so a
story beat that changes the party is immediately visible to checks."""


def check_party(state, name):
    return name in state.party


def add_member(state, name):
    if not check_party(state, name):
        state.party.append(name)


def remove_member(state, name):
    if check_party(state, name):
        state.party.remove(name)
        return True
    return False
