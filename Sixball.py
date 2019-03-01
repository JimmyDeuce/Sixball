#!/usr/bin/python3

import socket
import random
import re

ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server = "irc.mibbit.net" # Server
channel = "#SROOC" # Channel
botnick = "Sixball" # Nickname
pwd = "" # Password if bot's nick is registered. Leave empty if bot is unregistered
adminname = "Jm2c" # Admin username
exitcode = "bye " + botnick
commlist = ["!r", "!roll", "!l5r", "!l5roll", "!owod"] # List of recognized roll commands

# Connect to IRC
ircsock.connect((server, 6667)) # Here we connect to the server using the port 6667
ircsock.send(bytes("USER "+ botnick +" "+ botnick +" "+ botnick + " " + botnick + "\n", "UTF-8")) #We are basically filling out a form with this line and saying to set all the fields to the bot nickname.
ircsock.send(bytes("NICK "+ botnick +"\n", "UTF-8")) # assign the nick to the bot

# Join channel
def joinchan(chan):
	ircmsg = ""
	while ircmsg.find("End of /MOTD command.") == -1:  
		ircmsg = ircsock.recv(2048).decode("UTF-8")
		ircmsg = ircmsg.strip('\n\r')
		# Supress any blank lines
		if not ircmsg:
			continue
		# Respond to pings during connect
		elif ircmsg.find("PING :") != -1:
			print(ircmsg)
			ping(ircmsg)
		# Print boilerplate text to console to verify everything is in order
		else:
			print(ircmsg)
	# Join channel once boilerplate ends
	ircsock.send(bytes("JOIN "+ chan +"\n", "UTF-8")) 

# Respond to server pings during normal operation
def ping(data):
	ircsock.send(bytes('PONG ' + data.split(':')[1] + '\r\n', "UTF-8"))

# Send messages to target
def sendmsg(msg, target=channel):
	ircsock.send(bytes("PRIVMSG "+ target +" :"+ msg +"\n", "UTF-8"))

# Decide what to do with a roll command
def watdo(name, command):
	# if statements comparing command[0], which should be the command preceded by a !, to specific strings
	# Generic roller for plain dice
	if command[0] == '!r' or command[0] == '!roll':
		# Sanitize input
		flag = 'genroll'
		san = sanitize(command[1],flag)
		# If there is a problem, return the error message
		if san:
			return f'{name}: ' + san
		# Otherwise, roll it
		else:
			return f'{name} rolled {command[1]}: ' + genroll(command[1])
	# L5R roll and keep
	elif command[0] == '!l5r' or command[0] == '!l5roll':
		return 'ごめんなさい、日本語わかりません　(´・ω・｀)'
	# oWoD roller
	elif command[0] == '!owod':
		return "I'm not edgy enough for that yet!"
	# Error if somehow none of the commands match
	else: 
		return "I'm not sure what you want me to do!"
 
def sanitize(input,flag):
	# Running check if input is still valid
	valid = True
	
	# General requirements that all input must fulfill
	# Check that first character is a number
	if not re.match('^[1-9][0-9]*', input):
		valid = False
		return "How many dice do you want me to roll?"
	# Check for duplicate operators. Remember to update when adding new dice functions!
	elif re.search('[d+*-/^%][d+*-/^%]+',input):
		valid = False
		return "You typed an operator twice, can you try again?"
	# Check for operators at end of string. Remember to update when adding new dice functions!
	elif re.search('[d+*-/^%(]$',input):
		valid = False
		return "Something's missing at the end, can you try again?"

	# If all these tests pass, roller-specific conditions
	# Conditions specific to the generic roller
	if valid and flag == 'genroll':
		# Check for illegal characters
		if re.search('[^d\d+*-/^%)(]',input):
			valid = False
			return "I don't know how to roll that!"
		
	# OK if input is still valid at this point
	if valid:
		return False

# Separate roll commands into numbers and operators. Remember to update when adding new dice functions!
def parse (input):
	parsed = re.split('([d+*-/^%)(])',input)
	while '' in parsed:
		parsed.remove('')
	return parsed

# Roll dice as a separate function to reference like an operator, for general use by all rollers
def dice(num, fac):
	# Limit number and size of dice to be rolled
	if num > 50:
		raise Exception("I can't hold that many dice!")
	if fac > 100:
		raise Exception("I don't have dice that big!")
	roll = [random.randint(1,fac) for i in range(num)]
	global cosmetic
	cosmetic = cosmetic + f'{num}d{fac} = ' + str(roll) + ', '
	return roll

