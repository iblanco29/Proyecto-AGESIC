#! /usr/bin/env python

from smartcard.scard import *
import smartcard.util
import base64
import binascii
import io
import os
import numpy as np
from array import array
import string

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
                #print(BIO_INFO)                               
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
                
                file = open("output.txt", "w")
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
                print('cacaaaa')      
                bdata = bytearray.fromhex(data)
                print('caca')
                file = open('/home/pi/Desktop/CI/knownFaces/X.jpeg', 'wb')
                file.write(bdata)
                file.close()
                
            finally:
                hresult = SCardDisconnect(hcard, SCARD_UNPOWER_CARD)
                if hresult != SCARD_S_SUCCESS:
                    raise Exception('Failed to disconnect: ' +
                        SCardGetErrorMessage(hresult))
                print ('Disconnected')

        except:
            pass

    finally:
        hresult = SCardReleaseContext(hcontext)
        if hresult != SCARD_S_SUCCESS:
            raise Exception('Failed to release context: ' +
                    SCardGetErrorMessage(hresult))
        print ('Released context.')

except:
    pass
  
import sys
if 'win32' == sys.platform:
    print ('press Enter to continue')
    sys.stdin.read(1)


