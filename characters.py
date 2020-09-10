import os
import re
import json
import pprint


def character_data():
    character_json = root_dir + "/resources/characters.txt"
    with open(character_json, "r") as data:
        x_character_data = json.load(data)

        for character_name, character_json in x_character_data.items():
            image = character_json['img']
            display_name = character_json['display_name']
            game = character_json['game']
            placement = character_json['placement']

            x_character = Character(
                character_name,
                image,
                display_name,
                game,
                placement)
            characters[character_name] = x_character
    return characters


class Character:
    def __init__(self, name, image, display_name, game, placement):
        self.name = name
        self.image = image
        self.display_name = display_name
        self.game = game
        self.placement = placement

    def __str__(self):
        return self.display_name + " (" + self.game + ")"

    def __eq__(self, other):
        if other is not None:
            return self.name == other.name
        else:
            return False

    @staticmethod
    def get_character(name):
        return characters[name]


root_dir = os.curdir
characters = {}
character_data()

if __name__ == '__main__':
    root_dir = os.curdir
    characters = {}

    character_data()
    for character in characters.values():
        print(character)
