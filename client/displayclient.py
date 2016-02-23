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

## @package displayclient Contains classes that implement a client for the displayserver of "Das grosse Quiz"
#   
# \file displayclient.py
# \brief Contains classes that implement a client for the displayserver of "Das grosse Quiz".
#
import socket
import pickle
import tlvobject

ERR_OK = 0
ERR_ERROR = 42

## \brief A class that implements a client for the displayserver of "Das grosse Quiz"
#
#  It implements the client side of the necessary protocol using TLV encoded data structures.
#
class SignClient:
    ## \brief Constructor. 
    #
    #  \param [host] A string. It has to conain the host name or the "dotted decimal" ip address of the machine which
    #         hosts the displayserver.
    #
    #  \param [port] An it. It has to hold the port on which the displayserver is listening.
    #    
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._is_connected = False
        self._sock = None

    ## \brief This method connects to the displayserver. The client stays connected as long as the game runs.
    #
    #  \returns An int. A return value of 0 signifies a successfull connect.
    #        
    def connect(self):
        result = ERR_OK
        try:
            if not self._is_connected:
                self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._sock.connect((self._host, self._port))
                self._is_connected = True
        except:
            result = ERR_ERROR
            if self._sock != None:
                self._sock.close()
                self._sock = None
                self._is_connected = False 
        
        return result           

    ## \brief This method disconnects the client from the displayserver.
    #
    #  \returns Nothing.
    #            
    def disconnect(self):
        try:
            if self._is_connected:
                self._sock.shutdown(socket.SHUT_RDWR)
                self._sock.close()
                self._sock = None                
        finally:
            self._is_connected = False

    ## \brief This method allows to send a command to the client.
    #
    #  \param [command] A string. It has to hold the command that is to be sent to the server.
    #        
    #  \param [parameters] A list of tlvobject.TlvEntry objects. These objects specify the parameters of the command.
    #        
    #  \returns An int. A return value of 0 signifies successfull execution of the command.
    #            
    def make_call(self, command, parameters = []):
        result = ERR_OK
        parm_sequence = [tlvobject.TlvEntry().to_string(command)] 
        parm_sequence = parm_sequence + parameters
         
        try:
            param = tlvobject.TlvEntry().to_sequence(parm_sequence)
            result = tlvobject.TlvStream.transact_client(self._sock, param)
        except:
            result = ERR_ERROR
        
        return result

    ## \brief This method allows to send a command to the client. The command has one parameter which is created by
    #         "pickling" a python object.
    #
    #  \param [command] A string. It has to hold the command that is to be sent to the server.
    #        
    #  \param [param_object] An object that can be pickled using pickle.dumps().
    #        
    #  \returns An int. A return value of 0 signifies successfull execution of the command.
    #                
    def make_pickle_call(self, command, param_object):
        param_sequence = [tlvobject.TlvEntry().to_byte_array(pickle.dumps(param_object))]
        return self.make_call(command, param_sequence)

    ## \brief This method sends the stop command to the server and subsequently disconnects the client.
    #
    #  \returns Nothing.
    #                
    def make_stop(self):
        result = self.make_call('stop')
        self.disconnect()
        return result

    ## \brief This method instucts the displayserver to show a question on the screen.
    #
    #  \param [question] A string. If the string contains '#' characters each of them is interpreted as a line break.
    #
    #  \param [time] An integer. It specifies the time in seconds which is left for answering the question.
    #    
    #  \returns An int. A return value of 0 signifies successfull execution of the command.
    #       
    def show_question(self, question, time):
        param_sequence = [tlvobject.TlvEntry().to_string(question), tlvobject.TlvEntry().to_int(time)]
        return self.make_call('showquestion', param_sequence)

    ## \brief This method instructs the displayserver to show an intro message.
    #
    #  \returns An int. A return value of 0 signifies successfull execution of the command.
    #       
    def show_intro(self):
        param_sequence = []
        return self.make_call('showintro', param_sequence)

    ## \brief This method instructs the displayserver to show a "Thank you" message.
    #
    #  \returns An int. A return value of 0 signifies successfull execution of the command.
    #
    def show_thanks(self):
        param_sequence = []
        return self.make_call('danksagung', param_sequence)

    ## \brief This method instucts the displayserver to display a message that describes the final result of the game.
    #
    #  The data structure required by this method is returned by PlayingField.calc_result().
    #
    #  \param [current_result] A dictionary. It maps the team name (a string) to the number of points this team has earned.
    #
    #  \returns An int. A return value of 0 signifies successfull execution of the command.
    #       
    def show_result(self, current_result):
        return self.make_pickle_call('showresult', current_result)

    ## \brief This method instucts the displayserver to display the playing field of the game.
    #
    #  The data structure required by this method can be obtained through the property PlayingField.playing_field.
    #
    #  \param [field_data] A dictionary. It maps the category names and question values (20, 40, 60, ...) to a result dictionary.
    #
    #  \returns An int. A return value of 0 signifies successfull execution of the command.
    #       
    def show_playing_field(self, field_data):
        return self.make_pickle_call('showplayingfield', field_data)

