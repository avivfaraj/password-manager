# import modules
import requests 
import hashlib 

# Return number of times the password
# appears in Pwned Password's database
def check_pass(passw):
	'''Check wether the password 'passw' 
	   appears in Pwned Password's database

	   Input:
	   ----------
	   passw ---> Password to be checked. (str) 

	   Output:
	   ----------
	   Return a number (int) represent the number of times 
	   that the password appears in databse'''

	# Hash it
	result = hashlib.sha1(passw.encode())

	# Upper Case 
	result = (result.hexdigest()).upper()


	# Making a get request 
	# b = '21BD1'
	b = result[:5]
	suffix = result[5:]

	# Making a get request
	# API v3: https://haveibeenpwned.com/API/v3#PwnedPasswords
	response = requests.get(f'https://api.pwnedpasswords.com/range/{b}') 
	  
	# Iterate over the response 
	# Look for suffix similar to the one we have
	for line in response.iter_lines():

		# Decode line ("Suffix:Number")
		data = line.decode("utf-8")

		# Split string to list: ["Suffix", "Number"]
		data = data.split(":")

		# Suffix on list ---> Password were leaked !!!
		# The number represents number of times 
		# the password appears in Pwned Password data set
		if suffix == data[0]:

			try:
				if int(data[1]) > 0:
					return data[1]

			# Empty lines - Nothing to do 
			# Continue to the next line
			except IndexError:
				pass

	return 0

# Ensure password is strong 
# Combination of numbers, letters, 
# capital letters, and symbols
def is_strong(pwd):
    # Count letters
    count = len(pwd)
    
    # Define symbols that might be used
    symbols = "!@#$%^&"

    # Sum numbers in password
    numbers = sum(c.isdigit() for c in pwd)

    # Sum lower letters in password
    letters = sum(c.islower() for c in pwd)

    # Sum capital letters in password
    capital = sum(c.isupper() for c in pwd)

    # Sum symbols in password
    sym = sum(c in symbols for c in pwd)

    if count > 8:
        if sym == 0:
            if letters > 0 and capital > 0:
                if numbers > 0: 
                    return pwd+ " is Good, but could be great with additional symbols (!@#$%&)"
                else:
                    return "Not strong! Numbers and/or symbols (!@#$%&) should be added to make it stronger"
            elif letters == 0 or capital == 0:
                if numbers > 0:
                    return "Better have a mix of capital and lowercase letters"
                else:
                    return "Better have a mix of numbers, capital and lowercase letters"
        else:
            if letters > 0 and capital > 0:
                if numbers > 0: 
                    return pwd + " is Great!"
                else:
                    return "You can add numbers to make it stronger"
            elif letters == 0 or capital == 0:
                if numbers > 0:
                    return "Better have a mix of capital and lowercase letters"
                else:
                    return "Better have a mix of numbers, capital and lowercase letters"
    else:
        return pwd+ " too short. At least 8 characters to make it strong"

