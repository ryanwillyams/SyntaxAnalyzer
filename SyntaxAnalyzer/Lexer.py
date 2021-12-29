#Lexical Analyser

import sys
import queue
import itertools, collections
from collections import deque

#global, will pass back to the SA for output
_filename = None
_linecounter = deque()
_printcommand = False               #toggle print to the command terminal
_fileNotFound = False

#Class that holds the token and corresponding lexeme
class Lex:
    def __init__(self, token = None, lexeme = None, line = None):
        self._token = token
        self._lexeme = lexeme
        self._line = line
    
    #token get/set property
    def setToken(self, token):
        self._token = token
    def getToken(self):
        return self._token
    token = property(getToken, setToken)
    
    #lexeme get/set property
    def setLexeme(self, lexeme):
        self._lexeme = lexeme
    def getLexeme(self):
        return self._lexeme
    lexeme = property(getLexeme, setLexeme)
    
    #line get/set property
    def setLine(self, line):
        self._line = line
    def getLine(self):
        return self._line
    line = property(getLine, setLine)  

#input:  list of elements to process and current machine state
#output: machine state value
def fsm_digits(omega, state):
    table = [[0,0,0,0,0,0,0,0,0,0,2,1],
             [1,1,1,1,1,1,1,1,1,1,1,1],
             [2,2,2,2,2,2,2,2,2,2,3,3],
             [3,3,3,3,3,3,3,3,3,3,3,3]]
             
    for i in omega:
        if i.isdigit(): 
            col = int(i)
        elif i == '.':
            col = 10
        else:
            col = 11
        state = table[state][col]
    
    return state        

#input:  list of elements to process and current machine state
#output: machine state value
def fsm_identifier(omega, state):
    table = [[1,0,4,3],
             [1,1,2,3],
             [1,1,2,4],
             [3,3,3,3],
             [4,4,4,4]]
             
    for i in omega:
        if i.isalpha():
            col = 0
        elif i.isdigit():
            col = 1
        elif i == '_':
            col = 2
        else:
            col = 3
        state = table[state][col]
    
    return state     
    
#input:  list of elements to process and current machine state
#output: two lists, tokens and lexemes
def lexer(todo):
    tokens = []
    lexemes = []
    token = ''
    
    #if given a file with no todo, exit lexer
    if len(todo) == 0:
        return tokens, lexemes
    
    #loop continues until all characters in 'todo' are processed
    while len(todo) > 0:
        valid = False
        state = 0               #starting state
        
        #if the top of the stack contains a space, pop it off
        while todo[0].isspace():
            todo.popleft()
            if not todo: break              #needed for pop, else out of bound if last char in todo
        if not todo: break
        
        #getchar and append it to token
        token += todo.popleft()             

        #handle two character operators
        #process 'todo' if there are characters in it. This is required because we need
        # to peek at the next character in 'todo'. This code handles the special cases of
        # operators and seporators (:=, <=, =>, !=, @@).
        if todo:                                   
            if token == ':' and todo[0] == '=':
                tokens.append('operator')
                lexemes.append(':=')
                todo.popleft()
                token = ''
                valid = True

            if token == '=' and todo[0] == '>':
                tokens.append('operator')
                lexemes.append('=>')
                todo.popleft()
                token = ''
                valid = True

            if token == '<' and todo[0] == '=':
                tokens.append('operator')
                lexemes.append('<=')
                todo.popleft()
                token = ''
                valid = True

            if token == '!' and todo[0] == '=':
                tokens.append('operator')
                lexemes.append('!=')
                todo.popleft()
                token = ''
                valid = True
        
            #handle two character separators
            if token == '@' and todo[0] == '@':
                tokens.append('operator')
                lexemes.append('@@')
                todo.popleft()
                token = ''
                valid = True

            #handle comments in code, /* and */ characters are also destroyed
            if token == '/' and todo[0] == '*':
                todo.popleft()
                token = ''
                valid = True
                #pop off all code in between comments
                while token != '*' and todo[0] != '/':
                    todo.popleft()
                todo.appendleft('*')

            if token == '*' and todo[0] == '/':
                todo.popleft()
                token = ''
                valid = True
        
        #check for separator           
        if check_separator(token) and valid == False:
            tokens.append('separator')
            lexemes.append(token)
            token = ''
            valid = True
            
        #check for operator
        if check_operator(token) and valid == False:
            tokens.append('operator')
            lexemes.append(token)
            token = ''
            valid = True

        #check for int and real
        while token and token[0].isdigit():
            if todo:
                token += todo.popleft()                      #getchar()
            elif any(char == '.' for char in token):
                tokens.append('real')
                lexemes.append(token)
                token = ''
                break
            else:
                tokens.append('integer')
                lexemes.append(token)
                token = ''
                break
            
            if fsm_digits(token, state) == 1:
                todo.appendleft(token[-1])
                token = token[:-1]
                tokens.append('integer')
                lexemes.append(token)
                token = ''

            elif fsm_digits(token, state) == 3:
                todo.appendleft(token[-1])
                token = token[:-1]
                tokens.append('real')
                lexemes.append(token)
                token = ''

            continue            #return to the top of the loop      
        
        #check for identifier
        # while token and any(char.isalpha() for char in token):
        while token and token[0].isalpha():
            if todo:
                token += todo.popleft()
            elif any(char.isalpha() for char in token):
                tokens.append('identifier')
                lexemes.append(token)
                token = ''
                break
                
            #check for keyword
            if check_keyword(token) and valid == False:
               tokens.append('keyword')
               lexemes.append(token)
               token = ''
               
            #identifier found
            if fsm_identifier(token, state) == 3:
                todo.appendleft(token[-1])
                token = token[:-1]
                tokens.append('identifier')
                lexemes.append(token)
                token = ''
            
            #unknown token
            if fsm_identifier(token, state) == 4:
                tokens.append('unknown')
                lexemes.append(token)
                token = ''

        #handle any unknowns that may have not hit            
        while token: 
            if todo:
                token += todo.popleft()                 #getchar
                if token[-1].isspace() or check_separator(token[-1]) or check_operator(token[-1]):
                    todo.appendleft(token[-1])          #backup
                    token = token[:-1]        
                    tokens.append('unknown')
                    lexemes.append(token)
                    token = ''
            else:
                break

    #if anything left over in token, append as unknown lexeme
    if token:
        tokens.append('unknown')
        lexemes.append(token)  
    
    print('...Lexer complete!')
    return tokens, lexemes



