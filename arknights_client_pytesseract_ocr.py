import asyncio
import datetime
import sys
import warnings
warnings.simplefilter("ignore", UserWarning)
sys.coinit_flags = 2
import pyautogui as pag
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog
from PyQt5.QtCore import QCoreApplication, QTimer, QThread, pyqtSignal, pyqtSlot
from PIL import ImageGrab, Image
from functools import partial
import cv2
import numpy as np
import pyperclip
from socket import *
import discord
from discord.ext import tasks
from PyQt5 import uic
from os import environ
import matplotlib as plt
import pytesseract
import threading

import os
from dotenv import load_dotenv


load_dotenv()


# 프로그램 실행 시 관리자 권한 획득
# import os
# import win32com.shell.shell as shell
# if sys.argv[-1] != 'asadmin':
#     script = os.path.abspath(sys.argv[0])
#     params = ' '.join([script] + sys.argv[1:] + ['asadmin'])
#     shell.ShellExecuteEx(lpVerb='runas', lpFile=sys.executable, lpParameters=params)
#     sys.exit(0)

# UI setting =======================================================================================================
form_class = uic.loadUiType(r"./resource/arknights_client.ui")[0]

def suppress_qt_warnings():

    environ["QT_DEVICE_PIXEL_RATIO"] = "0"
    environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    environ["QT_SCALE_FACTOR"] = "1"
# ==================================================================================================================

# Client ============================================================================================================
class Client(QThread):
    connection_error_signal = pyqtSignal()
    data_received_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.total_sanity = '-'
        self.present_sanity = '-'
        self.estimated_time = 0
        
        self.clientSock = None
        self.ip_3num = os.environ.get('IP_3NUM')
        # self.ip_3num = '127.0.0.'
        # self.ip_1num = '1'
        self.port = int(os.environ.get('PORT'))
        
        self.is_connected = False
        
    def connect(self):
        self.clientSock = socket(AF_INET, SOCK_STREAM)
        # self.clientSock.settimeout(3)
        
        try:
            with open(r"./resource/ip.txt", "r") as f:
                self.ip_1num = f.read()
            f.close()
            
            ip = self.ip_3num + self.ip_1num
            self.clientSock.connect((ip, self.port))
            print(f'{ip}에 접속되었습니다.')
            self.is_connected = True
            recv_thread = threading.Thread(target=self.receive, daemon=True)
            recv_thread.start()

            self.send('Detect')

        except:
            self.connection_error_signal.emit()
        
    def send(self, _status):
        try:
            sendData = str(self.total_sanity) + ',' + str(self.present_sanity) + ',' + _status
            self.clientSock.send(sendData.encode())
        except:
            self.connection_error_signal.emit()

    def receive(self):
        while True:
            try:
                recvData = self.clientSock.recv(1024)
                
                if recvData.decode():
                    print(f'Data received: {recvData.decode()}')
                    recvData = list(map(lambda x: x.strip(), recvData.decode().split(',')))
                    print(recvData)
                    
                    try:
                        self.total_sanity = int(recvData[0])
                        self.present_sanity = int(recvData[1])
                        self.estimated_time = (self.total_sanity - self.present_sanity) * 6
                        self.data_received_signal.emit()
                    except:
                        print(f'Data is not valid')
            except:
                self.shutdown()
                self.connect()
                break
    
    def shutdown(self):
        self.is_connected = False
        self.clientSock.shutdown(SHUT_RDWR)
        
# ==================================================================================================================

