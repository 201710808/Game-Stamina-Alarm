import asyncio
import datetime
import sys
import warnings
warnings.simplefilter("ignore", UserWarning)
sys.coinit_flags = 2
import pywinauto as pw
import pyautogui as pag
import time
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QLabel, QInputDialog
from PyQt5.QtCore import QCoreApplication, QRect, QTimer, QThread
from PIL import ImageGrab, Image
from functools import partial
import cv2
import numpy as np
import pytesseract
import pyperclip
from socket import *
import discord
from discord.ext import tasks

global present_sanity
global total_sanity
global estimated_time
global sock
present_sanity = '-'
total_sanity = '-'


# UI
class MyApp(QMainWindow, QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def identify_sanity(self):
        global sock
        pag.screenshot('screenshot.png')
        time.sleep(0.5)
        img = cv2.imread('screenshot.png')
        tmp = cv2.imread("operation.PNG")
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray_tmp = cv2.cvtColor(tmp, cv2.COLOR_BGR2GRAY)

        detector = cv2.xfeatures2d.SIFT_create()

        kp1, desc1 = detector.detectAndCompute(gray_tmp, None)
        kp2, desc2 = detector.detectAndCompute(gray_img, None)
        matcher = cv2.BFMatcher()
        matches = matcher.knnMatch(desc1, desc2, k=2)

        good = [first for first, second in matches if first.distance < second.distance * 0.3]

        src_pts = np.float32([kp1[m.queryIdx].pt for m in good])
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good])
        try:
            mtrx, mask = cv2.findHomography(src_pts, dst_pts)
            h, w, = tmp.shape[:2]
            pts = np.float32([[[0, 0]], [[0, h - 1]], [[w - 1, h - 1]], [[w - 1, 0]]])
            dst = cv2.perspectiveTransform(pts, mtrx)

            x1 = int(2.14 * dst[0][0][0] - 1.14 * dst[3][0][0])
            y1 = int(dst[0][0][1])
            x2 = int(dst[0][0][0])
            y2 = int(dst[1][0][1] + (dst[1][0][1] - dst[0][0][1]) / 2.2)

            cropped = gray_img[y1: y2, x1: x2]
            _, binarized = cv2.threshold(cropped, 100, 255, cv2.THRESH_BINARY)
            pil_img = Image.fromarray(binarized)

            x1 = int((2.14 - 0.6) * dst[0][0][0] - (1.14 - 0.6) * dst[3][0][0])
            y1 = int(dst[1][0][1] + (dst[1][0][1] - dst[0][0][1]) / 2.2)
            x2 = int((dst[0][0][0]) - (dst[0][0][0] - x1) * 0.3)
            y2 = int(dst[1][0][1] + (dst[1][0][1] - dst[0][0][1]) / 1.1)

            cropped2 = gray_img[y1: y2, x1: x2]
            _, binarized = cv2.threshold(cropped2, 100, 255, cv2.THRESH_BINARY)
            flip = cv2.bitwise_not(binarized, cv2.IMREAD_COLOR)
            pil_img2 = Image.fromarray(flip)

            global present_sanity
            global total_sanity

            present_sanity = pytesseract.image_to_string(pil_img, config='--psm 6')
            total_sanity = pytesseract.image_to_string(pil_img2, config='--psm 6')
            if present_sanity[0] == 'O':
                present_sanity = 0

            text1 = '현재 이성: ' + str(present_sanity) + '/' + str(total_sanity)
            text1 = text1.replace("\n", "")
            self.label1.setText(str(text1))
            self.label1.repaint()

            global estimated_time

            estimated_time = (int(total_sanity) - int(present_sanity)) * 6
            text2 = '예상 소요 시간: ' + str(estimated_time) + '분'
            text2 = text2.replace("\n", "")
            self.label2.setText(str(text2))
            self.label2.repaint()

            _, _, _, hh, mm, _, _, _, _ = time.localtime(time.time())
            hh = int(hh + estimated_time / 60)
            mm += (estimated_time % 60)
            if mm >= 60:
                mm -= 60
                hh += 1
            if hh >= 24:
                hh -= 24
            text3 = '완충 완료 시각: ' + str(int(hh)) + ':' + format(mm, '02')
            self.label3.setText(str(text3))
            self.label3.repaint()

            def send():
                global sock
                while True:
                    try:
                        port = 8080

                        with open("ip.txt", "r") as f:
                            ip = f.read()
                        f.close()
                        ip = '[[INPUT YOUR 9 IP NUMBERS HERE(ex: xxx.xxx.xxx.123)]]' + ip
                        print(ip)

                        clientSock = socket(AF_INET, SOCK_STREAM)
                        clientSock.connect((ip, port))

                        print('접속 완료')
                        sock = clientSock

                        global total_sanity
                        global present_sanity
                        print("능지 detect")
                        sendData = str(total_sanity) + ',' + str(present_sanity) + ',' + 'Detect'
                        sock.send(sendData.encode())
                        time.sleep(5)
                        break
                    except:
                        ip_text, ok = QInputDialog.getText(self, 'Input IP', 'The IP has changed.\n'
                                                                             'Please check and input changed IP:')
                        if ip_text != '':
                            f = open("ip.txt", "w")
                            f.write(ip_text)
                            f.close()

            send()

        except:
            pass

    def every_6min(self):
        global total_sanity
        global present_sanity
        global estimated_time

        if present_sanity != '-' and int(present_sanity) < int(total_sanity):
            present_sanity = int(present_sanity) + 1
            estimated_time -= 6

            text1 = '현재 이성: ' + str(present_sanity) + '/' + str(total_sanity)
            text1 = text1.replace("\n", "")
            self.label1.setText(str(text1))
            self.label1.repaint()

            text2 = '예상 소요 시간: ' + str(estimated_time) + '분'
            text2 = text2.replace("\n", "")
            self.label2.setText(str(text2))
            self.label2.repaint()

    def initUI(self):
        self.setWindowTitle('Sanity Detector')
        self.move(1920, 0)
        self.resize(150, 170)

        self.timer = QTimer()
        self.timer.setInterval(360000)
        self.timer.timeout.connect(self.every_6min)
        self.timer.start()

        b1 = QPushButton('Detect Sanity', self)
        b1.move(25, 18)
        b1.clicked.connect(self.identify_sanity)

        self.b4 = QPushButton('Quit', self)
        self.b4.move(25, 55)
        self.b4.clicked.connect(self.timer.stop)
        self.b4.clicked.connect(QCoreApplication.instance().quit)

        self.label1 = QLabel('Present Sanity', self)
        self.label1.setGeometry(QRect(10, 106, 150, 15))
        text1 = '현재 이성: ' + '-/-'
        self.label1.setText(str(text1))

        self.label2 = QLabel('Estimated Time', self)
        self.label2.setGeometry(QRect(10, 126, 150, 15))
        text2 = '예상 소요 시간: ' + '-' + '분'
        self.label2.setText(str(text2))

        self.label3 = QLabel('Estimated Completion Time', self)
        self.label3.setGeometry(QRect(10, 146, 150, 15))
        text3 = '완충 완료 시각: ' + '-:-'
        self.label3.setText(str(text3))

        self.show()


# 모니터가 한 개 이상일 경우 모든 모니터에서 이미지 검색
ImageGrab.grab = partial(ImageGrab.grab, all_screens=True)

# UI 실행
if __name__ == '__main__':
   app = QApplication(sys.argv)
   ex = MyApp()
   sys.exit(app.exec_())

