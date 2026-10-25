
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import re

NUM_REDUCERS = 2

PROJECT_FOLDER = Path(__file__).resolve().parent.parent
INPUT_FOLDER = PROJECT_FOLDER / "datasets" / "text-files"
OUTPUT_FOLDER = Path(__file__).resolve().parent / "output"


# Map: turn each word into (word, 1)
def mapper(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read().lower()

    words = re.findall(r"[a-z0-9]+", text)
    pairs = []

    for word in words:
        pairs.append((word, 1))

    return pairs


# Combine: count repeated words inside one file
def combiner(pairs):
    counts = defaultdict(int)

    for word, number in pairs:
        counts[word] += number

    return counts


# Partition: choose which reducer receives a word
def partition(word):
    return sum(ord(letter) for letter in word) % NUM_REDUCERS


# Reduce: return words in alphabetical order
def reducer(counts):
    result = {}

    for word in sorted(counts):
        result[word] = counts[word]

    return result


def main():
    files = sorted(INPUT_FOLDER.glob("book_*.txt"))

    if not files:
        print("No input files found!")
        return

    # Run mappers using multiple threads
    with ThreadPoolExecutor(max_workers=len(files)) as executor:
        mapped_results = list(executor.map(mapper, files))

    # Create two reducers
    partitions = [defaultdict(int) for _ in range(NUM_REDUCERS)]

    # Combine and partition the mapper results
    for pairs in mapped_results:
        combined = combiner(pairs)

        for word, count in combined.items():
            reducer_number = partition(word)
            partitions[reducer_number][word] += count

    # Save each reducer's results in a separate file
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    for number in range(NUM_REDUCERS):
        final_result = reducer(partitions[number])
        output_file = OUTPUT_FOLDER / f"reducer_{number}.txt"

        with open(output_file, "w", encoding="utf-8") as file:
            for word, count in final_result.items():
                file.write(f"{word} {count}\n")

        print(f"Reducer {number} finished.")

    print("MapReduce finished successfully!")


if __name__ == "__main__":
    main()
