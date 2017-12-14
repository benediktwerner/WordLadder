#!/usr/bin/env python3

"""
Author: Benedikt Werner
Program to compute the shortest path between two words.
"""

from collections import defaultdict
import sys
import string
import os.path
import gzip

GZIP = True
GZIP_FILE_MODE = {"r": "rt", "w": "wt"}

WORD_LIST_FILE = "wordList.txt"
OUTPUT_FILE = "output.txt"
DATA_FILE = "data.gz" if GZIP else "data.txt"

WORDS_TO_INDEX = {}
INDEX_TO_WORD = {}
NEIGHBORS = {}


def open_data(mode="r"):
    """Open the data file to read or write"""
    if GZIP:
        return gzip.open(DATA_FILE, GZIP_FILE_MODE.get(mode, mode))
    return open(DATA_FILE, mode)


def sort_letters(word):
    """Sort the letters in a word"""
    return "".join(sorted(word))


def print_stdout(text):
    """Write text to stdout and flush"""
    sys.stdout.write(text)
    sys.stdout.flush()


def precompute():
    """Precompute data to speed up operation"""
    words = defaultdict(set)
    print("Reading words...", end="")
    with open(WORD_LIST_FILE, "r") as word_list:
        for i, line in enumerate(word_list):
            word = line.strip().lower()
            words[sort_letters(word)].add(i)
    print(" Done")
    print("Read", i, "words\n")

    length = len(words)
    output_steps = length // 100
    progress = 0
    print_stdout("Calculating neighbors: [" + "-"*40 + "]" + chr(8)*41)
    words_done = 0

    with open_data("w") as data_file:
        for word in words:
            if words_done % output_steps == 0:
                new_progress = (words_done * 40) // length
                print_stdout("#" * (new_progress - progress))
                progress = new_progress
            words_done += 1

            neighbors = set()
            for c in string.ascii_letters:
                new = sort_letters(word + c)
                if new in words:
                    neighbors |= words[new]
            for i in range(len(word)):
                new = sort_letters(word[:i] + word[i+1:])
                if new in words:
                    neighbors |= words[new]

            neighbors_string = " ".join(map(str, neighbors))
            for i in words[word]:
                data_file.write(str(i) + " " + neighbors_string + "\n")
    print_stdout("#"*(40-progress) + "] Done\n")


def load_data():
    """Loads the word list and the precomputed data"""
    with open(WORD_LIST_FILE, "r") as word_list:
        for i, line in enumerate(word_list):
            word = line.strip().lower()
            WORDS_TO_INDEX[word] = i
            INDEX_TO_WORD[i] = word
    print("Loaded", len(WORDS_TO_INDEX), "words")

    if not os.path.isfile(DATA_FILE):
        print("No precomputed data found. Generating...")
        precompute()
    with open_data("r") as data_file:
        for line in data_file:
            line = line.strip().split(" ")
            NEIGHBORS[int(line[0])] = set(map(int, line[1:]))


def generate_path(came_from, start, goal):
    """Generate the path of words from the 'came_from' dictionary"""
    path = []
    while goal != start:
        path.append(goal)
        goal = came_from[goal]
    path.append(start)
    return list(map(lambda x: INDEX_TO_WORD[x], reversed(path)))


def generate_output(path=None):
    """Write the result to the output file"""
    if path is None:
        return open(OUTPUT_FILE, "w").close()
    print("Found path:")
    with open(OUTPUT_FILE, "w") as output_file:
        print(*path, sep="\n")
        output_file.write("\n".join(path))


def check_words(*words):
    """Check if words are in the word list"""
    for word in words:
        if word not in WORDS_TO_INDEX:
            print("Invalid word:", word)
            return False
    return True


def compute(start, goal):
    """Compute a path from start to end"""
    if not check_words(start, goal):
        generate_output()
        return

    start = WORDS_TO_INDEX[start]
    goal = WORDS_TO_INDEX[goal]
    stack = [start]
    done = set(stack)
    came_from = {}
    words_done = 0
    output_steps = len(WORDS_TO_INDEX) // 100

    while stack:
        word = stack.pop(0)
        if words_done % output_steps == 0:
            print_stdout("Words visited: {}\r".format(words_done))
        words_done += 1
        for neighbor in NEIGHBORS[word]:
            if neighbor == goal:
                came_from[neighbor] = word
                print_stdout("Words visited: {}\n".format(words_done))
                generate_output(generate_path(came_from, start, goal))
                return
            if neighbor not in done:
                stack.append(neighbor)
                done.add(neighbor)
                came_from[neighbor] = word
    print_stdout("Words visited: {} (All reachable)\n".format(words_done))
    print("No path found")
    generate_output()


def main():
    """Main method"""
    if len(sys.argv) == 2 and sys.argv[1] == "precompute":
        precompute()
        return
    if len(sys.argv) != 3:
        print("Invalid arguments:", *sys.argv)
        print("Usage:", sys.argv[0], "startword", "goalword")
        print("Usage:", sys.argv[0], "precompute")
        return
    load_data()
    compute(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
