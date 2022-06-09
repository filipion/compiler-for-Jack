# -*- coding: utf-8 -*-
"""
Created on Sun Mar  6 14:27:43 2022

@author: filip
"""

keyWords = {'class', 'method', 'function', 'constructor', 'int', 'boolean', 'char',
            'void', 'var', 'static', 'field', 'let', 'do', 'if', 'else', 'while',
            'return', 'true', 'false', 'null', 'this'}

keyWordConsts = {'true':-1, 'false':0, 'null':0, 'this':0}
kindToSegment = {'var':'local', 'argument':'argument', 'field':'this', 'static':'static'}
opToVM = {'+':'add', '-':'sub', '|':'or', '&':'and', '<':'lt', '>':'gt', '=':'eq', '*':'call Math.multiply 2', '/':'call Math.divide 2'}

OPS = "+-*/&|<>="
UNARY_OPS = "-~"

### 1 Tokenizer

# Part of the tokenizer. Splits a Jack program string into
# a list of tokens
def word_split(s):
    s = s + " "
    words = []
    current = ""
    in_string = False
    for c in s:
        if c == "\"" and not in_string:
            in_string = True
            if current != "":
                words.append(current)
            current = c
        elif c == "\"":
            in_string = False
            current += c
            words.append(current)
            current = ""     
        elif c in " \n\t" and not in_string:
            if current != "":
                words.append(current)
                current = ""
        elif c in '{}()[].,;+-*/&|<>=~' and not in_string:
            if current != "":
                words.append(current)
                current = ""
            words.append(c)
        else:
            current = current + c
    
    return words


# tokenize for the Jack toy language. Duck typing the separated tokens
# that may occur in Jack
def tokenizer(s):
    
    def tokenize(word):
        if word in keyWords:
            return ['keyword', word]
        elif word.isnumeric() and 0 <= int(word) <= 32767:
            return ['integerConstant', word]
        elif len(word) == 1 and word in '{}()[].,;+-*/&|<>=~':
            return ['symbol', word]
        elif word[0] == '\"' and word[-1] == '\"':
            return ['stringConstant', word]
        elif not word[0] in '1234567890':
            return ['identifier', word]
        else:
            raise ValueError("Invalid token: {}".format(word))
        
    return [tokenize(w) for w in word_split(s)]


# takes in a Jack program and returns the same program with comments removed
def uncomment(s):
    ans = ""
    comment = 0
    
    for c, nex in zip(s, s[1:]):
        if comment == 0:
            if c == '/' and nex == '/':
                comment = 1
            elif c == '/' and nex == '*':
                comment = 2
            else:
                ans += c
        elif comment == 1 and c == '\n':
            comment = 0
        elif comment == 2 and c == '*' and nex == '/':
            comment = 3
        elif comment == 3:
            comment = 0
            
    return(ans)


### 2 Environment symbol tables

# The entries in our compiler's symbol table
class VarBinding():
    def __init__(self, typ, kind, idx):
        self.kind = kind #field, static, var (normal local variable) or argument
        self.typ = typ
        self.idx = idx

    def __repr__(self):
        return "{} variable of type {} bound at index {}".format(self.kind, self.typ, self.idx)


# List of hash tables to maintain the environment of a program
class Environment():
    
    def __init__(self):
        self.symbols = [{}] #list of frames
        self.curr = 0 #maintain a pointer to the current frame of the env
        self.varcount_list = [{'field':0, 'static':0, 'var':0, 'argument':0}] #we keep a frequency vector of each variable kind. one per frame
    
    def __repr__(self):
        return str(self.symbols)
    
    def push(self):
        # creates a new frame. must be called when a new scope is created by the program
        self.symbols.append({})
        self.varcount_list.append({'field':0, 'static':0, 'var':0, 'argument':0})
        self.curr += 1
        
    def pop(self):
        self.symbols.pop()
        self.varcount_list.pop()
        self.curr -= 1
        
    def add(self, variable_name, typ, kind):
        # adds a VarBinding to the current frame
        counts = self.varcount_list[self.curr]
        self.symbols[self.curr][variable_name] = VarBinding(typ, kind, counts[kind])
        counts[kind] += 1
    
    def lookup(self, name):
        # finds the most recent frame that contains a binding for an input variable name
        table = self.symbols
        where = -1
        for where in range(-1, -len(table) - 1, -1):
            if name in table[where].keys():
                return table[where][name]
        
        return None
    
    def get_local_count(self):
        idx = self.varcount_list[self.curr]
        return idx['var']


