import characters
import game
import tkinter as tk
import os
import time
import re
import game_mode_config
import colors
import stages

from PIL import ImageTk, Image
from tkinter import font

character_image_folder = os.curdir + "/character_images"
stage_image_folder = os.curdir + "/stage_images"
stage_json = os.curdir + "/resources/stages.json"
game_log = os.curdir + "/resources/games.txt"


# FONT_NORMAL = font.Font(family="Segoe UI", size=12)
# FONT_BOLD = font.Font(family="Segoe UI Black")


class SmashApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Setting up overall window functionality
        self.attributes("-fullscreen", True)
        self.state = False
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.end_fullscreen)

    def toggle_fullscreen(self, event=None):
        self.state = not self.state  # Just toggling the boolean
        self.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.attributes("-fullscreen", False)
        return "break"


class SmashGui(tk.Frame):
    """
    SmashGui is a frame that can be placed inside another Frame or Window
    Contains:
        Character Selection
        Game History
        Current Game Status
    """

    def __init__(self, master=None):
        super().__init__(master)

        default_font = font.Font(family="Segoe UI Semibold", size=10)
        self.option_add("*Font", default_font)

        # Sorting prereqs. sort_reverse_bit is the variable for the reverse checkbutton
        self.sort_group = SelectionButtonGroup()
        self.sort_reverse_bit = tk.IntVar(0)

        # Variable will store all previously played Game objects
        self.game_history = []

        self.game_mode = 'sp'
        self.sort_mode = 'place'

        # Holds the game handler class for the selected game mode
        # This is the default value. To change, change this, and the self.game_mode above
        self.game_handler = self.SinglePlayerHandler(self)

        # Tag to track who is currently selecting the character
        self.selection_mode = 'owner'
        self.stage = None

        self.pack(fill='both', expand='yes')

        self.master = master
        # Places all components within SmashGui
        self._populate_interface()

        self.game_selection_group.set(self.game_mode)
        self.sort_group.set(self.sort_mode)
        self._sort_character_gui(SmashGui.NameSorter())

    class GameHandler:
        """
        GameHandler class is an "abstract" class to outline the Specific Game Handlers for
            Single Player
            Multi Player
            Free For All
        modes
        """

        def __init__(self, smash_gui):
            self.stage = "final_destination"
            self.selection_turn = None
            self.player_group = SelectionButtonGroup()
            self.smash_gui = smash_gui
            self.character_tracker = {}
            self.turn_index = 0
            self.turn_keys = []

        def create_character_overview(self, tag, d, master):
            """
            Function creates the selected character areas on the bottom panel.
            Always places the gui in the right most position of the frame

            :param tag: This is the dictionary key so that the proper player config is loaded for this Gui
            :param d: Player config dictionaries
            :param master:
            :return: Returns the complete Character overview gui
            """
            character_data = d[tag]
            gui = self.smash_gui.CharacterSelectedGui(master, tag, self.smash_gui)
            col = master.grid_size()[0]
            gui.grid(column=col, row=0, sticky='news')
            master.grid_columnconfigure(col, weight=1, uniform="key")
            master.grid_rowconfigure(0, weight=1)
            gui.set_color(character_data['color'])
            return gui

        # abstract
        def select_character(self, character_gui):
            """
            Saves the selected character to the handlers character/player data dictionary

            :param character_gui:
            :return:
            """
            current_data = self.character_tracker[self.selection_turn]
            previous_character = current_data["character"]

            # If the player had a character previously selected, deselect it first before selecting the new one
            if previous_character is not None:
                print("Deselecting: " + str(previous_character))
                current_data["character"] = None
                current_data["gui"].clear()
                current_data["ccg"].deselect_character(self.selection_turn)

            # If the player selects their already selected character, then no processing needs to be done
            if previous_character != character_gui.character:
                print("Selecting: " + str(character_gui.character))
                current_data["character"] = character_gui.character
                current_data["gui"].select_character(character_gui)
                current_data["ccg"] = character_gui
                character_gui.select_character(self.selection_turn, current_data["color"])
                value = self.next_selection_turn()

                self.set_turn(value)

        # abstract
        def ready_to_save(self):
            """
            Checks whether all necessary data is present in the dictionary to create a game object.
            :return: True or False
            """
            for player in self.character_tracker.keys():
                if self.character_tracker[player]["character"] is None or \
                        self.character_tracker[player]["stocks"] is None:
                    return False
            return True

        def next_selection_turn(self):
            """
            Sets the active players turn to the next player in the logical order
            :return:
            """
            self.turn_index = (self.turn_index + 1) % len(self.turn_keys)
            return self.turn_keys[self.turn_index]

        def set_stock(self, tag, num):
            """
            Updates the stock value for a specific player in the game dicitonary
            :param tag: designates the player to set the stock value for
            :param num:
            :return:
            """
            self.character_tracker[tag]["stocks"] = num

        def set_stage(self, stage):
            self.stage = stage

        def populate_player_frame(self):
            """
            Creates the display that shows which player is choosing their character
            :return:
            """
            self.player_group = SelectionButtonGroup()
            frame = self.smash_gui.player_frame

            # Each loop creates a display for a specific character.
            # If it is clicked, it will switch to that player's turn
            for key in self.turn_keys:
                data = self.character_tracker[key]
                button = SelectionButtonGroup.SelectionButton(frame, self.player_group, value=key)
                button.set_colors(abg=data["color"], afg=colors.SMASH_DARK, bg=colors.SMASH_NEUTRAL,
                                  fg=colors.SMASH_DARK)
                button.configure(command=lambda key=key: self.set_turn(key), text=data["short_name"], relief='flat')
                button.pack(side='left', fill='both')

            # Set the default player to the first one
            self.player_group.set(self.turn_keys[0])

        def set_turn(self, value):
            """
            Sets which player the next selected character will be assigned to
            Updates the player indicator displays
            :param value:
            :return:
            """
            self.selection_turn = value
            self.turn_index = self.turn_keys.index(value)
            self.player_group.set(self.selection_turn)

        def update_overview_frame(self):
            pass

        def save_game(self):
            """
            Takes the game dictionary and creates a Game object with it
            Records the game in the game_log
            :return:
            """
            current_game = game.Game.from_dict(self.assemble_game_dict())
            print("Created game: " + str(current_game))
            current_game.record_game(game_log)

        def assemble_game_dict(self):
            """
            Takes the current game dictionary which has data assigned to user's of the gui and
                transforms it into a dictionary structure that can be parsed into a Game Object
            :return: game object dictionary structure
            """
            characters = []
            stocks = []
            for key in self.turn_keys:
                characters.append(self.character_tracker[key]['character'])
                stocks.append(self.character_tracker[key]['stocks'])
            d = {
                'time': time.time(),
                'type': self.type,
                'characters': characters,
                'stocks': stocks,
                'stage': self.stage
            }

            print("Game dict: " + str(d))
            return d

    class SinglePlayerHandler(GameHandler):
        """
        Game Handler for 1 v 1 games
        Tag = 'sp'
        Players = 'own', 'opp'
        """

        def __init__(self, smash_gui):
            super().__init__(smash_gui)
            self.selection_turn = "own"
            self.type = 'sp'
            self.turn_keys = ["own", "opp"]
            print("Initializing Single Player Handler")

        def populate_overview_frame(self, character_overview_frame):
            """
            Method creates 2 current player selection frames. One for each player
            :param character_overview_frame:
            :return:
            """

            self.character_tracker = game_mode_config.character_tracker[self.type]

            self.character_tracker["own"]["gui"] = self.create_character_overview("own",
                                                                                  self.character_tracker,
                                                                                  character_overview_frame)
            self.character_tracker["opp"]["gui"] = self.create_character_overview("opp",
                                                                                  self.character_tracker,
                                                                                  character_overview_frame)

    class MultiPlayerHandler(GameHandler):
        """
        Game Handler for 2 v 2
        Tag = 'mp'
        players = "own1", "own2", "opp1", "opp2"
        """

        def __init__(self, smash_gui):
            super().__init__(smash_gui)
            self.selection_turn = "own1"
            self.type = 'mp'
            self.turn_index = 0
            self.turn_keys = ["own1", "own2", "opp1", "opp2"]
            print("Initializing Multi Player Handler")

        def populate_overview_frame(self, character_overview_frame):
            """
            Method creates 4 current player selection frames. 2 for the users team and 2 for the opponents
            :return:
            """
            self.character_tracker = game_mode_config.character_tracker[self.type]
            self.character_tracker["own1"]["gui"] = self.create_character_overview("own1",
                                                                                   self.character_tracker,
                                                                                   character_overview_frame)
            self.character_tracker["own2"]["gui"] = self.create_character_overview("own2",
                                                                                   self.character_tracker,
                                                                                   character_overview_frame)
            self.character_tracker["opp1"]["gui"] = self.create_character_overview("opp1",
                                                                                   self.character_tracker,
                                                                                   character_overview_frame)
            self.character_tracker["opp2"]["gui"] = self.create_character_overview("opp2",
                                                                                   self.character_tracker,
                                                                                   character_overview_frame)

    class FreeForAllHandler(GameHandler):
        def __init__(self, smash_gui):
            super().__init__(smash_gui)
            self.selection_turn = "own"
            self.type = 'ffa'
            self.turn_index = 0
            self.turn_keys = ["own", "opp1", "opp2", "opp3"]
            print("Initializing Single Player Handler")

            # abstract

        def populate_overview_frame(self, character_overview_frame):
            """
            Method creates 4 current player selection frames. the user and then 3 opponents
            :param character_overview_frame:
            :return:
            """
            self.character_tracker = game_mode_config.character_tracker[self.type]
            self.character_tracker["own"]["gui"] = self.create_character_overview("own",
                                                                                  self.character_tracker,
                                                                                  character_overview_frame)
            self.character_tracker["opp1"]["gui"] = self.create_character_overview("opp1",
                                                                                   self.character_tracker,
                                                                                   character_overview_frame)
            self.character_tracker["opp2"]["gui"] = self.create_character_overview("opp2",
                                                                                   self.character_tracker,
                                                                                   character_overview_frame)
            self.character_tracker["opp3"]["gui"] = self.create_character_overview("opp3",
                                                                                   self.character_tracker,
                                                                                   character_overview_frame)

    class CharacterSelectedGui(tk.Frame):
        """
        Class constructs the player's selected characters display.
        Contains:
            The image of the character
            The name of the character
            A column of buttons that set the stocks remaining at the end of the match
        """

        def __init__(self, master, tag, smash_gui):
            super().__init__(master)
            self.character_gui = None
            self.tag = tag
            self.smash_gui = smash_gui
            self.stock_group = SelectionButtonGroup()
            self.image_panel = tk.Label(self)
            self.character_label = tk.Label(self)
            self.image_panel.grid(column=0, row=0, sticky='news')

            self.stock_frame = tk.Frame(self)

            # Create an array of buttons within a range that sets the remaining stocks for this player
            for i in range(0, 4):
                stock_button = self.stock_group.SelectionButton(self.stock_frame, self.stock_group, value=i)
                stock_button.configure(text=str(i), relief='flat', command=lambda i=i: self.set_stock(i))
                stock_button.grid(row=i, column=0, sticky='news')
                self.stock_frame.grid_rowconfigure(i, weight=1, uniform="y")

            # Set the default number of stocks to 0
            self.stock_group.set(0)

            self.stock_frame.grid(column=2, row=0, sticky='news')
            self.character_label.grid(column=1, row=0, sticky='news')
            self.grid_rowconfigure(0, weight=1)
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=1)

        def select_character(self, character):
            """
            Populates the image and name associated with the selected character into the frames widgets
            :param character:
            :return:
            """
            self.character_gui = character
            self.image_panel.configure(image=self.character_gui.img)
            self.character_label.configure(text=self.character_gui.character.display_name)
            self.image_panel.grid(column=0, row=0, sticky='news')

        def clear(self):
            """
            Removes the image and name of the character. Keeps the selected stock value
            :return:
            """
            self.character_gui = None
            self.image_panel.configure(image='')
            self.character_label.configure(text='')
            self.image_panel.grid_forget()

        def set_color(self, color):
            """
            Sets the color theme for the frane and it's children
            :param color:
            :return:
            """
            self.configure(bg=color)
            for child in self.winfo_children():
                child.configure(bg=color)

            for child in self.stock_frame.winfo_children():
                child.set_colors(abg='black', afg=color, bg=color, fg='black')
                child.configure(bg=color)
            self.stock_group.update()

        def set_stock(self, num):
            """
            Updates the selected stock display
            Tells the smash gui that a stock value has been selected
            :param num:
            :return:
            """
            self.stock_group.set(num)
            self.smash_gui.set_stock(self.tag, num)

    class StageButton:
        def __init__(self, master, stage, smash_gui):
            self.master = master
            self.stage = stage
            self.smash_gui = smash_gui

            self.image_frame = ImageTk.PhotoImage(
                Image.open(stage_image_folder + "/" + self.stage.image).resize((177, 100)))
            self._create_on_state()
            self._create_off_state()

            for child in master.winfo_children():
                child.bind("<Button-1>", lambda e: self._set_stage(e))

        def _create_on_state(self):
            self.on_frame = tk.Frame(self.master, bg=colors.SMASH_DARK, highlightthickness=4,
                                     highlightbackground=colors.SMASH_DARK)
            image = tk.Label(self.on_frame, image=self.image_frame)
            image.image = self.image_frame
            name = tk.Label(self.on_frame, text=self.stage.display_name)
            name.pack(expand='yes', fill='x', anchor='s')
            image.pack(expand='yes', fill='both')
            for child in self.on_frame.winfo_children():
                child.bind("<Button-1>", lambda e: self._set_stage(e))

        def _create_off_state(self):
            self.off_frame = tk.Frame(self.master)
            image = tk.Label(self.off_frame, image=self.image_frame)
            image.image = self.image_frame
            name = tk.Label(self.off_frame, text=self.stage.display_name)
            name.pack(expand='yes', fill='x', anchor='s')
            image.pack(expand='yes', fill='both')

            for child in self.off_frame.winfo_children():
                child.bind("<Button-1>", lambda e: self._set_stage(e))

        def _set_stage(self, event):
            self.smash_gui.set_stage(self.stage.name)

    def _populate_interface(self):
        """
        Creates all containers the are slaved to the root of Smash Gui
        Calls methods to populate each of these containers
        """

        # Character Frame
        self.character_frame = tk.Frame(self)
        self.character_canvas = tk.Canvas(self.character_frame)
        self.character_canvas.pack(side='left', fill='both', expand='yes')
        self._populate_character_frame()

        # Stage Frame
        self.stage_frame = tk.Frame(self)
        self._populate_stage_frame()

        # Overview Frame
        self.overview_frame = tk.Frame(self, bg='red', height=400)
        self._populate_overview_frame()

        # Game Player Frame
        self.game_player_frame = tk.Frame(self)
        self._populate_game_player_frame()

        # Game History Frame
        self.game_log_frame = tk.Frame(self)
        self._populate_game_log_frame()

        self.game_player_frame.grid(row=0, column=0, sticky='news')
        self.character_frame.grid(row=1, column=0, sticky='news')
        self.stage_frame.grid(row=2, column=0, sticky='news')
        self.overview_frame.grid(row=3, column=0, sticky='news')
        self.game_log_frame.grid(row=0, column=1, rowspan=4, sticky='news')

        self.grid_rowconfigure(0, weight=5)
        self.grid_rowconfigure(1, weight=80)
        self.grid_rowconfigure(2, weight=15)
        self.grid_rowconfigure(3, weight=15)
        self.grid_columnconfigure(0, weight=1)

    def _populate_character_frame(self):
        """
        Populates the character frame.
        Creates the icon frame and adds scrolling function with canvas
        """
        self.recommended_cols = 10

        # Create the frame that lives inside of the character canvas
        self.character_icon_frame = tk.Frame(self.character_canvas)
        self.character_icon_frame.pack(fill='both', expand='yes')
        self.character_icon_frame.bind("<Configure>",
                                       lambda e: self.character_canvas.configure(
                                           scrollregion=self.character_canvas.bbox("all")
                                       )
                                       )

        # Create Scrollbar and attach it to canvas
        self.character_icon_scroll = tk.Scrollbar(self.character_frame)
        self.character_icon_scroll.configure(command=self.character_canvas.yview)
        self.character_icon_scroll.pack(side="right", fill='y')

        # Configure canvas to house/display inner frame correctly.
        # Configure canvas to work with scrollbar
        self.character_canvas.create_window((0, 0), window=self.character_icon_frame, anchor="nw")
        self.character_canvas.configure(yscrollcommand=self.character_icon_scroll.set)
        self.character_canvas.bind("<Configure>", self._configure_grid_params)
        self.character_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.character_guis = []
        characters_data = characters.character_data()

        # From all the characters, create a CharacterGui object for each one
        for character in characters_data.values():
            gui = CharacterGui(character, self.character_icon_frame, self)
            self.character_guis.append(gui)

        # Start off by having all guis able to be displayed
        self.displayable_character_guis = self.character_guis

        # Default sorting value
        self._sort_character_gui(SmashGui.PlacementSorter())

    def _on_mousewheel(self, event):
        """
        Given a mouse wheel event, scroll the canvas acccordingly
        :param event:
        :return:
        """
        self.character_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _configure_grid_params(self, event):
        """
        Method determines the recommended number of columns for the character grid
        This value is based on the individual width of each character and the overall width of the canvas
        Triggered on window resize event
        If the calculated number of columns isnt equal to the current one, reconfigure grid to calculated number
        :param event:
        :return:
        """
        gui_width = self.character_guis[0].winfo_width()
        current_cols = self.character_icon_frame.grid_size()[0]
        canvas_width = event.width
        self.recommended_cols = int(canvas_width / gui_width)

        if self.recommended_cols != current_cols:
            print("Updating character columns to " + str(self.recommended_cols))
            self._replace_character_guis()

    def _replace_character_guis(self):
        """
        When refreshing character guis
        Used for searching, sorting, reconfiguring grid size
        :return:
        """
        print("Replacing all character guis")
        # Remove ALL character guis from frame
        for gui in self.character_guis:
            gui.grid_forget()

        # Add the displayable guis back
        for c, gui in enumerate(self.displayable_character_guis):
            row = int(c / self.recommended_cols)
            col = int(c % self.recommended_cols)

            gui.grid(column=col, row=row)
            # self.character_icon_frame.grid_columnconfigure(col, weight=1)

    def _sort_character_gui(self, sorting_comparator=None):
        """
        Sorts the character grid by the sorting_comparator passed in
        :param sorting_comparator: Abstract class that contains compare method.
        :return:
        """
        if sorting_comparator is None:
            sorting_comparator = self.current_sorting_comparator
        rev = bool(self.sort_reverse_bit.get())
        print("Sorting characters by: " + sorting_comparator.tag + " " + str(rev))

        self.displayable_character_guis = sorted(self.displayable_character_guis, key=sorting_comparator.compare,
                                                 reverse=rev)

        self._replace_character_guis()
        self.sort_group.set(sorting_comparator.tag)
        self.sort_mode = sorting_comparator.tag
        self.current_sorting_comparator = sorting_comparator

    def _search_character_gui(self, expr=''):
        """
        Updates the list of character guis that should be displayed based on the search term provided
        :param expr:
        :return:
        """
        # If nothing is specified. Display all
        if expr == '':
            self.displayable_character_guis = self.character_guis
        else:
            print("Search for characters with %s" % expr)
            pattern = re.escape(expr)
            self.displayable_character_guis = []
            for character_gui in self.character_guis:
                if re.search(pattern, character_gui.character.name, re.I):
                    self.displayable_character_guis.append(character_gui)

        self._replace_character_guis()

        # Return true for validate command
        return True

    # Comparator class that will sort character gui by name when passed into sorted method
    class NameSorter:
        tag = 'name'

        @staticmethod
        def compare(character_gui):
            return character_gui.character.name

    # Comparator class that will sort character gui by placement when passed into sorted method
    class PlacementSorter:
        tag = 'place'

        @staticmethod
        def compare(character_gui):
            return character_gui.character.placement

    # Comparator class that will sort character gui by game when passed into sorted method
    class GameSorter:
        tag = 'game'

        @staticmethod
        def compare(character_gui):
            return character_gui.character.game

    def _populate_stage_frame(self):
        self.stage_group = SelectionButtonGroup()
        stage_order = ['battlefield', 'final_destination', 'small_battlefield', 'other']
        stage_dict = stages.Stage.get_stages(stage_json)

        for stage_tag in stage_order:
            selection_gui = SelectionButtonGroup.SelectionFrame(self.stage_frame, self.stage_group, value=stage_tag)
            stage_gui = SmashGui.StageButton(selection_gui, stage_dict[stage_tag], self)
            selection_gui.set_on_display(stage_gui.on_frame)
            selection_gui.set_off_display(stage_gui.off_frame)
            selection_gui.pack(side='left', expand='yes', fill='both')

        self.set_stage("final_destination")

    def _populate_overview_frame(self):
        """
        Tells game handler to create all player selection guis within overview frame
        Then creates Save button
        :return:
        """

        self.character_overview_frame = tk.Frame(self.overview_frame)
        self.game_handler.populate_overview_frame(self.character_overview_frame)
        self.character_overview_frame.grid(column=0, row=0, sticky='news')

        self.save_game_button = tk.Button(self.overview_frame, text="Save", bg="#66ff66", fg="white", state="disabled",
                                          command=self.save_game)
        self.save_game_button.grid(column=1, row=0, sticky='news')

        self.overview_frame.grid_columnconfigure(0, weight=5)
        self.overview_frame.grid_columnconfigure(1, weight=1)
        self.overview_frame.grid_rowconfigure(0, weight=1)

    def _populate_game_player_frame(self):
        self._populate_player_frame()
        self._populate_search_frame()
        self._populate_sort_frame()
        self._populate_game_selection_frame()

        self.game_player_frame.grid_rowconfigure(0, weight=1)

    def _update_overview_frame(self):
        """
        Sets the state of the save button if the game is or isnt ready to be saved
        :return:
        """
        if self.game_handler.ready_to_save():
            self.save_game_button.configure(state="normal")
        else:
            self.save_game_button.configure(state="disabled")

    def _populate_player_frame(self):
        """
        Creates the player frame
        Tells game handler to create the player indicators.
        :return:
        """
        self.player_frame = tk.Frame(self.game_player_frame)
        self.game_handler.populate_player_frame()
        self.player_frame.grid(column=3, row=0, sticky='w')
        self.game_player_frame.grid_columnconfigure(3, weight=1)

    def _populate_search_frame(self):
        """
        Creates search bar configures it to run command with every key press
        :return:
        """
        self.search_frame = tk.Frame(self.game_player_frame)
        vcmd = self.register(self._search_character_gui)
        self.search_bar = tk.Entry(self.search_frame, vcmd=(vcmd, '%P'), validate='key')
        self.search_bar.pack(fill='both', expand='yes')
        self.search_frame.grid(column=1, row=0, sticky='ew')
        self.game_player_frame.grid_columnconfigure(1, weight=1)

    def _populate_sort_frame(self):
        """
        Creates buttons that will initiate the sort functions to sort the character guis
        Creates a checkbutton that will reverse the order of the sort
        :return:
        """
        self.sort_frame = tk.Frame(self.game_player_frame)
        name_sort_button = SelectionButtonGroup.SelectionButton(self.sort_frame, self.sort_group, value="name")
        name_sort_button.configure(command=lambda sorter=SmashGui.NameSorter: self._sort_character_gui(sorter),
                                   text="Name", relief='solid')
        placement_sort_button = SelectionButtonGroup.SelectionButton(self.sort_frame, self.sort_group, value="place")
        placement_sort_button.configure(
            command=lambda sorter=SmashGui.PlacementSorter: self._sort_character_gui(sorter),
            text="Orig", relief='solid')
        game_sort_button = SelectionButtonGroup.SelectionButton(self.sort_frame, self.sort_group, value="game")
        game_sort_button.configure(command=lambda sorter=SmashGui.GameSorter: self._sort_character_gui(sorter),
                                   text="Game", relief='solid')

        name_sort_button.pack(side='left', expand='yes', fill='both')
        placement_sort_button.pack(side='left', expand='yes', fill='both')
        game_sort_button.pack(side='left', expand='yes', fill='both')

        self.reverse_sort_button = tk.Checkbutton(self.sort_frame, text="Reverse", variable=self.sort_reverse_bit)
        self.reverse_sort_button.configure(command=self._sort_character_gui)
        self.reverse_sort_button.pack(side='left', expand='yes', fill='both')
        self.sort_frame.grid(column=2, row=0, sticky='news')

    def _populate_game_selection_frame(self):
        """
        Creates buttons that allow user to switch between game modes.
        Can switch between:
            sp
            mp
            ffa
        :return:
        """
        self.game_selection_group = SelectionButtonGroup()

        self.game_selection_frame = tk.Frame(self.game_player_frame)
        self.single_player_button = SelectionButtonGroup.SelectionButton(self.game_selection_frame,
                                                                         self.game_selection_group, value="sp")
        self.single_player_button.configure(command=lambda: self.change_game_mode("sp"))
        self.single_player_button.configure(text="1v1", relief='solid')
        self.multi_player_button = SelectionButtonGroup.SelectionButton(self.game_selection_frame,
                                                                        self.game_selection_group, value="mp")
        self.multi_player_button.configure(command=lambda: self.change_game_mode("mp"))
        self.multi_player_button.configure(text="2v2", relief='solid')
        self.free_for_all_button = SelectionButtonGroup.SelectionButton(self.game_selection_frame,
                                                                        self.game_selection_group, value="ffa")
        self.free_for_all_button.configure(command=lambda: self.change_game_mode("ffa"))
        self.free_for_all_button.configure(text="FFA", relief='solid')

        for button in self.game_selection_group.button_list:
            button.pack(side='left', fill='both')

        self.game_selection_frame.grid(column=0, row=0, sticky='news')
        self.game_player_frame.grid_columnconfigure(0, weight=1)

    def _populate_game_log_frame(self):
        """
        Creates the list of previous games player
        :return:
        """
        self.game_history_box = tk.Listbox(self.game_log_frame)
        self.game_history_box.pack(fill='both', expand='yes')
        self._update_game_history()

    def _update_game_history(self):
        """
        Reads the entire game history from the game_log
        Updates the game history display with these games
        :return:
        """
        new_game_history = game.Game.load_all_games_sorted(game_log, True)
        self.game_history_box.delete(0, len(self.game_history) - 1)
        for new_game in new_game_history:
            self.game_history_box.insert(self.game_history_box.size(), new_game)

        self.game_history = new_game_history

    def change_game_mode(self, mode):
        """
        Swaps between the game modes.
        Creates a new GameHandler
        Then destroys affected widgets and repopulates them
        :param mode:
        :return:
        """
        if mode == "sp" and self.game_mode != "sp":
            self.game_handler = SmashGui.SinglePlayerHandler(self)
            self.game_selection_group.set("sp")
        if mode == "mp" and self.game_mode != "mp":
            self.game_handler = SmashGui.MultiPlayerHandler(self)
            self.game_selection_group.set("mp")
        if mode == "ffa" and self.game_mode != "ffa":
            self.game_handler = SmashGui.FreeForAllHandler(self)
            self.game_selection_group.set("ffa")
        self.character_overview_frame.destroy()
        self.player_frame.destroy()

        [gui.deselect_character("all") for gui in self.character_guis]

        self._populate_overview_frame()
        self._populate_player_frame()

    def clear(self):
        """
        Clears all selections. Sets the game mode to itself.
        Then method destroys and resets everything. Then repoulates same gamemode
        :return:
        """
        self.change_game_mode(self.game_selection_group.get())

    def save_game(self):
        """
        Received from save game button. Initiates game handler save.
        Then clears the selections so that gui is ready for next use
        Updates game history. Basically just adds this new game to the list
        :return:
        """
        self.game_handler.save_game()
        self.clear()
        self._update_game_history()

    def set_stock(self, tag, num):
        self.game_handler.set_stock(tag, num)
        self._update_overview_frame()

    def set_stage(self, stage):
        print("SmashGui: set_stage: Setting stage to: " + str(stage))
        self.game_handler.set_stage(stage)
        self.stage_group.set(stage)

    def select_character(self, character_gui):
        self.game_handler.select_character(character_gui)
        self._update_overview_frame()


