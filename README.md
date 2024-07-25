# Compiler Project

This repository contains the implementation of a compiler. The project includes various modules and components required for compiling code, handling memory management, and generating executable instructions.

## Table of Contents
- [Contents](#contents)
- [Project Structure](#project-structure)
  - [CodeGenerator.py](#codegeneratorpy)
  - [Compiler.py](#compilerpy)
  - [instructions.txt](#instructionstxt)
  - [kod.txt](#kodtxt)
  - [Memory.py](#memorypy)
  - [preCompilingAnalyzing.py](#precompilinganalyzingpy)
  - [text.txt](#texttxt)
- [Memory Management](#memory-management)
- [License](#license)
- [Instructions](#instructions)

## Contents

- **CodeGenerator.py**: Contains the logic for generating machine code or intermediate code from the parsed source code.
- **Compiler.py**: The main compiler driver that orchestrates the entire compilation process.
- **instructions.txt**: A text file containing instructions or reference information used by the compiler.
- **kod.txt**: A sample source code file to be compiled.
- **Memory.py**: Manages memory allocation, deallocation, and memory-related operations during compilation.
- **preCompilingAnalyzing.py**: Performs pre-compilation analysis such as syntax and semantic checks.
- **text.txt**: An auxiliary text file, possibly containing additional information or test data.

## Project Structure

### CodeGenerator.py

This module is responsible for translating the parsed abstract syntax tree (AST) or intermediate representation (IR) of the source code into machine code or another target language. It includes functions for:
- Emitting instructions
- Handling control flow constructs
- Managing code optimization

### Compiler.py

This is the main entry point of the compiler. It coordinates the different stages of the compilation process:
- Reading the source code
- Performing lexical analysis
- Parsing the source code into an AST or IR
- Running pre-compilation analysis
- Generating the target code using `CodeGenerator.py`
- Managing memory through `Memory.py`

### instructions.txt

This file contains a list of instructions or reference data that the compiler uses during the code generation phase. It includes multiplying and divide instructions.

### kod.txt

A sample source code file that demonstrates the input for the compiler. This file is used for testing and demonstration purposes.

### Memory.py

This module handles memory management for the compiler. It includes functionality for:
- Allocating memory for variables and data structures
- Deallocating memory when it is no longer needed
- Managing scope and lifetime of variables
- Keeping track of memory usage and optimizing memory allocation

### preCompilingAnalyzing.py

Performs pre-compilation checks on the source code to ensure it adheres to the language's syntax and semantics. This includes:
- Syntax checking using a parser
- Semantic analysis to ensure correct use of variables and operations
- Reporting errors and warnings

### text.txt

An auxiliary file that may contain additional data or test cases for the compiler. It is used during the development and testing of the compiler to ensure correctness and robustness.

## Memory Management

The memory management in this compiler is handled by the `Memory.py` module. It performs the following tasks:

1. **Allocation**: Dynamically allocates memory for variables and data structures as needed during compilation.
2. **Deallocation**: Frees memory that is no longer in use to prevent memory leaks.
3. **Scope Management**: Keeps track of variable scope and ensures that memory is properly allocated and deallocated as variables enter and leave scope.
4. **Optimization**: Optimizes memory usage by reusing memory locations and minimizing fragmentation.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Instructions

For detailed documentation of the language, please refer to the [language_desc.pdf](language_desc.pdf) file.

