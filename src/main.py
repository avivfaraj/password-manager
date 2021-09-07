import PySimpleGUI as sg
from backend import KeysDatabase, HashDatabase
from pass_check import pass_check
from other import notes
from encryption import encrypt, decrypt
from change_pwd import change_pwd
from createPDF import PDF
import os

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
    buttons = [sg.Button("Account",size = (9,1), border_width = 0, button_color = ('white','#00b300'), tooltip = "Click to change your log in password to this program"),
               sg.Button("Create PDF",size = (9,1), border_width = 0, button_color = ('white','#4B0082'), tooltip = "Create a password protected pdf file"),
               sg.Button("Exit",size = (9,1), border_width = 0, button_color = ('white','#ff6666'), tooltip = "Back to Log In")]

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
        window['-app-'].update(app)
        window['-user-'].update(username)
        window['-pass-'].update(password)
        window['-comment-'].update(comment)

    def update_list(rows = ""):
        # Get all passwords
        if not rows:
            rows = h_db.view(hash_id)

        # Ensure rows is not empty
        if rows:

            # Initialize parmeters
            _,elements = [],[]

            # Iterate over rows
            for row in rows:
                # Append to list of elements
                _ = [row[2],row[3],row[7], row[6]]
                elements.append(_)

            # Clear and update list
            window['-ls-'].update([])
            window.Refresh()
            window['-ls-'].update(elements)

    def update_msg(msg):
        # Construct a new message
        new = notes(msg, values['-msg-'])

        # Update msg element
        window['-msg-'].update(new)

    def fields_values():
        # Save values in variables
        return values['-app-'], values['-user-'],values['-pass-'], values['-comment-']

    def insert_encryption(app, username, password, comment, index):

        key, ciphered_text = encrypt(password)

        if key and ciphered_text:
            if index == 1:
                # Store encrypted password in database
                h_db.insert_hash(key_id, app, username, ciphered_text, comment)

                # Store key in database
                k_db.insert_key(key_id,app ,username, key)

            else:
                # Store updated hash in database
                h_db.update_hash(key_id, app, username, ciphered_text, comment)

                # Store updated key in database
                k_db.update_key(key_id,app ,username, key)
        else:
            update_msg("Error: didn't encrypt")

    def manager_password():

        # Search for this user in db
        hash_r = h_db.search_user(user_id = hash_id)
        key_r = k_db.search_user(user_id = key_id)

        curr = ""

        # Ensure found
        if hash_r and key_r:
            hash_r = hash_r[0]
            key_r = key_r[0]
            curr = decrypt(key_r[2],hash_r[2])

        # Return password
        return curr


    #----------------------------------------------------#

    #----------------------------------------------------#
    # Event loop

    # Connect database
    k_db = KeysDatabase(keys_path)
    h_db = HashDatabase(hash_path)

    # Update list with the data from db
    update_list()

    # Initialize variables
    current_pwd, current_usr,current_app = "", "", ""
    decrypted = False

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

        # Chose one row from list
        if event == '-ls-':

            # Ensure row is not empty
            if values['-ls-']:

                # Get values from list
                [app, username, time_mod, date_mod] = values['-ls-'][0]

                # Search in dbs
                h_row = h_db.search_hash(hash_id,app,username)
                k_row = k_db.search_key(key_id,app,username)

                # Ensure there were not errors
                if h_row == -1 or k_row == -2:
                    sg.popup_error("Something went wrong")

                # No error occured
                else:
                    # Decrypt password
                    pwd = decrypt(k_row[0][4],h_row[0][4])

                    # Ensure no error in decryption
                    if pwd:

                        # Update Fields
                        update_fields(app,username,pwd,h_row[0][5])

                        # Update variables to current row
                        current_pwd = pwd 
                        current_usr = username
                        current_app = app
                    
                    # An error occured 
                    else:
                        # Show all data in list
                        update_fields()

                        # Clear variables
                        current_pwd, current_usr, current_app = "", "", ""

                        # Inform the user
                        update_msg("Error: Something Went Wrong. Key doesn't match")


        if event == "Add":
            # Store values in variables
            app, username, password, comment = fields_values()

            # Ensure parameters were filled by the user
            if app and username and password:

                # Ensure it is a new user
                if username != current_usr or app != current_app:

                    insert_encryption(app,username,password,comment,1)

                    # Clear inputs
                    update_fields()

                    # Update List of apps and usernames
                    update_list()

                    # Inform the user 
                    update_msg("Successfully Added!")


        if event == "Delete":

            # Store values in variables
            app, username, _, _ = fields_values()
            if username == current_usr and current_app == app:
                l = sg.popup_yes_no("You are about to delete an account in database.\n once deleted it's gone. Are you sure?",title = "Delete an item", keep_on_top = True)

                if l == "Yes":

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

                        # Inform the user 
                        update_msg("Item Deleted!")

        if event == "Search":
            # Save values in variables
            app, username, _, _ = fields_values()

            if app:
                rows = h_db.search_hash(hash_id, app, username)

                if rows != -1:
                    update_list(rows)

                if not rows:
                    window['-ls-'].update([])
            else:
                update_list()

        if event == "Update":

            # Store values in variables
            app, username, password, comment = fields_values()

            if username == current_usr:

                if current_pwd != password:

                    l = sg.popup_yes_no("You are about to update password for an account in database.\n Once updated the current password and key are gone. Are you sure?",title = "Update Password", keep_on_top = True)

                    if l == "Yes":

                        # Encrypt new password and update database
                        insert_encryption(app,username,password,comment,0)

                        # Inform the user 
                        update_msg("Password was updated!")

                else:
                    # Update comment in database
                    h_db.update_comment(hash_id, app, username, comment)

                    # Inform the user 
                    update_msg("Comment was updated!")


        if event == "Account":
            # Application Password
            curr = manager_password()
            
            # Hide this window
            window.Hide()

            # Get a new password from user
            new_pass = change_pwd(curr)

            # Ensure new password is not empty
            if new_pass:

                # Encrypt new password
                key, ciphered_text = encrypt(new_pass)

                # Update key db
                k_db.update_user(key_id,key)

                # Update hash db
                h_db.update_user(hash_id,ciphered_text)

                # Inform user
                update_msg("Successfully Changed")

            # Back to main.py
            window.UnHide()

        if event == "Create PDF":
            curr = manager_password()

            # Get hash and keys data from dbs
            h_rows = h_db.view(hash_id)
            k_rows = k_db.view(key_id)

            # Initialize Para
            ls = []
            pwd = ""

            # Ensure rows are not empty
            if h_rows and k_rows:

                # Iterate over hash and keys
                for _hash, key in zip(h_rows,k_rows):

                    # Decrypt password
                    pwd = decrypt(key[4],_hash[4])

                    # Append a row to list: [Application, Username, Password, Time modified, Date modified]
                    ls.append([_hash[2], _hash[3],pwd,_hash[7],_hash[6]])
            # Create PDF 
            _ = PDF(ls,curr)

            # Ensure pdf created and inform the user
            if _:
                update_msg(f"PDF file named \'password.pdf\' was created in: {os.getcwd()}")


    # Close Window
    window.close()


