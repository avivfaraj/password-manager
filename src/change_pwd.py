# Import Packages
import PySimpleGUI as sg
from generate_pass import generate_pass
from other import notes, date_time
from backend import KeysDatabase, HashDatabase
from encryption import encrypt, decrypt
from pass_check import pass_check

def change_pwd(current_pass):

    #----------------------------------------------------#
    # Setting Layout

    # Set Theme
    sg.theme('DarkTeal12')

    # Set Window Options - Default Font
    form = sg.FlexForm('Everything bagel' ,default_element_size=(40, 1))
    sg.SetOptions(font =("David", 15),slider_orientation='h')


    column_1 = sg.Column([[sg.T("Current Password: ")],[sg.T("New Password: ")],[sg.T("New Password: ")]])

    column_2 = sg.Column([[sg.In(password_char = "*", key = "-curr_pass-",size = (25,1))],
                          [sg.In(password_char = "*", key = "-new_pass_1-",size = (25,1))],
                          [sg.In(password_char = "*", key = "-new_pass_2-",size = (25,1))]])
    column_3 = sg.Column([[],[],[sg.Button("Help", tooltip = "Press to open a window in which the \n password will be generated for you.\n Also, you will be able to check if the\n new password was not leaked before")]
        ])

    column = [column_1,column_2,column_3]

    # Message on the bottom of the window
    message = [sg.Multiline(default_text='',size=(500, 20), 
                key = '-message-', font = ("David", 15))]

    # Buttons
    buttons = [sg.Button("Submit", bind_return_key = True,button_color = ('white','#00b300')),
               sg.Button("Exit",size = (6,1), border_width = 0, button_color = ('white','#ff6666')),
               ]

    # Window's Layour  = [[row1], [row2], [row3]]
    layout = [
        [sg.Text('Change Password',size=(20, 1), justification='center')],
        [sg.Text('')], # Vertical space
        column,
        [sg.Text('')], # Vertical space
        buttons,
        message,
        ]

    # Create a Window object with title 'Password Manager'
    window = sg.Window('Password Manager', layout,element_justification='center', size = (550,400),finalize = True)

    #----------------------------------------------------#
    
    #----------------------------------------------------#
    # Functions:

    def update_msg(msg):
        # Construct a new message
        new = notes(msg, values['-message-'])

        # Update msg element
        window['-message-'].update(new)

    def fields_values():
        # Save values in variables
        return values['-curr_pass-'], values['-new_pass_1-'],values['-new_pass_2-']


    # -----------------------------------------------------#

    # -----------------------------------------------------#
    # Event Loop

    new_1 = ""
    # Event Loop to process "events" (keys) and get the "values" of the inputs
    while True:

        # Reading events and values from window
        event, values = window.read(timeout = 100)

        # if user closes window or clicks cancel 
        # Quit loop
        if event == sg.WIN_CLOSED or event == 'Cancel' or event == 'Exit':
            break

        # Take user to Password Generator window
        if event == "Help":

            # Hide Register window
            window.Hide()

            # Show Password Generator
            _ , generated_pwd = pass_check()

            # Ensure Password Generator window is closed
            if _:

                window['-new_pass_1-'].update(generated_pwd)

                # UnHide Register Window
                window.UnHide()

                # Refresh current window
                window.Refresh()

        if event == 'Submit':
            curr, new_1, new_2 = fields_values()
            if curr and new_1 and new_2:
                if new_1 == new_2:
                    if current_pass == curr:
                        break
                    else:
                        update_msg("Invalid Password")
                else:
                    update_msg("New Password do not match")

    # Close the program
    window.close()

    return new_1
# change_pwd(1,"/Users/avivfaraj/Desktop/Project/5/keys.db",1,"/Users/avivfaraj/Desktop/Project/5/hash.db")