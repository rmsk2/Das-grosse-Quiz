################################################################################
# Copyright 2016 Martin Grap
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

## @package dgqcontrol Contains a class that implements a program that allows the game master to control the display of "Das grosse Quiz"
#   
# \file dgqcontrol.py
# \brief Contains a class that implements a program that allows the game master to control the display of "Das grosse Quiz"

import pickle
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf
import playingfield
import questions

ERR_OK = 0
ERR_ERROR = 42

APP_NAME = 'Das große Quiz'
## \brief A string. Used as team name when no team gave a correct answer
TEAM_NONE = 'Niemand'
AUTOSAVE_FILE_NAME = 'autosave.dgq'

## \brief A string. A CSS (!!!) which is used to color the button backgrounds
CSS_IDIOTIE = """
.team_a_button{
    background: #c00000;
}

.team_b_button{
    background: #00c000;
}

.team_c_button{
    background: #5159E8;
}

.team_none_button{
    background: #e00d81;
}

.question_button{
    background: #f7ff14;
}
"""

## \brief A string. Describes the menu structure.
MENU_INFO = """
<ui>
  <menubar name='menu_bar'>
    <menu action='general'>
      <menuitem action='reconnect'/>
      <menuitem action='clear'/>      
      <menuitem action='save'/>
      <menuitem action='load'/>
      <separator />
      <menuitem action='quit'/>      
    </menu>
    <menu action='information'>
      <menuitem action='info'/>
      <menuitem action='about'/>      
    </menu>
  </menubar>
</ui>
"""

