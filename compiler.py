# -*- coding: utf-8 -*-
"""
Created on Sun Mar  6 14:27:43 2022

@author: user
"""
keyWords = {'class', 'method', 'function', 'constructor', 'int', 'boolean', 'char',
            'void', 'var', 'static', 'field', 'let', 'do', 'if', 'else', 'while',
            'return', 'true', 'false', 'null', 'this'}

keyWordConsts = {'true':-1, 'false':0, 'null':0, 'this':0}
kindToSegment = {'var':'local', 'argument':'argument', 'field':'this', 'static':'static'}
opToVM = {'+':'add', '-':'sub', '|':'or', '&':'and', '<':'lt', '>':'gt', '=':'eq'}

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
    def __init__(self, typ, kind, idx):
        self.kind = kind
        self.typ = typ
        self.idx = idx

    def __repr__(self):
        return "{}, {}, {}".format(self.typ, self.kind, self.idx)


class Environment():
    symbols = [{}]
    curr = 0
    indices = [{'field':0, 'static':0, 'var':0, 'argument':0}]

    
    def __repr__(self):
        return str(self.symbols)
    
    
    def push(self):
        self.symbols.append({})
        self.indices.append({'field':0, 'static':0, 'var':0, 'argument':0})
        self.curr += 1
        
    def pop(self):
        self.symbols.pop()
        self.indices.pop()
        self.curr -= 1

        
    def add(self, name, typ, kind):
        idx = self.indices[self.curr]
        
        
        self.symbols[self.curr][name] = Identifier(typ, kind, idx[kind])
        idx[kind] += 1
        
    
    def lookup(self, name):
        table = self.symbols.copy()
        def helper(self, name, table):
            if table == [{}] or len(table) == 0:
                return None
            elif name in table[-1].keys():
                return table[-1][name]
            else:
                return helper(self, name, table[:-1])
        
        return helper(self, name, table)
        
        