### 3 Compiler
# class to compile the Jack language
class Compiler():
    
    def __init__(self):
        self.env = Environment()
        self.cls_name = "_"
        self.cls_size = 0
        self.cursor = 0  #a cursor to where the next code block to be compiled starts, most methods will advance this cursor as they compile the code
        self.tokens = [] #tokens to compile
        self.label_id = 0
    

    # used by almost every function in the compiler to read the current token
    def get_token(self):
        return self.tokens[self.cursor].copy()
      

    def compileClass(self, input_tokens):
        self.tokens = input_tokens
        self.cls_name = self.tokens[self.cursor + 1][1]
        self.cursor += 3
        code = ""
        
        while(self.get_token() in [['keyword', 'static'], ['keyword', 'field']]):
            self.compileClassVarDec()
        while(self.get_token() != ['symbol', '}']):
            code += self.compileSubDec()
            
        return code
            
    
    def compileClassVarDec(self):
        if(self.get_token()[1] == 'field'):
            self.cls_size += 1
            
        self.env.add(self.tokens[2 + self.cursor][1], self.tokens[1 + self.cursor][1], self.tokens[self.cursor][1])
        self.cursor += 4
    
    
    def compileSubDec(self):
        self.env.push() # we require a new stack frame for local names
        fn_kind = self.tokens[self.cursor][1]
        fn_type = self.tokens[self.cursor + 1][1]
        fn_name = self.tokens[self.cursor + 2][1]
        if fn_kind == 'method':
            self.env.add("this", self.cls_name, "argument")
        
        # function header
        self.cursor += 1 #skip (method|function|constructor)
        self.cursor += 1 #skip return type
        self.cursor += 1 #skip fn name
        self.cursor += 1 #skip '('
        self.compileParamList()
        self.cursor += 1 # ')'
        
        # function body
        body = self.compileSubBody()
        num_var = self.env.get_local_count()
        self.env.pop()
        
        # VM code
        ans = ""
        ans += "function {}.{} {}\n".format(self.cls_name, fn_name, num_var)
        if(fn_kind == 'constructor'): # constructors call a special Memory.alloc function under the hood
            body = "  push constant {}\n".format(self.cls_size) \
                 + "  call Memory.alloc 1\n" \
                 + "  pop pointer 0\n" \
                 + body
        elif(fn_kind == 'method'):
            body = "  push argument 0\n"\
                 + "  pop pointer 0\n"\
                 + body
        ans += body
        return  ans
    
    
    def compileParamList(self):
        if(self.get_token() == ['symbol', ')']): # no args case
            return
        
        while(self.tokens[self.cursor + 2] == ['symbol', ',']):
            self.env.add(self.tokens[self.cursor + 1][1], self.tokens[self.cursor + 0][1], "argument")
            self.cursor += 3
        
        self.env.add(self.tokens[self.cursor + 1][1], self.tokens[self.cursor + 0][1], "argument")
        self.cursor += 2
            
    
    def compileSubBody(self):
        self.cursor += 1
        while(self.get_token() == ['keyword', 'var']):
            self.compileVarDec()
            
        body = self.compileStatements()
        self.cursor += 1
        return body
    
    
    def compileVarDec(self):
        ptr = self.cursor
        self.env.add(self.tokens[2 + ptr][1], self.tokens[1 + ptr][1], self.tokens[ptr][1])
        self.cursor += 4
            

    def compileStatements(self):
        ans = ""
        while(self.get_token()[1] in {'let', 'do', 'while', 'if', 'return'}):
            first_statement = self.compileStatement()
            ans += first_statement
        return ans
        
    
    def compileStatement(self):
        current = self.tokens[self.cursor]
        self.cursor += 1
        
        if current[1] == 'return':
            if self.get_token()[1] == ';':
                returned = "  push constant 0\n"
                self.cursor += 1
                return returned + "  return\n"
            else:
                returned = self.compileExpr()
                self.cursor += 1 # skip ';'
                return returned + "  return\n"
                  
        elif current[1] == 'let':
            to_variable = self.get_token()
            base = self.pushVM(to_variable)
            self.cursor += 1
            if self.get_token() == ['symbol', '=']: # assignment to normal variable
                self.cursor += 1
                exp = self.compileExpr()
                self.cursor += 1
                return exp + self.popVM(to_variable[1])
            elif self.get_token() == ['symbol', '[']: # assignment to array
                self.cursor += 1
                idx = self.compileExpr()
                self.cursor += 1
                self.cursor += 1
                exp = self.compileExpr()
                self.cursor += 1
                ans = base + idx + "  add\n  pop temp 0\n"
                ans += exp
                ans += "  push temp 0\n  pop pointer 1\n  pop that 0\n"
                return ans
            else:
                raise ValueError("Illegal let expression")
        
        elif current[1] == 'while':
            self.cursor += 1 # skip '('
            condition = self.compileExpr()
            self.cursor += 2 # skip ')' '{'
            body = self.compileStatements()
            self.cursor += 1 # skip '}'
            
            lines = "  label LOOP_{}\n".format(self.label_id)
            lines += condition
            lines += "  not\n"
            lines += "  if-goto END_LOOP_{}\n".format(self.label_id)
            lines += body
            lines += "  goto LOOP_{}\n".format(self.label_id)
            lines += "  label END_LOOP_{}\n".format(self.label_id)
            
            self.label_id += 1
            return lines
        
        elif current[1] == 'if':
            self.cursor += 1 # skip '('
            condition = self.compileExpr()
            self.cursor += 2 # skip ')' '{'
            branch_1_code = self.compileStatements()
            self.cursor += 1 # skip '}'
            
            if(self.get_token()[1] == 'else'):
                self.cursor += 2 # skip else {
                branch_2_code = self.compileStatements()
                self.cursor += 1
            else:
                branch_2_code = ""
    
            lines = ""
            lines += condition
            lines += "  not\n"
            lines += "  if-goto ELSE_{}\n".format(self.label_id)
            lines += branch_1_code
            lines += "  goto ENDIF_{}\n".format(self.label_id)
            lines += "  label ELSE_{}\n".format(self.label_id)
            lines += branch_2_code
            lines += "  label ENDIF_{}\n".format(self.label_id)
            
            self.label_id += 1
            return lines
        
        elif current[1] == 'do':
            ans = self.compileTerm()
            self.cursor += 1
            ans += "  pop temp 0\n"
            return ans
                 
        else:
            raise ValueError("Illegal statement " + self.tokens[self.cursor])
            
    
    def compileExpr(self):
        first_term = self.compileTerm()
        next_t = self.get_token()
        
        if next_t[1] in OPS:
            self.cursor += 1
            rest_of_expr = self.compileExpr()
            return first_term + rest_of_expr + "  " + opToVM[next_t[1]] + "\n"
        else:
            return first_term
    

    def compileExprList(self):
        if(self.get_token() == ['symbol', ')']): # no args case
            return "", 0
        
        first_expr = self.compileExpr()
        if self.get_token()[1] == ",": # 2 or more args
            self.cursor += 1
            other_args, n_args = self.compileExprList()
            return first_expr + other_args, 1 + n_args
        else: # 1 arg
            return first_expr, 1
    
    
    def compileTerm(self):
        current = self.tokens[self.cursor]
        self.cursor += 1
        
        #identifier(), class.method or VarName case
        if current[0] == 'identifier':
            if self.get_token()[1] == '(': 
                self.cursor += 1
                args, n_args = self.compileExprList()
                self.cursor += 1
                return args + "  call {}.{} {}\n".format(self.cls_name, current[1], n_args)
            
            elif self.get_token()[1] == '.': # method-like call
                self.cursor += 1
                method_name = self.get_token()[1]
                self.cursor += 2
                args, n_args = self.compileExprList()
                self.cursor += 1
                
                # Method calls need to be handles separately and will look different
                # in the case of a method call, the function will also accept
                # a reference to the calling object, as argument 0
                binding = self.env.lookup(current[1])
                if(binding == None):
                    ans = args
                    ans += "  call {}.{} {}\n".format(current[1], method_name, n_args)
                else:
                    ans = self.pushVM(current)
                    ans += args
                    ans += "  call {}.{} {}\n".format(binding.typ, method_name, n_args + 1) #different for method calls
                
                    
                return ans
            
            elif self.get_token()[1] == '[': # array evaluation
                ans = self.pushVM(current)
                self.cursor += 1
                ans += self.compileExpr()
                ans += "  add\n"
                ans += "  pop pointer 1\n"
                ans += "  push that 0\n"
                return ans
            
            else: #variable
                return self.pushVM(current)
        
        # '(' expr ')' case
        elif current[1] == "(": 
            ans = self.compileExpr() 
            self.cursor += 1 # skips ')'
            return ans
        
        # '-' expr case
        elif current[1] in "-~":
            return self.compileTerm() + "  neg\n"
        
        # constant case
        elif current[0] in {'integerConstant', 'stringConstant'} or \
            current[1] in keyWordConsts:
            return self.pushVM(current)
        
        else:
            raise ValueError("Invalid term {}".format(self.tokens[self.cursor: self.cursor+5]))
            

    # bytecode for a basic push instruction:
    # The Environment keeps track of variable type and remembers the correct 
    # segment of each variable name (the segments are 'var', 'static', object 'field' (mapped to 'this')), or function 'argument'
    def pushVM(self, token):
        
        [typ, name] = token
        data = self.env.lookup(name)
        if data:
            arg1, arg2 = kindToSegment[data.kind], data.idx
        else:
            if typ == 'integerConstant':
                arg1, arg2 = 'constant', name
            elif typ == 'keyword' and name == 'this':
                arg1, arg2 = 'pointer', 0
            elif typ == 'keyword' and name in keyWordConsts.keys():
                arg1, arg2 = 'constant', keyWordConsts[name]
            else:
                raise ValueError("{} not defined".format(name))

        line = "  push {} {}\n".format(arg1, arg2)
        
        return line
    
    
    # bytecode for a basic pop instruction
    # see also pushVM
    def popVM(self, name):
        data = self.env.lookup(name)
        if data:
            arg1, arg2 = kindToSegment[data.kind], data.idx
        else:
            raise ValueError("{} not defined in the Jack environment".format(name))
        line = "  pop {} {}\n".format(arg1, arg2)
        return line
        
    
    def debug(self, message = ""):
        print(message)
        view = self.tokens[self.cursor: self.cursor + 3]
        print(view)


def unit_test(test_num):
    i = test_num
    comp = Compiler()
    f = open("testing/ex{}.jack".format(i))
    jack_program = f.read()
    f_ok = open("testing/ex{}_ok.vm".format(i))
    vm_program = f_ok.read()
    compiled_program = comp.compileClass(tokenizer(jack_program))
    
    try:
        assert(compiled_program == vm_program)
    except:
        print("Possible compilation failure:")
        print(compiled_program)
        print("Reference version for test {}:".format(test_num))
        print(vm_program)


def main():
    f_name = "testing/ex1.jack".format(3)
    comp = Compiler()
    print(comp.env)
    f = open(f_name)
    jack_program = f.read()
    compiled_program = comp.compileClass(tokenizer(jack_program))
    print(compiled_program)

for i in {1, 2, 3, 5, 6, 7}:
    unit_test(i)

#main()



    