class CharacterGui(tk.Frame):
    """
    Class creates the character widgets that players can click to select their characters
    Contains the character image and name
    Visually tracks which player has selected the characted
    """

    def __init__(self, character, parent, smash_gui):
        super().__init__(parent)

        margins = 15  # %

        self.banner_dict = {}
        self.banner_height = 20

        self.smash_gui = smash_gui
        self.character = character

        # Image configuration
        self.img = self.character_icon()
        self.image_panel = tk.Label(self, image=self.img)
        self.image_panel.pack(padx=margins, pady=[margins, 0], fill='both', expand='yes')

        # Name configuration
        self.name_label = tk.Label(self, text=character.display_name)
        self.name_label.pack(padx=margins, pady=[0, 0], fill='both', expand='yes')

        # Player Indicator configurtion
        self.banner_frame = tk.Frame(self, height=20)
        self.banner_frame.pack(fill='both', expand='yes', padx=margins, pady=[0, margins])

        self.bind("<Button-1>", self._initiate_selection)
        self.image_panel.bind("<Button-1>", self._initiate_selection)

    def _initiate_selection(self, event):
        """
        Sends processing up to smash gui. tells it which character was selected
        :param event:
        :return:
        """
        self.smash_gui.select_character(self)

    def select_character(self, tag, color):
        """
        Comes from smash_gui game handler
        Responsible for changing appearance of gui when selected
        """
        print("Adding " + str(color) + " banner to " + str(self.character))
        banner = tk.Frame(self.banner_frame, bg=color, height=self.banner_height)
        banner.pack(side='left', expand='yes', fill='x')
        self.banner_dict[tag] = banner

    def deselect_character(self, tag):
        """
        Responsible for changing appearance of gui when deselected
        """
        if tag == "all":
            for v in self.banner_dict.values():
                v.destroy()
            self.banner_dict = {}
        else:
            if tag in self.banner_dict:
                self.banner_dict.pop(tag).destroy()

    def character_icon(self):
        return ImageTk.PhotoImage(Image.open(character_image_folder + "/" + self.character.image))