# UI ================================================================================================================
class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('Sanity Detector')
        self.move(1920, 0)

        self.b1.clicked.connect(self.identify_sanity)
        self.b4.clicked.connect(self.close_program)
        
        self.client = Client()
        self.client.connection_error_signal.connect(self.connection_error)
        self.client.data_received_signal.connect(self.update_ui)
        self.client.connect()

        # self.ui_mode = 'Normal'
        self.ui_mode = 'R6'

        self.error_recovery_timer = QTimer()
        self.error_recovery_timer.timeout.connect(self.error_recovery)
        self.error_recovery_timer.start(60000)
    
    @pyqtSlot()
    def connection_error(self):
        ip_text, ok = QInputDialog.getText(self, 'Input IP', 'The IP has changed.\n'
                                                                'Please check and input changed IP:')
        if ip_text != '':
            f = open(r"./resource/ip.txt", "w")
            f.write(ip_text)
            f.close()
        
        self.client.connect()
    
    def identify_sanity(self):
        # pag.screenshot(r'./resource/screenshot.png')
        
        # 모니터가 한 개 이상일 경우 모든 모니터에서 이미지 검색
        ImageGrab.grab = partial(ImageGrab.grab, all_screens=True)
        img = ImageGrab.grab()
        img.save(r"./resource/screenshot.png")
        img = cv2.imread(r'./resource/screenshot.png')
        tmp = cv2.imread(f"./resource/operation_{self.ui_mode}.PNG")
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray_tmp = cv2.cvtColor(tmp, cv2.COLOR_BGR2GRAY)

        detector = cv2.SIFT_create()

        kp1, desc1 = detector.detectAndCompute(gray_tmp, None)
        kp2, desc2 = detector.detectAndCompute(gray_img, None)
        matcher = cv2.BFMatcher()
        matches = matcher.knnMatch(desc1, desc2, k=2)

        good = [first for first, second in matches if first.distance < second.distance * 0.3]

        src_pts = np.float32([kp1[m.queryIdx].pt for m in good])
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good])

        # img_matches = cv2.drawMatchesKnn(tmp, kp1, img, kp2, matches, None,
        #                                  flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

        # 좋은 매칭만 그리기
        # img_good_matches = cv2.drawMatches(tmp, kp1, img, kp2, good, None,
        #                                    flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

        # cv2.imwrite('./resource/matches.jpg', img_matches)
        # cv2.imwrite('./resource/good_matches.jpg', img_good_matches)

        try:
            mtrx, mask = cv2.findHomography(src_pts, dst_pts)
            h, w, = tmp.shape[:2]
            pts = np.float32([[[0, 0]], [[0, h - 1]], [[w - 1, h - 1]], [[w - 1, 0]]])
            dst = cv2.perspectiveTransform(pts, mtrx)

            # dst에 저장된 값은 좌상단, 좌하단, 우하단, 우상단 순
            # img = cv2.rectangle(img, (int(2.5 * dst[0][0][0] - 1.5 * dst[3][0][0]), dst[0][0][1]),
            #                     (dst[0][0][0], int(dst[1][0][1] + (dst[1][0][1] - dst[0][0][1]) / 2)),
            #                     (0, 0, 255), 2)

            # Present Sanity
            if self.ui_mode == 'Normal':
                x1 = int(2.04 * dst[0][0][0] - 1.04 * dst[3][0][0])
                y1 = int(dst[0][0][1])
                x2 = int(dst[0][0][0])
                y2 = int(dst[1][0][1] + (dst[1][0][1] - dst[0][0][1]) / 2.2)
            
            elif self.ui_mode == 'R6':
                x1 = int(dst[0][0][0] - (dst[3][0][0] - dst[0][0][0]) * 1.8)
                y1 = int(dst[0][0][1] - (dst[1][0][1] - dst[0][0][1]) * 3.0)
                x2 = int(dst[0][0][0] - (dst[3][0][0] - dst[0][0][0]) * 0.3)
                y2 = int(dst[1][0][1] + (dst[1][0][1] - dst[0][0][1]) / 2.2)

            cropped = gray_img[y1: y2, x1: x2]
            if self.ui_mode == 'Normal':
                _, binarized = cv2.threshold(cropped, 100, 255, cv2.THRESH_BINARY)
            elif self.ui_mode == 'R6':
                _, binarized = cv2.threshold(cropped, 200, 255, cv2.THRESH_BINARY)

            pil_img = Image.fromarray(binarized)
            # w, h = pil_img.size
            # scale_factor = 50 / h
            # pil_img = pil_img.resize((int(w * scale_factor), int(h * scale_factor)))
            # pil_img.save(r'./resource/preprocessed_img1.png')
            
            # Total Sanity
            if self.ui_mode == 'Normal':
                x1 = int((2.04 - 0.55) * dst[0][0][0] - (1.04 - 0.55) * dst[3][0][0])
                y1 = int(dst[1][0][1] + (dst[1][0][1] - dst[0][0][1]) / 2.2)
                x2 = int((dst[0][0][0]) - (dst[0][0][0] - x1) * 0.3)
                y2 = int(dst[1][0][1] + (dst[1][0][1] - dst[0][0][1]) / 1.1)
            
            elif self.ui_mode == 'R6':
                x1 = int((2.04 - 0.0001) * dst[0][0][0] - (1.04 - 0.0001) * dst[3][0][0])
                y1 = int(dst[1][0][1] + (dst[1][0][1] - dst[0][0][1]) / 2.8)
                x2 = int((dst[0][0][0]) - (dst[0][0][0] - x1) * 0.3)
                y2 = int(dst[1][0][1] + (dst[1][0][1] - dst[0][0][1]) / 0.5)

            cropped2 = gray_img[y1: y2, x1: x2]
            if self.ui_mode == 'Normal':
                _, binarized = cv2.threshold(cropped2, 100, 255, cv2.THRESH_BINARY)
                cropped2 = cv2.bitwise_not(binarized, cv2.IMREAD_COLOR)
            pil_img2 = Image.fromarray(cropped2)
            # w, h = pil_img2.size
            # scale_factor = 30 / h
            # pil_img2 = pil_img2.resize((int(w * scale_factor), int(h * scale_factor)))
            # pil_img2.save(r'./resource/preprocessed_img2.png')

            # pipeline = keras_ocr.pipeline.Pipeline()
            # image1 = keras_ocr.tools.read(r'./resource/preprocessed_img1.png')
            # image2 = keras_ocr.tools.read(r'./resource/preprocessed_img2.png')
            # prediction_groups = pipeline.recognize([image1, image2])

            # # print(prediction_groups[0][0][0], prediction_groups[1][0][0])
            # present_sanity = prediction_groups[0][0][0]
            # total_sanity = prediction_groups[1][0][0]


            # pyTesseract OCR digits.traineddata
            # https://github.com/Shreeshrii/tessdata_shreetest/blob/master/digits.traineddata
            present_sanity = pytesseract.image_to_string(pil_img, lang='digits', config='--psm 6')
            total_sanity = pytesseract.image_to_string(pil_img2, lang='digits', config='--psm 6')
            # print(f'present_sanity: {present_sanity}, total_sanity: {total_sanity}')
            present_sanity = ''.join([i for i in present_sanity if i.isdigit()])
            total_sanity = ''.join([i for i in total_sanity if i.isdigit()])

            if present_sanity[0] == 'O':
                present_sanity = 0
                
            print(f'present_sanity: {present_sanity}, total_sanity: {total_sanity}')
                
            text1 = '현재 이성: ' + str(present_sanity) + '/' + str(total_sanity)
            text1 = text1.replace("\n", "")
            # self.label1.setText(str(text1))
            # self.label1.repaint()

            estimated_time = (int(total_sanity) - int(present_sanity)) * 6
            text2 = '예상 소요 시간: ' + str(estimated_time) + '분'
            text2 = text2.replace("\n", "")
            # self.label2.setText(str(text2))
            # self.label2.repaint()

            _, _, _, hh, mm, _, _, _, _ = time.localtime(time.time())
            hh = int(hh + estimated_time / 60)
            mm += (estimated_time % 60)
            if mm >= 60:
                mm -= 60
                hh += 1
            if hh >= 24:
                hh -= 24
            text3 = '완충 완료 시각: ' + str(int(hh)) + ':' + format(mm, '02')
            # self.label3.setText(str(text3))
            # self.label3.repaint()

            self.client.total_sanity = total_sanity
            self.client.present_sanity = present_sanity
            self.client.estimated_time = estimated_time
            self.client.send('Detect')

        except:
            pass
    
    def error_recovery(self):
        if self.client.is_connected:
            self.client.total_sanity = '-'
            self.client.present_sanity = '-'
            self.client.send('Check')

    # Update UI
    @pyqtSlot()
    def update_ui(self):
        text1 = '현재 이성: ' + str(self.client.present_sanity) + '/' + str(self.client.total_sanity)
        text1 = text1.replace("\n", "")
        self.label1.setText(str(text1))
        # self.label1.repaint()

        text2 = '예상 소요 시간: ' + str(self.client.estimated_time) + '분'
        text2 = text2.replace("\n", "")
        self.label2.setText(str(text2))
        # self.label2.repaint()
        
        _, _, _, hh, mm, _, _, _, _ = time.localtime(time.time())
        hh = int(hh + self.client.estimated_time / 60)
        mm += (self.client.estimated_time % 60)
        if mm >= 60:
            mm -= 60
            hh += 1
        if hh >= 24:
            hh -= 24
        text3 = '완충 완료 시각: ' + str(int(hh)) + ':' + format(mm, '02')
        self.label3.setText(str(text3))
        # self.label3.repaint()

    def close_program(self):
        self.client.send('Close')
        self.client.shutdown()
        # time.sleep(1)
        QApplication.quit()
        
    def closeEvent(self, event):
        self.close_program()

# UI 실행
if __name__ == "__main__":
    suppress_qt_warnings()
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()
# if __name__ == '__main__':
#    app = QApplication(sys.argv)
#    ex = MyApp()
#    sys.exit(app.exec_())

