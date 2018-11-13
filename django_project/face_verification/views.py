import face_recognition
import cv2
from django.shortcuts import render
from face_verification.models import *
from smartcard.scard import *
import smartcard.util
import base64
import binascii
import io
import os
import numpy as np
from array import array
import string
from picamera.array import PiRGBArray
from picamera import PiCamera
import time

#from imutils.video import FPS

global nameCI
global surnameCI
global idNumberCI
global data 

def home(request):
    return render(request, 'face_verification/index.html')


def info(request):
    return render(request, 'face_verification/info.html')

def getData(request):
    return render(request, 'face_verification/info.html')

def camera(request):
    IMAGEPATH = './face_verification/KnownFaces/X.jpeg'
    #'/home/pi/Desktop/CI/knownFaces/X.jpeg'
    DATAPATH = "./face_verification/output.txt"
    #APDU commands------------------------------------------------------------
    SELECTIAS = [0x00, 0xA4, 0x04, 0x00, 0x0C, 0xA0, 0x00, 0x00, 0x00, 0x18, 0x40, 0x00, 0x00, 0x01, 0x63, 0x42, 0x00, 0x00]
    #biographic data
    SELECTDATA = [0x00, 0xA4, 0x00, 0x00, 0x02, 0x70, 0x02]
    GETRESPONSE_DATA = [0x00, 0xC0, 0x00, 0x00, 0x15] # Le=0x15 (fijo)
    READBINARY_DATA = [0x00, 0xB0, 0x00, 0x00] # FALTA Le (viene de comando anterior) CLA INS P1 P2 - Le 6c
    #image
    SELECTIMAGE = [0x00, 0xA4, 0x00, 0x00, 0x02, 0x70, 0x04]
    GETRESPONSE_IMAGE = [0x00, 0xC0, 0x00, 0x00, 0x15]
    READBINARY_IMAGE = [0x00, 0xB0, 0x00, 0x00, 0xFF]

    #info obtained
    BIO_INFO = ""
    IMAGE_SIZE = 0
    IMAGE=[]

    try:
        hresult, hcontext = SCardEstablishContext(SCARD_SCOPE_USER)
        if hresult != SCARD_S_SUCCESS:
            raise Exception('Failed to establish context : ' +
                SCardGetErrorMessage(hresult))
        print ('Context established!')

        try:
            hresult, readers = SCardListReaders(hcontext, [])
            if hresult != SCARD_S_SUCCESS:
                raise Exception('Failed to list readers: ' +
                    SCardGetErrorMessage(hresult))
            print ('PCSC Readers:', readers)

            if len(readers) < 1:
                raise Exception('No smart card readers')

            reader = readers[0]
            print ("Using reader:", reader)

            try:
                hresult, hcard, dwActiveProtocol = SCardConnect(hcontext, reader,
                    SCARD_SHARE_SHARED, SCARD_PROTOCOL_T0)
                if hresult != SCARD_S_SUCCESS:
                    raise Exception('Unable to connect: ' +
                        SCardGetErrorMessage(hresult))
                print ('Connected with active protocol', dwActiveProtocol)

                try:
                    hresultIas, responseIas = SCardTransmit(hcard, dwActiveProtocol, SELECTIAS)                
                    hresultData, responseData = SCardTransmit(hcard, dwActiveProtocol, SELECTDATA)
                    hresultGetResponse_Data, responseGetResponse_Data = SCardTransmit(hcard, dwActiveProtocol, GETRESPONSE_DATA)
                    READBINARY_DATA.append(responseGetResponse_Data[5])
                    hresultReadB_Data, responseReadB_Data = SCardTransmit(hcard, dwActiveProtocol, READBINARY_DATA)
                    
                    #image
                    hresultImage, responseImage = SCardTransmit(hcard, dwActiveProtocol, SELECTIMAGE)
                    hresultGetResponse_Image, responseGetResponse_Image = SCardTransmit(hcard, dwActiveProtocol, GETRESPONSE_IMAGE)
                
                    if hresultIas != SCARD_S_SUCCESS:
                        raise Exception('Failed to transmit: ' +
                            SCardGetErrorMessage(hresultIas))
                    
                    #biographic data
                    if hresultData != SCARD_S_SUCCESS:
                        raise Exception('Failed to transmit: ' +
                            SCardGetErrorMessage(hresultData))

                    if hresultGetResponse_Data != SCARD_S_SUCCESS:
                        raise Exception('Failed to transmit: ' +
                            SCardGetErrorMessage(hresultGetResponse_Data))
                    
                    if hresultReadB_Data != SCARD_S_SUCCESS:
                        raise Exception('Failed to transmit: ' +
                            SCardGetErrorMessage(hresultReadB_Data))
                    
                    #BIO_INFO = smartcard.util.toHexString(responseReadB_Data, smartcard.util.HEX) 
                    #BIO_INFO = bytes(responseReadB_Data).decode('utf16')
                    responseReadB_Data.pop(0)
                    responseReadB_Data.pop(0)
                    responseReadB_Data.pop(0)
                    BIO_INFO = smartcard.util.toASCIIString(responseReadB_Data)
                    
                                                 
                    printable = set(string.printable)
                    #BIO_INFO = filter(lambda x: x in printable, BIO_INFO)
                    BIO_STR = ''
                    for x in BIO_INFO:
                        if x in printable:
                            BIO_STR = BIO_STR + x
                        else:
                            BIO_STR = BIO_STR + ' '
                    BIO_STR = BIO_STR.replace('    ', ' ')
                    BIO_STR = str.split(BIO_STR, '   ')
                    OUTPUT_STR = BIO_STR[0]+'\n'+BIO_STR[1]+'\n'+BIO_STR[5]
                    #print OUTPUT_STR
                    
                    file = open(DATAPATH, "w")
                    file.write(OUTPUT_STR)
                    file.close()
    #*********************************************************************************                
                    #image data
                    if hresultImage != SCARD_S_SUCCESS:
                        raise Exception('Failed to transmit: ' +
                            SCardGetErrorMessage(hresultImage))
                    
                    if hresultGetResponse_Image != SCARD_S_SUCCESS:
                        raise Exception('Failed to transmit: ' +
                            SCardGetErrorMessage(hresultGetResponse_Image))
                    
                    str_1 = str(hex(responseGetResponse_Image[4]))
                    str_2 = str(hex(responseGetResponse_Image[5]))
                    str_3 = str_1 + str.split(str_2, 'x')[1]
                    
                    IMAGE_SIZE = int(str_3, 0)
                    
                    r = IMAGE_SIZE%255 # bytes restantes
                    n = int((IMAGE_SIZE-r)/255) # cantidad de iteraciones 0xFF

                    #print ('FOTO ***********************************************')
                    P1 = 0x00
                    P2 = 0x00
                    Le = 0xFF
                    LeInt = 0
                    READBINARY_IMAGE = [0x00, 0xB0, P1, P2, Le] # FALTA Le (viene de comando anterior)CLA INS P1 P2 - Le 6c
                    
                    for i in range(0,n):
                        hresultRead_Image, responseReadB_Image = SCardTransmit(hcard, dwActiveProtocol, READBINARY_IMAGE)
                        responseReadB_Image.pop()
                        responseReadB_Image.pop()
                        IMAGE.extend(responseReadB_Image)
                        LeInt = LeInt + 255
                        remaining_data = format(LeInt, '04x')
                        P1 = remaining_data[:2]
                        P1 = int(P1, base=16)
                        P2 = remaining_data[2:]
                        P2 = int(P2, base=16)
                        
                        READBINARY_IMAGE = [0x00, 0xB0, P1, P2, Le]
                    
                    READBINARY_IMAGE = [0x00, 0xB0, P1, P2, r]
                    hresultRead_Image, responseReadB_Image = SCardTransmit(hcard, dwActiveProtocol, READBINARY_IMAGE)

                    if hresultRead_Image != SCARD_S_SUCCESS:
                        raise Exception('Failed to transmit: ' +
                            SCardGetErrorMessage(hresultRead_Image))
                    responseReadB_Image.pop()
                    responseReadB_Image.pop()                
                    IMAGE.extend(responseReadB_Image)
                    #print ('IMAGE***************')
                    cont = 0
                    
                    IMAGE.pop(0)
                    IMAGE.pop(0)
                    IMAGE.pop(0)
                    IMAGE.pop(0)
                    IMAGE.pop(0)
                    
                    HEX_IMAGE = smartcard.util.toHexString(IMAGE, smartcard.util.HEX)               
                    HEX_LIST = str.split(HEX_IMAGE,' 0x')
                    HEX_STRING = str.split(''.join(HEX_LIST), '0x')[1]
                
                    BIN_IMAGE = smartcard.util.HexListToBinString(IMAGE)
                    data = ""
                    
                    for j in range(0,len(HEX_LIST)):
                        data = data + HEX_LIST[j]
                    
                    data = str.split(data, 'x')[1]
                    data = data.replace(' ','')
                    
                    #data.encode("hex")                       
                    bdata = bytearray.fromhex(data)
                    #print('faja2')
                    file = open(IMAGEPATH, 'wb')
                    file.write(bdata)
                    file.close()
                    file = open('./face_verification/static/images/X.jpeg', 'wb')
                    file.write(bdata)
                    file.close()
                    
                finally:
                    hresult = SCardDisconnect(hcard, SCARD_UNPOWER_CARD)
                    if hresult != SCARD_S_SUCCESS:
                        raise Exception('Failed to disconnect: ' +
                            SCardGetErrorMessage(hresult))
                    print ('Disconnected')
            except ExException as err:
                return render(request, 'face_verification/info.html',context ={'msg': "Debe colocar la cédula"})

        finally:
            hresult = SCardReleaseContext(hcontext)
            if hresult != SCARD_S_SUCCESS:
                raise Exception('Failed to release context: ' +
                        SCardGetErrorMessage(hresult))
            print ('Released context.')

    except Exception as err:
        return render(request, 'face_verification/info.html',context ={'msg': "Debe colocar la cédula"})
    
    import sys
    if 'win32' == sys.platform:
        print ('press Enter to continue')
        sys.stdin.read(1)
    return render(request, 'face_verification/camera.html')


