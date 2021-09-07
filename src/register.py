import PySimpleGUI as sg
import time
from backend import KeysDatabase, HashDatabase
from pass_check import pass_check
from cryptography.fernet import Fernet

def register():
    #----------------------------------------------------#
    # Setting Layout

    # Window's Theme
    sg.theme('DarkTeal12')

    # Set Window's options
    form = sg.FlexForm('Everything bagel' ,default_element_size=(40, 1))
    sg.SetOptions(font =("David", 15))


    # Rows
    # Row 2,3,4 - Frame of Databases
    column = [[sg.Column([[sg.Text('Hash', pad = (0,10)),sg.In(key = '-hash-'),sg.FolderBrowse(tooltip = "Select a folder to store database")],
           [sg.Text('Key'),sg.In(key = '-keys-'), sg.FolderBrowse(tooltip = "Select a folder to store database")],
           ])]]

    databses = [sg.Frame(' Databases ',column)]

    # Row 8 - Username Input
    username = [sg.Text('Username:'),
                sg.InputText(justification='left', size = (20,1), key = '-user-',pad=(5,10))]

    # Row 9 - Password Input
    password = [sg.Text('Password:' ,pad=(7,10)), 
                sg.InputText(justification='left', size = (20,1), key = '-pass-', password_char = '*'),
                sg.Button("Help", tooltip = "Press to open a window in which the \n password will be generated for you.\n Also, you will be able to check if the\n new password was not leaked before")]

    # Frame of Log In
    register = [sg.Frame(' Register ', [[sg.Column([username,password])]])]

    # Buttons
    buttons = [sg.Button("Register",size = (6,1), border_width = 0, pad = (20,3), button_color = ('white','#00b300'), tooltip = "Create new database"), 
               sg.Button("Exit",size = (6,1), border_width = 0, button_color = ('white','#ff6666'), tooltip = "Back to Log In")]

    layout = [[sg.T()], # Blank space
        
        # Database Frame
        databses,

        # Error - Database file
        [sg.T('', visible = True ,size=(29, 1), text_color = "red", key = '-derror-')], 

        # Horizontal Seperator
        [sg.T('_'*90)], 

        # Blank space
        [sg.T()], 

        # Register Frame
        register,

        # Error - Log In 
        [sg.T("",text_color = "White",size=(50, 1), justification='center', key='-Error-')],

        # Buttons 
        buttons,
        ]


    # Create Window
    window = sg.Window('Password Manager', layout,element_justification='center', size = (700,425),finalize = True)
    
    #----------------------------------------------------#

    #----------------------------------------------------#
    # Functions: 

    # 1. Log in Error
    def update_txt():
        window['-Error-'].update("Error: Username or password incorrect")

    #----------------------------------------------------#

    #----------------------------------------------------#
    # Event loop

    while True:

        # Read evens and Values
        event, values = window.read(timeout = 100)

        # Log In Event
        if event == 'Log In':
            update_txt()

        # Close window
        if event == sg.WIN_CLOSED or event == 'Exit': # if user closes window or clicks cancel
            break


        # Register a new database
        if event == "Register":

            # Read values
            [keys,hashes,usr,pwd] = values['-keys-'],values['-hash-'],values['-user-'],values['-pass-']

            # Ensure no values are missing
            if keys and hashes and usr and pwd:

                # Create keys.db
                keys_path = keys + "/keys.db" 
                k_db = KeysDatabase(keys_path)

                # Create hash.db
                hsh_path = keys + "/hash.db" 
                h_db = HashDatabase(hsh_path)

                
                # Generate a key
                key = Fernet.generate_key()

                # Encrypt password
                cipher_suite = Fernet(key)
                _hash = cipher_suite.encrypt(str.encode(pwd))

                # Insert user to both dbs. 
                # Also insert key to keys and hash to hash db
                k_db.insert_user(usr,key)
                h_db.insert_user(usr,_hash)

                # Quit while loop
                break
            
            # One or more files were missing
            else:
                sg.popup("Error","Some fields are missing")

        # Take user to Password Generator window
        if event == "Help":

            # Hide Register window
            window.Hide()

            # Show Password Generator
            _ , generated_pwd = pass_check()

            # Ensure Password Generator window is closed
            if _:

                # UnHide Register Window
                window.UnHide()

                # Refresh current window
                window.Refresh()

            # Ensure password was generated and update 
            # the text -pass- with the new  password
            if generated_pwd != "":
                window['-pass-'].update(generated_pwd)


    # Close Window
    window.close()
    return True

