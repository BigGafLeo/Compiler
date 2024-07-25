from sly import Lexer, Parser
from Memory import Memory, Array, Variable
import sys
from CodeGenerator import CodeGenerator
from preCompilingAnalyzing import preCompilingAnalyzing as preCompile


class MyLexer(Lexer):
    # Zdefiniowanie tokenów
    tokens = {LETTERS, NUMBER, PROGRAM, IS, IF, THEN, ELSE, ENDIF, WHILE, DO, ENDWHILE, REPEAT, UNTIL, READ, WRITE,
              PROCEDURE, IN, END,
              SET, NEQ, GEQ, LEQ, EQ, GT, LT, T}
    literals = ['+', '-', '*', '/', '%', '(', ')', '[', ']', ';', ',']

    # Ignorowanie białych znaków
    ignore = ' \t'

    # Zdefiniowanie wyrażeń regularnych dla tokenów
    LETTERS = r"[_a-z]+"
    NUMBER = r'\d+'

    # Zdefiniowanie słów kluczowych
    PROGRAM = r'PROGRAM'
    IS = r'IS'
    IF = r'IF'
    THEN = r'THEN'
    ELSE = r'ELSE'
    ENDIF = r'ENDIF'
    WHILE = r'WHILE'
    DO = r'DO'
    ENDWHILE = r'ENDWHILE'
    END = r'END'
    REPEAT = r'REPEAT'
    UNTIL = r'UNTIL'
    READ = r'READ'
    WRITE = r'WRITE'
    PROCEDURE = r'PROCEDURE'
    IN = r'IN'

    SET = r":="
    NEQ = r"!="
    GEQ = r">="
    LEQ = r"<="
    EQ = r"="
    GT = r">"
    LT = r"<"

    T = r"T"

    # Obsługa komentarzy
    @_(r'\#.*')
    def ignore_comment(self, t):
        self.lineno += t.value.count('\n')

    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)

    # Obsługa błędów
    def error(self, t):
        print(f"Illegal character '{t.value[0]}' at line {t.lineno}, position {t.index}")
        self.index += 1


