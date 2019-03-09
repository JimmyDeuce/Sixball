#!/usr/bin/python3

import socket
import random
import re

# Settings
ircsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server = 'irc.rizon.net' # Server
channel = '#sixball-test' # Channel
botnick = 'Sixball' # Nickname
pwd = '' # Password if bot's nick is registered. Leave empty if bot is unregistered
adminname = 'Jm2c' # Admin username
exitcode = 'bye ' + botnick
commlist = ['!r', '!roll', '!l5r', '!l5roll', '!owod', '!cwod'] # List of recognized roll commands

# Regex strings
mathparse = '([+*-/^%)(])' # Regex string for parsing arithmetic string input as a list
diceparse = '([dker])' # Regex string for parsing dice expression strings as a list
dicestring = '\d+d\d+(?:[ker]\d+)*' # Regex string for detecting a dice expression
dicesplit = '(\d+d\d+(?:[ker]\d+)*)' # Regex string for splitting the dice expression(s) out of a string
opstring = '[ker]' # Regex string for recognizing allowed dice operators

# Connect to IRC
ircsock.connect((server, 6667)) # Here we connect to the server using the port 6667
ircsock.send(bytes('USER '+ botnick +' '+ botnick +' '+ botnick + ' ' + botnick + '\n', 'UTF-8')) #We are basically filling out a form with this line and saying to set all the fields to the bot nickname.
ircsock.send(bytes('NICK '+ botnick +'\n', 'UTF-8')) # assign the nick to the bot

# IRC interface class
class irc:

	# Join channel
	def joinchan(self, chan):
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
				self.ping(ircmsg)
			# Print boilerplate text to console to verify everything is in order
			else:
				print(ircmsg)
		# Join channel once boilerplate ends
		ircsock.send(bytes("JOIN "+ chan +"\n", "UTF-8")) 

	# Respond to server pings during normal operation
	def ping(self, data):
		ircsock.send(bytes('PONG ' + data.split(':')[1] + '\r\n', "UTF-8"))

	# Send messages to target
	def sendmsg(self, msg, target=channel):
		ircsock.send(bytes("PRIVMSG "+ target +" :"+ msg +"\n", "UTF-8"))

#Input handler class
class handler:
	
	# Take roll commands and decide what to do with them
	def watdo(self, name, command):
		# if statements comparing command[0], which should be the command preceded by a !, to specific strings
		# Generic roller for plain dice
		if command[0] == '!r' or command[0] == '!roll':
			# Sanitize input
			flag = 'genroll'
			san = self._sanitize(command[1],flag)
			# If there is a problem, return the error message
			if san:
				return f"{name}: " + san
			# Otherwise, roll it
			else:
				return f"{name} rolled {command[1]}: " + self._resolve(command[1])
		# L5R roll and keep
		elif command[0] == '!l5r' or command[0] == '!l5roll':
			# Sanitize input
			flag = 'weebroll'
			san = self._sanitize(command[1],flag)
			# If there is a problem, return the error message
			if san:
				return f"{name}: " + san
			# Otherwise, roll it
			else:
				return f"{name} rolled {command[1]}: " + self._weebroll(command[1])
		# oWoD roller
		elif command[0] == '!owod' or command[0] == '!cwod':
			return "I'm not edgy enough for that yet!"
		# Error if somehow none of the commands match
		else: 
			return "I'm not sure what you want me to do!"
	
	def _sanitize(self, input, flag):
		# Running check if input is still valid
		valid = True
		
		# General requirements that all input must fulfill
		# Check that first character is a number
		if not re.match('^[1-9][0-9]*', input):
			valid = False
			return "How many dice do you want me to roll?"
		# Check for duplicate operators. Remember to update when adding new dice functions!
		elif re.search('[dker+*-/^%][dker+*-/^%]+',input):
			valid = False
			return "You typed an operator twice, can you try again?"
		# Check for operators at end of string. Remember to update when adding new dice functions!
		elif re.search('[dker+*-/^%(]$',input):
			valid = False
			return "Something's missing at the end, can you try again?"

		# If all these tests pass, roller-specific conditions
		# Conditions specific to the generic roller
		if valid and flag == 'genroll':
			# Check for illegal characters
			if re.search('[^dker\d+*-/^%)(]',input):
				valid = False
				return "I don't know how to roll that!"
		
		if valid and flag == 'weebroll':
			# Check for illegal characters
			if re.search('[^ker\d+*-/^%)(]', input):
				valid = False
				return "I don't know how to roll that!"
		
		# OK if input is still valid at this point
		if valid:
			return False
	
	# Take an input string and pass blocks of it to math and dice as appropriate
	def _resolve(self, input):
		RNJesus = rng()
		# Find any dice expressions in the input string
		if re.search(dicestring, input):
			parts = re.split(dicesplit, input)
			# For each dice expression found, pass that to rng to resolve it
			for i, expr in enumerate(parts):
				if re.match(dicestring, expr):
					# Substitute the expressions in the input string with the rng results
					parts[i] = RNJesus.genroll(expr)
			# Concatenate the parts list back together and pass the remaining arithmetic to math
			arithmetic = ''.join(parts)
		else:
			arithmetic = input
		Magic = math()
		res = Magic.calculate(arithmetic)
		# Return the final value and cosmetic string
		return f"{res} ({RNJesus.cosmetic.rstrip(', ')})"

	
	# Specialized roll functions that translate a simplified input to particular dice strings
	# L5R roller
	def _weebroll(self, input):
		# Find roll and keep expression(s) in the input string
		if re.search('\d+k\d+', input):
			parts = re.split('(\d+k\d+)', input)
			# For each roll and keep expression found...
			for i, expr in enumerate(parts):
				if re.match('\d+k\d+', expr):
					# ...translate that into genroll notation
					parts[i] = f'{re.split("k", expr)[0]}d10e10k{re.split("k", expr)[1]}'
			# Concatenate back together and pass to resolve
			dicery = ''.join(parts)
		else:
			dicery = input
		res = self._resolve(dicery)
		# Return the final value and cosmetic string
		return f"{res}"


