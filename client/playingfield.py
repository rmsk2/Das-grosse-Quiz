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

## @package playingfield Contains a class that implements the playing field of "Das grosse Quiz"
#   
# \file playingfield.py
# \brief Contains a class that implements the playing field of "Das grosse Quiz".

import pickle
import questions
import displayclient

ERR_OK = 0
ERR_ERROR = 42

## \brief An excpetion class that is used for constructing exception objects in this module. 
#
class PlayingFieldException(Exception):
    ## \brief An excpetion class that is used for constructing exception objects in this module. 
    #
    #  \param [error_message] Is a string. It has to contain an error message that is to be conveyed to 
    #         receiver of the corresponding exception.
    #
    def __init__(self, error_message):
        Exception.__init__(self, 'PlayingField error:' + error_message)

## \brief This class implements the playing field of "Das grosse Quiz".
#
#  The central data structure is a multi level dictionary which is referenced through the self._field member.
#  The outmost dictionary has the category names as its keys. The values of each of these categories is another
#  dictionary that has the keys 20, 40, 60, 80, 100. The value of these keys is a third dictionary that has the
#  keys 'answeredby' and 'wronganswersby'. The value for the 'answeredby' key is either None (when the question has
#  not been answered yet) or a string which specifies the name of the team that answered the question. The key
#  'wronganswersby' has a set() as its value which contains the names of the team(s) that have given a wrong answer
#  to the question.
#
class PlayingField:
    ## \brief Constructor.
    #
    #  \param [question_repo] An object of type questions.QuestionRepository which holds information about questions, teams
    #         and network configuration.
    #
    def __init__(self, question_repo):
        ## \brief An object of type questions.QuestionRepository.
        self._repo = question_repo
        ## \brief A list of strings. Each list element denotes a category.
        self._categories = self._repo.categories
        ## \brief A multi level dictionary that holds the playing field information.
        self._field = {}
        ## \brief A multi level dictionary that holds the question for each cell in the playing field.
        self._questions = {}
        ## \brief A list of strings. Each list element denotes a name of a team.        
        self._teams = self._repo.teams
        ## \brief An object of type displayclient.SignClient which is used to talk to the displayserver.
        self._sign_client = displayclient.SignClient(self._repo.config['host'], self._repo.config['port'])
        ## \brief An object of type questions.Question. It holds the question which is currently displayed by the displayserver.
        self._current_question = None
        
        field_column = {20:None, 40:None, 60:None, 80:None, 100:None}
        
        # Initialize the self._field and self._questions dictionaries
        for i in self._categories:
            self._field[i] = field_column.copy()
            self._questions[i] = field_column.copy()
        
        # Retrieve all questions the the repository
        for i in self._categories:
            for j in [20, 40, 60, 80, 100]:
                self._questions[i][j] = self._repo.get_question(i, j)
                self._field[i][j] = {'answeredby':None, 'wronganswersby':set()}

    ## \brief Returns a reference to the playing field dictionary.
    #
    #  \returns A dictionary as described in the class documentation.
    #    
    @property
    def playing_field(self):
        return self._field

    ## \brief Returns a reference to displayserver client object which is in use in this PlayingField instance.
    #
    #  \returns An object of type displayclient.SignClient.
    #        
    @property
    def raspi(self):
        return self._sign_client

    ## \brief Returns a string describing the hostname and port which have been specified in the question repository that is used
    #         by this PlayingField instance.
    #
    #  \returns A string.
    #        
    @property
    def server_info(self):
        return '{}:{}'.format(self._repo.config['host'], self._repo.config['port'])

    ## \brief Returns a reference to the questions.Question object which represents the question currently displayed by the displaserver.
    #
    #  \returns An object of type questions.Question or None.
    #                
    @property
    def current_question(self):
        return self._current_question

    ## \brief This method allows to deserialize the current state of the playing field from a file.
    #
    #  \param [file_name] A string. Has to contain the name of the file which contains a serialized state.
    #
    #  \returns A boolean. A return value of True means that reconstructing the state was successfull.
    #                    
    def load_state(self, file_name):
        result = ERR_OK
        dumped_playing_field = None
        
        try:
            with open(file_name, 'rb') as f:
                dumped_playing_field = f.read()
            
            restored_playing_field = pickle.loads(dumped_playing_field)
            
            for i in self._categories:
                for j in [20, 40, 60, 80, 100]:
                    for t in restored_playing_field[i][j]['wronganswersby']:
                        if not (t in self.current_teams):
                           raise PlayingFieldException('Loaded state contains unknown team names')

           # NB: If restored_playing_field[i][j]['answeredby'] contains an unknown team name the question is regarded as 
           #     answered by noone.
            
            self._field = restored_playing_field
            self._current_question = None
        except:
            result = ERR_ERROR
        
        return result

    ## \brief This method allows to serialize the current state of the playing field into a file.
    #
    #  \param [file_name] A string. Has to contain the name of the file into which the serialized state should be stored.
    #
    #  \returns A boolean. A return value of True means that saving the state was successfull.
    #                        
    def save_state(self, file_name):
        result = ERR_OK
        
        try:
            dumped_playing_field = pickle.dumps(self._field)
            with open(file_name, 'wb') as f:
                f.write(dumped_playing_field)
        except:
            result = ERR_ERROR
        
        return result

    ## \brief This method clears the state of playing field, i.e. sets all cells to the default value which
    #         means that no question has been answered either right or wrong yet.
    #
    #  \returns Nothing.
    #                            
    def clear(self):
        for i in self._categories:
            for j in [20, 40, 60, 80, 100]:
                self._field[i][j] = {'answeredby':None, 'wronganswersby':set()}        

    ## \brief This method evaluates the current state of the playing field. It iterates over all cells and sums up the
    #         points earned by each team. A correct answer adds the value of the question to the team result. In case of
    #         a wrong answer the question value is substracted from the team result.
    #
    #  \returns A dictionary. It maps a string key to an int value. Each key is the name of a team and its value
    #           is the number of points earned by the corresponding team.
    #                                    
    def calc_result(self):
        result = {}
        
        for i in self._teams:
            result[i] = 0
        
        for i in self._categories:
            for j in [20, 40, 60, 80, 100]:
                
                if self._field[i][j]['answeredby'] in self._teams:
                    result[self._field[i][j]['answeredby']] += j
                
                for k in self._field[i][j]['wronganswersby']:
                    if k in self._teams:
                        result[k] -= j
        
        return result

    ## \brief This method evaluates the current state of the playing field. It iterates over all cells and counts the
    #         questions which have already been answered.
    #
    #  \returns An int.
    #                                    
    def num_questions_answered(self):
        result = 0
                
        for i in self._categories:
            for j in [20, 40, 60, 80, 100]:
                
                if self._field[i][j]['answeredby'] != None:
                    result += 1
        
        return result

    ## \brief Instructs the displayserver to display the intro message and resets the value of self._current_question to None.
    #
    #  \returns An int. A return value of 0 indicates a successfull execution.
    #                                        
    def show_intro(self):
        self._current_question = None
        return self._sign_client.show_intro()

    ## \brief Instructs the displayserver to display the "Thank you" message and resets the value of self._current_question to None.
    #
    #  \returns An int. A return value of 0 indicates a successfull execution.
    #                                        
    def show_thanks(self):
        self._current_question = None
        return self._sign_client.show_thanks()

    ## \brief Instructs the displayserver to display final result message and resets the value of self._current_question to None.
    #
    #  \returns An int. A return value of 0 indicates a successfull execution.
    #                                            
    def show_result(self):
        self._current_question = None
        res = self.calc_result()
        return self._sign_client.show_result(res)

    ## \brief Instructs the displayserver to display the playing field and resets the value of self._current_question to None.
    #
    #  \returns An int. A return value of 0 indicates a successfull execution.
    #                                                
    def show(self):
        self._current_question = None
        return self._sign_client.show_playing_field(self._field)

    ## \brief Records that a team has answered a question correctly. If the question has already been answered this method
    #         does nothing.
    #
    #  \param [category] A string. Denotes the category of the question that has been answered correctly.
    #
    #  \param [value] An int. Denotes the value of the question that has been answered correctly.
    #
    #  \param [who_answered] A string. Specifies the name of the team which has answered the question correctly.
    #
    #  \returns Nothing.
    #                                                    
    def answer_question(self, category, value, who_answered):
        if (self._field[category][value]['answeredby'] == None) and (who_answered not in self._field[category][value]['wronganswersby']):
            self._field[category][value]['answeredby'] = who_answered            
            self._current_question = None

    ## \brief Resets the state of a question to its default value (no correct and no wrong answers).
    #
    #  \param [category] A string. Denotes the category of the question that has been answered correctly.
    #
    #  \param [value] An int. Denotes the value of the question that has been answered correctly.
    #
    #  \returns Nothing.
    #                                                            
    def clear_question(self, category, value):
        self._field[category][value]['answeredby'] = None
        self._field[category][value]['wronganswersby'] = set()
        self._current_question = None

    ## \brief Records that a team has given a wrong answer to a question. If the question has already been answered this method
    #         does nothing.
    #
    #  \param [category] A string. Denotes the category of the question that has been answered wrongly.
    #
    #  \param [value] An int. Denotes the value of the question that has been answered wrongly.
    #
    #  \param [who_answered] A string. Specifies the name of the team which has answered the question wrongly.
    #
    #  \returns Nothing.
    #                                                    
    def wrong_answer_question(self, category, value, who_answered):
        if self._field[category][value]['answeredby'] == None:
            self._field[category][value]['wronganswersby'].add(who_answered)

    ## \brief Records that a team has answered the current question correctly. If the question has already been answered this method
    #         does nothing. Additionaly this method instructs the displayserver to show the playing field again. The current question
    #         is also reset to None.
    #
    #  \param [who_answered] A string. Specifies the name of the team which has answered the question correctly.
    #
    #  \returns An int. A value of 0 indicates that displaying the playing field was successfull.
    #                                                    
    def answer_current_question(self, who_answered):
        result = ERR_OK
        
        if self._current_question != None:
            c = self._current_question.category
            v = self._current_question.value
            if (self._field[c][v]['answeredby'] == None) and (who_answered not in self._field[c][v]['wronganswersby']):
                self.answer_question(c, v, who_answered)
                result = self.show()
            
        return result

    ## \brief Resets the state of the current question to its default value (no correct and no wrong answers). Additionaly this method instructs 
    #         the displayserver to show the playing field again. The current question is also reset to None.
    #
    #  \returns An int. A value of 0 indicates that displaying the playing field was successfull.
    #                                                    
    def clear_current_question(self):
        result = ERR_OK
        
        if self._current_question != None:
            self.clear_question(self._current_question.category, self._current_question.value)
            result = self.show()
            
        return result

    ## \brief Records that a team has answered the current question wrongly. If the question has already been answered this method
    #         does nothing.
    #
    #  \param [who_answered] A string. Specifies the name of the team which has given a wrong answer.
    #
    #  \returns Nothing.
    #                                                    
    def wrong_answer_current_question(self, who_answered):        
        if self._current_question != None:
            self.wrong_answer_question(self._current_question.category, self._current_question.value, who_answered)

    ## \brief Returns the category names in use in this PlayingField instance.
    #
    #  \returns A list of strings. The strings denote the category names and the list is sorted.
    #                                                    
    @property
    def current_categories(self):
        result = self._categories[:]
        result.sort()
        return result

    ## \brief Returns the names of the three teams names in use in this PlayingField instance.
    #
    #  \returns A list of strings. The strings denote the team names and the list is sorted.
    #                                                    
    @property
    def current_teams(self):
        result = self._teams[:]
        result.sort()
        return result

    ## \brief Returns the name of the team that has answered the specified question correctly.
    #
    #  \param [category] A string. Denotes the category of the question for which the answer information is to be retrieved.
    #
    #  \param [value] An int. Denotes the value of the question for which the answer information is to be retrieved.
    #
    #  \returns A string. The name of the team which has given a correct answer or None in case the question
    #           has not been answered yet.
    #        
    def question_answered_by(self, category, value):
        return self._field[category][value]['answeredby']

    ## \brief Returns the names of the teams that have given a wrong answer to the specified question.
    #
    #  \param [category] A string. Denotes the category of the question for which the answer information is to be retrieved.
    #
    #  \param [value] An int. Denotes the value of the question for which the answer information is to be retrieved.
    #
    #  \returns A set of strings. The set contains the names of the teams which have given a wrong answer.
    #        
    def question_answered_wrong_by(self, category, value):
        return self._field[category][value]['wronganswersby']

    ## \brief This method instructs the display server to show a certain question. This question then becomes the current question
    #         and the time value which specifies how many seconds remain to answer the question is set to its start value.
    #
    #  \param [category] A string. Denotes the category of the question which is to become the current question.
    #
    #  \param [value] An int. Denotes the value of the question which is to become the current question.
    #
    #  \returns An int. A value of 0 indicates that displaying the question was successfull.
    #                        
    def ask_question(self, category, value):
        question = self._questions[category][value]
        time = question.time_allowance
        
        if not question.show_time:
            time = -1
        
        self._current_question = question
        self._current_question.reset()
        
        return self._sign_client.show_question(question.text, time)        

    ## \brief This method decrements the number of seconds that remain to answer the current question and updates the display to
    #         reflect the changed timer value.
    #
    #  \returns An int. A value of 0 indicates that displaying the question was successfull.
    #                            
    def decrement_question_time(self):
        result = ERR_OK
        
        # Check if there is a valid current question, that its timer value is positive and that a time value should be displayed
        if (self._current_question != None) and (self._current_question.current_time > 0) and (self._current_question.show_time):
            self._current_question.current_time -= 1
    
            result = self._sign_client.show_question(self._current_question.text, self._current_question.current_time)
        
        return result

