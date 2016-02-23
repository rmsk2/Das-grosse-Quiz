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

## @package displayserver This service allows to display the playing field, the questions and generic messages.
#           
# \file displayserver.py
# \brief Service that lets a client display the playing field and some messages.
#

import select
import socket
import tlvobject
import time
import pickle
import pygame

ERR_OK = 0
ERR_ERROR = 42

## \brief TCP port on which the service is listening
PORT = 4321
## \brief X size of the window which is used to draw the playing field
PLAYING_FIELD_X = 1024
## \brief X size of the window which is used to draw the playing field
PLAYING_FIELD_Y = 768

## \brief Size of the font (in pixels) which is used when displaying a question
QUESTION_FONT_SIZE = (PLAYING_FIELD_X * 5) // 100
## \brief Size of the font (in pixels) which is used when displaying the intro message
INTRO_FONT_SIZE = (PLAYING_FIELD_X * 875) // 10000
## \brief Size of the font (in pixels) which is used when displaying the final result
RESULT_FONT_SIZE = INTRO_FONT_SIZE
## \brief Size of the font (in pixels) which is used to render the values on the playing field
PLAYFIELD_FONT_SIZE = (PLAYING_FIELD_X * 5625) // 100000
## \brief Size of the font (in pixels) which is used when displaying the "Thank You" message
THANKS_FONT_SIZE = (PLAYING_FIELD_X * 75) // 1000