# RNG class
class rng:

	# Initialize variables for the dice arguments to track them between methods
	def __init__(self):
		self._num = 0 # Number of dice to be rolled
		self._fac = 0 # Number of faces
		self._re = 0 # Number which should trigger a reroll
		self._kp = 0 # Number of dice to be kept
		self._exp = 0 # Number which should explode (equal or higher)
		self._tgt = 0 # Target number for rolls comparing individual die results to a target number
		self._botch = 0 # Number which should count as negative successes on target rolls (equal or lower)
		self.cosmetic = "" # Cosmetic string for tracking individual roll operations
	
	# Read the dice expression passed to class rng and resolve it left to right
	def genroll(self, input):
		# Parse expression into a list
		queue = self._parse(input)
		# Reverse list to use as a queue
		queue.reverse()
		# We require that the expression starts with XdY, but other roll operators can be in any order and combination
		# Convert first element to int and assign as _num
		self._num = int(queue.pop())
		# Discard second element since it should always be 'd'
		del queue[-1]
		# Convert third element to int and assign as _fac
		self._fac = int(queue.pop())
		# Call _dice to resolve the basic roll and store
		rolls = self._dice(self._num, self._fac)
		# As long as items are in the queue...
		while len(queue) > 0:
			# Get next item
			item = queue.pop()
			# As we require input to be alternating numbers and operators, the top item should always be an operator when checked
			if re.match(opstring, item):
				# If there is another element in the queue and it's a number
				if len(queue) >= 1:
					# Perform the appropriate operation
					if item == 'k':
						self._kp = int(queue.pop())
						rolls = self._keep(rolls)
					elif item == 'r':
						self._re = int(queue.pop())
						rolls = self._reroll(rolls)
					elif item == 'e':
						self._exp = int(queue.pop())
						rolls = self._explode(rolls)
					else:
						raise Exception(f"What's a(n) {item}?")
				else:
					raise Exception("Can you check your operators? I'm kind of fussy!")
			else:
				raise Exception("Can you check your operators? I'm kind of fussy!")
		# If the final output is a list of die results, sum them (if the final result is just a number of successes, it will still be in the rolls list, so sum works)
		result = sum(rolls)
		# Then return the result as a string
		return str(result)
	
	# Separate dice expression strings into numbers and operators
	def _parse(self,input):
		parsed = re.split(diceparse,input)
		return parsed
	
	# Resolve basic rolls
	def _dice(self, num, fac, track=True):
		# Limit number and size of dice to be rolled
		if num > 50:
			raise Exception("I can't hold that many dice!")
		if fac > 100:
			raise Exception("I don't have dice that big!")
		roll = [random.randint(1,fac) for i in range(num)]
		if track:
			self.cosmetic = self.cosmetic + f"{num}d{fac} = " + str(roll) + ", "
		return roll
	
	# Take a list of die results and reroll particular values, replacing those values with the new roll and documenting the rerolls
	def _reroll(self, pool, repeat=False):
		# Count the dice to be rerolled
		toreroll = pool.count(self._re)
		# As long as there are any dice showing the reroll number...
		while toreroll > 0:
			# For each die in the pool showing that number...
			for i, die in enumerate(pool):
				if die == self._re:
					# Replace it with a new roll, without tracking those rolls
					pool[i] = random.randint(1,self._fac)
			# Then report the rerolls to cosmetic
			self.cosmetic = self.cosmetic + f"reroll {toreroll} {self._re}(s) -> " + str(pool) + ", "
			# If repeat is toggled off, stop there
			if not repeat:
				break
			# Otherwise, recount dice to be rolled in the new pool and continue until no more dice show the reroll value
			toreroll = pool.count(self._re)
		# Return the pool
		return pool
	
	# Take a list of die results and explode particular values, adding the new roll results to the old values
	def _explode(self, pool, extrawurst=True):
		# No exploding everything!
		if self._exp <= 1:
			raise Exception("Please no ;_;")
		# Actually, let's limit the explosions to a sane level
		if self._exp < self._fac / 2:
			raise Exception("That's too explosive!")
		# Count the dice to be exploded, which is any dice showing the explode number or higher
		tnt = sum(1 for die in pool if die >= self._exp)
		# If there are no dice to explode, just return the original pool and be done
		if tnt == 0:
			return pool
		# Initialize list to hold explosions
		boom = []
		# As long as any dice show the explosion number(s)...
		while tnt > 0:
			# Roll that many dice and add them to boom
			boom.append([random.randint(1,self._fac) for i in range(tnt)])
			# Report them to cosmetic
			self.cosmetic = self.cosmetic + f"explode {tnt} dice over {self._exp} -> " + str(boom[-1]) + ", "
			# Then count any dice to explode again
			tnt = sum(1 for die in boom[-1] if die >= self._exp)
		# Once done exploding, check if this explosion cares about which dice exploded into which dice
		if extrawurst:
			# If it does, go backwards through the explosion pools
			while len(boom) > 1:
				item = boom.pop()
				item.reverse() # Reverse to be able to pop from left to right
				for i, die in enumerate(boom[-1]):
					# Find the dice that exploded in the second to last boom pool left to right
					if die >= self._exp:
						# For each of them, add one of the dice in the last pool, left to right
						boom[-1][i] = boom[-1][i] + item.pop()
			# Once only one pool is left in boom, do the same one more time with the original pool
			final = boom.pop()
			final.reverse()
			for i, die in enumerate(pool):
				if die >= self._exp:
					pool[i] = pool[i] + final.pop()
		# If not, just put all the dice together
		else:
			for res in boom:
				pool = pool + res
		# Return the final result
		self.cosmetic = self.cosmetic + "total: " + str(pool) + ", "
		return pool
	
	# Take a list of die results and keep either the highest or the lowest N
	def _keep(self, pool, aim='highest'):
		# Drop kept dice in excess of rolled dice
		if self._kp > len(pool):
			Sixball.sendmsg(f"Dropping {self._kp-len(dice)} excess kept dice...")
			self._keep = len(pool)
		# Keep highest
		if aim == 'highest':
			kept = sorted(pool)[-self._kp:]
		# Keep lowest
		if aim == 'lowest':
			kept = sorted(pool, reverse=True)[-self._kp:]
		# Track in cosmetic
		self.cosmetic = self.cosmetic + f"keep {aim} {self._kp} -> " + str(kept) + ", "
		# Return results
		return kept
			
	# Take a list of die results and compare each to a target number and botch number, returning the final number of successes as an int