#input:  A deque() containing Lex objects and string of filehandle
#output: None
def write_tokens_lexemes(deck, fh):
    #print to screen
    if _printcommand:
        print('{0:14}{1:14}{2:1}'.format('Tokens', 'Lexemes', 'Line'))
        print('{0:14}{1:14}{2:1}'.format('------','-------', '----'))
        for l in deck:
            print('{0:14}{1:14}{2:1}'.format(l.token, l.lexeme, l.line))

    #open file so that we can write to it. This will create a new file if DNE
    outputFileHandle = open(outputFilename(fh),'w')

    #print to file
    print('{0:14}{1:14}{2:1}'.format('Tokens', 'Lexemes', 'Line'), file = outputFileHandle)
    print('{0:14}{1:14}{2:1}'.format('------','-------', '----'), file = outputFileHandle)
    for l in deck:
        print('{0:14}{1:14}{2:1}'.format(l.token, l.lexeme, l.line), file = outputFileHandle)

    #close file after writing to it
    print('Your Tokens and Lexemes have been saved as {} in the working directory.'.format(outputFilename(fh)))
    outputFileHandle.close()


#Purpose: to make an output file name from the initial user entered file
#input:  filename
#output: filename with the proper extension
def outputFilename(filename):
    global _filename
    #example input is 'foo.txt'
    #        output is 'foo.RAT'
    dotIndex = filename.find('.')      #find '.'
    name = filename[:dotIndex]         #start at beginning and go to dotIndex
    _filename = name
    extension = '.RAT'
    return name + extension    

#input:  Token
#output: True if keyword hit, otherwise False
def check_keyword(token):
   if token == 'int' or token == 'boolean' or token == 'real' or token == 'if' or token == 'else' or token == 'endif' or token == 'while' or token == 'return' or token == 'read' or token == 'write' or token == 'true' or token == 'false' or token == 'function':
       return True
   else:
       return False
    
#input:  Token
#output: True if single character separator, otherwise return false
def check_operator(c):
    if c == '<' or c == '>' or c == '+' or c == '*' or c == '-' or c == '/' or c == '=':
        return True
    else:
        return False

#input:  Token
#output: True if single character separator, otherwise return false
def check_separator(c):
    if c == '(' or c == ')' or c == '{' or c == '}' or c == '[' or c == ']' or c == ':' or c == ';' or c == ',':
        return True
    else:
        return False


#process file and prepare list of characters to process
#input:  User's filename
#output: List of characters that are in text file          
def process_file(user_file):
    global _linecounter
    global _fileNotFound
    value = 1
    file = []
    todo = deque()  
      
    #open file
    #try and open file, if fail then give error and exit
    try:
        with open(user_file) as fh:
     #   with open('testcase1.txt') as fh:          #implicitly open and close the file
            if (fh):
                print('File open!')
                for i in fh:
                    line = i
                   # line = i.rstrip()       #removes leading and trailing characters (e.g. EOF)
                    file.append(line)
            else: 
                print('File empty')
    
        #print contents of file
        if _printcommand:
            print('')
            print('Contents of file:')
            print('-----------------')
        for i in file:
            if _printcommand:
                print(i)      
            for j in i:
                if j == '\n':
                    todo.append(' ')
                    value += 1
                else:
                    todo.append(j)
                    if j != ' ':
                        _linecounter.append(value)
        if _printcommand:
            print('-----------------')
            print('')
    
    except FileNotFoundError:
        _fileNotFound = True
        print('')
        print('Your file was not found!')
        print('')
        
    return todo, user_file

#Purpose: initilize necessary variables, run a loop which opens user .txt file and collects
# lexemes and tokens from the file and prints them to terminal/file. Once user types 'quit'
# the loop is broken and the program exits.
def main():
    #initialize necessary variables
    tokens = []           #will hold tokens
    lexemes = []          #will hold lexemes
    todo = []             #list of characters left to process
    user = ''             #users filehandle or escape command (quit)
    dequeOfLex = deque()
    global _linecounter 
    global _fileNotFound
    _fileNotFound = False
    _linecounter = deque()
     
    #run loop until user enters quit
   # while True:
    user_file = input('Enter file you would like to open (type "quit" to exit): ')
    if user_file != 'quit':
        print('\nLexer working...')
        todo, user_fh = process_file(user_file)
        tokens, lexemes = lexer(todo)
    #user wants to quit    
    else:
        print('Goodbye!')
        sys.exit()
     
    if not _fileNotFound:    
        #append tokens, lexemes, and line number to deque
        for i in range(len(tokens)):
            lex = Lex(tokens[i], lexemes[i], _linecounter[0])
            for length in range(len(lex.lexeme)):
                _linecounter.popleft()
            dequeOfLex.append(lex)   

        #print the tokens, lexemes, and cooresponsing line number to user file
        write_tokens_lexemes(dequeOfLex, user_fh)
    
    return dequeOfLex, _filename
    
if __name__ == '__main__':
    main()