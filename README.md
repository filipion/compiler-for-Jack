# Compiler-for-Jack
Python implementation of a compiler for the Jack programming language from Nand2Tetris. Jack is a Java-like language designed to teach compiler concepts, which we compile to a lower-level 
bytecode VM (virtual machine) language. The specifications for Jack and the VM language were designed by Noam Nisan and Simon Schocken as part of [The Elements of Computing Systems](https://www.amazon.com/Elements-Computing-Systems-Building-Principles/dp/0262640686/ref=ed_oe_p)
# Example Jack program and its compiled version
Example, the Jack program:

    class program2{
        field int a;
        static string b;
        static string dragon;

        constructor void program(){
      return this;
        }

        method int foo(char a, int b, float c){
            var int counter;
      let counter = b; 
        }  
    }

Should compile to something like:

    function program2.program 0
    push constant 1
    call Memory.alloc 1
    pop pointer 0
    push pointer 0
    return
    function program2.foo 1
    push argument 0
    pop pointer 0
    push argument 2
    pop local 0

# Features
* Our compiler is single pass and works by the method of mutual recursion of functions that correspond to the syntactic elements of the language
* Features of Jack are only the basics of programming languages in general: nested expressions, array indexing, method calls, branching, lexical scoping through a symbol table,
* The VM specification already abstracts procedure calls and basic memory segment management so those do not have to be implemented here
# References
Noam Nisan and Simon Schocken - [The Elements of Computing Systems](https://www.amazon.com/Elements-Computing-Systems-Building-Principles/dp/0262640686/ref=ed_oe_p)