# Non-roll math class
class math:
	
	# Separate arithmetic input strings into numbers and operators
	def _parse(self, input):
		parsed = re.split(mathparse,input)
		while '' in parsed:
			parsed.remove('')
		return parsed
	
	# Convert a parsed list of operators and operands to RPN
	def _convert(self, input):
		# Define order of precedence for operations
		precedence = {'^': 6, '%': 5, '*': 5, '/': 5, '+': 4, '-': 4, '(': 0, ')': 0}
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
	
	# Take a string arithmetic input and do math with it
	def calculate(self, input):
		# Parse input and convert to a RPN queue
		parsed = self._parse(input)
		queue = self._convert(parsed)
		stack = []
		# As long as there are items in the queue...
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


def main():
	Sixball.joinchan(channel)	# Join
	if pwd:
		Sixball.sendmsg(f"identify {pwd}", "NickServ")	# Authenticate if a password is set
	Sixball.sendmsg("Hi!")	# Confirm successful join
	
	while True:
		# Get messages
		ircmsg = ircsock.recv(2048).decode('UTF-8')
		ircmsg = ircmsg.strip('\n\r')
		print(ircmsg)
		if ircmsg.find('PRIVMSG') != -1:
			# Split incoming message into name of sender and content
			name = ircmsg.split('!',1)[0][1:]
			message = ircmsg.split('PRIVMSG',1)[1].split(':',1)[1]
			if len(name) < 17 and name != botnick:
				# Determine if a message needs to be acted on
				
				# First, trivial call and response functions: 
				# Respond in kind to a greeting
				if message.find('Hi ' + botnick) != -1:
					Sixball.sendmsg("Hello " + name + "!")
				# Recite the runner mantra
				if message == '!fixalot':
					Sixball.sendmsg("(ﾉ≧∀≦)ﾉ \"Watch your back. Shoot straight. Conserve ammo. And never, ever deal with a dragon!\"")
				# Squid
				if message == '!squid':
					Sixball.sendmsg("＜コ:彡")
				# Leave channel command
				if name.lower() == adminname.lower() and message.rstrip() == exitcode:
					Sixball.sendmsg("Bye! <3")
					ircsock.send(bytes("QUIT \n", 'UTF-8'))
					return
				
				# Roll commands: compare first word in message to list of commands
				if message.split(' ')[0] in commlist: 
					# Call the roll command handler with message.split(' ') and do something with it!
					try: 
						res = Process.watdo(name, message.split(' '))
						Sixball.sendmsg(res)
					except Exception as e:
						Sixball.sendmsg(f"{name}: " + str(e))
		else:
			if ircmsg.find('PING :') != -1:
				Sixball.ping(ircmsg)

# Initialize classes
Sixball = irc()
Process = handler()

main()
