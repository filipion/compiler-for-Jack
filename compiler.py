# -*- coding: utf-8 -*-
"""
Created on Sun Mar  6 14:27:43 2022

@author: user
"""
keyWords = {'class', 'method', 'function', 'constructor', 'int', 'boolean', 'char',
            'void', 'var', 'static', 'field', 'let', 'do', 'if', 'else', 'while',
            'return', 'true', 'false', 'null', 'this'}

keyWordConsts = {'true', 'false', 'null', 'this'}

# Splits the input string into a list of words. We have to reimplement
# string.split here in order to tokenize strings like '2+3'
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


# tokenize for the Jack toy language. This just names the separated tokens
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


class Identifier():
    def __init__(self, typ, kind):
        self.kind = kind
        self.typ = typ

    def __repr__(self):
        return "{}, {}".format(self.typ, self.kind)


class Environment():
    symbols = [{}]
    curr = 0

    def __repr__(self):
        return str(self.symbols)
    
    def push(self):
        self.symbols.append({})
        self.curr += 1
        
    def pop(self):
        self.symbols.pop()
        self.curr -= 1
        
    def add(self, name, typ, kind):
        
        self.symbols[self.curr][name] = Identifier(typ, kind)
        print(self)




class Parser():
    
    env = Environment()
    
        
    def nextblock(words, isblock):
            alias = words.copy()
            alias[0] = [1,1]
            lst = [isblock(x[1]) for x in alias]
            if True in lst:
                return lst.index(True)
            else:
                return len(words)
    
    
    #done. the recursive nextmethod function is inefficient (maybe)
    def compileClass(self, words):
        ans = ['class', words[0], words[1], words[2]]
    
        def classBody(words):
            if len(words) == 0:
                return []
            elif words[0][1] in {'static', 'field'}:
                i = words.index(['symbol', ';'])
                return [Parser.compileClassVarDec(self, words[0:i+1])] + classBody(words[i+1:])
            elif ismethod(words[0][1]):
                i = Parser.nextblock(words, ismethod) # small function that finds where current method ends
                return [Parser.compileSubDec(self, words[0:i])] + classBody(words[i:])
            else:
                raise ValueError("Invalid class declaration")
                
        def ismethod(x):
            return (x in {'constructor', 'function', 'method'})
        
        ans = ans + classBody(words[3:-1]) + [words[-1]]
        print(self.env)
        
        return ans
    
    
    #done
    def compileClassVarDec(self, words):
        self.env.add(words[2][1], words[1][1], words[0][1])
        return ['classVarDec'] + words
    
    
    #done
    def compileSubDec(self, words):
        i = words.index(['symbol', ')'])
        self.env.push()
        
        ans = ['subroutineDec'] + words[0:4]
        ans += [Parser.compileParamList(self, words[4:i])]
        ans += [['symbol', ')']]
        ans += [Parser.compileSubBody(self, words[i+1:])]
        self.env.pop()
        return  ans
    
    
    #done
    def compileParamList(self, words):
        for arg, typ in zip(words[1::3], words[0::3]):
            self.env.add(arg[1], typ[1], "arg")
        return ["parameterList"] + words
    
    
    #done
    def compileSubBody(self, words):
        
        def innerBody(words):
            if ['keyword', 'var'] in words:
                self.env.add(words[2][1], words[1][1], words[0][1])
                i = words.index(['symbol', ';'])
                ans = []
                ans += [Parser.compileVarDec(words[:i+1])]
                ans += innerBody(words[i+1:])
                return ans
            else:
                return [Parser.compileStatements(words)]
        
        return ['subroutineBody', words[0]] + innerBody(words[1:-1]) + [words[-1]]
    
    
    #done
    def compileVarDec(words):
        return ["varDec"] + words
    
    
    #done
    def compileStatements(words):
        ans = ["statements"]
        
        def innerStats(words):
            if len(words) == 0:
                return []
            else:
                i = Parser.firstStat(words)
                return [Parser.compileStat(words[:i+1])] + innerStats(words[i+1:])
        
        return ans + innerStats(words)
        
    
    # parse a single generic statement
    def compileStat(words):
        
        if words[0][1] == 'return':
            if len(words) > 2:
                return ['returnStatement'] + [words[0]] + \
                        [Parser.compileExpr(words[1:-1])] + [words[-1]]
            else: 
                return ['returnStatement'] + words
                   
        elif words[0][1] == 'let':
            if words[2] == ['symbol', '=']:
                return ['letStatement'] + words[0:3] + \
                    [Parser.compileExpr(words[3:-1])] + [words[-1]]
            elif words[2] == ['symbol', '['] and \
                 words[4] == ['symbol', ']']:
                return ['letStatement'] + words[0:3] + \
                    [Parser.compileExpr([words[3]])] + words[4:6] + \
                    [Parser.compileExpr(words[6:-1])] + [words[-1]]
            else:
                raise ValueError("Unusual let expression")
        
        elif words[0][1] == 'while':
            idx = words.index(['symbol', '{'])
            return ['whileStatement'] + words[0:2] + \
                [Parser.compileExpr(words[2:idx-1])] + \
                words[idx-1:idx+1] + [Parser.compileStatements(words[idx+1:-1])] + \
                [words[-1]]
        
        elif words[0][1] == 'if':
            idx = words.index(['symbol', '{'])
            ridx = Parser.accolade(words, idx)
            ans = ['ifStatement'] + words[0:2] + \
                [Parser.compileExpr(words[2:idx-1])] + \
                words[idx-1:idx+1] + [Parser.compileStatements(words[idx+1:ridx])] + \
                [words[ridx]]
            if ridx == len(words) - 1:
                return ans
            else:
                return ans + words[ridx+1: ridx+3] +\
                    [Parser.compileStatements(words[ridx+3:-1])] +\
                    [["symbol", "}"]]
        
        elif words[0][1] == 'do':
            return ['doStatement'] + [words[0]] + \
                    Parser.compileTerm(words[1:-1])[1:] + [words[-1]]
                 
        else:
            return ['Xstatement'] + words
    
    
    # receives list of tokens enclosed by {}. checks if the endpoints are linked
    def accolade(words, startptr, lp='{', rp='}'):
        LEFT = ['symbol', lp]
        RIGHT = ['symbol', rp]
        
        counter = 1
        ptr = startptr + 1
        
        while counter > 0:
            x = words[ptr]
            if x == LEFT:
                counter += 1
            if x == RIGHT:
                counter -= 1
            ptr += 1
            
        return ptr - 1
    
    
    # takes a block of statements and delimits the first statement
    def firstStat(words):
        if words[0][1] in {'return', 'let', 'do'}:
            return words.index(['symbol', ';'])
        elif words[0][1] in {'while', 'if'}:
            lidx = words.index(['symbol', '{'])
            ridx = Parser.accolade(words, lidx)
            if ridx == len(words) - 1:
                return ridx
            elif words[ridx + 1] == ['keyword', 'else']:
                lidx2 = ridx + 2
                ridx2 = Parser.accolade(words, lidx2)
                return ridx2
            else:
                return ridx
            
    
    def compileExpr(words):
        
        def helper(words):
            opptr, first_term = Parser.findTermEnd(words)
            opptr += 1
            if opptr < len(words):
                return [first_term] + [words[opptr]] + helper(words[opptr+1:])
            else:
                return [first_term]
            
        return ['expression'] + helper(words)
    
    
    #last function
    def compileExprList(words):
        def helper(words):
            if words == []:
                return []
            
            elif ['symbol', ','] not in words:
                return [Parser.compileExpr(words)]
            
            else:
                i = words.index(['symbol', ','])
                return [Parser.compileExpr(words[:i])] + [words[i]] + helper(words[i+1:])            
        return ['expressionList'] + helper(words)
    
    
    # use findTermEnd instead
    def compileTerm(words):
        return Parser.findTermEnd(words)[1]
    
    
    # takes an input starting with a term and delimits that term
    def findTermEnd(words):
        ans = ['term']
        # edge case when we have a single token
        if len(words) == 1:
                return 0, ans + [words[0]]
        
        #identifier(variable), function/method call, [] operator
        if words[0][0] == 'identifier':
            if words[1][1] == '(':
                ans += words[0:2] 
                lidx = Parser.accolade(words, 1, '(', ')')
                ans += [Parser.compileExprList(words[2:lidx])]
                ans += [words[lidx]]
                return lidx, ans
            elif words[1][1] == '.':
                ans += words[0:4] 
                lidx = Parser.accolade(words, 3, '(', ')')
                ans += [Parser.compileExprList(words[4:lidx])]
                ans += [words[lidx]]
                return lidx, ans
            elif words[1][1] == '[':
                ans += words[0:2]
                lidx = Parser.accolade(words, 1, '[', ']')
                ans += [Parser.compileExpr(words[2:lidx])]
                ans += [words[lidx]]
                return Parser.accolade(words, 1, '[', ']'), ans
            else:
                return 0, ans + [words[0]]
            
        elif words[0][1] == "(":
            ans += words[0:1]
            lidx = Parser.accolade(words, 0, '(', ')')
            ans += [Parser.compileExpr(words[1:lidx])]
            ans += [words[lidx]]
            return Parser.accolade(words, 0, '(', ')'), ans
        
        elif words[0][1] in "-~":
            next_words = words[1:].copy()
            next_end, next_compiled = Parser.findTermEnd(next_words)
            
            return (next_end + 1), ans + [words[0]] + [next_compiled]
                
        elif words[0][0] in {'integerConstant', 'stringConstant'} or \
            words[0][1] in keyWordConsts:
            return 0, ans + [words[0]]
        
        else:
            raise ValueError("Invalid term {}".format(words))
        
    
    def unit_tests():
        assert(Parser.firstStat(tokenizer('while {{}}{}} then {} else {}')) == 4)
        assert(Parser.firstStat(tokenizer('if {{}}{}} let {} else {}')) == 4)
        assert(Parser.firstStat(tokenizer('if {} else {} ')) == 5)
        assert(Parser.firstStat(tokenizer('if (YES) {YESS} else{}')) == 9)
        

