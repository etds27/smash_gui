import json
import os


class Stage:
    def __init__(self, name, image, display_name):
        self.name = name
        self.image = image
        self.display_name = display_name

    def __str__(self):
        return self.display_name

    @staticmethod
    def get_stages(stage_json):
        stage_dict = {}
        with open(stage_json, "r") as open_json:
            stage_data = json.load(open_json)

        for key, value in stage_data.items():
            stage_dict[key] = Stage.from_dict(value)

        return stage_dict

    @staticmethod
    def from_dict(d):
        return Stage(d['name'], d['img'], d['display_name'])


if __name__ == "__main__":
    path = os.curdir + "/resources/stages.json"
    print(Stage.get_stages(path))
