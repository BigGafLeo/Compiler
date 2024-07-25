#Karol Dzwonkowski 247373

class Variable:
    def __init__(self, memoryCounter, isParam = False, isArray = False):
        self.memoryCounter = memoryCounter
        self.isInitialized = False
        self.isParam = isParam
        self.isArray = isArray

    def __str__(self):
        if not self.isInitialized:
            information = f"Uninitialised variable at {self.memoryCounter}"
        else:
            information = f"Variable is initialized at {self.memoryCounter}"
        return information


class Array:
    def __init__(self, size, memoryCounter, isParam = False):
        self.memoryCounter = memoryCounter
        self.isInitialized = False
        self.isParam = isParam
        self.size = size
        self.isArray = True

    def __str__(self):
        if not self.isInitialized:
            information = f"Uninitialised array at {self.memoryCounter}"
        else:
            information = f"Array is initialized at {self.memoryCounter}"
        return information


class Method:
    def __init__(self, address, identifier, paramsNumber, backIndex, spaceForProceduresParameters):
        self.address = address
        self.identifier = identifier
        self.paramsNumber = paramsNumber
        self.backIndex = backIndex # Ineks w pamięci zawierający adres powrotu
        self.procedureMemory = Memory(spaceForProceduresParameters)
        self.paramIterator = spaceForProceduresParameters[0] + spaceForProceduresParameters[1]


class Memory(dict):
    def __init__(self, preCompileData, spaceForProceduresParameters = (0,0)):
        super().__init__()
        self.paramsCounterAdd = spaceForProceduresParameters[0]
        self.methodCounterAdd = spaceForProceduresParameters[1]
        self.memoryCounter = spaceForProceduresParameters[0] + spaceForProceduresParameters[1]
        self.memoryCounterForProcedures = 0
        self.methodDict = dict()
        self.spaceForProceduresParameters = spaceForProceduresParameters[0]
        self.methodCounter = 0
        self.parametersIterator = 7
        self.preCompileData = preCompileData

    def addVariable(self, name, current_procedure_name = None, isParam = False, isArray = False):
        if current_procedure_name is not None:
            method = self.methodDict[current_procedure_name]
            if name in method.procedureMemory:
                raise Exception(f"Variable {name} already declared in procedure {current_procedure_name}")
            procedureNumber = self.preCompileData[current_procedure_name][1]
            if isParam:
                method.procedureMemory[name] = Variable(self.memoryCounterForProcedures + procedureNumber, isParam, isArray)
                method.paramsNumber += 1
            else:
                method.procedureMemory[name] = Variable(self.memoryCounterForProcedures + procedureNumber)
            method.procedureMemory.memoryCounter += 1
            self.memoryCounterForProcedures += 1
        else:
            if name in self:
                raise Exception(f"Variable {name} already declared at {self.getAddress(name)}")
            self.setdefault(name, Variable(self.memoryCounter))
            self.memoryCounter += 1

    def addArray(self, name, size, current_procedure_name = None, isParam = False):
        numberSize = int(size)
        if current_procedure_name is not None:
            method = self.methodDict[current_procedure_name]
            if name in method.procedureMemory:
                raise Exception(f"Variable {name} already declared in procedure {current_procedure_name}")
            if numberSize <= 0:
                raise Exception(f"Array {name} size has to be greater than 0")
            procedureNumber = self.preCompileData[current_procedure_name][1]
            method.procedureMemory.setdefault(name, Array(numberSize, self.memoryCounterForProcedures + procedureNumber))
            self.memoryCounterForProcedures += numberSize
            method.procedureMemory.memoryCounter += numberSize

        else:
            if name in self:
                raise Exception(f"Array {name} already declared at {self.getAddress(name)}")
            if numberSize <= 0:
                raise Exception(f"Array {name} size has to be greater than 0")
            self.setdefault(name, Array(numberSize, self.memoryCounter))
            self.memoryCounter += numberSize

    def getVariable(self, name):
        if name not in self:
            raise NameError(f"Tried to access to undeclared variable {name}")
        return self[name]

    def addConstVariable(self, name):
        if name not in self:
            self.setdefault(name, Variable(self.memoryCounter))
            self.memoryCounter += 1

    def getAddress(self, target):
        return self.getVariable(target).memoryCounter

    def isVariableParam(self, name):
        return self.getVariable(name).isParam

    def isArrayType(self, name):
        return self.getVariable(name).isArray

    def addMethod(self, identifier, index):
        if identifier in self.methodDict:
            raise Exception(f"Method {identifier} already declared")
        self.methodCounter += 1
        preCompiledIndex = list(self.preCompileData.values())[self.methodCounter]
        backindexForMethod = preCompiledIndex[0] + preCompiledIndex[1] - 1
        self.methodDict.setdefault(identifier,
                                   Method(index, identifier, 0, backindexForMethod,
                                          self.preCompileData[identifier]))

    def getMethod(self, identifier):
        if identifier in self.methodDict:
            return self.methodDict[identifier]
        raise Exception(f"Method {identifier} is unknown")

    def getMethodAddress(self, target):
        return self.getMethod(target).address

    def getBackIndexForMethod(self, target):
        return self.getMethod(target).backIndex

    def getMethodParametersNumber(self, identifier):
        if identifier in self.methodDict:
            return self.methodDict[identifier].paramsNumber
        raise Exception(f"Method {identifier} is unknown")

    def resetParameterIterator(self):
        self.parametersIterator = 0

    def resetMethodParamIterator(self, methodName):
        self.methodDict[methodName].paramIterator = 0

    def incMethodParamIterator(self, methodName):
        self.methodDict[methodName].paramIterator += 1

    def checkIfDeclared(self, name, current_procedure_name):
        if current_procedure_name is not None:
            methodDict = self.methodDict[current_procedure_name].procedureMemory
            return name in methodDict
        else:
            return name in self