Parser.unit_tests()


def xmlize(syn_tree, deep=0):
    if type(syn_tree) is str:
        ans = ""
        if syn_tree == "<":
            ans = "&lt;"
        elif syn_tree == ">":
            ans = "&gt;"
        elif syn_tree == "&":
            ans = "&amp;"
        elif syn_tree == "\"":
            ans = "&quot;"
        elif syn_tree[0] == "\"":
            ans = syn_tree[1:-1]
        else:
            ans = syn_tree
        return " " + ans + " "
    else:
        tag = syn_tree[0]
        body = "".join([xmlize(x, deep+1) for x in syn_tree[1:]])
        d = "  " * deep
        if len(syn_tree) == 2 and type(syn_tree[1]) is str:
            return "{}<{}>{}</{}>\n".format(d, tag, body, tag)  
        else:
            return "{}<{}>\n{}{}</{}>\n".format(d, tag, body, d, tag)


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


def create_test_xml(location):
    fname = "Square\\Square"
    infile = location + fname + ".jack"
    with open(infile) as f:
        code = f.read()
        code = uncomment(code)
        tokens = tokenizer(code)
        xml = xmlize(Parser.compileClass(tokens))
        
    with open(location + fname + "ANS.xml", "w") as fout:
        fout.write(xml)
        
pr = Parser()
    
EX1 = pr.compileClass(tokenizer("""
class program{
    method void do_stuff (){
        var int counter = 0;
        
        while (a > 0){
            let b = b + 1;
            let q = \" asdad adasga dfdf while (a > 0) \" - 2;
            do a();
        }
        
        if (expr) 
            {do nothing();}
        else
            {do something(one, two);}

    }
}
"""
))


EX2 = pr.compileClass(tokenizer("""
class program2{
    field int a;
    static string b;
    
    constructor void program(){}
    method int foo(char a, int b, float c){
        var int counter = 0;    
        
    }  
}
"""
))

EX3 = pr.compileSubDec(tokenizer("""
method int foo(int a, int b, int c){
    return 0;
}  
"""
))

EX4 = Parser.compileStat(tokenizer("""
if(s){
    return v[10];
}
else{
     
}  
"""
))

