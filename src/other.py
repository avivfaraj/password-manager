from datetime import datetime


def notes(new_msg, old_message):
    # Get date and time as string
    time,date = date_time()

    # Construct a message including date and time
    message = "*** " +time +"*** " + new_msg 

    # Construct a message including the previous ones
    # old = values['-message-']
    new = message +"\n" + old_message

    return new
    

# 2. Return string of date and time
def date_time():
    time = datetime.now()
    return time.strftime("%H:%M:%S"),time.strftime("%d/%m/%Y")