class MyParser(Parser):
    # debugfile = 'debugParser.out'

    def __init__(self):
        self.current_procedure_name = None
        self.current_procedure_args = None
        self.pending_procedure_args = None

    # Kolejność wykonywanie działań
    precedence = (
        ('left', '+', '-'),
        ('left', '*', '/', '%'),
    )

    tokens = MyLexer.tokens

    # with open(sys.argv[1], 'r') as inFile:
    with open("text.txt", 'r') as inFile:
        content = inFile.read()
        inFile.close()
    preCompileData = preCompile.getMemoryNeedForProcedures(content)

    memory = Memory(preCompileData, preCompileData["main"])
    code = list()

    with open("instructions.txt") as inFile:
        for line in inFile:
            code.append(line.rstrip('\n'))

    # Program structure
    @_("procedures main", "main")
    def basic(self, p):
        if hasattr(p, 'procedures'):
            return p.procedures, p.main
        else:
            return p.main

    @_('')
    def main(self, p):
        action = None

    @_('PROGRAM IS declarations IN commands END',
       'PROGRAM IS IN commands END')
    def main(self, p):
        mainIndex = len(self.code)
        self.code[0] = f"JUMP {mainIndex}"

        k = CodeGenerator(p.commands, self.memory, self.code)
        newCode = k.runGenerator()
        return newCode

    @_('procedures procedure', 'procedure')
    def procedures(self, p):
        # Jeśli p.procedures jest listą, rozszerz ją o nową procedurę
        # W przeciwnym razie, utwórz nową listę z pojedynczą procedurą
        return p.procedures + [p.procedure] if hasattr(p, 'procedures') else [p.procedure]

    @_('PROCEDURE proc_head IS declarations IN commands END',
       'PROCEDURE proc_head IS IN commands END')
    def procedure(self, p):
        if self.current_procedure_args is not None:
            for arg in self.current_procedure_args.split(','):
                arg_name = arg.strip()
                self.memory.addVariable(arg_name, self.current_procedure_name, isParam=True)

        # Generowanie kodu dla procedury
        method = self.memory.methodDict[self.current_procedure_name]
        generator = CodeGenerator(p.commands, method.procedureMemory, self.code, mainMemory=self.memory)
        generated = generator.runGenerator(isMethod=True)

        # Dodawanie skoku powrotnego dla procedury
        self.code.extend(
            generator.getInstructionsForSettingRegisterValue("a", self.memory.getBackIndexForMethod(p.proc_head)))
        self.code.append(f"LOAD a")
        self.code.append(f"JUMPR a")

        # Resetowanie nazwy i argumentów procedury
        self.current_procedure_name = None
        self.current_procedure_args = None

        return generated

    # Declarations
    @_('declarations "," LETTERS "[" num "]"',
       'LETTERS "[" num "]"')
    def declarations(self, p):
        self.memory.addArray(p[-4], p[-2], self.current_procedure_name)

    @_('declarations "," LETTERS',
       'LETTERS')
    def declarations(self, p):
        self.memory.addVariable(p[-1], self.current_procedure_name)

    # Commands and statements
    @_('commands command')
    def commands(self, p):
        action = p[0] + [p[1]]
        return action

    @_('command')
    def commands(self, p):
        action = [p[0]]
        return action

    @_('identifier SET expression ";"')
    def command(self, p):
        action = 'assign', p.identifier, p.expression
        return action

    @_('IF condition THEN commands ELSE commands ENDIF')
    def command(self, p):
        action = 'ifelse', p.condition, p.commands0, p.commands1
        return action

    @_('IF condition THEN commands ENDIF')
    def command(self, p):
        action = ('if', p.condition, p.commands)
        return action

    @_('WHILE condition DO commands ENDWHILE')
    def command(self, p):
        action = ('while', p.condition, p.commands)
        return action

    @_('REPEAT commands UNTIL condition ";"')
    def command(self, p):
        action = ('doWhile', p.condition, p.commands)
        return action

    @_('proc_call ";"')
    def command(self, p):
        return (p.proc_call)

    @_('READ identifier ";"')
    def command(self, p):
        action = ('read', p.identifier)
        return action

    @_('WRITE value ";"')
    def command(self, p):
        action = ('write', p.value)
        return action

    @_('LETTERS "(" args_raw ")"')
    def proc_head(self, p):
        self.memory.addMethod(p[0], len(self.code))
        self.current_procedure_name = p.LETTERS
        self.pending_procedure_args = p.args_raw
        self.process_procedure_args()
        return p.LETTERS

    def process_procedure_args(self):
        if self.pending_procedure_args is not None and self.current_procedure_name is not None:
            for arg_type, arg_name in self.pending_procedure_args:
                if arg_type == 'array':
                    self.memory.addVariable(arg_name, self.current_procedure_name, isParam=True, isArray=True)
                else:
                    self.memory.addVariable(arg_name, self.current_procedure_name, isParam=True)
            self.pending_procedure_args = None

    @_('args_raw "," "T" LETTERS', '"T" LETTERS',
       'args_raw "," LETTERS', 'LETTERS')
    def args_raw(self, p):
        if 'T' in p:
            arg_type = 'array'
            arg_name = p.LETTERS
        else:
            arg_type = 'variable'
            arg_name = p[-1]

        if 'args_raw' in p._namemap:
            return p.args_raw + [(arg_type, arg_name)]
        else:
            return [(arg_type, arg_name)]

    @_('LETTERS "(" arguments ")"')
    def proc_call(self, p):
        action = ('methodCall', p.LETTERS, p.arguments)
        return action

    @_('arguments "," LETTERS', 'LETTERS', '')
    def arguments(self, p):
        if len(p) == 0:
            return
        elif len(p) == 1:
            return [p[0]]
        else:
            return p.arguments + [p[2]]

    # Expressions

    @_('value')
    def expression(self, p):
        action = p[0]
        return action

    @_('value "+" value')
    def expression(self, p):
        action = "addition", p[0], p[2]
        return action

    @_('value "-" value')
    def expression(self, p):
        action = "subtraction", p[0], p[2]
        return action

    @_('value "*" value')
    def expression(self, p):
        action = "multiply", p[0], p[2]
        return action

    @_('value "/" value')
    def expression(self, p):
        action = "dividing", p[0], p[2]
        return action

    @_('value "%" value')
    def expression(self, p):
        action = "modulo", p[0], p[2]
        return action

    # Conditions
    @_('value EQ value')
    def condition(self, p):
        action = "eq", p[0], p[2]
        return action

    @_('value NEQ value')
    def condition(self, p):
        action = "neq", p[0], p[2]
        return action

    @_('value LT value')
    def condition(self, p):
        action = "lt", p[0], p[2]
        return action

    @_('value GT value')
    def condition(self, p):
        action = "gt", p[0], p[2]
        return action

    @_('value LEQ value')
    def condition(self, p):
        action = "leq", p[0], p[2]
        return action

    @_('value GEQ value')
    def condition(self, p):
        action = "geq", p[0], p[2]
        return action

    # Values
    @_('identifier')
    def value(self, p):
        action = "load", p[0]
        return action

    @_('num')
    def value(self, p):
        action = "const", p[0]
        return action

    @_('LETTERS "[" num "]"',
       'LETTERS "[" identifier "]"',
       'LETTERS')
    def identifier(self, p):
        if len(p) == 1:
            # Obsługa zwykłej zmiennej
            return self.handle_variable(p[0])
        else:
            # Obsługa dostępu do elementów tablicy
            return self.handle_array_access(p[0], p[2])

    def handle_variable(self, name):
        if self.current_procedure_name is None:
            if name in self.memory:
                return "variable", name
            else:
                return "undeclared", name
        else:
            if name in self.memory.methodDict[self.current_procedure_name].procedureMemory:
                return "variable", name
            else:
                return "undeclared", name

    def handle_array_access(self, array_name, index):
        if self.current_procedure_name:
            proc_memory = self.memory.methodDict[self.current_procedure_name].procedureMemory
            if array_name in proc_memory:
                var_or_array = proc_memory[array_name]
                if isinstance(var_or_array, Array) or (isinstance(var_or_array, Variable) and var_or_array.isArray):
                    return "array_access", array_name, index
                else:
                    return "undeclared", array_name
        else:
            if array_name in self.memory:
                var_or_array = self.memory[array_name]
                if isinstance(var_or_array, Array) or (isinstance(var_or_array, Variable) and var_or_array.isArray):
                    return "array_access", array_name, index
                else:
                    return "undeclared", array_name

    # Numbers
    @_('NUMBER')
    def num(self, p):
        action = p.NUMBER
        return action

    # Error handling rule
    def error(self, p):
        if p:
            print(f"Syntax error at token {p.type}, {p.value} in line {p.lineno}. {p}")
            self.errok()
        else:
            print("Syntax error at EOF")


