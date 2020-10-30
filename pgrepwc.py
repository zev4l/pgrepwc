import sys, getopt, os
from math import ceil
import re

# Cor
CRED = '\033[91m'
CEND = '\033[0m'
os.system('color')


def main(argv):

    try:
        opts, args = getopt.getopt(argv,"clp:")

        # print(opts)

        # print(args)

    except getopt.GetoptError:
        print("Utilização: pgrepwc [-c|-l] [-p n] palavra {ficheiros}")
        sys.exit(2)


    totalWC = 0
    totalLC = 0
    numberOfProcesses = 1

    allFiles = args[1:]

    for opt in opts:
        if opt[0] == "-p":
            numberOfProcesses = opt[1]

    numberOfFilesPerProcess = ceil(len(allFiles)/numberOfProcesses)

    while len(allFiles)>0:

        filesToHandle = []

        for i in range(numberOfFilesPerProcess):

            if i >= len(allFiles)-1:
                filesToHandle.append(allFiles.pop(i))


        wc, lc = matchFinder(filesToHandle, args, args[0])
        totalWC += wc
        totalLC += lc


    if any("-c" in opt for opt in opts):
        print(f"Total de ocorrências: {totalWC}")

    if any("-l" in opt for opt in opts):
        print(f"Total de linhas: {totalLC}")


def matchFinder(files, args, word):

    wc = 0
    lc = 0

    regex = fr"\b{word}\b"
    
    for file in files:
        # se -p omitido ou 0
        with open(file, "r") as f:

            print(f"PID: {os.getpid()}\nFicheiro: {file}\n")

            lines = f.readlines()
            
            for lineIndex in range(len(lines)):
                line = lines[lineIndex]
                matches = re.findall(regex, line)
                if matches:
                    lc += 1
                    wc += len(matches)

                    processedLine = re.sub(regex, CRED + word + CEND, line) #replace matches with colored versions
                    print(f"{lineIndex+1}: {processedLine}")

    return wc, lc

                    

if __name__ == "__main__":
   main(sys.argv[1:])