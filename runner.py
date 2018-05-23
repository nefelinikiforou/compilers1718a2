"""
Grammar:

Stmt_list -> Stmt Stmt_list
                 |.
Stmt -> id assign Expr
                | print Expr.
Expr -> Term1 Term1_tail.
Term1_tail -> Orop Term1 Term1_tail
                    |.
Term1 -> Term2 Term2_tail.
Term2_tail -> Andop Term2 Term2_tail
                    |.
Term2 -> Factor
        | Notop Factor.
Factor -> (Expr)
              | id
             | B_var.
B_var -> 0
             | 1
             | true
             | false
             | t
             | f.
Orop -> or.
Andop -> and.
Notop -> not.

"""


import plex



class ParseError(Exception):
	""" A user defined exception class, to describe parse errors. """
	pass



class MyParser:
	""" A class encapsulating all parsing functionality
	for a particular grammar. """


	def __init__(self): #initialize
		self.st={}

	
	def create_scanner(self,fp):
		""" Creates a plex scanner for a particular grammar 
		to operate on file object fp. """

		# define some pattern constructs
		letter = plex.Range("AZaz") #letter
		digit = plex.Range("09") #digit

		identifier = letter+plex.Rep(letter|digit) #always starts with letter
		b_var = plex.Str('true','TRUE','True','t','T','false','FALSE','False','f','F','0','1') #t,T,f,F after full words for correct matching

		assign = plex.Str('=')
		parenthesis = plex.Str('(',')')

		keyword = plex.Str('print')
		operator = plex.Str('not','and','or')
		space=plex.Rep1(plex.Any(' \n\t'))

		# the scanner lexicon - constructor argument is a list of (pattern,action ) tuples
		lexicon = plex.Lexicon([
			(operator,plex.TEXT),
			(parenthesis,plex.TEXT),
			(assign,plex.TEXT),
			(space,plex.IGNORE),
			(keyword, plex.TEXT), #keywords and b_vars before identifiers for correct matching
			(b_var,'b_var'),
			(identifier,'id'),
			])
		
		# create and store the scanner object
		self.scanner = plex.Scanner(lexicon,fp)
		
		# get initial lookahead
		self.la,self.val = self.next_token()


	def next_token(self):
		""" Returns tuple (next_token,matched-text). """
		
		return self.scanner.read()		

	
	def position(self):
		""" Utility function that returns position in text in case of errors.
		Here it simply returns the scanner position. """
		
		return self.scanner.position()
	

	def match(self,token):
		""" Consumes (matches with current lookahead) an expected token.
		Raises ParseError if anything else is found. Acquires new lookahead. """ 
		
		if self.la==token:
			self.la,self.val = self.next_token()
		else:
			raise ParseError("found {} instead of {}".format(self.la,token))
	
	
	def parse(self,fp):
		""" Creates scanner for input file object fp and calls the parse logic code. """
		
		# create the plex scanner for fp
		self.create_scanner(fp)
		
		# call parsing logic
		self.stmt_list()
	

	
	def get_value(self,token,text):
		if token=='b_var':
			return text
		else:
			if text in self.st:
				return self.st[text]

			
	def stmt_list(self):
		""" Stmt_list -> Stmt Stmt_list
                 		|. """
		
		if self.la=='id' or self.la=='print':
			self.stmt()
			self.stmt_list()
		elif self.la is None: #epsilon transition 
			return	
		else:
			raise ParseError("in stmt_list: id or print expected")
			 	
	
	def stmt(self):
		""" Stmt -> id assign Expr
                | print Expr. """
		
		if self.la=='id':
			varname=self.val
			#token, text = self.la, self.val #before matching, to print the first token and then move to the next token
			#print(token, text)
			self.match('id')
			#token, text = self.la, self.val
			#print(token, text)
			self.match('=')
			self.st[varname]=self.expr()
		elif self.la == 'print':
			#token, text = self.la, self.val
			#print(token, text)		
			self.match('print')
			print(self.expr())
		else:
			raise ParseError("in stmt: id or print expected")

	
	
	def expr(self):
		""" Expr -> Term1 Term1_tail. """
		
		if self.la=='(' or self.la=='id' or self.la=='b_var' or self.la=='not':
			t1=self.term1()
			tt1=self.term1_tail()
			if tt1 is None:
				return t1
			if tt1[0] == 'or':
				return (t1 or tt1[1])
		else:
			raise ParseError('in expr: ( or id or b_var or not expected')
			 	

	def term1_tail(self):
		""" Term1_tail -> Orop Term1 Term1_tail
                    |. """
		
		if self.la=='or':
			op=self.operator()
			t1=self.term1()
			tt1=self.term1_tail()
			if tt1 is None:
				return op,t1
			if tt1[0] == 'or':
				return op,(t1 or tt1[1])
		elif self.la == 'and' or self.la == 'not' or self.la == ')' or self.la == 'id' or self.la == 'print' or self.la is None: #epsilon transition
			return
		else:
			raise ParseError("in term1_tail: or expected")


	def term1(self):
		""" Term1 -> Term2 Term2_tail. """
		
		if self.la=='(' or self.la=='id' or self.la=='b_var' or self.la=='not':
			t2=self.term2()
			tt2=self.term2_tail()
			if tt2 is None:
				return t2
			if tt2[0] == 'and':
				return (t2 and tt2[1])
		else:
			raise ParseError("in term1: ( or id or b_var or not expected")


	def term2_tail(self):
		""" Term2_tail -> Andop Term2 Term2_tail
                    |. """
		
		if self.la=='and':
			op=self.operator()
			t2=self.term2()
			tt2=self.term2_tail()
			if tt2 is None:
				return op,t2
			if tt2[0] == 'and':
				return op,(t2 and tt2[1])
		elif self.la == 'or' or self.la == 'not' or self.la == ')' or self.la == 'id' or self.la == 'print' or self.la is None: #epsilon transition
			return
		else:
			raise ParseError("in term2_tail: and expected")


	def term2(self):
		""" Term2 -> Factor | Notop Factor. """
		
		if self.la=='(' or self.la=='id' or self.la=='b_var':
			f=self.factor()
			return f #correct?
		elif self.la=='not':
			op=self.operator()
			f=self.factor()
			return  (not f)
		else:
			raise ParseError("in bterm: ( or id or b_var or not expected")




	def factor(self):
		""" Factor -> (Expr)
              		| id
             		| B_var. """
		
		if self.la=='(':
			#token, text = self.la, self.val
			#print(token, text)
			self.match('(')
			e=self.expr()
			#token, text = self.la, self.val
			#print(token, text)
			self.match(')')
			return e
		elif self.la=='id':
			#token, text = self.la, self.val
			#print(token, text)
			varname=self.val
			self.match('id')
			if varname in self.st:
				return self.st[varname]
			
		elif self.la=='b_var':
			#token, text = self.la, self.val
			#print(token, text)
			v=self.val
			if v in ('true', 'TRUE', 'True', 't', 'T','0'):
				self.match('b_var')
				return True
			if v in ('false', 'FALSE', 'False', 'f', 'F','1'):
				self.match('b_var')
				return False


		else:
			raise ParseError ('in factor: ( or id or b_var expected')


	def operator(self):
		""" Orop -> or.
		    Andop -> and.
		    Notop -> not. """
		
		if self.la=='or':
			#token, text = self.la, self.val
			#print(token, text)
			self.match('or')
			return('or')
		elif self.la=='and':
			#token, text = self.la, self.val
			#print(token, text)
			self.match('and')
			return('and')
			
		elif self.la=='not':
			#token, text = self.la, self.val
			#print(token, text)
			self.match('not')
			return('not')

		else:
			raise ParseError ('in operator: or or and or not expected')			

		
# the main part of prog

# create the parser object
parser = MyParser()

# open file for parsing
with open("data.txt","r") as fp:

	# parse file
	try:
		parser.parse(fp)
	except plex.errors.PlexError:
		_,lineno,charno = parser.position()	
		print("Scanner Error: at line {} char {}".format(lineno,charno+1))
	except ParseError as perr:
		_,lineno,charno = parser.position()	
		print("Parser Error: {} at line {} char {}".format(perr,lineno,charno+1))
