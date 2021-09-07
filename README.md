# Password Manager

Manage your password and save them either on your computer or on external disk (prefered for better security). Also, it allows the user to automatically
generate a strong password and also to check wether this password was leaked by using 'Have I Been Pwned' database. The password are save in 2 different databases 
one with the encryption and the other with the key. 

## Getting Started

Launching program for the first time the user must register and insert 2 paths in which databases (encryption, key) will be created. Also the user creates username and password in order to log in.
This password is also encrypted and saved in the database. Then, in the log in form you insert the paths to the databases and the username and password. Once you logged in
you will see a new window with a list of all of your accounts. Pressing on one account will immediatly upload the info to the fields so you can add, delete, update a password 
or search for an application and see its password. Also, you will be able to generate a password protected PDF file with a table containing all accounts with passwords.
This PDF file is configured to be printable. You can also change the password of the account of the program. In this case you will insert the current password and new password
and a verification. In all fields required password there is a button ("Help") that pressing on it will take you to another window in which you can generate passwords 
and check wether they were leaked before using Have I Been Pwned database.

### Setup
1. Clone repository <br>
   ```git clone https://github.com/avivfaraj/password-manager.git```<br>
3. Add either "py2app" or "py2exe" to the requirements.txt file:
   - For Mac users open terminal at the repo folder and run:<br>
     ```echo 'py2app' >>./requirements.txt```
   - For Windows user open cmd at the repo folder and run: <br>
     ```echo py2exe >> requirements.txt```
  
   If that doesn't work, add it manually to requirements.txt<br>
   
3. Install all requirements by running the command:<br>
   ```pip install -r requirements.txt```<br>
4. Create standalone app:
   - On Mac run the following command on Terminal:<br>
   ```python3 setup.py py2app -A```
   - On Windows run the following command on cmd:<br>
   ```python3 setup.py py2exe```
 
 
 'Have I Been Pwned' - Internet Connection is Required

## Packages

* [Have I Been Pwned](https://haveibeenpwned.com/) - The database used to check if password was leaked before
* [PySimpleGUI](https://pysimplegui.readthedocs.io/en/latest/) - Created the GUI
* [cryptography.fernet](https://github.com/pyca/cryptography) - Encrypt and decrypt passwords
* [ReportLab](https://www.reportlab.com/) - Generate a password protected PDF file with all usernames and passwords
* [sqlite3](https://www.sqlite.org/index.html) - Create and manage database
* [hashlib](https://docs.python.org/3/library/hashlib.html) - Create SH-1 hash to be used with Have I Been Pwned database
* [requests](https://requests.readthedocs.io/en/master/) - Create GET requests from website