def success(request):
    
#    context = {
#       'persons': persons
#    }
    return render(request, 'face_verification/success.html', context)


def failure(request):
    return render(request, 'face_verification/failure.html')


def face_verification(request):

    if request.POST:

        #video_capture = cv2.VideoCapture(0)
        camera = PiCamera()
        camera.resolution = (640, 480)
        camera.framerate = 32
        rawCapture = PiRGBArray(camera,size=(640,480))
        time.sleep(0.1)
        
        # Load a second sample picture and learn how to recognize it.
        X_image = face_recognition.load_image_file("./face_verification/KnownFaces/X.jpeg")
        X_face_encoding = face_recognition.face_encodings(X_image)[0]

        # Create arrays of known face encodings and their names
        known_face_encodings = [
            X_face_encoding
        ]
        known_face_names = [
            "X"
        ]

        # Initialize some variables
        face_locations = []
        face_encodings = []
        face_names = []
        process_this_frame = True
        contadorTrue = 0
        contadorFalse = 0

        #while True:
        for frame in camera.capture_continuous(rawCapture,format="bgr",use_video_port=True):
            # Grab a single frame of video
            #ret, frame = video_capture.read()
            frame = frame.array
            #https://www.pyimagesearch.com/2017/02/06/faster-video-file-fps-with-cv2-videocapture-and-opencv/
            
            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = small_frame[:, :, ::-1]

            # Only process every other frame of video to save time
            if process_this_frame:
                # Find all the faces and face encodings in the current frame of video
                face_locations = face_recognition.face_locations(
                    rgb_small_frame)
                face_encodings = face_recognition.face_encodings(
                    rgb_small_frame, face_locations)

                face_names = []
                for face_encoding in face_encodings:
                    # See if the face is a match for the known face(s)
                    matches = face_recognition.compare_faces(
                        known_face_encodings, face_encoding)
                    name = "Unknown"

                    # If a match was found in known_face_encodings, just use the first one.
                    data = [0,0,0]
                    if True in matches:
                        first_match_index = matches.index(True)
                        name = known_face_names[first_match_index]
                        filepath = "./face_verification/output.txt"  
                        f=open(filepath, "r")
                        fl =f.readlines()
                        cnt = 0
                        for x in fl:    
                            data[cnt] = x
                            cnt += 1
                        print(data[0])
                        persons = [{
                            'name': data[1],
                            'surname': data[0]
                        }]
                        context = {'persons': persons}
                        camera.close()
                        if allowedUsers.objects.filter(idNumber=data[2]):
                            user = User(name = data[1],surname = data[0], idNumber = data[2], result = True)
                            user.save()
                            return render(request, 'face_verification/success.html', context)
                        else:
                            user = User(name = data[1],surname = data[0], idNumber = data[2], result = False)
                            user.save()
                            return render(request, 'face_verification/failure.html',context = {'msg':'el usuario no tiene permisos de acceso'})
                    elif True not in matches:
                        user = User(name = data[1],surname = data[0], idNumber = data[2], result = False)
                        user.save()
                        camera.close()
                        return render(request, 'face_verification/failure.html', context = {'msg':'el rostro no coincide con el de la cedula'})


            process_this_frame = not process_this_frame

            # Display the results
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a box around the face
                cv2.rectangle(frame, (left, top),
                              (right, bottom), (0, 0, 255), 2)

                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35),
                              (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6),
                            font, 1.0, (255, 255, 255), 1)

            # Display the resulting image
            #cv2.imshow('Video', frame)

            # Hit 'q' on the keyboard to quit!
            #if cv2.waitKey(1) & 0xFF == ord('q'):
            #   break
            
        # Release handle to the webcam
        #video_capture.release()
        camera.close()
        # cv2.destroyAllWindows()

