import PySimpleGUI as sg
from backend import KeysDatabase, HashDatabase
from pass_check import pass_check
from cryptography.fernet import Fernet



def main(key_id, keys_path, hash_id, hash_path):
    #----------------------------------------------------#
    # Setting Layout

    # Window's Theme
    sg.theme('DarkTeal12')

    # Set Window's options
    form = sg.FlexForm('Everything bagel' ,default_element_size=(20, 1))
    sg.SetOptions(font =("Times-Roman", 15))

    # Application name, Username and Password inputs
    column_1 =sg.Column([[sg.Text("Application:",pad = (0,8)),sg.Input(size = (25,1),key = '-app-')],
            [ sg.Text("Username:", pad = (5,8)),sg.In(size = (25,1),key = '-user-')],
           [sg.Text("Password: ",pad = (7,8)),sg.In(size = (25,1),key = '-pass-'), sg.Button("Help", tooltip = "Press to open a window in which the \n password will be generated for you.\n Also, you will be able to check if the\n new password was not leaked before")],
           ]) 

    # Comment - Multiline
    column_2 = sg.Column([[sg.Text("Comment: ")], [sg.Multiline(key='-comment-',size = (25,4))]])

    # Buttons - Add, Delete, Update, Search, View All
    column_3 = sg.Column([[sg.Button("Add",size = (6,1))],
                          [sg.Button("Search",size = (6,1))],
                          [sg.Button("Update", size = (6,1))],
                          [sg.Button("Delete", size = (6,1))]
                        ])
    # Rows
    # Row 2,3,4 - Frame of Databases
    column = [[column_1, column_2, column_3]]

    info = [sg.Frame(' Information ',column)]

    elements = []
    # Frame of Data
    data = sg.Frame(' Data ', [[sg.Listbox(enable_events = True, key = '-ls-',size = (30,16),values = elements)  ]])
    
    message = sg.Frame(' Message ', [[sg.Multiline( key = '-msg-',size = (35,17)) ]])

    # Buttons
    buttons = [sg.Button("Exit",size = (6,1), border_width = 0, button_color = ('white','#ff6666'), tooltip = "Back to Log In")]

    layout = [[sg.T()], # Blank space
        
        # Database Frame
        info,

        # Blank space
        [sg.T()], 

        # Data Frame
        [data,sg.T(""),sg.T(""),sg.T(""),message ],

        [sg.T()],
        # Buttons 
        buttons,
        ]


    # Create Window
    window = sg.Window('Password Manager', layout,element_justification='center', size = (700,625),finalize = True)
    
    #----------------------------------------------------#

    #----------------------------------------------------#
    # Functions: 

    def update_fields(app = "", username = "", password = "", comment = ""):
        # Clear Fields
        window[ls[0]].update(app)
        window[ls[1]].update(username)
        window[ls[2]].update(password)
        window[ls[3]].update(comment)

    def update_list(rows = ""):
        if not rows:
            rows = h_db.view(hash_id)

        if rows:
            _,elements = [],[]
            for row in rows:
                _ = [row[2],row[3]]
                elements.append(_)
            window['-ls-'].update([])
            window.Refresh()
            window['-ls-'].update(elements)

    #----------------------------------------------------#

    #----------------------------------------------------#
    # Event loop

    # Connect database
    k_db = KeysDatabase(keys_path)
    h_db = HashDatabase(hash_path)

    ls = ['-app-','-user-','-pass-','-comment-']

    update_list()

    while True:

        # Read evens and Values
        event, values = window.read(timeout = 100)

        # Close window
        if event == sg.WIN_CLOSED or event == 'Exit': # if user closes window or clicks cancel
            break

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

        if event == '-ls-':
            [app, username] = values['-ls-'][0]
            h_row = h_db.search_hash(hash_id,app,username)
            k_row = k_db.search_key(key_id,app,username)

            if h_row == -1 or k_row == -2:
                sg.popup_error("Something went wrong")

            else:
                #### Repeat
                 # Define Cipher Suite using the key
                cipher_suite = Fernet(k_row[0][4])

                # Decrypt password
                unciphered_text = str(cipher_suite.decrypt(h_row[0][4])).replace('b','').replace('\'','').replace("\"","")

                # Update Fields
                update_fields(app,username,unciphered_text,h_row[0][5])


        if event == "Add":

            # Save values in variables
            app, username, password, comment = values[ls[0]], values[ls[1]], values[ls[2]], values[ls[3]]

            # Ensure parameters were filled by the user
            if app and username and password:

                # Generate a new key
                key = Fernet.generate_key()

                # Save key in database
                k_db.insert_key(key_id,app ,username, key)

                # Encrypt password with special key
                cipher_suite = Fernet(key)
                ciphered_text = cipher_suite.encrypt(str.encode(password))

                # Save encrypted password in database
                h_db.insert_hash(key_id, app, username, ciphered_text, comment)

                # Clear inputs
                update_fields()

                # Update List of apps and usernames
                update_list()


        if event == "Delete":

            # Save values in variables
            app, username = values[ls[0]], values[ls[1]]

            # Ensure fields were given
            if app and username:

                # Delete password hash
                _ = h_db.delete_hash(hash_id,app,username)

                # Ensure password deleted before deleting key!
                if _ == 0:
                    k_db.delete_key(key_id,app,username)

                # Clear inputs
                update_fields()

                # Update List of apps and usernames
                update_list()

        if event == "Search":
            # Save values in variables
            app, username = values[ls[0]], values[ls[1]]

            if app:
                rows = h_db.search_hash(hash_id, app, username)

                if rows != -1:
                    update_list(rows)
            else:
                update_list()


    # Close Window
    window.close()


main(1,"/Users/avivfaraj/Desktop/Project/3/keys.db",1,"/Users/avivfaraj/Desktop/Project/3/hash.db")


##########################
# import PySimpleGUI as sg

# tasks = [["something", "Wow"], "something2", "something3"]

# layout = [
#     [sg.Text('ToDo')],
#     [sg.InputText('Enter ToDo Item', key='todo_item'), sg.Button(button_text='Add', key="add_save")],
#     [sg.Listbox(values=tasks, size=(40, 10), key="items"), sg.Button('Delete'), sg.Button('Edit')],
# ]

# window = sg.Window('ToDo App', layout)
# while True:  # Event Loop
#     event, values = window.Read()
#     if event == "add_save":
#         tasks.append(values['todo_item'])
#         window.FindElement('items').Update(values=tasks)
#         window.FindElement('add_save').Update("Add")
#     elif event == "Delete":
#         tasks.remove(values["items"][0])
#         window.FindElement('items').Update(values=tasks)
#     elif event == "Edit":
#         edit_val = values["items"][0]
#         sg.Print(edit_val)
#         # tasks.remove(values["items"][0])
#         # window.FindElement('items').Update(values=tasks)
#         # window.FindElement('todo_item').Update(value=edit_val)
#         # window.FindElement('add_save').Update("Save")
#     elif event == None:
#         break

# window.Close()