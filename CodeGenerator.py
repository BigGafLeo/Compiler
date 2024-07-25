#Karol Dzwonkowski 247373
import re

class CodeGenerator:

    def __init__(self, commands, memory, code=[], mainMemory = None):
        self.commands = commands
        self.memory = memory
        self.code = code
        self.iterators = []
        self.mainMemory = mainMemory

    def runGenerator(self, isMethod=False):
        #print(len(self.code))
        self.startGenerator(self.commands)
        if not isMethod:
            self.code.append("HALT")
        return self.code

    def startGenerator(self, commands):
        # print (f"{commands}")
        # for key, var in self.memory.items():
        #     print(
        #         f"Klucz: {key}, MemoryCounter: {var.memoryCounter}, IsInitialized: {var.isInitialized}, IsParam: {var.isParam}, IsArray: {var.isArray}")
        for command in commands:
            if command[0] == "write":
                value = command[1]
                processingCommand = value[0]
                variable = value[1]
                variable = variable[1] if isinstance(variable, tuple) else variable
                if processingCommand == "load":
                    address = self.getVariableAddress(variable)
                    # Sytuacja Array
                    if command[1][1][0] == "array_access":
                        # Pointer jest const
                        if not isinstance(command[1][1][2], tuple):
                            if not self.isVariableParam(variable):
                                address += int(command[1][1][2])
                            self.code.extend(self.getInstructionsForSettingRegisterValue("a", address))
                            self.addInstructionsIfProcedureParameter(variable, "a")
                            if self.isVariableParam(variable):
                                self.code.append(f"PUT b")
                                self.code.extend(self.getInstructionsForSettingRegisterValue("a", command[1][1][2]))
                                self.code.append(f"ADD b")
                            self.code.append(f"LOAD a")
                            self.code.append(f"WRITE")
                        # Pointer jest var
                        else:
                            pointer = command[1][1][2][1]
                            pointerMemory = self.getVariableAddress(pointer)
                            self.code.extend(self.getInstructionsForSettingRegisterValue("c", address))
                            self.addInstructionsIfProcedureParameter(variable, "c")
                            self.code.extend(self.getInstructionsForSettingRegisterValue("a", pointerMemory))
                            self.addInstructionsIfProcedureParameter(pointer, "a")
                            self.code.append(f"LOAD a")
                            self.code.append(f"ADD c")
                            self.code.append(f"LOAD a")
                            self.code.append(f"WRITE")
                    # Sytuacja var
                    else:
                        self.code.extend(self.getInstructionsForSettingRegisterValue("a", address))
                        self.addInstructionsIfProcedureParameter(variable, "a")
                        self.code.append(f"LOAD a")
                        self.code.append(f"WRITE")

                elif processingCommand == "const":
                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", variable))
                    self.code.append(f"WRITE")

            elif command[0] == "read":
                variable = command[1][1]
                if variable in self.memory:
                    targetMemory = self.memory.getAddress(variable)
                    # Dla array
                    if command[1][0] == "array_access":
                        # Jeżeli pointerem jest const
                        if not isinstance(command[1][2], tuple):
                            shift = int(command[1][2])
                            if not self.isVariableParam(variable):
                                targetMemory += shift
                                self.code.extend(self.getInstructionsForSettingRegisterValue("a", targetMemory))
                            else:
                                self.code.extend(self.getInstructionsForSettingRegisterValue("a", targetMemory))
                                self.addInstructionsIfProcedureParameter(variable)
                                self.code.extend(self.getInstructionsForSettingRegisterValue("b", shift))
                                self.code.append("ADD b")
                            self.code.append(f"PUT b")
                        # Jeżeli pointerem jest var
                        else:
                            variablePointer = command[1][2][1]
                            variablePointerMemory = self.getVariableAddress(variablePointer)
                            self.code.extend(self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                            self.addInstructionsIfProcedureParameter(variablePointer, "g")
                            self.code.append(f"LOAD g")
                            self.code.append(f"PUT g")

                            self.code.extend(self.getInstructionsForSettingRegisterValue("a", targetMemory))
                            self.addInstructionsIfProcedureParameter(variable)
                            self.code.append(f"ADD g")
                            self.code.append(f"PUT b")
                    # Dla var
                    else:
                        self.code.extend(self.getInstructionsForSettingRegisterValue("a", targetMemory))
                        self.addInstructionsIfProcedureParameter(variable)
                        self.code.append(f"PUT b")
                    self.code.append(f"READ")
                    self.code.append(f"STORE b")
                else:
                    raise Exception(f"Tried to read to undeclared variable: {variable}")

            elif command[0] == "assign":
                target = command[1][1]
                targetMemory = self.getVariableAddress(target)

                # # Ustawienie rb na adres zmiennej
                if command[1][0] == "array_access":
                    if not isinstance(command[1][2], tuple):
                        shift = int(command[1][2])
                        if not self.isVariableParam(target):
                            targetMemory += shift
                            self.code.extend(self.getInstructionsForSettingRegisterValue("b", targetMemory))
                        else:
                            self.code.extend(self.getInstructionsForSettingRegisterValue("a", targetMemory))
                            self.addInstructionsIfProcedureParameter(target)
                            self.code.extend(self.getInstructionsForSettingRegisterValue("b", shift))
                            self.code.append(f"ADD b")
                            self.code.append("PUT b")
                    else:
                        variablePointer = command[1][2][1]
                        variablePointerMemory = self.getVariableAddress(variablePointer)
                        self.code.extend(self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                        self.addInstructionsIfProcedureParameter(variablePointer, "g")
                        self.code.append(f"LOAD g")
                        self.code.append(f"PUT g")

                        self.code.extend(self.getInstructionsForSettingRegisterValue("a", targetMemory))
                        self.addInstructionsIfProcedureParameter(target)
                        self.code.append(f"ADD g")
                        self.code.append(f"PUT b")
                else:
                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", targetMemory))
                    self.addInstructionsIfProcedureParameter(target)
                    self.code.append("PUT b")

                if command[2][0] == "const":
                    # Ustawienie variable i zapisanie
                    variable = command[2][1]
                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", variable))
                    self.code.append(f"STORE b")
                elif command[2][0] == "load":

                    # Przetwarzanie variable
                    variable = command[2][1][1]
                    variableMemory = self.getVariableAddress(variable)
                    if command[2][1][0] == "array_access":
                        if not isinstance(command[2][1][2], tuple):
                            shift = command[2][1][2]
                            if not self.isVariableParam(variable):
                                variableMemory += shift
                                self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                self.code.append(f"LOAD a")
                            else:
                                self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                self.addInstructionsIfProcedureParameter(variable)
                                self.code.extend(self.getInstructionsForSettingRegisterValue("g", shift))
                                self.code.append(f"ADD g")
                                self.code.append(f"LOAD a")
                        else:
                            variablePointer = command[2][1][2][1]
                            variablePointerMemory = self.getVariableAddress(variablePointer)
                            self.code.extend(self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                            self.addInstructionsIfProcedureParameter(variablePointer, "g")
                            self.code.append(f"LOAD g")
                            self.code.append(f"PUT g")

                            self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                            self.addInstructionsIfProcedureParameter(variable)
                            self.code.append(f"ADD g")
                            self.code.append(f"LOAD a")
                    else:
                        self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                        self.addInstructionsIfProcedureParameter(variable)
                        self.code.append(f"LOAD a")
                    self.code.append(f"STORE b")

                else:
                    # Obliczenie wyrażenia
                    self.calculateExpression(command[2])
                    # # Ustawienie rb na adres zmiennej
                    if command[1][0] == "array_access":
                        if not isinstance(command[1][2], tuple):
                            shift = int(command[1][2])
                            if not self.isVariableParam(target):
                                targetMemory += shift
                                self.code.extend(self.getInstructionsForSettingRegisterValue("b", targetMemory))
                            else:
                                self.code.extend(self.getInstructionsForSettingRegisterValue("a", targetMemory))
                                self.addInstructionsIfProcedureParameter(target)
                                self.code.extend(self.getInstructionsForSettingRegisterValue("b", shift))
                                self.code.append(f"ADD b")
                                self.code.append("PUT b")
                        else:
                            variablePointer = command[1][2][1]
                            variablePointerMemory = self.getVariableAddress(variablePointer)
                            self.code.extend(self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                            self.addInstructionsIfProcedureParameter( variablePointer, "g")
                            self.code.append(f"LOAD g")
                            self.code.append(f"PUT g")

                            self.code.extend(self.getInstructionsForSettingRegisterValue("a", targetMemory))
                            self.addInstructionsIfProcedureParameter(target)
                            self.code.append(f"ADD g")
                            self.code.append(f"PUT b")
                    else:
                        self.code.extend(self.getInstructionsForSettingRegisterValue("a", targetMemory))
                        self.addInstructionsIfProcedureParameter(target)
                        self.code.append("PUT b")

                    # Ustawienie variable i zapisanie
                    self.code.append(f"GET c")
                    self.code.append(f"STORE b")

            elif command[0] == "if":
                condition = self.simpleConditionAnalizy(command[1])
                if isinstance(condition, bool):
                    if condition:
                        self.startGenerator(command[2])
                else:
                    self.dealConditionData(command[1], command[2])

            elif command[0] == "ifelse":
                condition = self.simpleConditionAnalizy(command[1])
                if isinstance(condition, bool):
                    if condition:
                        self.startGenerator(command[2])
                    else:
                        self.startGenerator(command[3])
                else:
                    self.dealConditionData(condition=command[1], commands=command[2], commands2=command[3], ifElse=True)

            elif command[0] == "while":
                condition = self.simpleConditionAnalizy(command[1])
                if isinstance(condition, bool):
                    if condition:
                        loopStartIndex = len(self.code)
                        self.startGenerator(command[2])
                        self.code.append(f"JUMP {loopStartIndex}")
                else:
                    conditionStartIndex = len(self.code)
                    self.dealConditionData(condition, command[2], ifWhile=True)
                    self.code.append(f"JUMP {conditionStartIndex}")

            elif command[0] == "doWhile":
                condition = self.simpleConditionAnalizy(command[1])
                if isinstance(condition, bool):
                    loopStartIndex = len(self.code)
                    self.startGenerator(command[2])
                    if not condition:
                        self.code.append(f"JUMP {loopStartIndex}")
                else:
                    loopStartIndex = len(self.code)
                    self.startGenerator(command[2])
                    if command[1][0] == "eq":
                        negCondition = "neq"
                    elif command[1][0] == "neq":
                        negCondition = "eq"
                    elif command[1][0] == "gt":
                        negCondition = "leq"
                    elif command[1][0] == "lt":
                        negCondition = "geq"
                    elif command[1][0] == "geq":
                        negCondition = "lt"
                    else:
                        negCondition = "gt"
                    self.dealConditionData(command[1], [], ifWhile=True, negCondition=negCondition)
                    self.code.append(f"JUMP {loopStartIndex}")

            elif command[0] == "methodCall":
                self.memory.resetParameterIterator()
                separetedParameters = command[2]
                methodName = command[1]

                # Sprawdzenie ilości parametrów
                if self.mainMemory is None:
                    if len(separetedParameters) != self.memory.getMethodParametersNumber(methodName):
                        raise Exception(f"Bad params number in procedure declaration & call for procedure: {methodName}")
                else:
                    if len(separetedParameters) != self.mainMemory.getMethodParametersNumber(methodName):
                        raise Exception(f"Bad params number in procedure declaration & call for procedure: {methodName}")

                # Przepisywanie parametrów i ustawianie ich ewentualnej referncji na głębszą
                for param in separetedParameters:
                    paramAddress = self.memory.getAddress(param)
                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", paramAddress))
                    self.addInstructionsIfProcedureParameter(param)

                    if self.mainMemory is None:
                        targetMemory = self.memory.methodDict[methodName].paramIterator
                        self.memory.incMethodParamIterator(methodName)
                    else:
                        targetMemory = self.mainMemory.methodDict[methodName].paramIterator
                        self.mainMemory.incMethodParamIterator(methodName)
                    self.code.extend(self.getInstructionsForSettingRegisterValue("b", targetMemory))
                    self.code.append(f"STORE b")

                if self.mainMemory is None:
                    self.memory.resetMethodParamIterator(methodName)
                else:
                    self.mainMemory.resetMethodParamIterator(methodName)


                if self.mainMemory is None:
                    methodBackIndex = self.memory.getBackIndexForMethod(methodName)
                else:
                    methodBackIndex = self.mainMemory.getBackIndexForMethod(methodName)
                self.code.extend(self.getInstructionsForSettingRegisterValue("b", methodBackIndex))
                self.code.extend(self.getInstructionsForSettingRegisterValue("c", 4)) #4 bo musimy dodać add, store, jump i jeden aby wskazać na wyjście
                self.code.append(f"STRK a")
                self.code.append(f"ADD c")
                self.code.append(f"STORE b")

                if self.mainMemory is None:
                    procedureAddress = self.memory.getMethodAddress(command[1])
                else:
                    procedureAddress = self.mainMemory.getMethodAddress(command[1])
                self.code.append(f"JUMP {procedureAddress}")

            else:
                raise Exception(f"Unknown processing command name {command[0]}")

    def dealConditionData(self, condition, commands, commands2=None, ifElse=False, ifWhile=False, negCondition = None):

        #print(f"Pełny warunek to: {condition}")
        firstVariable = condition[1][1]
        secondVariable = condition[2][1]
        firstVariable = firstVariable[1] if isinstance(firstVariable, tuple) else firstVariable
        secondVariable = secondVariable[1] if isinstance(secondVariable, tuple) else secondVariable
        if negCondition is None:
            operator = condition[0]
        else:
            operator = negCondition

        # Ustawianie 1 wartości pod rejestr b
        # Obsługa const
        if condition[1][0] == "const":
            self.code.extend(self.getInstructionsForSettingRegisterValue("b", firstVariable))
        # Obsługa array
        elif condition[1][1][0] == "array_access":
            firstMemory = self.getVariableAddress(firstVariable)
            # Jeżeli pointerem jest const
            if not isinstance(condition[1][1][2], tuple):
                shift = int(condition[1][1][2])
                if not self.isVariableParam(firstVariable):
                    firstMemory += shift
                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", firstMemory))
                else:
                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", firstMemory))
                    self.addInstructionsIfProcedureParameter(firstVariable)
                    self.code.extend(self.getInstructionsForSettingRegisterValue("b", shift))
                    self.code.append(f"ADD b")
                self.code.append(f"LOAD a")
                self.code.append(f"PUT b")
            # Jeżeli pointerem jest var
            else:
                variablePointer = condition[1][1][2][1]
                variablePointerMemory = self.getVariableAddress(variablePointer)
                self.code.extend(self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                self.addInstructionsIfProcedureParameter(variablePointer, "g")
                self.code.append(f"LOAD g")
                self.code.append(f"PUT g")

                self.code.extend(self.getInstructionsForSettingRegisterValue("a", firstMemory))
                self.addInstructionsIfProcedureParameter(firstVariable)
                self.code.append(f"ADD g")
                self.code.append(f"LOAD a")
                self.code.append(f"PUT b")
        # Obsługa var
        elif condition[1][1][0] == "variable":
            firstMemory = self.getVariableAddress(firstVariable)
            self.code.extend(self.getInstructionsForSettingRegisterValue("a", firstMemory))
            self.addInstructionsIfProcedureParameter(firstVariable)
            self.code.append(f"LOAD a")
            self.code.append(f"PUT b")

        # Ustawianie 2 wartości pod rejestr c
        # Obsługa const
        if condition[2][0] == "const":
            self.code.extend(self.getInstructionsForSettingRegisterValue("c", secondVariable))
        # Obsługa array
        elif condition[2][1][0] == "array_access":
            secondMemory = self.getVariableAddress(secondVariable)
            # Jeżeli pointerem jest const
            if not isinstance(condition[2][1][2], tuple):
                shift = int(condition[2][1][2])
                if not self.isVariableParam(secondVariable):
                    secondMemory += shift
                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", secondMemory))
                else:
                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", secondMemory))
                    self.addInstructionsIfProcedureParameter(secondVariable)
                    self.code.extend(self.getInstructionsForSettingRegisterValue("c", shift))
                    self.code.append(f"ADD c")
                self.code.append(f"LOAD a")
                self.code.append(f"PUT c")
            # Jeżeli pointerem jest var
            else:
                variablePointer = condition[2][1][2][1]
                variablePointerMemory = self.getVariableAddress(variablePointer)
                self.code.extend(self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                self.addInstructionsIfProcedureParameter(variablePointer, "g")
                self.code.append(f"LOAD g")
                self.code.append(f"PUT g")

                self.code.extend(self.getInstructionsForSettingRegisterValue("a", secondMemory))
                self.addInstructionsIfProcedureParameter(secondVariable)
                self.code.append(f"ADD g")
                self.code.append(f"LOAD a")
                self.code.append(f"PUT c")
        # Obsługa var
        elif condition[2][1][0] == "variable":
            secondMemory = self.getVariableAddress(secondVariable)
            self.code.extend(self.getInstructionsForSettingRegisterValue("a", secondMemory))
            self.addInstructionsIfProcedureParameter(secondVariable)
            self.code.append(f"LOAD a")
            self.code.append(f"PUT c")


        if operator == "eq":
            self.code.append(f"GET c")
            self.code.append(f"SUB b")
            firstOutJumpIndex = len(self.code)
            self.code.append(f"JPOS")
            self.code.append(f"GET b")
            self.code.append(f"SUB c")
            secondOutJumpIndex = len(self.code)
            self.code.append(f"JPOS")
            self.startGenerator(commands)

            if ifElse:
                thirdOutJumpIndex = len(self.code)
                self.code.append(f"JUMP")
                self.startGenerator(commands2)
                outIndex = len(self.code)
                self.code[thirdOutJumpIndex] = f"JUMP {outIndex}"
                self.code[firstOutJumpIndex] = f"JPOS {thirdOutJumpIndex + 1}"
                self.code[secondOutJumpIndex] = f"JPOS {thirdOutJumpIndex + 1}"
            else:
                outIndex = len(self.code)
                if ifWhile:
                    outIndex += 1
                self.code[firstOutJumpIndex] = f"JPOS {outIndex}"
                self.code[secondOutJumpIndex] = f"JPOS {outIndex}"

        elif operator == "neq":
            self.code.append(f"GET c")
            self.code.append(f"SUB b")
            instructionsIndex = len(self.code) + 4 #JPOS, GET, SUB JZERO
            self.code.append(f"JPOS {instructionsIndex}")
            self.code.append(f"GET b")
            self.code.append(f"SUB c")
            firstOutJumpIndex = len(self.code)
            self.code.append(f"JZERO")
            self.startGenerator(commands)

            if ifElse:
                secondOutJumpIndex = len(self.code)
                self.code.append(f"JUMP")
                self.startGenerator(commands2)
                outIndex = len(self.code)
                self.code[secondOutJumpIndex] = f"JUMP {outIndex}"
                self.code[firstOutJumpIndex] = f"JZERO {secondOutJumpIndex + 1}"
            else:
                outIndex = len(self.code)
                if ifWhile:
                    outIndex += 1
                self.code[firstOutJumpIndex] = f"JZERO {outIndex}"

        elif operator == "gt" or operator == "leq":
            self.code.append(f"GET b")
            self.code.append(f"SUB c")

            firstOutJumpIndex = len(self.code)
            self.code.append(f"JZERO / JPOS")
            self.startGenerator(commands)

            if ifElse:
                secondOutJumpIndex = len(self.code)
                self.code.append(f"JUMP")
                self.startGenerator(commands2)
                outIndex = len(self.code)
                self.code[secondOutJumpIndex] = f"JUMP {outIndex}"
                if operator == "gt":
                    self.code[firstOutJumpIndex] = f"JZERO {secondOutJumpIndex + 1}"
                else:
                    self.code[firstOutJumpIndex] = f"JPOS {secondOutJumpIndex + 1}"
            else:
                outIndex = len(self.code)
                if ifWhile:
                    outIndex += 1
                if operator == "gt":
                    self.code[firstOutJumpIndex] = f"JZERO {outIndex}"
                else:
                    self.code[firstOutJumpIndex] = f"JPOS {outIndex}"

        elif operator == "lt" or operator == "geq":
            self.code.append(f"GET c")
            self.code.append(f"SUB b")

            firstOutJumpIndex = len(self.code)
            self.code.append(f"JZERO / JPOS")
            self.startGenerator(commands)

            if ifElse:
                secondOutJumpIndex = len(self.code)
                self.code.append(f"JUMP")
                self.startGenerator(commands2)
                outIndex = len(self.code)
                self.code[secondOutJumpIndex] = f"JUMP {outIndex}"
                if operator == "lt":
                    self.code[firstOutJumpIndex] = f"JZERO {secondOutJumpIndex + 1}"
                else:
                    self.code[firstOutJumpIndex] = f"JPOS {secondOutJumpIndex + 1}"
            else:
                outIndex = len(self.code)
                if ifWhile:
                    outIndex += 1
                if operator == "lt":
                    self.code[firstOutJumpIndex] = f"JZERO {outIndex}"
                else:
                    self.code[firstOutJumpIndex] = f"JPOS {outIndex}"

    def simpleConditionAnalizy(self, condition):
        #print(f"Simple: ondition[1][0] = {condition[1]}, condition[2][0] = {condition[2]}")
        if condition[1][0] == "const" and condition[2][0] == "const":
            if condition[0] == "leq":
                return condition[1][1] <= condition[2][1]
            elif condition[0] == "geq":
                return condition[1][1] >= condition[2][1]
            elif condition[0] == "lt":
                return condition[1][1] < condition[2][1]
            elif condition[0] == "gt":
                return condition[1][1] > condition[2][1]
            elif condition[0] == "eq":
                return condition[1][1] == condition[2][1]
            elif condition[0] == "neq":
                return condition[1][1] != condition[2][1]

        elif condition[1][0] == "const" and condition[1][1] == 0:
            if condition[0] == "leq":
                return True
            elif condition[0] == "gt":
                return False
            else:
                return condition

        elif condition[2][0] == "const" and condition[2][1] == 0:
            if condition[0] == "geq":
                return True
            elif condition[0] == "lt":
                return False
            else:
                return condition

        elif condition[1][1] == condition[2][1]:
            if condition[0] in ["geq", "leq", "eq"]:
                return True
            else:
                return False

        else:
            return condition

    def calculateExpression(self, expression):
        if expression[1][0] == "const" and expression[2][0] == "const":
            if expression[0] == "addition":
                result = int(expression[1][1]) + int(expression[2][1])
            elif expression[0] == "subtraction":
                result = int(expression[1][1]) - int(expression[2][1])
                if result < 0:
                    result = 0
            elif expression[0] == "multiply":
                result = int(expression[1][1]) * int(expression[2][1])
            elif expression[0] == "dividing":
                if int(expression[2][1]) == 0:
                    result = 0
                else:
                    result = float(expression[1][1]) / float(expression[2][1])
            else:
                result = int(expression[1][1]) % int(expression[2][1])

            self.code.extend(self.getInstructionsForSettingRegisterValue("c", int(result)))

        else:
            #print(f"Pełne expression to: {expression}")
            if expression[0] == "addition":
                if expression[1][0] == "const":
                    variable = expression[2][1][1]
                    variableMemory= self.getVariableAddress(variable)

                    if expression[2][1][0] == "array_access":
                        if not isinstance(expression[2][1][2], tuple) and not self.isVariableParam(variable):
                            variableMemory += int(expression[2][1][2])
                            self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                            self.addInstructionsIfProcedureParameter(variable)
                            self.code.append(f"LOAD a")
                            self.code.append(f"PUT b")
                        else:
                            if not self.isVariableParam(variable):
                                # Najpierw ustawmy odpowiednią wartość pointera dla variable
                                variablePointer = expression[2][1][2][1]
                                variablePointerMemory = self.getVariableAddress(variablePointer)
                                self.code.extend(self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                                # Dla pointera będącego parametrem ładujemy referencje
                                self.addInstructionsIfProcedureParameter(variablePointer, "g")
                                self.code.append(f"LOAD g")
                                self.code.append(f"PUT g")

                                self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                self.addInstructionsIfProcedureParameter(variable)
                                self.code.append(f"ADD g")
                                self.code.append(f"LOAD a")
                                self.code.append(f"PUT b")
                            else:
                                # Sytuacja gdzie variable to parametr i indeksowany jest const
                                if not isinstance(expression[2][1][2], tuple):
                                    shift = int(expression[2][1][2])
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                    self.addInstructionsIfProcedureParameter(variable, "a")
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("b", shift))
                                    self.code.append(f"ADD b")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT b")
                                else:
                                    # Najpierw ustawmy odpowiednią wartość pointera dla variable
                                    variablePointer = expression[2][1][2][1]
                                    variablePointerMemory = self.getVariableAddress(variablePointer)
                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                                    # Dla pointera będącego parametrem ładujemy referencje
                                    self.addInstructionsIfProcedureParameter(variablePointer, "g")
                                    self.code.append(f"LOAD g")
                                    self.code.append(f"PUT g")

                                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                    self.addInstructionsIfProcedureParameter(variable)
                                    self.code.append(f"ADD g")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT b")
                    else:
                        self.code.extend(self.getInstructionsForSettingRegisterValue("e", self.getVariableAddress(expression[2][1])))
                        self.addInstructionsIfProcedureParameter(expression[2][1][1], "e")
                        self.code.append(f"LOAD e")
                        self.code.append(f"PUT b")

                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", expression[1][1]))
                    self.code.append(f"ADD b")
                    self.code.append(f"PUT c")

                elif expression[2][0] == "const":
                    variable = expression[1][1][1]
                    variableMemory= self.getVariableAddress(variable)

                    if expression[1][1][0] == "array_access":
                        if not isinstance(expression[1][1][2], tuple) and not self.isVariableParam(variable):
                            variableMemory += int(expression[1][1][2])
                            self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                            self.addInstructionsIfProcedureParameter(variable)
                            self.code.append(f"LOAD a")
                            self.code.append(f"PUT b")
                        else:
                            if not self.isVariableParam(variable):
                                # Najpierw ustawmy odpowiednią wartość pointera dla variable
                                variablePointer = expression[1][1][2][1]
                                variablePointerMemory = self.getVariableAddress(variablePointer)
                                self.code.extend(self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                                # Dla pointera będącego parametrem ładujemy referencje
                                self.addInstructionsIfProcedureParameter(variablePointer, "g")
                                self.code.append(f"LOAD g")
                                self.code.append(f"PUT g")

                                self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                self.addInstructionsIfProcedureParameter(variable)
                                self.code.append(f"ADD g")
                                self.code.append(f"LOAD a")
                                self.code.append(f"PUT b")
                            else:
                                # Sytuacja gdzie variable to parametr i indeksowany jest const
                                if not isinstance(expression[1][1][2], tuple):
                                    shift = int(expression[1][1][2])
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                    self.addInstructionsIfProcedureParameter(variable, "a")
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("b", shift))
                                    self.code.append(f"ADD b")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT b")
                                else:
                                    # Najpierw ustawmy odpowiednią wartość pointera dla variable
                                    variablePointer = expression[1][1][2][1]
                                    variablePointerMemory = self.getVariableAddress(variablePointer)
                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                                    # Dla pointera będącego parametrem ładujemy referencje
                                    self.addInstructionsIfProcedureParameter(variablePointer, "g")
                                    self.code.append(f"LOAD g")
                                    self.code.append(f"PUT g")

                                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                    self.addInstructionsIfProcedureParameter(variable)
                                    self.code.append(f"ADD g")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT b")

                    else:

                        self.code.extend(self.getInstructionsForSettingRegisterValue("e", self.getVariableAddress(expression[1][1])))
                        self.addInstructionsIfProcedureParameter(expression[1][1][1], "e")
                        self.code.append(f"LOAD e")
                        self.code.append(f"PUT b")

                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", expression[2][1]))
                    self.code.append(f"ADD b")
                    self.code.append(f"PUT c")

                else:
                    variableSecond = expression[2][1][1]
                    variableSecondMemory= self.getVariableAddress(variableSecond)

                    if expression[2][1][0] == "array_access":
                        if not isinstance(expression[2][1][2], tuple) and not self.isVariableParam(variableSecond):
                            variableSecondMemory += int(expression[2][1][2])
                            self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableSecondMemory))
                            self.addInstructionsIfProcedureParameter(variableSecond)
                            self.code.append(f"LOAD a")
                            self.code.append(f"PUT e")
                        else:
                            if not self.isVariableParam(variableSecond):
                                # Najpierw ustawmy odpowiednią wartość pointera dla variableSecond
                                variableSecondPointer = expression[2][1][2][1]
                                variableSecondPointerMemory = self.getVariableAddress(variableSecondPointer)
                                self.code.extend(self.getInstructionsForSettingRegisterValue("g", variableSecondPointerMemory))
                                # Dla pointera będącego parametrem ładujemy referencje
                                self.addInstructionsIfProcedureParameter(variableSecondPointer, "g")
                                self.code.append(f"LOAD g")
                                self.code.append(f"PUT g")

                                self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableSecondMemory))
                                self.addInstructionsIfProcedureParameter(variableSecond)
                                self.code.append(f"ADD g")
                                self.code.append(f"LOAD a")
                                self.code.append(f"PUT e")
                            else:
                            # Sytuacja gdzie variable to parametr i indeksowany jest const
                                if not isinstance(expression[2][1][2], tuple):
                                    shift = int(expression[2][1][2])
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableSecondMemory))
                                    self.addInstructionsIfProcedureParameter(variableSecond, "a")
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("b", shift))
                                    self.code.append(f"ADD b")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT e")
                                else:
                                    # Najpierw ustawmy odpowiednią wartość pointera dla variable
                                    variablePointer = expression[2][1][2][1]
                                    variablePointerMemory = self.getVariableAddress(variablePointer)
                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                                    # Dla pointera będącego parametrem ładujemy referencje
                                    self.addInstructionsIfProcedureParameter(variablePointer, "g")
                                    self.code.append(f"LOAD g")
                                    self.code.append(f"PUT g")

                                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableSecondMemory))
                                    self.addInstructionsIfProcedureParameter(variableSecond)
                                    self.code.append(f"ADD g")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT e")
                    else:
                        self.code.extend(self.getInstructionsForSettingRegisterValue("e", self.getVariableAddress(expression[2][1])))
                        self.addInstructionsIfProcedureParameter(expression[2][1][1], "e")
                        self.code.append(f"LOAD e")
                        self.code.append(f"PUT e")


                    variableOne = expression[1][1][1]
                    variableOneMemory= self.getVariableAddress(variableOne)

                    if expression[1][1][0] == "array_access":
                        if not isinstance(expression[1][1][2], tuple) and not self.isVariableParam(variableOne):
                            variableOneMemory += int(expression[1][1][2])
                            self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableOneMemory))
                            self.addInstructionsIfProcedureParameter(variableOne)
                            self.code.append(f"LOAD a")
                            self.code.append(f"PUT b")
                        else:
                            if not self.isVariableParam(variableOne):
                                # Najpierw ustawmy odpowiednią wartość pointera dla variableOne
                                variableOnePointer = expression[1][1][2][1]
                                variableOnePointerMemory = self.getVariableAddress(variableOnePointer)
                                self.code.extend(self.getInstructionsForSettingRegisterValue("g", variableOnePointerMemory))
                                # Dla pointera będącego parametrem ładujemy referencje
                                self.addInstructionsIfProcedureParameter(variableOnePointer, "g")
                                self.code.append(f"LOAD g")
                                self.code.append(f"PUT g")

                                self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableOneMemory))
                                self.addInstructionsIfProcedureParameter(variableOne)
                                self.code.append(f"ADD g")
                                self.code.append(f"LOAD a")
                                self.code.append(f"PUT b")
                            else:
                                # Sytuacja gdzie variable to parametr i indeksowany jest const
                                if not isinstance(expression[1][1][2], tuple):
                                    shift = int(expression[1][1][2])
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableOneMemory))
                                    self.addInstructionsIfProcedureParameter(variableOne, "a")
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("b", shift))
                                    self.code.append(f"ADD b")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT b")
                                else:
                                    # Najpierw ustawmy odpowiednią wartość pointera dla variable
                                    variablePointer = expression[1][1][2][1]
                                    variablePointerMemory = self.getVariableAddress(variablePointer)
                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                                    # Dla pointera będącego parametrem ładujemy referencje
                                    self.addInstructionsIfProcedureParameter(variablePointer, "g")
                                    self.code.append(f"LOAD g")
                                    self.code.append(f"PUT g")

                                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableOneMemory))
                                    self.addInstructionsIfProcedureParameter(variableOne)
                                    self.code.append(f"ADD g")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT b")
                    else:
                        self.code.extend(self.getInstructionsForSettingRegisterValue("f", self.getVariableAddress(expression[1][1])))
                        self.addInstructionsIfProcedureParameter(expression[1][1][1], "f")
                        self.code.append(f"LOAD f")
                        self.code.append(f"PUT b")


                    self.code.append(f"GET b")
                    self.code.append(f"ADD e")
                    self.code.append(f"PUT c")

            if expression[0] == "subtraction":
                if expression[1][0] == "const":
                    variable = expression[2][1][1]
                    variableMemory= self.getVariableAddress(variable)

                    if expression[2][1][0] == "array_access":
                        if not isinstance(expression[2][1][2], tuple) and not self.isVariableParam(variable):
                            variableMemory += int(expression[2][1][2])
                            self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                            self.addInstructionsIfProcedureParameter(variable)
                            self.code.append(f"LOAD a")
                            self.code.append(f"PUT e")
                        else:
                            if not self.isVariableParam(variable):
                                # Najpierw ustawmy odpowiednią wartość pointera dla variable
                                variablePointer = expression[2][1][2][1]
                                variablePointerMemory = self.getVariableAddress(variablePointer)
                                self.code.extend(self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                                # Dla pointera będącego parametrem ładujemy referencje
                                self.addInstructionsIfProcedureParameter(variablePointer, "g")
                                self.code.append(f"LOAD g")
                                self.code.append(f"PUT g")

                                self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                self.addInstructionsIfProcedureParameter(variable)
                                self.code.append(f"ADD g")
                                self.code.append(f"LOAD a")
                                self.code.append(f"PUT e")
                            else:
                                # Sytuacja gdzie variable to parametr i indeksowany jest const
                                if not isinstance(expression[2][1][2], tuple):
                                    shift = int(expression[2][1][2])
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                    self.addInstructionsIfProcedureParameter(variable, "a")
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("b", shift))
                                    self.code.append(f"ADD b")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT e")
                                else:
                                    # Najpierw ustawmy odpowiednią wartość pointera dla variable
                                    variablePointer = expression[2][1][2][1]
                                    variablePointerMemory = self.getVariableAddress(variablePointer)
                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                                    # Dla pointera będącego parametrem ładujemy referencje
                                    self.addInstructionsIfProcedureParameter(variablePointer, "g")
                                    self.code.append(f"LOAD g")
                                    self.code.append(f"PUT g")

                                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                    self.addInstructionsIfProcedureParameter(variable)
                                    self.code.append(f"ADD g")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT e")
                    else:
                        self.code.extend(self.getInstructionsForSettingRegisterValue("e", self.getVariableAddress(expression[2][1])))
                        self.addInstructionsIfProcedureParameter(expression[2][1][1], "e")
                        self.code.append(f"LOAD e")
                        self.code.append(f"PUT e")

                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", expression[1][1]))
                    self.code.append(f"SUB e")
                    self.code.append(f"PUT c")

                elif expression[2][0] == "const":
                    variable = expression[1][1][1]
                    variableMemory= self.getVariableAddress(variable)

                    if expression[1][1][0] == "array_access":
                        if not isinstance(expression[1][1][2], tuple) and not self.isVariableParam(variable):
                            variableMemory += int(expression[1][1][2])
                            self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                            self.addInstructionsIfProcedureParameter(variable)
                            self.code.append(f"LOAD a")
                            self.code.append(f"PUT e")
                        else:
                            if not self.isVariableParam(variable):
                                # Najpierw ustawmy odpowiednią wartość pointera dla variable
                                variablePointer = expression[1][1][2][1]
                                variablePointerMemory = self.getVariableAddress(variablePointer)
                                self.code.extend(self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                                # Dla pointera będącego parametrem ładujemy referencje
                                self.addInstructionsIfProcedureParameter(variablePointer, "g")
                                self.code.append(f"LOAD g")
                                self.code.append(f"PUT g")

                                self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                self.addInstructionsIfProcedureParameter(variable)
                                self.code.append(f"ADD g")
                                self.code.append(f"LOAD a")
                                self.code.append(f"PUT e")
                            else:
                                # Sytuacja gdzie variable to parametr i indeksowany jest const
                                if not isinstance(expression[1][1][2], tuple):
                                    shift = int(expression[1][1][2])
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                    self.addInstructionsIfProcedureParameter(variable, "a")
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("b", shift))
                                    self.code.append(f"ADD b")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT e")
                                else:
                                    # Najpierw ustawmy odpowiednią wartość pointera dla variable
                                    variablePointer = expression[1][1][2][1]
                                    variablePointerMemory = self.getVariableAddress(variablePointer)
                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                                    # Dla pointera będącego parametrem ładujemy referencje
                                    self.addInstructionsIfProcedureParameter(variablePointer, "g")
                                    self.code.append(f"LOAD g")
                                    self.code.append(f"PUT g")

                                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                    self.addInstructionsIfProcedureParameter(variable)
                                    self.code.append(f"ADD g")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT e")

                    else:
                        self.code.extend(self.getInstructionsForSettingRegisterValue("e", self.getVariableAddress(expression[1][1])))
                        self.addInstructionsIfProcedureParameter(expression[1][1][1], "e")
                        self.code.append(f"LOAD e")
                        self.code.append(f"PUT e")

                    self.code.extend(self.getInstructionsForSettingRegisterValue("b", expression[2][1]))
                    self.code.append(f"GET e")
                    self.code.append(f"SUB b")
                    self.code.append(f"PUT c")

                else:
                    variableSecond = expression[2][1][1]
                    variableSecondMemory= self.getVariableAddress(variableSecond)

                    if expression[2][1][0] == "array_access":
                        if not isinstance(expression[2][1][2], tuple) and not self.isVariableParam(variableSecond):
                            variableSecondMemory += int(expression[2][1][2])
                            self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableSecondMemory))
                            self.addInstructionsIfProcedureParameter(variableSecond)
                            self.code.append(f"LOAD a")
                            self.code.append(f"PUT e")
                        else:
                            if not self.isVariableParam(variableSecond):
                                # Najpierw ustawmy odpowiednią wartość pointera dla variableSecond
                                variableSecondPointer = expression[2][1][2][1]
                                variableSecondPointerMemory = self.getVariableAddress(variableSecondPointer)
                                self.code.extend(self.getInstructionsForSettingRegisterValue("g", variableSecondPointerMemory))
                                # Dla pointera będącego parametrem ładujemy referencje
                                self.addInstructionsIfProcedureParameter(variableSecondPointer, "g")
                                self.code.append(f"LOAD g")
                                self.code.append(f"PUT g")

                                self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableSecondMemory))
                                self.addInstructionsIfProcedureParameter(variableSecond)
                                self.code.append(f"ADD g")
                                self.code.append(f"LOAD a")
                                self.code.append(f"PUT e")
                            else:
                                # Sytuacja gdzie variable to parametr i indeksowany jest const
                                if not isinstance(expression[2][1][2], tuple):
                                    shift = int(expression[2][1][2])
                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("a", variableSecondMemory))
                                    self.addInstructionsIfProcedureParameter(variableSecond, "a")
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("b", shift))
                                    self.code.append(f"ADD b")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT e")
                                else:
                                    # Najpierw ustawmy odpowiednią wartość pointera dla variable
                                    variablePointer = expression[2][1][2][1]
                                    variablePointerMemory = self.getVariableAddress(variablePointer)
                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                                    # Dla pointera będącego parametrem ładujemy referencje
                                    self.addInstructionsIfProcedureParameter(variablePointer, "g")
                                    self.code.append(f"LOAD g")
                                    self.code.append(f"PUT g")

                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("a", variableSecondMemory))
                                    self.addInstructionsIfProcedureParameter(variableSecond)
                                    self.code.append(f"ADD g")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT e")
                    else:
                        self.code.extend(self.getInstructionsForSettingRegisterValue("e", self.getVariableAddress(expression[2][1])))
                        self.addInstructionsIfProcedureParameter(expression[2][1][1], "e")
                        self.code.append(f"LOAD e")
                        self.code.append(f"PUT e")


                    variableOne = expression[1][1][1]
                    variableOneMemory= self.getVariableAddress(variableOne)

                    if expression[1][1][0] == "array_access":
                        if not isinstance(expression[1][1][2], tuple) and not self.isVariableParam(variableOne):
                            variableOneMemory += int(expression[1][1][2])
                            self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableOneMemory))
                            self.addInstructionsIfProcedureParameter(variableOne)
                            self.code.append(f"LOAD a")
                            self.code.append(f"PUT b")
                        else:
                            if not self.isVariableParam(variableOne):
                                # Najpierw ustawmy odpowiednią wartość pointera dla variableOne
                                variableOnePointer = expression[1][1][2][1]
                                variableOnePointerMemory = self.getVariableAddress(variableOnePointer)
                                self.code.extend(self.getInstructionsForSettingRegisterValue("g", variableOnePointerMemory))
                                # Dla pointera będącego parametrem ładujemy referencje
                                self.addInstructionsIfProcedureParameter(variableOnePointer, "g")
                                self.code.append(f"LOAD g")
                                self.code.append(f"PUT g")

                                self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableOneMemory))
                                self.addInstructionsIfProcedureParameter(variableOne)
                                self.code.append(f"ADD g")
                                self.code.append(f"LOAD a")
                                self.code.append(f"PUT b")
                            else:
                                # Sytuacja gdzie variable to parametr i indeksowany jest const
                                if not isinstance(expression[1][1][2], tuple):
                                    shift = int(expression[1][1][2])
                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("a", variableOneMemory))
                                    self.addInstructionsIfProcedureParameter(variableOne, "a")
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("b", shift))
                                    self.code.append(f"ADD b")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT b")
                                else:
                                    # Najpierw ustawmy odpowiednią wartość pointera dla variable
                                    variablePointer = expression[1][1][2][1]
                                    variablePointerMemory = self.getVariableAddress(variablePointer)
                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                                    # Dla pointera będącego parametrem ładujemy referencje
                                    self.addInstructionsIfProcedureParameter(variablePointer, "g")
                                    self.code.append(f"LOAD g")
                                    self.code.append(f"PUT g")

                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("a", variableOneMemory))
                                    self.addInstructionsIfProcedureParameter(variableOne)
                                    self.code.append(f"ADD g")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT b")
                    else:
                        self.code.extend(self.getInstructionsForSettingRegisterValue("f", self.getVariableAddress(expression[1][1])))
                        self.addInstructionsIfProcedureParameter(expression[1][1][1], "f")
                        self.code.append(f"LOAD f")
                        self.code.append(f"PUT b")

                    self.code.append(f"GET b")
                    self.code.append(f"SUB e")
                    self.code.append(f"PUT c")

            if expression[0] == "multiply" or expression[0] == "dividing" or expression[0] == "modulo":
                if expression[1][0] == "const":

                    variable = expression[2][1][1]
                    variableMemory = self.getVariableAddress(variable)

                    if expression[2][1][0] == "array_access":
                        if not isinstance(expression[2][1][2], tuple) and not self.isVariableParam(variable):
                            variableMemory += int(expression[2][1][2])
                            self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                            self.addInstructionsIfProcedureParameter(variable)
                            self.code.append(f"LOAD a")
                            self.code.append(f"PUT e")
                        else:
                            if not self.isVariableParam(variable):
                                # Najpierw ustawmy odpowiednią wartość pointera dla variable
                                variablePointer = expression[2][1][2][1]
                                variablePointerMemory = self.getVariableAddress(variablePointer)
                                self.code.extend(self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                                # Dla pointera będącego parametrem ładujemy referencje
                                self.addInstructionsIfProcedureParameter(variablePointer, "g")
                                self.code.append(f"LOAD g")
                                self.code.append(f"PUT g")

                                self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                self.addInstructionsIfProcedureParameter(variable)
                                self.code.append(f"ADD g")
                                self.code.append(f"LOAD a")
                                self.code.append(f"PUT e")
                            else:
                                # Sytuacja gdzie variable to parametr i indeksowany jest const
                                if not isinstance(expression[2][1][2], tuple):
                                    shift = int(expression[2][1][2])
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                    self.addInstructionsIfProcedureParameter(variable, "a")
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("b", shift))
                                    self.code.append(f"ADD b")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT e")
                                else:
                                    # Najpierw ustawmy odpowiednią wartość pointera dla variable
                                    variablePointer = expression[2][1][2][1]
                                    variablePointerMemory = self.getVariableAddress(variablePointer)
                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                                    # Dla pointera będącego parametrem ładujemy referencje
                                    self.addInstructionsIfProcedureParameter(variablePointer, "g")
                                    self.code.append(f"LOAD g")
                                    self.code.append(f"PUT g")

                                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                    self.addInstructionsIfProcedureParameter(variable)
                                    self.code.append(f"ADD g")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT e")
                    else:
                        self.code.extend(
                            self.getInstructionsForSettingRegisterValue("e", self.getVariableAddress(expression[2][1])))
                        self.addInstructionsIfProcedureParameter(expression[2][1][1], "e")
                        self.code.append(f"LOAD e")
                        self.code.append(f"PUT e")

                    self.code.extend(self.getInstructionsForSettingRegisterValue("b", expression[1][1]))

                elif expression[2][0] == "const":
                    variable = expression[1][1][1]
                    variableMemory= self.getVariableAddress(variable)

                    if expression[1][1][0] == "array_access":
                        if not isinstance(expression[1][1][2], tuple) and not self.isVariableParam(variable):
                            variableMemory += int(expression[1][1][2])
                            self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                            self.addInstructionsIfProcedureParameter(variable)
                            self.code.append(f"LOAD a")
                            self.code.append(f"PUT b")
                        else:
                            if not self.isVariableParam(variable):
                                # Najpierw ustawmy odpowiednią wartość pointera dla variable
                                variablePointer = expression[1][1][2][1]
                                variablePointerMemory = self.getVariableAddress(variablePointer)
                                self.code.extend(self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                                # Dla pointera będącego parametrem ładujemy referencje
                                self.addInstructionsIfProcedureParameter(variablePointer, "g")
                                self.code.append(f"LOAD g")
                                self.code.append(f"PUT g")

                                self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                self.addInstructionsIfProcedureParameter(variable)
                                self.code.append(f"ADD g")
                                self.code.append(f"LOAD a")
                                self.code.append(f"PUT b")
                            else:
                                # Sytuacja gdzie variable to parametr i indeksowany jest const
                                if not isinstance(expression[1][1][2], tuple):
                                    shift = int(expression[1][1][2])
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                    self.addInstructionsIfProcedureParameter(variable, "a")
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("b", shift))
                                    self.code.append(f"ADD b")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT b")
                                else:
                                    # Najpierw ustawmy odpowiednią wartość pointera dla variable
                                    variablePointer = expression[1][1][2][1]
                                    variablePointerMemory = self.getVariableAddress(variablePointer)
                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                                    # Dla pointera będącego parametrem ładujemy referencje
                                    self.addInstructionsIfProcedureParameter(variablePointer, "g")
                                    self.code.append(f"LOAD g")
                                    self.code.append(f"PUT g")

                                    self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableMemory))
                                    self.addInstructionsIfProcedureParameter(variable)
                                    self.code.append(f"ADD g")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT b")
                    else:
                        self.code.extend(self.getInstructionsForSettingRegisterValue("e", self.getVariableAddress(expression[1][1])))
                        self.addInstructionsIfProcedureParameter(expression[1][1][1], "e")
                        self.code.append(f"LOAD e")
                        self.code.append(f"PUT b")

                    self.code.extend(self.getInstructionsForSettingRegisterValue("e", expression[2][1]))

                else:
                    variableSecond = expression[2][1][1]
                    variableSecondMemory= self.getVariableAddress(variableSecond)

                    if expression[2][1][0] == "array_access":
                        if not isinstance(expression[2][1][2], tuple) and not self.isVariableParam(variableSecond):
                            variableSecondMemory += int(expression[2][1][2])
                            self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableSecondMemory))
                            self.addInstructionsIfProcedureParameter(variableSecond)
                            self.code.append(f"LOAD a")
                            self.code.append(f"PUT e")
                        else:
                            if not self.isVariableParam(variableSecond):
                                # Najpierw ustawmy odpowiednią wartość pointera dla variableSecond
                                variableSecondPointer = expression[2][1][2][1]
                                variableSecondPointerMemory = self.getVariableAddress(variableSecondPointer)
                                self.code.extend(self.getInstructionsForSettingRegisterValue("g", variableSecondPointerMemory))
                                # Dla pointera będącego parametrem ładujemy referencje
                                self.addInstructionsIfProcedureParameter(variableSecondPointer, "g")
                                self.code.append(f"LOAD g")
                                self.code.append(f"PUT g")

                                self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableSecondMemory))
                                self.addInstructionsIfProcedureParameter(variableSecond)
                                self.code.append(f"ADD g")
                                self.code.append(f"LOAD a")
                                self.code.append(f"PUT e")
                            else:
                                # Sytuacja gdzie variable to parametr i indeksowany jest const
                                if not isinstance(expression[2][1][2], tuple):
                                    shift = int(expression[2][1][2])
                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("a", variableSecondMemory))
                                    self.addInstructionsIfProcedureParameter(variableSecond, "a")
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("b", shift))
                                    self.code.append(f"ADD b")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT e")
                                else:
                                    # Najpierw ustawmy odpowiednią wartość pointera dla variable
                                    variablePointer = expression[2][1][2][1]
                                    variablePointerMemory = self.getVariableAddress(variablePointer)
                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                                    # Dla pointera będącego parametrem ładujemy referencje
                                    self.addInstructionsIfProcedureParameter(variablePointer, "g")
                                    self.code.append(f"LOAD g")
                                    self.code.append(f"PUT g")

                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("a", variableSecondMemory))
                                    self.addInstructionsIfProcedureParameter(variableSecond)
                                    self.code.append(f"ADD g")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT e")
                    else:
                        self.code.extend(self.getInstructionsForSettingRegisterValue("e", self.getVariableAddress(expression[2][1])))
                        self.addInstructionsIfProcedureParameter(expression[2][1][1], "e")
                        self.code.append(f"LOAD e")
                        self.code.append(f"PUT e")


                    variableOne = expression[1][1][1]
                    variableOneMemory= self.getVariableAddress(variableOne)

                    if expression[1][1][0] == "array_access":
                        if not isinstance(expression[1][1][2], tuple) and not self.isVariableParam(variableOne):
                            variableOneMemory += int(expression[1][1][2])
                            self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableOneMemory))
                            self.addInstructionsIfProcedureParameter(variableOne)
                            self.code.append(f"LOAD a")
                            self.code.append(f"PUT b")
                        else:
                            if not self.isVariableParam(variableOne):
                                # Najpierw ustawmy odpowiednią wartość pointera dla variableOne
                                variableOnePointer = expression[1][1][2][1]
                                variableOnePointerMemory = self.getVariableAddress(variableOnePointer)
                                self.code.extend(self.getInstructionsForSettingRegisterValue("g", variableOnePointerMemory))
                                # Dla pointera będącego parametrem ładujemy referencje
                                self.addInstructionsIfProcedureParameter(variableOnePointer, "g")
                                self.code.append(f"LOAD g")
                                self.code.append(f"PUT g")

                                self.code.extend(self.getInstructionsForSettingRegisterValue("a", variableOneMemory))
                                self.addInstructionsIfProcedureParameter(variableOne)
                                self.code.append(f"ADD g")
                                self.code.append(f"LOAD a")
                                self.code.append(f"PUT b")
                            else:
                                # Sytuacja gdzie variable to parametr i indeksowany jest const
                                if not isinstance(expression[1][1][2], tuple):
                                    shift = int(expression[1][1][2])
                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("a", variableOneMemory))
                                    self.addInstructionsIfProcedureParameter(variableOne, "a")
                                    self.code.extend(self.getInstructionsForSettingRegisterValue("b", shift))
                                    self.code.append(f"ADD b")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT b")
                                else:
                                    # Najpierw ustawmy odpowiednią wartość pointera dla variable
                                    variablePointer = expression[1][1][2][1]
                                    variablePointerMemory = self.getVariableAddress(variablePointer)
                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("g", variablePointerMemory))
                                    # Dla pointera będącego parametrem ładujemy referencje
                                    self.addInstructionsIfProcedureParameter(variablePointer, "g")
                                    self.code.append(f"LOAD g")
                                    self.code.append(f"PUT g")

                                    self.code.extend(
                                        self.getInstructionsForSettingRegisterValue("a", variableOneMemory))
                                    self.addInstructionsIfProcedureParameter(variableOne)
                                    self.code.append(f"ADD g")
                                    self.code.append(f"LOAD a")
                                    self.code.append(f"PUT b")
                    else:
                        self.code.extend(self.getInstructionsForSettingRegisterValue("f", self.getVariableAddress(expression[1][1])))
                        self.addInstructionsIfProcedureParameter(expression[1][1][1], "f")
                        self.code.append(f"LOAD f")
                        self.code.append(f"PUT b")

                # Ustawianie odpowiedniej wartości rh jako back point
                self.code.append(f"RST h")
                self.code.append(f"STRK a")
                self.code.append(f"INC h")
                self.code.append(f"SHL h")
                self.code.append(f"SHL h")
                self.code.append(f"SHL h")
                self.code.append(f"ADD h")
                self.code.append(f'PUT h')

                if expression[0] == "multiply":
                    self.code.append(f"JUMP 1")
                elif expression[0] == "dividing":
                    self.code.append(f"JUMP 19")
                else:
                    self.code.append(f"JUMP 19")
                    self.code.append(f"GET f")
                    self.code.append(f"PUT c")

    def getVariableAddress(self, name):
        if isinstance(name, tuple):
            name = name[1]
        if not self.isVariableParam(name):
            if self.mainMemory is not None and name.isdigit():
                address = self.getVariableAddressForMainMemory(name)
            else:
                address = self.memory.getAddress(name)
        else:
            address = self.memory.getAddress(name)
        return address

    def getVariableAddressForMainMemory(self, name):
        address = self.mainMemory.getAddress(name)
        return address

    def isVariableParam(self, name):
        return self.memory.isVariableParam(name)

    def isArrayType(self, name):
        return self.memory.isArrayType(name)

    def getInstructionsForSettingRegisterValue(self, register, value):
        instructions = []

        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                raise ValueError(f"The value '{value}' is not a valid integer string.")

        binary_value = bin(value)[2:]

        instructions.append(f"RST {register}")

        for i, bit in enumerate(binary_value):
            if bit == '1':
                instructions.append(f"INC {register}")
            if i < len(binary_value) - 1:
                instructions.append(f"SHL {register}")

        return instructions

    def addInstructionsIfProcedureParameter(self, name, register="a"):
        if self.isVariableParam(name):
            self.code.append(f"LOAD {register}")
            if register != "a":
                self.code.append(f"PUT {register}")