import sys
import getopt
import os
import re
import platform
from math import ceil
from multiprocessing import Value, Process, Lock
import time

# Constante/Definição de cor
RED_START = '\033[91m'
GREEN_START = '\033[92m'
COLOR_END = '\033[0m'
if platform.system() == "Windows":
    os.system('color')


def main(argv):
    try:
        # Obter argumentos, opções
        opts, args = getopt.getopt(argv, "clp:")

    except getopt.GetoptError:
        # Mensagem de ajuda caso o comando seja malformado
        print("Utilização: pgrepwc [-c|-l] [-p n] palavra {ficheiros}")
        sys.exit(2)

    # Por omissão, todas as pesquisas/contagens são feitas no processo pai, pelo que não se dá paralelização
    numberOfProcesses = 1
    parallelization = False

    if len(args) == 1:  # Caso apenas seja dada a palavra, e não os nomes dos ficheiros
        print("Introduza os nomes dos ficheiros a pesquisar, numa linha, separados por espaços:")
        allFiles = removeDuplicates(input().split())  # Evitar pesquisar nos mesmos ficheiros várias vezes
        print()  # Razões Estéticas
    else:
        allFiles = removeDuplicates(args[1:])  # Evitar pesquisar nos mesmos ficheiros várias vezes

    for opt in opts:
        if opt[0] == "-p":
            numberOfProcesses = int(opt[1])
            parallelization = True  # Ativar paralelização caso a opção "-p n" seja utilizada
            if numberOfProcesses == 0:  # Evitar erros se for pedido "-p 0", desligando a paralelização
                parallelization = False

    if numberOfProcesses > len(allFiles):  # Evitar ciclos do for desnecessários, utilizar no máximo tantos
        numberOfProcesses = len(allFiles)  # processos como ficheiros referidos

    # Definição das variáveis de contagem em memória partilhada
    totalWC = Value("i", 0)
    totalLC = Value("i", 0)

    if parallelization:

        # Definição do número estimado de ficheiros a lidar por cada processo
        numberOfFilesPerProcess = ceil(len(allFiles) / numberOfProcesses)

        # Definição de lista de processos a executar
        p = []

        # Definição de um mutex para evitar problemas de sincronização / outputs intercalados
        mutex = Lock()

        # Divisão do trabalho pelos vários processos
        for process in range(numberOfProcesses):
            while len(allFiles) > 0:

                filesToHandle = []

                for i in range(numberOfFilesPerProcess):

                    if len(allFiles) >= 1:
                        filesToHandle.append(allFiles.pop(0))

                p.append(Process(target=matchFinder, args=(filesToHandle, opts, args[0], totalWC, totalLC, mutex)))

        # Execução e espera pela conclusão dos processos filhos 

        before = time.time()
        for process in p:
            process.start()
        for process in p:
            process.join()
        after = time.time()

    else:  # Caso a paralelização esteja desligada, todo o trabalho é feito pelo processo pai

        before = time.time()
        matchFinder(allFiles, opts, args[0], totalWC, totalLC)
        after = time.time()

    if parallelization:
        print(f"PID PAI: {os.getpid()}")

    if any("-c" in opt for opt in opts):
        print(f"Total de ocorrências: {totalWC.value}")

    if any("-l" in opt for opt in opts):
        print(f"Total de linhas: {totalLC.value}")
    
    print("Tempo total:", after - before)


def matchFinder(files, args, word, totalWC, totalLC, mutex=None):

    # Expressão regular responsável por identificar instâncias da palavra isolada
    regex = fr"\b{word}\b"

    for file in files:

        output = []
        wc = 0
        lc = 0
        try:
            with open(file, "r", encoding="utf-8") as f:
                output.append("==================================================")
                output.append(f"PID: {os.getpid()}\nFicheiro: {file}\n")

                lineNumber = 0

                for line in f:
                    lineNumber += 1
                    matches = re.findall(regex, line)
                    if matches:
                        lc += 1
                        wc += len(matches)

                        # Uso do método re.sub() para substituir todas as instâncias da palavra isolada
                        # por instâncias da mesma em versão colorida
                        processedLine = re.sub(regex, RED_START + word + COLOR_END, line)
                        output.append(f"{GREEN_START}{lineNumber}{COLOR_END}: {processedLine}")

                # Output do resultado de cada processo
                # O mutex ajuda a impedir outputs intercalados e que o acesso às variáveis globais seja mediado

                if mutex:
                    mutex.acquire()

                for line in output:
                    print(line)

                print()
                for opt in args:
                    if opt[0] == "-c":
                        print(f"Total de ocorrências da palavra: {wc}\n"
                              f"A enviar para o processo pai ({os.getppid()})...")
                    if opt[0] == "-l":
                        print(f"Total de linhas em que a palavra apareceu: {lc}\n"
                              f"A enviar para o processo pai ({os.getppid()})...")
                print(f"==================================================\n")

            # Incrementação nas variáveis de contagem em memória partilhada
            totalWC.value += wc
            totalLC.value += lc

            # Libertação do mutex para que os outros processos possam imprimir o seu resultado
            if mutex:
                mutex.release()

        except FileNotFoundError:
            print(f"Ficheiro '{file}' não encontrado. Verifique o seu input.")


def removeDuplicates(inputList):
    """
    Função responsável por retirar elementos duplicados de uma lista.
    Requires: inputList diferente de None.
    Ensures: uma lista semelhante a inputList, sem elementos duplicados.
    """
    return list(dict.fromkeys(inputList))


if __name__ == "__main__":
    main(sys.argv[1:])