# def main():
#     if len(sys.argv) != 3:
#         print("Użycie: ./nazwa_pliku plik_wejściowy plik_wyjściowy")
#         sys.exit(1)
#
#         plik_wejsciowy = sys.argv[1]
#         plik_wyjsciowy = sys.argv[2]
#
#     try:
#         with open(plik_wejsciowy, 'r') as inFile:
#             content = inFile.read()
#             inFile.close()
#         lexer = MyLexer()
#         parser = MyParser()
#
#         parser.parse(lexer.tokenize(content))
#         CodeGenerator = MyParser.code
#
#         with open(plik_wyjsciowy, 'w') as file:
#             for item in MyParser.code:
#                 file.write(f"{item}\n")
#
#     except Exception as e:
#         print(f"Wystąpił błąd: {e}")
#         sys.exit(1)
#
#
# if __name__ == "__main__":
#     sys.tracebacklimit = 0
#     main()

if __name__ == '__main__':
    sys.tracebacklimit = 0
    with open("text.txt", 'r') as inFile:
        content = inFile.read()
        inFile.close()

    lexer = MyLexer()
    parser = MyParser()

    parser.parse(lexer.tokenize(content))
    CodeGenerator = MyParser.code
    # print(MyParser.code)
    # for element in MyParser.code:
    #     print(element)
    with open("kod.txt", 'w') as file:
        for item in MyParser.code:
            file.write(f"{item}\n")

