import re

class preCompilingAnalyzing():

    """
    Klasa preCompilingAnalyzing służy do analizy potrzeb pamięciowych dla procedur w danym kodzie.
    Analiza opiera się na prekompilacji i przetwarzaniu tekstu źródłowego w celu określenia zużycia pamięci.
    """

    @staticmethod
    def getMemoryNeedForProcedures(content):
        """
                Metoda statyczna getMemoryNeedForProcedures analizuje tekst źródłowy, aby określić wymagania pamięciowe dla poszczególnych procedur.

                :param content: Tekst źródłowy, który ma zostać przeanalizowany.
                :return: Słownik, gdzie kluczem jest nazwa procedury, a wartością jest krotka (tuple).
                         Pierwszym elementem krotki jest skumulowana ilość zużytej pamięci dla procedury (uwzględniając parametry i zmienne lokalne),
                         drugim elementem jest numer porządkowy procedury w kontekście całego przetwarzanego kodu.
                """
        content = re.sub('#.*$', '', content, flags=re.MULTILINE)
        content = content.replace('\n', ' ').replace('\r', ' ')
        content = re.sub(' +', ' ', content).strip()

        procedures = re.findall(r'PROCEDURE\s+.*?\s+IS.*?END', content, re.DOTALL)
        memory_requirements = {}
        cumulative_parameters = 0
        cumulative_local_vars = 0

        for i, procedure in enumerate(procedures):
            # Ekstrakcja nazwy procedury
            procedure_name = re.search(r'PROCEDURE\s+(\w+)', procedure).group(1)

            # Ekstrakcja argumentów procedury
            arguments_str = re.search(r'\((.*?)\)', procedure)
            parameters_count = 0
            if arguments_str:
                arguments = arguments_str.group(1).split(',')
                parameters_count = len([arg for arg in arguments if arg.strip()])  # Liczenie parametrów

            # Zliczanie zmiennych lokalnych
            local_vars_str = re.search(r'IS(.*?)IN', procedure, re.DOTALL)
            local_vars_count = 0
            if local_vars_str:
                local_vars = re.findall(r'(\w+)\[?(\d*)\]?', local_vars_str.group(1))
                local_vars_count = sum(int(size) if size else 1 for var, size in local_vars)

            # Dodanie informacji o procedurze do słownika
            memory_requirements[procedure_name] = (cumulative_parameters + cumulative_local_vars, i)

            # Aktualizacja sumarycznych wartości dla następnej procedury
            cumulative_parameters += parameters_count
            cumulative_local_vars += local_vars_count

        # Dodanie wpisu dla "main"
        memory_requirements["main"] = (cumulative_parameters + cumulative_local_vars, len(procedures))

        return memory_requirements


def main():
    with open("text.txt", "r") as file:
        content = file.read()

    memory_requirements = preCompilingAnalyzing.getMemoryNeedForProcedures(content)

    print(f"Wymagania pamięciowe procedur: {memory_requirements}")

if __name__ == "__main__":
    main()
