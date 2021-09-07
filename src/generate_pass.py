# Packages
import secrets, random
import string

global symbols
symbols='@#$%&!'

def generate_pass(letters_count = 4,digits_count = 4,symbols_count = 0):
	'''Generate a secure random password 

	   Inputs:
	   ----------
	   1. letters_count ---> Amount of letters in the string. (int)

	   1. digits_count ---> Amount of digits in the string. (int)

	   1. symbols_count ---> Amount of symbols (@#$%&!) in the string. (int)

	   Output:
	   ----------
	   Random string - password(str)'''

	# Lists:
	# Random letters
	letters = [random.choice(string.ascii_letters) for i in range(letters_count)]

	# Random numbers
	numbers = [random.choice(string.digits) for i in range(digits_count)]

	# Random symbols
	sym = [random.choice(symbols) for i in range(symbols_count)]

	# Initalizing final string 
	final_string = ""

	if len(letters) > 0:
		# Lists for uppercase and lowercase letters
		l = [c for c in letters if c.isupper()]
		p = [c for c in letters if c.islower()]

		# Ensure there is an uppercase letter in the final_string
		if len(l) == 0:
			for i in range(0, round(len(letters)/2)):
				letters[i] = letters[i].upper()

		# Ensure there is a lowercase letter in the final_string
		if len(p) == 0:
			for i in range(0, round(len(letters)/2)):
				letters[i] = letters[i].lower()


	# Random sorting
	while True:

		# Insert letter to the final string 
		if letters:

			# Random number
			rand = random.randint(0,len(letters)-1)

			# Add the letter to the final string
			# And remove it from the list
			final_string += letters.pop(rand)

		# Insert numers to the final string 
		if numbers:
			rand = random.randint(0,len(numbers)-1)
			final_string += numbers.pop(rand)

		# Insert symbols to the final string 
		if sym:
			rand = random.randint(0,len(sym)-1)
			final_string += sym.pop(rand)
		
		# Stop loop if all lists are empty
		if not sym and not numbers and not letters:
			break

	# Return random string
	return final_string

