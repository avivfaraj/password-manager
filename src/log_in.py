# """PySimpleGUI The Complete Course Lesson 7 - Multiple Windows"""  
import PySimpleGUI as sg
from register import register
from pass_check import pass_check
from backend import KeysDatabase, HashDatabase
from cryptography.fernet import Fernet
from main import main
from encryption import encrypt, decrypt

# Window's Theme
sg.theme('DarkTeal12')

# Set Window's options
form = sg.FlexForm('Everything bagel' ,default_element_size=(40, 1))
sg.SetOptions(font =("David", 15))


# Rows
# Row 2,3,4 - Frame of Databases
column = [[sg.Column([[sg.Text('Hash', pad = (0,10)),sg.In(key = '-hash-'),sg.FileBrowse()],
       [sg.Text('Key'),sg.In(key = '-keys-'), sg.FileBrowse()],
       ])]]

databses = [sg.Frame(' Databases ',column)]

# Row 8 - Username Input
username = [sg.Text('Username:'),
            sg.InputText(justification='left', size = (20,1), key = '-user-',pad=(5,10))]

# Row 9 - Password Input
password = [sg.Text('Password:' ,pad=(7,10)), 
            sg.InputText(justification='left', size = (20,1), key = '-pass-', password_char = '*')]

# Frame of Log In
log_in = [sg.Frame(' Log In ', [[sg.Column([username,password])]])]

# Buttons
buttons = [sg.Button("Register",size = (6,1), border_width = 0, pad = (10,3), button_color = ('white','#00b300'), tooltip = "Create a new database"),
           sg.Button("Log In",size = (6,1), border_width = 0, pad = (20,3), button_color = ('white','#00b300')),
           sg.Button("Exit",size = (6,1), border_width = 0, button_color = ('white','#ff6666'), tooltip = "Close Program")]

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
    log_in,

    # Error - Log In 
    [sg.T("",text_color = "White",size=(50, 1), justification='center', key='-Error-')],

    # Buttons 
    buttons,
    ]


# Create Window
window = sg.Window('Log In', layout,element_justification='center', size = (700,440),finalize = True)


# Functions: 
# 1. Log in Error
def update_txt():
    window['-Error-'].update("Error: Username or password incorrect")

# 2. Database file Error
def db_error(keys, _hash):

    # Ensure keys or hash files are .db
    if keys[len(keys)-3:] != ".db" or _hash[len(_hash)-3:] != ".db":

        # Show an error if one file is not a database
        window['-derror-'].update('Error: File Must Be a Database (.db)!')

    # Delete error if the files are .db
    else:
        window['-derror-'].update('')


# Previous databse files path
prev = ["",""]

# 
# empty = False

# Event loop
while True:

    # Read evens and Values
    event, values = window.read(timeout = 100)

    # Log In Event
    if event == 'Log In':

        if values['-keys-'] and values['-hash-'] and values['-user-'] and values['-pass-']:
            # Connect to database
            db_key = KeysDatabase(values['-keys-'])
            db_hash = HashDatabase(values['-hash-'])

            # Search users in both databases
            hash_usr = db_hash.search_user(username = values['-user-'])
            key_usr= db_key.search_user(username = values['-user-'])

            # Ensure list is not empty
            if hash_usr and key_usr:

                # Take first element
                hash_usr = hash_usr[0]
                key_usr = key_usr[0]

                # Ensure username is equal in both tables (both dbs)
                if key_usr[1] == hash_usr[1]:

                    # #### Repeat
                    # # Define Cipher Suite using the key
                    # cipher_suite = Fernet(key_usr[2])

                    # # Decrypt password
                    # unciphered_text = str(cipher_suite.decrypt(hash_usr[2])).replace('b','').replace('\'','').replace("\"","")
                    unciphered_text = decrypt(key_usr[2],hash_usr[2])

                    # Ensure decrypted password equal the password entered by the user
                    # In this case - Log In Successfully!
                    if unciphered_text == values['-pass-']:
                        window.close()
                        main(key_usr[0], values['-keys-'], hash_usr[0], values['-hash-'])
                        
                         

                    # Error - password incorrect
                    else:
                        sg.popup_error("Username and/or password are incorrect!", title = "Error!")

                # Error - Username incorrect
                else:
                    sg.popup_error("Username and/or password are incorrect!",title = "Error!")

            # Error - No username found in database
            else:
                sg.popup_error("No username found!",title = "Error!")
        


    # Close window
    if event == sg.WIN_CLOSED or event == 'Exit': # if user closes window or clicks cancel
        break

    # Register a new database
    if event == "Register":
        window.Hide()
        a = register()
        if a:
            window.UnHide()
            window.Refresh()

    # Ensure hash , keys files are databases
    if prev[1] != values['-keys-'] or prev[0] != values['-hash-']:
        db_error(values['-keys-'],values['-hash-'])
        prev[1] = values['-keys-']
        prev[0] = values['-hash-']

# Close Window
window.close()

