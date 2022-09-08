from collections import defaultdict
import itertools
import math
import random
import termcolor
from tqdm import tqdm

class wordle_bot:
    def __init__(self, answers_filepath):
        self.word_length = 5
        self.remaining_words = self.parse_word_file(answers_filepath)
        self.sequence_dictionary = self.generate_sequence_dictionary()
        self.all_words = self.remaining_words.copy()
        self.first_guess = True
    
    # used for consecutive test runs so that the sequence dictionary does not need to be rebuilt each time
    def reset(self):
        self.remaining_words = self.all_words.copy()
        self.first_guess = True

    # parses a file containing words separated by newlines into a set
    def parse_word_file(self, filepath):
        file = open(filepath, "r")
        content = file.read()
        word_list = content.splitlines()
        return set(word_list)

    # given a string 'guess', returns the sequence of greens, yellows, and greys if 'actual' was the correct word
    # 0: grey, 1: yellow, 2: green
    def compute_sequence(self, guess, actual):
        sequence = [0] * self.word_length
        actual_copy = list(actual)

        for idx in range(self.word_length):
            if actual_copy[idx] == guess[idx]:
                sequence[idx] = 2
                actual_copy[idx] = ""
        
        for idx in range(self.word_length):
            if guess[idx] in actual_copy and sequence[idx] != 2:
                sequence[idx] = 1
                for idx2 in range(len(actual_copy)):
                    if guess[idx] == actual_copy[idx2]:
                        actual_copy[idx2] = ""
                        break

        return tuple(sequence)

    # generates a dictionary of dictionaries that map from string -> sequences -> set of strings
    # contains every word, every possible sequence, and all the words that would remain given that sequence
    def generate_sequence_dictionary(self):
        sequence_dictionary = defaultdict(lambda: defaultdict(set))
        print("Generating sequence dictionary...\n")
        for word1 in tqdm(self.remaining_words):
            for word2 in self.remaining_words:
                sequence = self.compute_sequence(word1, word2)
                sequence_dictionary[word1][sequence].add(word2)
        return dict(sequence_dictionary)
    
    # computes the expected bits of information attained by each word
    def compute_entropies(self):
        entropy_dict = {}
        print("Computing entropies...\n")
        for word in tqdm(self.remaining_words):
            entropy_sum = 0
            for sequence in list(itertools.product([0,1,2], repeat=5)):
                matches = self.sequence_dictionary[word][sequence]
                matches = matches.intersection(self.remaining_words)

                probability = len(matches)/len(self.remaining_words)

                if probability != 0:
                    entropy = math.log(1/probability, 2)
                else:
                    entropy = 0
                entropy_sum += probability*entropy

            entropy_dict[word] = entropy_sum
        return entropy_dict
    
    # updates the remaining words after a guess (and its returned sequence) using the sequence dictionary 
    def update_remaining_words(self, guess, sequence):
        matches = self.sequence_dictionary[guess][sequence]
        self.remaining_words = self.remaining_words.intersection(matches)
    
    # chooses the word with the highest entropy among the remaining words
    def guess(self):
        if self.first_guess:
            self.first_guess = False
            return "crane"
           
        entropies = self.compute_entropies()
        guess = max(entropies, key=entropies.get)
        return guess
    
    # allows the user to play a game of wordle with suggestions from the bot
    def interactive(self):
        for i in range(6):
            guess = self.guess()
            print("Bot's suggestion:", guess)

            print("Enter results: (0:grey, 1:yellow, 2:green)")
            result_str = input()
            result = []

            for letter in result_str:
                result.append(int(letter))

            self.update_remaining_words(guess, tuple(result))


class wordle_engine:
    def __init__(self, allowed_words_filepath, answers_filepath, wordle_bot, correct_word = None):
        self.wordle_bot = wordle_bot
        self.num_guesses = 0
        self.game_over = False
        self.board = ""
        self.allowed_word_list = self.parse_word_file(allowed_words_filepath)
        self.answers_word_list = self.parse_word_file(answers_filepath)
        if correct_word == None:
            self.correct_word = self.generate_word()
        else:
            self.correct_word = correct_word

    def parse_word_file(self, filepath):
        file = open(filepath, "r")
        content = file.read()
        allowed_word_list = content.splitlines()
        return allowed_word_list

    def generate_word(self):
        return random.choice(self.answers_word_list)
    
    def simulate(self):
        while self.num_guesses < 7:
            guess = self.prompt()
            while not self.validate_guess(guess):
                guess = self.prompt()
            
            self.num_guesses += 1
            result = self.update_board(guess)
            
            self.wordle_bot.update_remaining_words(guess,tuple(result))

            if self.game_over:
                print("\nCurrent game board:")
                print(self.board)
                print("Congrats!", self.correct_word, "was the correct word")
                return self.num_guesses
        
        print("\nCurrent game board:")
        print(self.board)
        print("Game over! The correct word was", self.correct_word)
        
        return self.num_guesses
    
    def validate_guess(self, guess):
        if guess not in self.allowed_word_list:
            print("\nNot in word list, try again!")
            return False
        return True

    def prompt(self):
        if self.board != "":
            print("\nCurrent game board:")
            print(self.board)
        
        if self.wordle_bot == None:
            print("Enter a guess:")
            guess = input()

        else:
            guess = self.wordle_bot.guess()
            print("Bot's guess:", guess)

        return guess
    
    def update_board(self, guess):
        result = [0,0,0,0,0]
        result_str = ""
        correct_word_copy = list(self.correct_word)

        for idx in range(len(guess)):
            if correct_word_copy[idx] == guess[idx]:
                result[idx] = 2
                correct_word_copy[idx] = ""
        
        for idx in range(len(guess)):
            if guess[idx] in correct_word_copy and result[idx] != 2:
                result[idx] = 1
                for idx2 in range(len(correct_word_copy)):
                    if guess[idx] == correct_word_copy[idx2]:
                        correct_word_copy[idx2] = ""
                        break

        for idx in range(len(result)):
            if result[idx] == 2:
                result_str += termcolor.colored(guess[idx], 'green')
            elif result[idx] == 1:
                result_str += termcolor.colored(guess[idx], 'yellow')
            else:
                result_str += guess[idx]

        result_str += "\n"
        self.board += result_str

        if guess == self.correct_word:
            self.game_over = True
        
        return result

if __name__ == "__main__":
    bot = wordle_bot("wordle-answers-alphabetical.txt")

    ## SOLVE THE REAL WORDLE

    bot.interactive()


    ## TEST AVERAGE GUESSES

    # sum = 0
    # for i in range(100):
    #     engine = wordle_engine("valid-wordle-words.txt", "wordle-answers-alphabetical.txt", bot)
    #     sum += engine.simulate()
    #     bot.reset()
    
    # print("Average guesses",sum/100)