## \brief This class implements the program dgqcontrol.py which serves as a kind of remote control for the display server.
#         It also automatically counts and displays the points earned by each team and supports the game master in different
#         other ways.
#
class DasGrosseQuiz:
    ## \brief Constructor.
    #
    #  \param [p_field] An object of type playingfield.PlayingField. It holds the current state of the game.
    #
    def __init__(self, p_field):
        ## \brief Holds the playing field, i.e. the game's state
        self._playing_field = p_field
        ## \brief Holds the main window
        self._window = Gtk.Window() 
        ## \brief Grid that holds the buttons which can be used to "ask" a question
        self._questions_grid = {}
        
        ## \brief Maps the team names to the color names in the CSS
        self._team_colors = {}
        self._team_colors[self._playing_field.current_teams[0]] = 'team_a_button'
        self._team_colors[self._playing_field.current_teams[1]] = 'team_b_button'        
        self._team_colors[self._playing_field.current_teams[2]] = 'team_c_button'
        # TEAM_NONE answers all questions which have not been answered by any "real" team
        self._team_colors[TEAM_NONE] = 'team_none_button' 
        # Counts the seconds the game has been running
        self._game_time = 0                       
        
        self._window.connect('destroy', Gtk.main_quit)
        self._window.set_title(APP_NAME)
        
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(CSS_IDIOTIE.encode())
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        self._background_box = Gtk.VBox(False, 0)
        
        # Create menus
        action_group = Gtk.ActionGroup("dgq_action_group")
        self.add_menu_actions(action_group)
        ui_manager = self.create_ui_manager()
        ui_manager.insert_action_group(action_group)
        menu_bar = ui_manager.get_widget("/menu_bar")      
        self._background_box.pack_start(menu_bar, False, False, 0)          
        
        # Create button grids
        ablauf_frame = Gtk.Frame(label='Spielablauf')
        self._background_box.pack_start(ablauf_frame, False, True, 0)

        fragen_frame = Gtk.Frame(label = 'Fragen')
        self._background_box.pack_start(fragen_frame, True, True, 0)
        
        # Fill Questions button grid
        button_grid = Gtk.Grid()
        fragen_frame.add(button_grid)
        grid_col_count = 0
        button_grid.set_column_homogeneous(True)
        button_grid.set_row_homogeneous(True)
        
        # Create question buttons
        for i in self._playing_field.current_categories:
            self._questions_grid[i] = {}
            button_grid.attach(Gtk.Label(i), grid_col_count, 0, 1, 1)
            grid_row_count = 1
            for j in [20, 40, 60, 80, 100]:
                self._questions_grid[i][j] = Gtk.Button(label = str(j))
                button_grid.attach(self._questions_grid[i][j], grid_col_count, grid_row_count, 1, 1)
                self._questions_grid[i][j].connect('clicked', self.ask_question, {'category':i, 'value':j})
                grid_row_count += 1

            grid_col_count += 1
        
        # Fill game control frame        
        ablauf_box = Gtk.VBox()
        ablauf_frame.add(ablauf_box)
        self._current_question = Gtk.Label('Aktuelle Frage: Keine')
        ablauf_box.pack_start(self._current_question, False, True, 0)

        self._current_result = Gtk.Label('Aktueller Spielstand:')
        ablauf_box.pack_start(self._current_result, False, True, 0)

        
        # Fill game control button grid
        ablauf_grid = Gtk.Grid()
        ablauf_grid.set_column_homogeneous(True)
        ablauf_grid.set_row_homogeneous(True)
        
        self._intro_button = Gtk.Button(label = 'Intro')
        ablauf_grid.attach(self._intro_button, 0, 0, 1, 1)
        self._intro_button.connect('clicked', self.show_intro)
        
        self._show_field_button = Gtk.Button(label = 'Spielfeld')
        ablauf_grid.attach(self._show_field_button, 1, 0, 1, 1)
        self._show_field_button.connect('clicked', self.show_field)

        self._final_result_button = Gtk.Button(label = 'Endstand')
        ablauf_grid.attach(self._final_result_button, 2, 0, 1, 1)
        self._final_result_button.connect('clicked', self.show_result)        

        self._thanks_button = Gtk.Button(label = 'Danksagung')
        ablauf_grid.attach(self._thanks_button, 3, 0, 1, 1)
        self._thanks_button.connect('clicked', self.show_thanks)        
        
        self._team_a_button = Gtk.Button(label = 'Team ' + self._playing_field.current_teams[0])
        ablauf_grid.attach(self._team_a_button, 0, 1, 1, 1)
        self._team_a_button.connect('clicked', self.answer_question, self._playing_field.current_teams[0]) 
        self._team_a_button.get_style_context().add_class(self._team_colors[self._playing_field.current_teams[0]])       

        self._team_b_button = Gtk.Button(label = 'Team ' + self._playing_field.current_teams[1])
        ablauf_grid.attach(self._team_b_button, 1, 1, 1, 1)
        self._team_b_button.connect('clicked', self.answer_question, self._playing_field.current_teams[1])        
        self._team_b_button.get_style_context().add_class(self._team_colors[self._playing_field.current_teams[1]])        

        self._team_c_button = Gtk.Button(label = 'Team ' + self._playing_field.current_teams[2])
        ablauf_grid.attach(self._team_c_button, 2, 1, 1, 1)
        self._team_c_button.connect('clicked', self.answer_question, self._playing_field.current_teams[2])        
        self._team_c_button.get_style_context().add_class(self._team_colors[self._playing_field.current_teams[2]])         

        self._none_button = Gtk.Button(label = 'Niemand')
        ablauf_grid.attach(self._none_button, 3, 1, 1, 1)
        self._none_button.connect('clicked', self.answer_question, TEAM_NONE)                
        self._none_button.get_style_context().add_class(self._team_colors[TEAM_NONE])              
        
        self._team_a_wrong_button = Gtk.Button(label = 'Falsch Team ' + self._playing_field.current_teams[0])
        ablauf_grid.attach(self._team_a_wrong_button, 0, 2, 1, 1)
        self._team_a_wrong_button.connect('clicked', self.wrong_answer_question, self._playing_field.current_teams[0]) 
        self._team_a_wrong_button.get_style_context().add_class(self._team_colors[self._playing_field.current_teams[0]])       

        self._team_b_wrong_button = Gtk.Button(label = 'Falsch Team ' + self._playing_field.current_teams[1])
        ablauf_grid.attach(self._team_b_wrong_button, 1, 2, 1, 1)
        self._team_b_wrong_button.connect('clicked', self.wrong_answer_question, self._playing_field.current_teams[1])        
        self._team_b_wrong_button.get_style_context().add_class(self._team_colors[self._playing_field.current_teams[1]])        

        self._team_c_wrong_button = Gtk.Button(label = 'Falsch Team ' + self._playing_field.current_teams[2])
        ablauf_grid.attach(self._team_c_wrong_button, 2, 2, 1, 1)
        self._team_c_wrong_button.connect('clicked', self.wrong_answer_question, self._playing_field.current_teams[2])        
        self._team_c_wrong_button.get_style_context().add_class(self._team_colors[self._playing_field.current_teams[2]])    
        
        self._free_question_button = Gtk.Button(label = 'Frage freigeben')
        ablauf_grid.attach(self._free_question_button, 3, 2, 1, 1)
        self._free_question_button.connect('clicked', self.clear_question)             
        
        ablauf_box.pack_start(ablauf_grid, False, True, 0)
        
        self._window.add(self._background_box)
        
        self._window.set_size_request(800, 600)
        self._window.show_all() 
        self.update_state()
        
        self._timer_id = GLib.timeout_add_seconds(1, self.countdown) 
        self.show_intro(None)      

    ## \brief This method returns a UIManager object which is used to construct the menu bar.
    #
    #  \returns An object of type Gtk.UIManager.
    #    
    def create_ui_manager(self):
        uimanager = Gtk.UIManager()        
        uimanager.add_ui_from_string(MENU_INFO)
        
        accelgroup = uimanager.get_accel_group()
        self._window.add_accel_group(accelgroup)
        return uimanager

    ## \brief This method adds all menu entries to the menu action group.
    #
    #  \param [action_group] An object of type Gtk.ActionGroup. This is the action group to which the menu 
    #         entries are added.
    #
    #  \returns Nothing.
    #    
    def add_menu_actions(self, action_group):
        action_group.add_actions([
            ('general', None, 'Allgemein'),
            ('reconnect', None, 'Erneut verbinden', None, None, self.on_reconnect),
            ('clear', None, 'Spiel zurücksetzen', None, None, self.on_clear),            
            ('save', None, 'Spielstand speichern ...', None, None, self.on_save),
            ('load', None, 'Spielstand laden ...', None, None, self.on_load),
            ('quit', Gtk.STOCK_QUIT, 'Beenden', None, None, self.on_quit),
            ('information', None, 'Information'),
            ('info', None, 'Informationen ...', None, None, self.on_info),
            ('about', None, 'About ...', None, None, self.on_about)
        ])

    ## \brief This method is the callback which is used to display the about dialog.
    #
    #  \param [widget] An object of type Gtk.Widget. This is the widget from which the event originated.
    #
    #  \returns Nothing.
    #        
    def on_about(self, widget):
        dialog = Gtk.AboutDialog(parent=self._window)
        dialog.set_title(APP_NAME)
        dialog.set_program_name('Das große Quiz')
        dialog.set_version('0.99 eternal Beta')
        dialog.set_authors(['Martin Grap'])
        logo = GdkPixbuf.Pixbuf.new_from_file('dgq.png')
        dialog.set_logo(logo)
        dialog.run()
        dialog.destroy()                

    ## \brief This method is the callback which is used to display the info dialog.
    #
    #  \param [widget] An object of type Gtk.Widget. This is the widget from which the event originated.
    #
    #  \returns Nothing.
    #                
    def on_info(self, widget):
        time_elapsed = self._game_time
        questions_answered = self._playing_field.num_questions_answered()
        spq = 'Ich teile nicht durch 0'
        
        if questions_answered != 0:
            spq = '{} Sec/Frage'.format(time_elapsed // questions_answered)
        
        # Display information about duration, number of answered questions and seconds per answered question
        self.info_message('Verbunden mit: {}\nSpiel läuft seit {} Minuten\n{} Fragen beantwortet\n{}'.format(self._playing_field.server_info, time_elapsed // 60, questions_answered, spq))

    ## \brief This method is the callback which is called by the "each second" timer. When a question is active. i.e. is
    #         currently being asked, this callback causes the time left in seconds of the displayed question to be decremented.
    #
    #  \returns A boolean. True means that the timer should be started again.
    #                    
    def countdown(self):                
        self._playing_field.decrement_question_time()
        self._game_time += 1
        
        return True

    ## \brief This method is is used as a callback when the user has requested to close the program.
    #
    #  \returns Nothing.
    #                    
    def on_quit(self, widget):
        Gtk.main_quit()

    ## \brief This method is the callback which is called when the user selected the 'Spiel zurücksetzen' menu entry.
    #
    #  \param [widget] An object of type Gtk.Widget. This is the menu item from which the event originated.
    #
    #  \returns Nothing.
    #                
    def on_clear(self, widget):
        dialog = Gtk.MessageDialog(self._window, 0, Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO, 'Wirklich?')
        dialog.set_title(APP_NAME)
        question_result = dialog.run()
        dialog.destroy()
        
        if question_result == Gtk.ResponseType.YES:    
            self._playing_field.clear()
            self.update_state()
            if self._playing_field.save_state(AUTOSAVE_FILE_NAME) != ERR_OK:
                self.error_message('Sicherung fehlgeschlagen')        

    ## \brief This method is the callback which is called when the user selected the 'Erneut verbinden' menu entry.
    #
    #  \param [widget] An object of type Gtk.Widget. This is the widget from which the event originated.
    #
    #  \returns Nothing.
    #                
    def on_reconnect(self, widget):
        self._playing_field.raspi.disconnect()
        
        if self._playing_field.raspi.connect() == ERR_OK:
            self.info_message('Verbindung wiederhergestellt')
        else:
            self.error_message('Verbindung konnte nicht wiederhergestellt werden')

    ## \brief This method is the callback which is called when the user selected the 'Spielstand laden' menu entry.
    #
    #  \param [widget] An object of type Gtk.Widget. This is the widget from which the event originated.
    #
    #  \returns Nothing.
    #                
    def on_load(self, widget):
        dialog = Gtk.FileChooserDialog("Datei mit Spielstand wählen", self._window, Gtk.FileChooserAction.OPEN, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        
        response = dialog.run()
        file_name = dialog.get_filename()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK:
            if self._playing_field.load_state(file_name) == ERR_OK:
                self.update_state()
                self.info_message("Spielstand erfolgreich geladen")
            else:
                self.error_message("Spielstand konne nicht geladen werden")


    ## \brief This method is the callback which is called when the user selected the 'Spielstand speichern' menu entry.
    #
    #  \param [widget] An object of type Gtk.Widget. This is the widget from which the event originated.
    #
    #  \returns Nothing.
    #                    
    def on_save(self, widget):
        dialog = Gtk.FileChooserDialog("Datei zum Speichern auswählen", self._window, Gtk.FileChooserAction.SAVE, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        
        response = dialog.run()
        file_name = dialog.get_filename()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK:
            if self._playing_field.save_state(file_name) == ERR_OK:
                self.info_message("Spielstand erfolgreich gespeichert")
            else:
                self.error_message("Spielstand konne nicht gespeichert werden")

    ## \brief A helper method which is used to display a message dialog with an informational message.
    #
    #  \param [message_text] A string. It has to contain the message displayed to the user.
    #
    #  \returns Nothing.
    #                    
    def info_message(self, message_text):
        dialog = Gtk.MessageDialog(self._window, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.CLOSE, message_text)
        dialog.set_title(APP_NAME)
        dialog.run()
        dialog.destroy()

    ## \brief A helper method which is used to display a message dialog with an error message.
    #
    #  \param [message_text] A string. It has to contain the message displayed to the user.
    #
    #  \returns Nothing.
    #                    
    def error_message(self, message_text):
        dialog = Gtk.MessageDialog(self._window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, message_text)
        dialog.set_title(APP_NAME)
        dialog.run()
        dialog.destroy()

    ## \brief This method is the callback which is called when the user clicked the 'Intro' button. It sends a message to the display
    #         server which makes it display the intro message.
    #
    #  \param [button] An object of type Gtk.Button. This is the button which was clicked.
    #
    #  \returns Nothing.
    #                    
    def show_intro(self, button):
        if self._playing_field.show_intro() != ERR_OK:
            self.error_message("Kann Intro nicht anzeigen")
        self.update_state()

    ## \brief This method is the callback which is called when the user clicked the 'Danksagung' button. It makes the "Thank you message"
    #         appear on the display server's screen.
    #
    #  \param [button] An object of type Gtk.Button. This is the button which was clicked.
    #
    #  \returns Nothing.
    #                    
    def show_thanks(self, button):
        if self._playing_field.show_thanks() != ERR_OK:
            self.error_message("Kann Danksagung nicht anzeigen")
        self.update_state()

    ## \brief This method is the callback which is called when the user clicked the 'Spielfeld' button. It makes the playing field
    #         appear on the display server's screen.
    #
    #  \param [button] An object of type Gtk.Button. This is the button which was clicked.
    #
    #  \returns Nothing.
    #                    
    def show_field(self, button):
        if self._playing_field.show() != ERR_OK:
            self.error_message("Kann Spielfeld nicht anzeigen")
        self.update_state()

    ## \brief This method is the callback which is called when the user clicked the 'Endstand' button. It makes a message which
    #         describes the game's result appear on the display server's screen.
    #
    #  \param [button] An object of type Gtk.Button. This is the button which was clicked.
    #
    #  \returns Nothing.
    #                    
    def show_result(self, button):
        if self._playing_field.show_result() != ERR_OK:
            self.error_message("Kann Endstand nicht anzeigen")
        self.update_state()

    ## \brief This method removes any of the the style classes defined in CSS_IDIOTIE from a given Gtk.Button object. It makes the
    #         corresponding button appear in the default grey background again.
    #
    #  \param [button_object] An object of type Gtk.Button. The styles of this button are cleaned up.
    #
    #  \returns Nothing.
    #                    
    def clear_css_classes(self, button_object):
        all_classes = button_object.get_style_context().list_classes()
        my_classes = list(self._team_colors.values())
        my_classes.append('question_button')
        
        for i in all_classes:
            if i in my_classes:
                button_object.get_style_context().remove_class(i)        

    ## \brief This method updates all GUI elements to reflect the current game state. It colors the button of the currently asked question in yellow,
    #         colors the other buttons in the color which belongs to the team that answered the question, updates the labels of the question buttons
    #         with information about which team has answered this question incorrectly and so on.
    #
    #  \returns Nothing.
    #                    
    def update_state(self):
        # Update current question label
        if self._playing_field.current_question == None:
            self._current_question.set_label('Aktuelle Frage: Keine')
        else:
            self._current_question.set_label('Aktuelle Frage: {} {}'.format(self._playing_field.current_question.category, self._playing_field.current_question.value))
        
        # Calculate current result and update correponding label accordingly
        current_result = self._playing_field.calc_result()
        teams = list(current_result.keys())
        teams.sort()
        text = 'Aktueller Spielstand:' 
        
        for i in teams:
            text += ' Team {}:{}'.format(i, current_result[i])
        
        self._current_result.set_label(text)
        
        # Color question buttons
        for i in self._playing_field.current_categories:
            for j in [20, 40, 60, 80, 100]:                
                self.clear_css_classes(self._questions_grid[i][j])                
                who_answered_question = self._playing_field.question_answered_by(i, j)
                who_answered_question_wrong = self._playing_field.question_answered_wrong_by(i, j)
                
                # Color any question button the question of which has been answered
                if who_answered_question != None:
                    self._questions_grid[i][j].get_style_context().add_class(self._team_colors[who_answered_question])
                                
                if len(who_answered_question_wrong) == 0:
                    # No wrong answers
                    self._questions_grid[i][j].set_label(str(j))
                else:
                    # Update question button labels to specifiy information about the teams which gave a wrong answer
                    label_appendix = ''
                    
                    # Construct new button label
                    for k in who_answered_question_wrong:
                        label_appendix += ' ' + k
                                            
                    label_appendix = label_appendix.strip()
                    label_appendix = ' (' + label_appendix + ')'
                    self._questions_grid[i][j].set_label(str(j) + label_appendix)
        
        q = self._playing_field.current_question
        # Make background of button for the current question appear in yellow
        if q != None:
            self._questions_grid[q.category][q.value].get_style_context().add_class('question_button')

    ## \brief This method is used as callback that is called when the user clicked on any button which indicates that a team
    #         answered the current question correctly or that all teams gave a wrong answer. In that case TEAM_NONE answered
    #         the question "correctly".
    #
    #  \param [button] An object of type Gtk.Button. This is the button from which has been clicked.
    #
    #  \param [who_answered] A string. It specifies the name of the team which gave an answer.
    #    
    #  \returns Nothing.
    #                        
    def answer_question(self, button, who_answered):
        if self._playing_field.answer_current_question(who_answered) != ERR_OK:
            self.error_message('Kann Spielfeld nicht anzeigen')
        self.update_state()
        if self._playing_field.save_state(AUTOSAVE_FILE_NAME) != ERR_OK:
            self.error_message('Sicherung fehlgeschlagen')

    ## \brief This method is used as callback that is called when the user clicked on the "Frage freigeben" Button. It deletes
    #         all information about correct or wrong answers in relation to to the current question.
    #
    #  \param [button] An object of type Gtk.Button. This is the button which has been clicked.
    #    
    #  \returns Nothing.
    #                        
    def clear_question(self, button):
        if self._playing_field.clear_current_question() != ERR_OK:
            self.error_message('Kann Spielfeld nicht anzeigen')
        self.update_state()
        if self._playing_field.save_state(AUTOSAVE_FILE_NAME) != ERR_OK:
            self.error_message('Sicherung fehlgeschlagen')

    ## \brief This method is used as callback that is called when the user clicked on any button which indicates that a team
    #         answered the current question question incorrectly.
    #
    #  \param [button] An object of type Gtk.Button. This is the button which has been clicked.
    #
    #  \param [who_answered] A string. It specifies the name of the team which gave a wrong answer.
    #    
    #  \returns Nothing.
    #
    def wrong_answer_question(self, button, who_answered):
        self._playing_field.wrong_answer_current_question(who_answered)
        self.update_state()
        if self._playing_field.save_state(AUTOSAVE_FILE_NAME) != ERR_OK:
            self.error_message('Sicherung fehlgeschlagen')

    ## \brief This method is used as callback that is called when the user wants the audience to start answering a question by clicking
    #         on a question button. The clicked question then also becomes the current question and is displayed on the display server's
    #         screen.
    #
    #  \param [button] An object of type Gtk.Button. This is the question button which has been clicked.
    #
    #  \param [question_object] A dictionary with the keys "category" and "value". "category" is mapped to a string which names the
    #         question's category. "value" is mapped to an integer which gives the value of the question.
    #    
    #  \returns Nothing.
    #    
    def ask_question(self, button, question_object):
        if self._playing_field.ask_question(question_object['category'], question_object['value']) != ERR_OK:
            self.error_message('Kann Frage nicht anzeigen')
        self.update_state()        

    ## \brief The program's main method which enters the Gtk message loop
    #
    #  \returns Nothing.
    #                                
    def main(self):
        Gtk.main()
    
if __name__ == "__main__":
    repo = questions.QuestionRepository()
    
    # Load questions
    if not repo.load('questions.xml'):
        print('Kann Fragendatei nicht laden')
    else:
        # Make playing field
        p = playingfield.PlayingField(repo)
        if p.raspi.connect() == ERR_OK:
            try:
                # Make game object
                game = DasGrosseQuiz(p) 
                # Enter message loop   
                game.main()        
            finally:
                # Save game state
                p.save_state('laststate.dgq')
                # Stop display server
                p.raspi.make_stop()
        else:
            print("Kann nicht mit Displayserver verbinden")


