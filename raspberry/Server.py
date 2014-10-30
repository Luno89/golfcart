# needs requests module from http://docs.python-requests.org/en/latest/
import requests
import io
import time
from log import *
import GPS
import Arduino

_URL = 'http://157.182.184.52/~agc/command.php'
_Pings = 0
_TimeLastPing = 0
_Sequence = 0

# session used to communicate with server
_Session = requests.session()

def open(url) :
    global _URL
    global _Session
    global _Pings
    global _TimeLastPing
    _URL = url
    _Session = requests.session()
    _Pings = 0
    _TimeLastPing = 0
    _Sequence = 0

    Ping(sequence_only=True)
    
def _formatUrl():
    formattedUrl = _URL + '?speed='+str(Arduino.Speed) + '&steer='+str(Arduino.Steer)
    if Arduino.Direction :
        formattedUrl += '&direction=BACK'
    else :
        formattedUrl += '&direction=FORWARD'
        
    if Arduino.Brake :
        formattedUrl += '&brake=ON'
    else :
        formattedUrl += '&brake=OFF'

    if Arduino.Steer_Mode :
        formattedUrl += '&steermode=ACTIVE'
    else :
        formattedUrl += '&steermode=PASSIVE'

    if GPS.Connected :
        formattedUrl += '&lat=' + str(GPS.Latitude)
        formattedUrl += '&long=' + str(GPS.Longitude)
        formattedUrl += '&GPSDir=' + str(GPS.Direction)
        formattedUrl += '&GPSSpeed=' + str(GPS.Speed)
    return formattedUrl

def _is_int(val) :
    try :
        intval = int(val)
        return True
    except :
        return False


def Ping(sequence_only=False):
    global _Sequence
    global _Pings
    global _TimeLastPing

    # don't ping too often or the server gets crabby
    curTime = time.time()
    if curTime - _TimeLastPing < 0.5 :
        return
    
    _Pings += 1
    
    try :
        command = _Session.get(_formatUrl(), timeout=1.0).text
        writeLog(LOG_PING_SERVER, 'Poll: ' + str(command.split()))
    except requests.HTTPError as err :
        command = str(_Sequence) + ' HTTP_error'
        writeLog(LOG_ERROR, 'HTTP Error: ' + str(err))
    except requests.Timeout as err :
        command = str(_Sequence) + ' HTTP_timeout'
        writeLog(LOG_ERROR, 'HTTP timeout: ' + str(err))

    commandParts = command.split()

    if (len(commandParts) != 2) or (not _is_int(commandParts[0])) :
        writeLog(LOG_ERROR, 'Invalid seq ' + str(commandParts))
        return
    curTime = time.time()
    if _TimeLastPing != 0 and curTime > _TimeLastPing + 1.5 :
        writeLog(LOG_SEQ_ERROR, 'Last ping at ' + time.ctime(_TimeLastPing))
	_TimeLastPing = curTime
    
    new_seq = int(commandParts[0])
    if sequence_only :
        _Sequence = new_seq
        return
    
    if new_seq > _Sequence:
        if new_seq != _Sequence + 1 :
            writeLog(LOG_SEQ_ERROR, 'Missed sequence number: ' + str(_Sequence) + ' ' + str(new_seq))
	    _Sequence = new_seq
	    writeLog(LOG_NEW_COMMAND, 'New command: ' + str(commandParts))
	    Arduino.Execute(commandParts)
	    Arduino.Get_Status()
	elif commandParts[1] == 'reset' :
	    _cmd_reset()

def _cmd_reset() :
    global _Sequence
    writeLog(LOG_DETAILS, 'reset Sequence number')
    _Sequence = 0

