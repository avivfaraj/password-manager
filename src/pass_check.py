# Import Packages
import PySimpleGUI as sg
from datetime import datetime
from check import check_pass, is_strong
from generate_pass import generate_pass
from other import notes, date_time

def pass_check():

    #----------------------------------------------------#
    # Setting Layout

    # Set Theme
    sg.theme('DarkTeal12')

    # Set Window Options - Default Font
    form = sg.FlexForm('Everything bagel' ,default_element_size=(40, 1))
    sg.SetOptions(font =("David", 15),slider_orientation='h')

    # Password row
    password = [sg.Text('Password:' ,pad=(7,0)), 
                sg.InputText(justification='left', size = (20,1),
                 key = '-pass-')]


    # Password Configuration Frame
    # Slider's label
    _ = (10,1)
    labels = [sg.Text('Numbers',size = _ ,justification='center'),
              sg.Text('Letters',size = _ ,justification='center'),
              sg.Text('Symbols',size = _ ,justification='center')]

    # Actual Frame
    sliders = [sg.Frame('Password Config.',[labels, # First row - Labels

              # Second row - Sliders
              [sg.Slider(range=(0, 10), size=(10, 15), default_value=4, key = '-num-'), 
               sg.Slider(range=(0, 10), size=(10, 15), default_value=4, key = '-str-'),
               sg.Slider(range=(0, 10), size=(10, 15), default_value=4, key = '-sym-')],

               # Third row - Button 
               [sg.T(' '  * 10), sg.T(' '  * 10),sg.T(' '  * 10),sg.T(' '  * 10),sg.T(' '  * 10),
                sg.Button("Generate Password")]])]


    # Message on the bottom of the window
    message = [sg.Multiline(default_text='',size=(500, 20), 
                key = '-message-', font = ("David", 15))]

    # Buttons
    buttons = [sg.Button("Submit", bind_return_key = False),
               sg.Button("Check Password", bind_return_key = True),
               sg.Button("Exit",size = (6,1), border_width = 0, button_color = ('white','#ff6666')),
               ]

    # Window's Layour  = [[row1], [row2], [row3]]
    layout = [
        [sg.Text('Password Generator',size=(20, 1), justification='center')],
        sliders,
        [sg.Text('')], # Vertical space
        password,
        [sg.Text('')], # Vertical space
        buttons,
        [],
        message,
        ]

    # Create a Window object with title 'Password Manager'
    window = sg.Window('Password Manager', layout,element_justification='center', size = (500,400),finalize = True)

    #----------------------------------------------------#
    
    #----------------------------------------------------#
    # Functions:

    # 1. Ensure password doesn't appear in database
    def check():

        # Password from user
        passw = values['-pass-']

        # Ensure pass was entered
        if passw != "":

            # Number of times this pass appears in database
            try:
                num = check_pass(passw)
            except:
                message("Error: No internet connection")
                return 1
    
            passw = "\'" +passw+"\'"

            # Password isn't appear on database
            if num == 0:
                msg = is_strong(passw)

            # Password appears on database at least once
            else:
                msg = passw + " was leaked! \n It appears " + str(num) +" times in database"
        
        # User didn't insert password
        else:
            msg = "Please enter password!"

        msg= notes(msg, values['-message-'])
        window['-message-'].update(msg)

        return 0

    # def message(msg):
    #     # Get date and time as string
    #     time = date_time()

    #     # Construct a message including date and time
    #     message = "*** " +time +"*** " + msg 

    #     # Construct a message including the previous ones
    #     old = values['-message-']
    #     new = message +"\n" + old

    #     window['-message-'].update(new)
        

    # # 2. Return string of date and time
    # def date_time():
    #     time = datetime.now()
    #     return time.strftime("%H:%M:%S")


    def generate_pwd():

        # Number of letters, numbers and symbols in the generated password
        letters = int(values['-str-'])
        nums = int(values['-num-'])
        symbols = int(values['-sym-'])

        # Total characters in the password
        total = letters + nums + symbols 

        # Ensure total character is greater than 0
        if total > 0:

            # Update text pass with the new generated password 
            window['-pass-'].update(generate_pass(letters,nums,symbols))

            # Message to be displayed to the user
            msg = "Password was successfuly generated"

            # Ensure total is greater than 8.
            # If not than a message recommending more than 8 chars is displayed
            if total < 8:
                msg = f"Password was successfuly generated, but more than 8 characters is recommended (got {total})"

        # Inform the user 
        else:
            msg = "No password was generated"

        # Display the message by updating text (-pass-)
        # sg.Print(values['-message-'])
        msg = notes(msg, values['-message-'])
        window['-message-'].update(msg)

    # -----------------------------------------------------#

    # -----------------------------------------------------#
    # Event Loop

    # Initialize pwd
    pwd = ""
    
    # Event Loop to process "events" (keys) and get the "values" of the inputs
    while True:

        # Reading events and values from window
        event, values = window.read(timeout = 100)

        # Execute a code for a specific event
        if event == 'Check Password':
            check()

        # if user closes window or clicks cancel 
        # Quit loop
        if event == sg.WIN_CLOSED or event == 'Cancel' or event == 'Exit':
            break

        # if event == "Register":
        #     update_txt()

        if event == 'Generate Password':
            generate_pwd()

            # password = sg.popup_get_text(
            # 'Password: (type gui for other window)', password_char='*')
        if event == "Submit":
            pwd = values['-pass-']
            break

    # Close the program
    window.close()

    return True, pwd
