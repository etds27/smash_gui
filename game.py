import characters
import time
import os
import json
from datetime import datetime


class Game:
    """
    Class contains the the data for the game
    Contains factory functions to create games from dictionaries
    """
    def __init__(self, game_characters, stocks, stage="fd", game_time=time.time()):
        x_characters = []
        for character in game_characters:
            if isinstance(character, str):
                x_characters.append(characters.Character.get_character(character))
            else:
                x_characters.append(character)

        self.characters = x_characters
        self.stocks = stocks
        self.stage = stage
        self.time = game_time
        self.type = None

    def __lt__(self, other):
        return self.time < other.time

    def record_game(self, game_log):
        """
        Takes the path to the game log and records the instance of this game
        Needs to load all games from game log first, then appends this game, then writes all games back to log
        :param game_log: path to game log file
        :return:
        """
        games = Game.load_all_games(game_log)
        games[self.time] = self.to_dict()
        with open(game_log, "w") as log_file:
            json.dump(games, log_file)

    @staticmethod
    def load_all_games(game_log):
        """
        Reads all games from the game log
        returns a dictionary of all the games as Dictionaries, not game objects
        :param game_log:
        :return:
        """
        with open(game_log, "r") as log_file:
            games = json.load(log_file)
        return games

    @staticmethod
    def load_all_games_sorted(game_log, rev=False):
        """
        Returns a sorted list of game objects
        :param game_log:
        :param rev:
        :return:
        """
        games = Game.load_all_games(game_log)
        game_list = []
        for game_json in games.values():
            game_obj = Game.from_dict(game_json)
            game_list.append(game_obj)

        # Sort game by the time they were recorded
        game_list = sorted(game_list, key=Game._game_sort_key, reverse=rev)

        return game_list

    @staticmethod
    def _game_sort_key(g):
        return g.time

    def to_dict(self):
        """
        Takes the current game and translates it to a dictionary so that it can be put into JSON
        :return:
        """
        x_characters = []
        # Need to save characters as names and not character objects
        for character in self.characters:
            if isinstance(character, characters.Character):
                x_characters.append(character.name)
            else:
                x_characters.append(character)

        return {
            'time': self.time,
            'type': self.type,
            'characters': x_characters,
            'stocks': self.stocks,
            'stage': self.stage
        }

    @staticmethod
    def from_dict(d):
        """
        Method creates a Game object from a dictionary passed in
        :param d:
        :return:
        """
        if 'time' not in d:
            d['time'] = time.time()

        if d['type'] == 'sp':
            return SinglePlayerGame(d['characters'], d['stocks'], stage=d['stage'], game_time=d['time'])
        if d['type'] == 'mp':
            return MultiPlayerGame(d['characters'], d['stocks'], stage=d['stage'], game_time=d['time'])
        if d['type'] == 'ffa':
            return FreeForAllGame(d['characters'], d['stocks'], stage=d['stage'], game_time=d['time'])


class SinglePlayerGame(Game):
    """
    Inherits the Game object. Contains analysis for 1 v 1 games
    """
    def __init__(self, x_characters, stocks, stage="fd", game_time=time.time()):
        super().__init__(x_characters,
                         stocks,
                         stage,
                         game_time)
        self.type = "sp"

    def __str__(self):
        string = ""
        if self.is_win():
            string += "W | "
        else:
            string += "L | "

        string += self.characters[0].display_name + " " + str(self.stocks[0]) + " | "
        string += self.characters[1].display_name + " " + str(self.stocks[1]) + " | " + \
                  datetime.utcfromtimestamp(self.time).strftime('%Y-%m-%d %H:%M:%S')
        return string

    def is_win(self):
        """
        If the player has more stocks than the opponent, then they win
        :return:
        """
        return self.stocks[0] > self.stocks[1]


class MultiPlayerGame(Game):
    """
    Inherits the Game object. Contains analysis for 2 v 2 games
    """
    def __init__(self, x_characters, stocks, stage="fd", game_time=time.time()):
        super().__init__(x_characters,
                         stocks,
                         stage,
                         game_time)
        self.type = "mp"

    def __str__(self):
        string = ""
        if self.is_win():
            string += "W | "
        else:
            string += "L | "
        string += "You: %s (%i), %s (%i) | Them: %s (%i), %s (%i) | " % (
            self.characters[0].display_name, self.stocks[0],
            self.characters[1].display_name, self.stocks[1],
            self.characters[2].display_name, self.stocks[2],
            self.characters[3].display_name, self.stocks[3])
        string += datetime.utcfromtimestamp(self.time).strftime('%Y-%m-%d %H:%M:%S')
        return string

    def is_win(self):
        """
        If your team has more total stocks than the other team, then you win
        :return:
        """
        return self.stocks[0] + self.stocks[1] > self.stocks[2] + self.stocks[3]


class FreeForAllGame(Game):
    """
    Inherits the Game object. Contains analysis for free for all games
    """
    def __init__(self, x_characters, stocks, stage="fd", game_time=time.time()):
        super().__init__(x_characters,
                         stocks,
                         stage,
                         game_time)
        self.type = "ffa"

    def __str__(self):
        string = ""
        if self.is_win():
            string += "W | "
        else:
            string += "L | "
        string += "You: %s (%i) | Them: %s (%i), %s (%i), %s (%i) | " % (
            self.characters[0].display_name, self.stocks[0],
            self.characters[1].display_name, self.stocks[1],
            self.characters[2].display_name, self.stocks[2],
            self.characters[3].display_name, self.stocks[3])
        string += datetime.utcfromtimestamp(self.time).strftime('%Y-%m-%d %H:%M:%S')
        return string

    def is_win(self):
        """
        If you have more stocks than all the opponents, then you win
        :return:
        """
        for stock in self.stocks[1::]:
            if self.stocks[0] < stock:
                return False
        return True


if __name__ == "__main__":

    game_log_path = os.curdir + "/resources/games.txt"
    games = Game.load_all_games_sorted(game_log_path)

    for game in games:
        print(game)