# Convert a parsed list of operators and operands to RPN
def convert(input):
	# Define order of precedence for operations
	precedence = {'d': 7, '^': 6, '%': 5, '*': 5, '/': 5, '+': 4, '-': 4, '(': 0, ')': 0}
	# Create empty queue and stack
	queue = []
	stack = []
	for item in input: # going through each item in input left to right
		# If item is a number, queue it
		if re.match('\d+',item):
			queue.append(item)
			# Leaving everything as strings, even the numbers, to avoid type confusion somewhere down the line. Convert the numbers to ints and then back to strings as part of resolving the math
		# If item is an open paren, stack it
		elif item == '(':
			stack.append(item)
		# If item is a close paren...
		elif item == ')':
			# Create empty string representing top operator on the stack
			operator = ''
			# As long as that operator isn't an open paren...
			while operator != '(':
				# If the stack is empty, there's a missing open paren and we have to throw an error
				if len(stack) == 0:
					raise Exception("I'm sorry, can you check your parentheses?")
				# Otherwise, get the top operator from the stack
				operator = stack.pop()
				# And queue it if it's not an open paren
				if operator != '(':
					queue.append(operator)
		# If item is a legal operator (is in the precedence dictionary)...
		elif item in precedence:
			# ...as long as there are other items already on the stack...
			while len(stack) > 0:
				# ...if the top item on the stack has higher precedence, queue that item
				if precedence[stack[-1]] >= precedence[item]:
					queue.append(stack.pop())
				# otherwise, exit the while
				else:
					break
			# After stacking higher precedence items, stack current item
			stack.append(item)
		# If item is anything else, throw an error
		else:
			raise Exception(f"What's a {item}?")
	
	# After going through the input, handle the stack
	while len(stack) > 0:
		item = stack.pop()
		# If the top element is an open paren, throw a missing close paren error
		if item == '(':
			raise Exception("I'm sorry, can you check your parentheses?")
		# Otherwise, queue the item
		queue.append(item)
		
	# Return the queue list
	return queue

# Now take the queue and do math with it!
def calculate(queue):
	stack = []
	# As long as there items in the queue...
	while len(queue) > 0:
		# Get the first item in the queue
		item = queue.pop(0)
		# If it's a number, convert to int and put on the stack
		if re.match('\d+',item):
			stack.append(int(item))
		# If it's an operator...
		else:
			# Assuming there are two numbers before it on the stack
			if len(stack) >= 2:
				right = stack.pop()
				left = stack.pop()
				value = 0
				# Perform appropriate operation
				if item == '*':
					value = left * right
				elif item == '/':
					value = left / right
				elif item == '%':
					value = left % right
				elif item == '+':
					value = left + right
				elif item == '-':
					value = left - right
				elif item == 'd':
					value = sum(dice(left, right))
				else:
					raise Exception("I don't know what to do with this!")
				stack.append(value)
			else:
				raise Exception("There's a missing operand somewhere!")
	
	# If all this completes and there is somehow not exactly one number left on the stack, something went wrong:
	if len(stack) != 1:
		raise Exception("Something doesn't match up here!")
	else:
		result = stack.pop()
		return str(result)

# Generic roller for rolling any combination of dice and adding results together
# All rollers should take a parsed list of operands and operators and return a single string
def genroll(input):
	# Parse the input
	dice = parse(input)
	# Initialize/flush global string to track individual die results
	global cosmetic
	cosmetic = ''
	# Convert input to RPN
	rpn = convert(dice)
	# resolve converted input
	total = calculate(rpn)
	# Return formatted results
	return f"{total} ({cosmetic.rstrip(', ')})"

def main():
	joinchan(channel)	# Join
	if pwd:
		sendmsg(f'identify {pwd}', 'NickServ')	# Authenticate if a password is set
	sendmsg("Hi!")	# Confirm successful join
	
	while True:
		# Get messages
		ircmsg = ircsock.recv(2048).decode("UTF-8")
		ircmsg = ircmsg.strip('\n\r')
		print(ircmsg)
		if ircmsg.find("PRIVMSG") != -1:
			# Split incoming message into name of sender and content
			name = ircmsg.split('!',1)[0][1:]
			message = ircmsg.split('PRIVMSG',1)[1].split(':',1)[1]
			if len(name) < 17 and name != botnick:
				# Determine if a message needs to be acted on
				
				# First, trivial call and response functions: 
				# Respond in kind to a greeting
				if message.find('Hi ' + botnick) != -1:
					sendmsg("Hello " + name + "!")
				# Recite the runner mantra
				if message == '!fixalot':
					sendmsg('(ﾉ≧∀≦)ﾉ "Watch your back. Shoot straight. Conserve ammo. And never, ever deal with a dragon!"')
				# Leave channel command
				if name.lower() == adminname.lower() and message.rstrip() == exitcode:
					sendmsg("Bye! <3")
					ircsock.send(bytes("QUIT \n", "UTF-8"))
					return
				
				# Roll commands: compare first word in message to list of commands
				if message.split(' ')[0] in commlist: 
					# Call the roll command handler with message.split(' ') and do something with it!
					try: 
						res = watdo(name, message.split(' '))
						sendmsg(res)
					except Exception as e:
						sendmsg(f"{name}: " + str(e))
		else:
			if ircmsg.find("PING :") != -1:
				ping(ircmsg)

main()
