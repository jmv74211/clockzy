from clockzy.lib.db.database_interface import get_last_clock_from_user


IN_ACTION = 'in'
PAUSE_ACTION = 'pause'
RETURN_ACTION = 'return'
OUT_ACTION = 'out'


def user_can_clock_this_action(user_id, action):
    """Check if the user can clock an action taking into account the last previous clocking made.

    Args:
        user_id (str): User id who wants to make the clocking.
        action (str): Action to check.

    Returns
        Tuple(boolean, str): If the user can clock the action and the error message in negative case.
    """
    last_clocked_object = get_last_clock_from_user(user_id)

    white_list = {
        IN_ACTION: [PAUSE_ACTION, OUT_ACTION],
        PAUSE_ACTION: [RETURN_ACTION],
        RETURN_ACTION: [PAUSE_ACTION, OUT_ACTION],
        OUT_ACTION: [IN_ACTION]
    }

    # If no previous records and action is not IN
    if last_clocked_object is None and action != IN_ACTION:
        return (False, 'You do not have any previous registration, so the coherent thing is that you sign an entry'
                       '(`IN`)')
    # If no previous records but the action is IN
    elif last_clocked_object is None:
        return (True, None)

    last_clocked_action = last_clocked_object.action.lower()

    # If previous records but the action is wrong
    if action not in white_list[last_clocked_action]:
        return (False, f"Your last clock action was `{last_clocked_action.upper()}`, so you can not `{action.upper()}`"
                       ' clock action')

    return (True, None)
