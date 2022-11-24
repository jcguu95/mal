// Compile this file with `g++ -o step0_repl step0_repl.cpp`

#include <iostream>
#include <memory>

std::string READ(const std::string input)
{
    return input;
}

std::string EVAL(const std::string ast)
{
    return ast;
}

std::string PRINT(const std::string ast)
{
    return ast;
}

std::string rep(const std::string input)
{
    return PRINT(EVAL(READ(input)));
}

int main(int argc, char* argv[])
{
    std::string input;
    std::string prompt = "user> ";
    for (;;) {
      std::cout << prompt;
      std::getline(std::cin, input);
      std::cout << rep(input) << std::endl;
    }
    return 0;
}