class Parser():
    
    env = Environment()
    code = ""
    
        
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
            self.env.add(arg[1], typ[1], "argument")
        return ["parameterList"] + words
    
    
    #done
    def compileSubBody(self, words):
        
        def innerBody(words):
            if ['keyword', 'var'] in words:
                i = words.index(['symbol', ';'])
                ans = []
                ans += [Parser.compileVarDec(self, words[:i+1])]
                ans += innerBody(words[i+1:])
                return ans
            else:
                return [Parser.compileStatements(self, words)]
        
        return ['subroutineBody', words[0]] + innerBody(words[1:-1]) + [words[-1]]
    
    
    #done
    def compileVarDec(self, words):
        self.env.add(words[2][1], words[1][1], words[0][1])
        return ["varDec"] + words
    
    
    #done
    def compileStatements(self, words):#TODO
        ans = ["statements"]
        
        def innerStats(words):
            if len(words) == 0:
                return []
            else:
                i = Parser.firstStat(words)
                return [Parser.compileStat(self, words[:i+1])] + innerStats(words[i+1:])
        
        return ans + innerStats(words)
        
    
    # parse a single generic statement
    def compileStat(self, words): #TODO
        
        if words[0][1] == 'return':
            if len(words) > 2:
                return ['returnStatement'] + [words[0]] + \
                        [Parser.compileExpr(self, words[1:-1])] + [words[-1]]
            else: 
                return ['returnStatement'] + words
                   
        elif words[0][1] == 'let':
            if words[2] == ['symbol', '=']:
                Parser.popVM(self, words[1][1])
                return ['letStatement'] + words[0:3] + [Parser.compileExpr(self, words[3:-1])] + [words[-1]]
            elif words[2] == ['symbol', '['] and \
                 words[4] == ['symbol', ']']:
                return ['letStatement'] + words[0:3] + \
                    [Parser.compileExpr(self, [words[3]])] + words[4:6] + \
                    [Parser.compileExpr(self, words[6:-1])] + [words[-1]]
            else:
                raise ValueError("Unusual let expression")
        
        elif words[0][1] == 'while':
            idx = words.index(['symbol', '{'])
            return ['whileStatement'] + words[0:2] + \
                [Parser.compileExpr(self, words[2:idx-1])] + \
                words[idx-1:idx+1] + [Parser.compileStatements(self, words[idx+1:-1])] + \
                [words[-1]]
        
        elif words[0][1] == 'if':
            idx = words.index(['symbol', '{'])
            ridx = Parser.accolade(words, idx)
            ans = ['ifStatement'] + words[0:2] + \
                [Parser.compileExpr(self, words[2:idx-1])] + \
                words[idx-1:idx+1] + [Parser.compileStatements(self, words[idx+1:ridx])] + \
                [words[ridx]]
            if ridx == len(words) - 1:
                return ans
            else:
                return ans + words[ridx+1: ridx+3] +\
                    [Parser.compileStatements(self, words[ridx+3:-1])] +\
                    [["symbol", "}"]]
        
        elif words[0][1] == 'do':
            return ['doStatement'] + [words[0]] + \
                    Parser.compileTerm(self, words[1:-1])[1:] + [words[-1]]
                 
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
            
    
    def compileExpr(self, words):
        
        def helper(words):
            opptr, first_term = Parser.findTermEnd(self, words)
            opptr += 1
            if opptr < len(words):
                return str(first_term) + helper(words[opptr+1:]) + "  " + opToVM[words[opptr][1]] + "\n"
            else:
                return first_term
            
        return ['expression'] + [helper(words)]
    
    
    #last function
    def compileExprList(self, words):
        def helper(words):
            if words == []:
                return '', 0
            
            elif ['symbol', ','] not in words:
                return Parser.compileExpr(self, words)[1], 1
            
            else:
                i = words.index(['symbol', ','])
                return Parser.compileExpr(self, words[:i])[1] + helper(words[i+1:])[0], 1 + helper(words[i+1:])[1]            
        
        return helper(words)[0], helper(words)[1]
    
    
    # use findTermEnd instead
    def compileTerm(self, words):
        return str(Parser.findTermEnd(self, words)[1])
    
    
    # takes an input starting with a term and delimits that term
    def findTermEnd(self, words):
        ans = ['term']
        # edge case when we have a single token
        if len(words) == 1:
                return 0, Parser.pushVM(self, words[0])
        
        #identifier(variable), function/method call, [] operator
        if words[0][0] == 'identifier' and len(words) > 1:
            if words[1][1] == '(':
                lidx = Parser.accolade(words, 1, '(', ')')
                [args, n_args] = Parser.compileExprList(self, words[2:lidx])
                return lidx, args + "  call CLS.{} {}\n".format(words[0][1], n_args)
            elif words[1][1] == '.':
                lidx = Parser.accolade(words, 3, '(', ')')
                [args, n_args] = Parser.compileExprList(self, words[4:lidx])
                return lidx, args + "  call {}.{} {}\n".format(words[0][1], words[2][1], n_args)
            elif words[1][1] == '[': #TODO
                ans += words[0:2]
                lidx = Parser.accolade(words, 1, '[', ']')
                ans += [Parser.compileExpr(self, words[2:lidx])]
                ans += [words[lidx]]
                return Parser.accolade(words, 1, '[', ']'), ans
            else:
                return Parser.findTermEnd(self, [words[0]])
            
        elif words[0][1] == "(":
            lidx = Parser.accolade(words, 0, '(', ')')
            return Parser.accolade(words, 0, '(', ')'), Parser.compileExpr(self, words[1:lidx])[1]
        
        elif words[0][1] in "-~":
            next_words = words[1:].copy()
            next_end, next_compiled = Parser.findTermEnd(self, next_words)
            
            return (next_end + 1), next_compiled + "  neg\n"
                
        elif words[0][0] in {'integerConstant', 'stringConstant'} or \
            words[0][1] in keyWordConsts:
            return 0, Parser.pushVM(self, words[0])
        
        else:
            raise ValueError("Invalid term {}".format(words))
            
    
    def pushVM(self, token):
        [typ, name] = token
        data = self.env.lookup(name)
        if data:
            arg1, arg2 = kindToSegment[data.kind], data.idx
        else:
            if typ == 'integerConstant':
                arg1, arg2 = 'const', name
            elif typ == 'keyword' and name in keyWordConsts.keys():
                arg1, arg2 = 'const', keyWordConsts[name]
            else:
                raise ValueError("{} not defined".format(name))

        line = "  push {} {}\n".format(arg1, arg2)
        return line
    
    
    def popVM(self, name):
        data = self.env.lookup(name)
        if data:
            arg1, arg2 = kindToSegment[data.kind], data.idx
        else:
            raise ValueError("{} not defined".format(name))
        line = "  pop {} {}\n".format(arg1, arg2)
        return line
        
    
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
    
# EX1 = pr.compileClass(tokenizer("""
# class program{
#     method void do_stuff (int lmao){
#         var int counter = 0;
#         var int a;
#         var int b;
#         var int q;
#         var bool expr;
        
#         while (a > 0){
#             let b = b + 1;
#             let q = 44 - 2;
#             do a();
#         }
        
#         if (expr) 
#             {do nothing();}
#         else
#             {do something(a, b);}

#     }
# }
# """
# ))


# EX2 = pr.compileClass(tokenizer("""
# class program2{
#     field int a;
#     static string b;
#     static string dragon;
    
#     constructor void program(){}
#     method int foo(char a, int b, float c){
#         var int counter = 0;    
        
#     }  
# }
# """
# ))
# print("----EX3----EX4----")
# print(pr.env.lookup("nothing"))

# EX3 = pr.compileSubDec(tokenizer("""
# method int foo(int a, int b, int c){
#     return 0;
# }  
# """
# ))

# EX4 = pr.compileStat(tokenizer("""
# if(true){
#     return v[10];
# }
# else{
     
# }  
# """
# ))



pr2 = Parser()
EX5 = pr2.compileClass(tokenizer("""
class init{
    function int main(int is_epic){
        var int a;
        var int b;
        let a = f(a, b, 3, 4);
        let a = ddd.f(b) + (- a);
    }
}
"""
))