class SelectionButtonGroup:
    """
    This class is basiccally a radio button class.  But they look like buttons instead of radio buttons
    """

    def __init__(self):
        self.selected_index = 0
        self.button_list = []

    def set(self, value):
        for c, button in enumerate(self.button_list):
            if value == button.value:
                button.set_selected_state()
                self.selected_index = c
            else:
                button.set_non_selected_state()

    def get(self):
        return self.button_list[self.selected_index].value

    def add(self, new_button, index=-1):
        if index < 0:
            index = len(self.button_list)
        for button in self.button_list:
            if button.value == new_button.value:
                raise ValueError('Value already in group: ' + str(button.value))
        self.button_list.insert(index, new_button)

        if index <= self.selected_index:
            self.selected_index += 1

    def update(self):
        for c, button in enumerate(self.button_list):
            if c == self.selected_index:
                button.set_selected_state()
            else:
                button.set_non_selected_state()

    class SelectionFrame(tk.Frame):

        def __init__(self, master, selection_group, value=None):
            super().__init__(master, bg='green')
            self.value = value
            self.on_display = None
            self.off_display = None

            selection_group.add(self)

        def set_on_display(self, on_display):
            self.on_display = on_display

        def set_off_display(self, off_display):
            self.off_display = off_display

        def set_selected_state(self):
            self.off_display.pack_forget()
            self.on_display.pack(expand='yes', fill='both')

        def set_non_selected_state(self):
            self.on_display.pack_forget()
            self.off_display.pack(expand='yes', fill='both')

    class SelectionButton(tk.Button):
        def __init__(self, parent, button_group, value=None, abg='black', afg='white', bg='white', fg='black',
                     index=-1):
            super().__init__(parent)
            self.value = value
            self.abg = abg
            self.afg = afg
            self.bg = bg
            self.fg = fg

            if index >= 0:
                button_group.add(self, index=index)
            else:
                button_group.add(self)

        def set_colors(self, abg='black', afg='white', bg='white', fg='black'):
            self.abg = abg
            self.afg = afg
            self.bg = bg
            self.fg = fg

        def set_non_selected_state(self):
            self.configure(bg=self.bg)
            self.configure(fg=self.fg)

        def set_selected_state(self):
            self.configure(bg=self.abg)
            self.configure(fg=self.afg)


if __name__ == "__main__":
    root = SmashApp()
    app = SmashGui(master=root)
    app.mainloop()
