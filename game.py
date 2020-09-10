import characters
import time
import os
import json
from datetime import datetime


class Game:

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
        games = Game.load_all_games(game_log)
        games[self.time] = self.to_dict()
        with open(game_log, "w") as log_file:
            json.dump(games, log_file)

    @staticmethod
    def load_all_games(game_log):
        with open(game_log, "r") as log_file:
            games = json.load(log_file)
        return games

    @staticmethod
    def load_all_games_sorted(game_log, rev=False):
        games = Game.load_all_games(game_log)
        game_list = []
        for game_json in games.values():
            game_obj = Game.from_dict(game_json)
            game_list.append(game_obj)

        game_list = sorted(game_list, key=Game._game_sort_key, reverse=rev)

        return game_list

    @staticmethod
    def _game_sort_key(g):
        return g.time

    def to_dict(self):
        x_characters = []
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
        if 'time' not in d:
            d['time'] = time.time()

        if d['type'] == 'sp':
            return SinglePlayerGame(d['characters'], d['stocks'], stage=d['stage'], game_time=d['time'])
        if d['type'] == 'mp':
            return MultiPlayerGame(d['characters'], d['stocks'], stage=d['stage'], game_time=d['time'])
        if d['type'] == 'ffa':
            return FreeForAllGame(d['characters'], d['stocks'], stage=d['stage'], game_time=d['time'])


class SinglePlayerGame(Game):
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
        return self.stocks[0] > self.stocks[1]


class MultiPlayerGame(Game):
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
        return self.stocks[0] + self.stocks[1] > self.stocks[2] + self.stocks[3]


class FreeForAllGame(Game):
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
        for stock in self.stocks[1::]:
            if self.stocks[0] < stock:
                return False
        return True


if __name__ == "__main__":

    game_log = os.curdir + "/resources/games.txt"
    games = Game.load_all_games_sorted(game_log)

    for game in games:
        print(game)
