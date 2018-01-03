#!/usr/bin/env python3

"""
Author: Benedikt Werner
Program to compute the shortest path between two words.
"""

from __future__ import print_function
from collections import defaultdict
from time import time
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


##########################################################
# Helper methods
##########################################################

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


##########################################################
# Methods to find the shortest word ladder
##########################################################

def precompute():
    """Precompute data to speed up operation"""
    words = defaultdict(set)
    print("Reading words...", end="")
    with open(WORD_LIST_FILE, "r") as word_list:
        for i, line in enumerate(word_list):
            word = line.strip().lower()
            words[sort_letters(word)].add(i)
    print(" Done")
    print("Read", i+1, "words\n")

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
                if neighbors_string:
                    data_file.write("{} {}\n".format(i, neighbors_string))
                else:
                    data_file.write("{}\n".format(i))
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
    print("Loaded precomputed data")


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


##########################################################
# Additional code for fun
##########################################################

def count_groups():
    """Count the number of connected components in the word graph"""
    print("Searching groups...")
    todo = set(INDEX_TO_WORD.keys())
    group_counts = []
    while todo:
        count = 0
        stack = [todo.pop()]
        while stack:
            word = stack.pop(0)
            count += 1
            for neighbor in NEIGHBORS[word]:
                if neighbor in todo:
                    stack.append(neighbor)
                    todo.remove(neighbor)
        group_counts.append(count)
    print("Found a total of", len(group_counts), "groups")
    counter = Counter(group_counts)
    for key in sorted(counter.keys()):
        print("{:7} groups with {:7} element(s)".format(counter[key], key))


def find_words_in_group(start_word):
    stack = [start_word]
    result = set(stack)
    while stack:
        word = stack.pop(0)
        for neighbor in NEIGHBORS[word]:
            if neighbor not in result:
                stack.append(neighbor)
                result.add(neighbor)
    return result


def format_time(time):
    time = int(time)
    if time > 3600:
        return "{}h {}".format(time // 3600, format_time(time % 3600))
    elif time > 60:
        return "{}m {}".format(time // 60, format_time(time % 60))
    return "{}s".format(time)


def get_next_output(output):
    if output % 1000 == 0:
        return output + 1000
    if output % 100 == 0:
        return output + 100
    return output + 10

def find_longest_path(start_word):
    """Find the longest word ladder in the group of a given word"""
    max_start = None
    max_end = None
    max_length = 0
    start_time = time()

    group = find_words_in_group(WORDS_TO_INDEX[start_word])
    length = len(group)
    words_checked = 0
    next_output = 10
    print("Words to check:", length)

    for start in group:
        stack = [start]
        done = set(stack)
        steps_to = {start: 0}

        if words_checked == next_output:
            ellapsed = time() - start_time
            time_left = (ellapsed / words_checked) * (length - words_checked)
            print(words_checked, "in",  format_time(ellapsed), "- estimated time left:", format_time(time_left))
            next_output = get_next_output(next_output)
        words_checked += 1

        while stack:
            word = stack.pop(0)
            curr_steps = steps_to[word]
            for neighbor in NEIGHBORS[word]:
                if neighbor not in done:
                    stack.append(neighbor)
                    done.add(neighbor)
                    steps_to[neighbor] = curr_steps + 1
        if steps_to[word] > max_length:
            max_length = steps_to[word]
            max_start = start
            max_end = word
            print("New longest path:", INDEX_TO_WORD[max_start], "to", INDEX_TO_WORD[max_end], "with length", max_length)

    print("Longest path is from", INDEX_TO_WORD[max_start], "to", INDEX_TO_WORD[max_end], "with length", max_length)


##########################################################
# Main method
##########################################################

def main():
    """Main method"""
    if len(sys.argv) == 2:
        if sys.argv[1] == "precompute":
            return precompute()
        if sys.argv[1] == "groups":
            load_data()
            return count_groups()
    if len(sys.argv) != 3:
        print("Invalid arguments:", *sys.argv)
        print("Usage:", sys.argv[0], "<startword>", "<goalword>")
        print("Usage:", sys.argv[0], "precompute")
        print("Usage:", sys.argv[0], "groups")
        print("Usage:", sys.argv[0], "findlongestpath", "<word_from_largest_connected_component>")
        return
    load_data()
    if sys.argv[1] == "findlongestpath":
        return find_longest_path(sys.argv[2])
    compute(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
