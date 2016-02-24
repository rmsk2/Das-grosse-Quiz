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

## @package questions Contains classes that implement a repository of categories and questions for "Das grosse Quiz"
#   
# \file questions.py
# \brief Contains a class that parses the questions.xml files and extracts the team names, the questions and some
#        configuration information from that file.
#
import xmltodict

## \brief An excpetion class that is used for constructing exception objects in this module. 
#
class ParseException(Exception):
    ## \brief An excpetion class that is used for constructing exception objects in this module. 
    #
    #  \param [error_message] Is a string. It has to contain an error message that is to be conveyed to 
    #         receiver of the corresponding exception.
    #
    def __init__(self, error_message):
        Exception.__init__(self, 'XML consistency error:' + error_message)

## \brief A class which describes a question in the context of "Das grosse Quiz".
#
class Question:
    ## \brief Constructor.
    #
    #  \param [category] A string. It has to specify the name of the category of this question
    #
    #  \param [value] An int. It has to specify the questions value (20, 40, 60, 80, 100)
    #
    def __init__(self, category, value):
        ## \brief A string. Text of the questions
        self.text = 'Wie heißt die Hauptstadt\nvon Albanien?'
        ## \brief A boolean. If True a countdown timer is displayed along with the text.
        self.show_time = True
        ## \brief An int. It contains the number of seconds during which the question has to be answered.
        self.time_allowance = 60
        ## \brief An int. Contains the number od seconds which remain for answering the question.
        self.current_time = self.time_allowance
        ## \brief A string. Holds the question's category.
        self.category = category
        ## \brief An int. Holds the question's value in points.
        self.value = value

    ## \brief This method resets self._current_time to the start value.
    #
    #  \returns Nothing.
    #    
    def reset(self):
        self.current_time = self.time_allowance

## \brief This class parses an XML file containg the questions and additional configuration information.
#
class QuestionRepository:
    ## \brief Constructor.
    #
    def __init__(self):
        self._xml = None
        pass

    ## \brief This method loads an XML file, parses it and verifies that it contains the necessary information.
    #
    #  \param [file_name] A string. It has to specify the name file containg the question data.
    #
    #  \returns A boolean. True means that the question data has been successfully loaded.
    #    
    def load(self, file_name):
        result = True
        
        try:
            # Parse file
            with open(file_name, 'rb') as f:
                 self._xml = xmltodict.parse(f)
            
            # Check for information about teams. There have to be exactly three.
            if len(self.teams) != 3:
                raise ParseException('There have to be exactly three teams')

            # Verify that categories have been loaded successfully
            if self.categories == None:
                raise ParseException('Error determining categories')

            # There have to be exactly five categories
            if len(self.categories) != 5:
                raise ParseException('There have to be exactly five categories')
            
            # Check whether host name and port can be read from the XML file
            if self.config == None:
                raise ParseException('Configuration data wrong')
             
            # Verify that there is a question for all categories and values
            for i in self.categories:
                for j in [20, 40, 60, 80, 100]:
                    if self.get_question(i, j) == None:
                        raise ParseException('{} {}'.format(i, j))
        except:
            result = False
            self._xml = None
        
        return result

    ## \brief This method returns the question for the given category and value.
    #
    #  \param [category] A string. It has to specify the category of the question which is to be returned.
    #
    #  \param [value] An int. It has to specify the value in points of the question which is to be returned.
    #
    #  \returns An object of type Question or None. None is returned if the XML file does not contain a suitable question.
    #        
    def get_question(self, category, value):
        result = None
        questions_in_category = []
        
        try:
            for i in self._xml['grossesquiz']['questions']['qcategory']:
                if i['@name'] == category:
                    questions_in_category = i['question']
                    break
            
            for i in questions_in_category:
                if int(i['@value']) == value:
                    temp = Question(category, value)
                    temp.text = i['text']
                    temp.show_time = (i['@hastime'] == 'True')
                    temp.time_allowance = int(i['@timeallowance'])
                    temp.reset()
                    result = temp
                    break            
        except:
            result = None
        
        return result

    ## \brief Returns the categories defined in the XML file.
    #
    #  \returns A list of strings. It contains the names of all the categories defined in the XML file.
    #            
    @property    
    def categories(self):
        result = None
        
        try:
            result = []
            
            for i in self._xml['grossesquiz']['questions']['qcategory']:
                result.append(i['@name'])
        except:
            result = None
        
        return result

    ## \brief Returns the network configuration data defined in the XML file.
    #
    #  \returns A dictionary with the keys 'host' and 'port' or None in case of an error.
    #                
    @property
    def config(self):
        result = None
        
        try:
            result = {}
            result['host'] = self._xml['grossesquiz']['configuration']['displayserverhost']
            result['port'] = int(self._xml['grossesquiz']['configuration']['displayserverport'])
        except:
            result = None
        
        return result

    ## \brief Returns the names of the three teams defined in the XML file.
    #
    #  \returns A list of strings. It contains the names of the three teams defined in the XML file.
    #                
    @property    
    def teams(self):
        return self._xml['grossesquiz']['teams']['team'][:]    