## \brief This class knows how to draw the playing field and how to render textual messages using
#         the pygame library.
#
#  This class knows six commands.
#  1. stop: Does not draw anything but changes self._stop_flag to true.
#  2. showqestion: Draws a textual message representing a question.
#  3. showintro: Draws an intro message into the background surface.
#  4. danksagung: Displays a "Thank you" message.
#  5. showresult: Displays the end result.
#  6. showplayingfield: Displays the playing field from which the players can choose questions.
#
class Processor:
    ## \brief Constructor. 
    #
    #  \param [background] Is an object of type pygame.Surface. It is expected that its size is equal
    #         to (PLAYING_FIELD_X, PLAYING_FIELD_Y). All drawing this class does is relative to this Surface.
    #
    #  The default tag is TAG_NULL and therefore there are no contens bytes.
    #    
    def __init__(self, background):
        ## \brief A boolean. Is set to true after the stop command has been received
        self._stop_flag = False
        ## \brief An object of type pygame.Surface. Represents the pygame window in which all drawing happens
        self._background = background
        
    ## \brief This property returns the current value of the stop flag. 
    #
    #  \returns A boolean. If true is returned the stop command has been received.
    #    
    @property
    def stop(self):
        return self._stop_flag    

    ## \brief This method parses the data received from the client, selects the handling method and executes it.
    #
    #  \param [tlv_param] An object of type tlvobject.TlvEntry. Contains the data sent by the client.
    #
    #  \returns A tlvobject.TlvEntry object which contains an integer value. The integer value represents the
    #           error code sent back to the client. A return value of 0 signifies success.
    #        
    def process(self, tlv_param):
        result = tlvobject.TlvEntry().to_int(ERR_OK)
        
        try:                        
            params = tlv_param.tlv_convert()
            out_text = ''

            if len(params) == 0:
                result.to_int(ERR_ERROR)
            elif params[0] == 'stop':                
                self._stop_flag = True
            elif params[0] == 'showquestion':
                self.show_question(params[1], params[2])            
            elif params[0] == 'showintro':            
                self.show_intro()
            elif params[0] == 'danksagung':            
                self.show_thanks()
            elif params[0] == 'showresult':
                self.show_result(pickle.loads(params[1]))
            elif params[0] == 'showplayingfield':
                self.show_playing_field(pickle.loads(params[1]))
            else:
                result.to_int(ERR_ERROR)
            
        except:
            result.to_int(ERR_ERROR)
        
        return result

    ## \brief The playing field consists of six rows and five columns. This method can be used to draw
    #         each one of these 30 cells.
    #
    #  \param [logical_x] An integer. It contains the logical x coordinate (0-5) of the cell which is to be drawn.
    #
    #  \param [logical_y] An integer. It contains the logical y coordinate (0-4) of the cell which is to be drawn.
    #
    #  \param [label] A string. It has to contain the text that is shown in the cell's center.
    #
    #  \param [font_size] An integer. Specifies the font size in pixels which is used to draw the value in the cell.
    #
    #  \param [num_rows] An integer. It contains the number of rows of the playing field (normally 6).
    #
    #  \param [num_columns] An integer. It contains the number of columns of the playing field (normally 5).
    #
    #  \param [has_border] A boolean. Has to be true if the cell is to be drawn with a border. Row 0 contains the
    #         column headers. These are normally drawn wthout a border.
    #
    #  \returns Nothing.
    #        
    def draw_cell(self, logical_x, logical_y, label, font_size, num_rows, num_columns, has_border = False):
        font = pygame.font.Font(None, font_size)
        bg_rect = self._background.get_rect()

        cell_width = bg_rect.width // num_columns
        cell_height = bg_rect.height // num_rows
        cell_x = logical_x * cell_width
        cell_y = logical_y * cell_height
        cell_center_x = cell_x + (cell_width // 2)
        cell_center_y = cell_y + (cell_height // 2)

        if label != '':
            text = font.render(label, 1, (255, 255, 255))
            textpos = text.get_rect()
            textpos.centerx = cell_center_x
            textpos.centery = cell_center_y
            self._background.blit(text, textpos)
                
        if has_border:
            pygame.draw.rect(self._background, (255, 255, 255), (cell_x, cell_y, cell_width, cell_height), 1)

    ## \brief This method draws the whole playing field.
    #
    #  \param [playing_field] A dictionary of dictionaries. It contains the current state of the game.
    #
    #  The outmost dictionary has the category names as its keys. The values of each of these categories is another
    #  dictionary that has the keys 20, 40, 60, 80, 100. The value of these keys is a third dictionary that has the
    #  keys 'answeredby' and 'wronganswersby'. The vlaue for the 'answeredby' key is either None (when the question has
    #  not been answered yet) or a string which specifies the name of the team that answered the question. The key
    #  'wronganswersby' has a set() as its value which contains the names of the team(s) that have given a wrong answer
    #  to the question.
    #
    #  \returns Nothing.
    #                
    def show_playing_field(self, playing_field):
        # Background is black
        self._background.fill((0, 0, 0))
        col_headers = list(playing_field.keys())
        col_headers.sort()
                
        current_col = 0
        
        for i in col_headers:
            # Draw column headers with category names
            self.draw_cell(current_col, 0, i, PLAYFIELD_FONT_SIZE, 6, 5, False)
            current_row = 1

            # Iterate over the questions in each catgory
            for j in [20, 40, 60, 80, 100]:
                l = ''
                # If the question has not been answered yet print its value in the center of the cell
                if playing_field[i][j]['answeredby'] == None:
                    l = str(j)
                self.draw_cell(current_col, current_row, l, PLAYFIELD_FONT_SIZE, 6, 5, True)                
                current_row += 1
                
            current_col += 1

    ## \brief This method displays a message which gives information about the final result of the game.
    #
    #  \param [result_dict] A dictionary. It contains the the result of the game.
    #
    #  The dictionary result_dict maps a string key to an int value. Each key is the name of a team and its value
    #  is the number of points earned by the corresponding team.
    #
    #  \returns Nothing.
    #                
    def show_result(self, result_dict):
        lines = ['ENDSTAND', '']
        help = []

        # transform dictionary into a list of the form [(team1, points_team1), (team2, points_team2), ... ]
        for i in result_dict:
            help.append((i, result_dict[i]))

        # Sort the help list according to the number of points in descending order
        help.sort(key=lambda x: x[1], reverse=True)

        # Prepare text for each team
        for i in help:
            lines.append('Team {}: {}'.format(i[0], i[1]))

        # Print text        
        self.print_centered(lines, RESULT_FONT_SIZE)        

    ## \brief This method displays a message on the screen in such a way that it is horizontally and vertically centered.
    #
    #  \param [line] A list of strings. Each string is printed as a separate line.
    #
    #  \param [font_size] An integer. It specifies the font size in pixels which is used to display the message.
    #
    #  \returns Nothing.
    #                
    def print_centered(self, lines, font_size):
        # Calculate the height of a single line
        line_sep = (font_size // 2) + (font_size // 3)
        # Calculate the y-position of the first line
        y_offset = -((len(lines) // 2) * line_sep)

        # Background is black
        self._background.fill((0, 0, 0))        
        font = pygame.font.Font(None, font_size)

        # Draw lines
        for i in lines:
            # Text is in white
            text = font.render(i, 1, (255, 255, 255))
            textpos = text.get_rect()
            textpos.centerx = self._background.get_rect().centerx 
            textpos.centery = self._background.get_rect().centery + y_offset
            self._background.blit(text, textpos)
            y_offset += line_sep

    ## \brief This method displays a predefined intro message on the screen
    #
    #  \returns Nothing.
    #                        
    def show_intro(self):
        self.print_centered(['DAS', 'GROSSE', 'QUIZ'], INTRO_FONT_SIZE)

    ## \brief This method displays a predefined "Thank you" message on the screen
    #
    #  \returns Nothing.
    #                        
    def show_thanks(self):
        self.print_centered(['Wir hoffen ihr hattet etwas Spaß', 'DANKE an alle, die mitgeholfen haben'], THANKS_FONT_SIZE)

    ## \brief This method displays a question on the screen.
    #
    #  \param [question] A string. If the string contains '#' characters each of them is interpreted as a line break.
    #
    #  \param [time] An integer. It specifies the time in seconds which is left for answering the question. A negative
    #                value ha to be used to indicate that not time value should be displayed.
    #    
    #  \returns Nothing.
    #                                
    def show_question(self, question, time):
        font_size = QUESTION_FONT_SIZE
        time_font_size = (font_size * 3) // 2
        question = question.split('#')
        self.print_centered(question, font_size)

        if time >= 0:        
            font = pygame.font.Font(None, time_font_size)
            text = font.render('{:03d}'.format(time), 1, (255, 255, 255))
            textpos = text.get_rect()
            textpos.centerx = self._background.get_rect().centerx 
            textpos.centery = time_font_size
            self._background.blit(text, textpos)

## \brief The main function of this program.
#
def main():
    # Create server socket
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    
    serversocket.bind(('', PORT))
    serversocket.listen(5)

    # Initialize pygame stuff
    pygame.init()
    size = width, height = PLAYING_FIELD_X, PLAYING_FIELD_Y
    black = 0, 0, 0    
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('Das große Quiz')
    screen.fill(black)            
    pygame.display.flip()

    background = pygame.Surface(screen.get_size())
    background = background.convert()    
    
    proc = Processor(background)    
    force_stop = False

    # Wait for client to connect    
    (client_socket, address) = serversocket.accept()
    # Main loop
    while not (proc.stop or force_stop):
        # Process pygame events
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    force_stop = True
                    continue

            # Test if a client has sent a message                    
            sel_res = select.select([client_socket], [], [], 0)

            # Yes! Handle it.
            if len(sel_res[0]) > 0:
                tlvobject.TlvStream.transact_server(client_socket, proc)

            # Make processing result visible
            screen.blit(background, (0, 0))
            pygame.display.flip()

        except:
            force_stop = True
            print("Bummer!")

    # Shutdown. The sleep is intended to make sure that the client closes the connection first. This
    # prevents the server socket to enter the TIME_WAIT state. If that happens the port is blocked and the server
    # can not be restarted until the server socket is finally disposed by the operating system.
    time.sleep(0.3)
    client_socket.shutdown(socket.SHUT_RDWR)
    client_socket.close()
    serversocket.shutdown(socket.SHUT_RDWR)
    serversocket.close()

if __name__ == "__main__":    
    main()
