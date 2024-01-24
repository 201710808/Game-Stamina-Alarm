# Game-Stamina-Alarm
## 프로젝트 요약
게임화면을 인식하여 스태미나를 확인하고 예정된 시각에 사용자에게 알람을 보내주는 프로젝트입니다.

```mermaid
graph TB;
    subgraph PC;
    Client;
    end;
    subgraph Mobile using Termux;
    Client-->Server;
    Server-->Condition{"Will stamina\nbe full in 60 mins?"};
    end;
    Condition-->|"No"|Server;
    Condition-->|"Yes"|Alarm["Discord Alarm"];
```

## 구현 방법
### Client
```mermaid
graph TB;
    Original_image-->Screenshot;
    Target_image-->Load;
    subgraph PC Client;
    Screenshot-->gray1[img2gray]
    Load-->gray2[img2gray]
    gray1-->SIFT;
    gray2-->SIFT;
    SIFT-->knnMatch;
    knnMatch-->dist_match[이웃 거리 30%로 매칭점 추출];
    dist_match-->orig_coord[원본 영상 좌표];
    dist_match-->tgt_coord[대상 영상 좌표];
    orig_coord-->homography;
    tgt_coord-->homography[원근 변환\n행렬 계산];
    homography-->transform_coord[원본 영상 좌표\n원근 변환];
    transform_coord-->calc_ROI[변환된 좌표 기반\n2개의 ROI 계산];
    calc_ROI-->Present_stamina;
    calc_ROI-->Max_stamina;
    Present_stamina-->bin_neg1[이진화\n및\n색반전];
    Max_stamina-->bin_neg2[이진화\n및\n색반전];
    bin_neg1-->OCR1[OCR];
    bin_neg2-->OCR2[OCR];
    OCR1-->calc_stamina[스태미나 충전\n예상 시간 계산];
    OCR2-->calc_stamina;
    end;
    calc_stamina-->connect_server[서버 연결\n및\n데이터 전송];
```
SIFT 검출기로 특징 영역 추출, knnMatch를 통한 매칭점 추출, homography matrix계산은 다음 링크를 참고하였습니다.  
[OpenCV - 29. 올바른 매칭점 찾기](https://bkshin.tistory.com/entry/OpenCV-29-%EC%98%AC%EB%B0%94%EB%A5%B8-%EB%A7%A4%EC%B9%AD%EC%A0%90-%EC%B0%BE%EA%B8%B0)  
<br>
OCR과정은 Tesseract OCR을 사용하였습니다.  
[tesseract github](https://github.com/UB-Mannheim/tesseract)  

### Server
```mermaid
graph TB;
    data[Client에서\n전송된 데이터]-->Accept;

    subgraph Server Socket;
    Socket-->Listen;
    Listen-->Accept;
    end;
    Accept-->|스태미나 정보 갱신|Stamina;
    Accept-->Listen;

    sec-->sec360;
    subgraph Timer;
    timer_start-->sec360;
    sec360[sec=360]-->condition{sec != 0};
    condition-->|"Yes"|process_time[sec -= 1\ntime.sleep 1];
    process_time-->condition;
    condition-->|"No"|sync_stamina[현재 스태미나 +1];
    sync_stamina-->sec360;
    end;

    process_time-->|"타이머 갱신"|sec;
    sync_stamina-->|스태미나 정보 갱신|Stamina;

    subgraph Discord_Bot;
    TOKEN-->Client[discord.Client];
    CHANNEL_ID-->Client;
    Client-->task.loop;
    task.loop-->discord_condition{Max - Present <= 0\nand\nsec == 0};
    discord_condition-->|"Yes"|discord_message[디스코드 알림\n메시지 전송]
    discord_condition-->|"No"|task.loop;
    end;
    
    subgraph UI;
    input_stamina[1. 스태미나 직접 입력];
    check_ip[2. 기기 IP 확인]-->output_ip[현재 IP\n정보 출력];
    check_stamina[3. 스태미나 확인]-->output_stamina[현재 스태미나\n정보 출력];
    
    end;
    input_stamina-->|스태미나 정보 갱신|Stamina;
```
서버는 모바일 환경에서 Termux라는 어플을 사용하여 Python코드를 구동하여 구축하였습니다.    
[Termux 앱으로 안드로이드 폰으로 SSH 서버 환경설정](https://oopaque.tistory.com/84)  

## 실제 동작
### Client
#### 이미지 인식 기능 시각화
<img src="https://github.com/201710808/Game-Stamina-Alarm/assets/79844211/2d9e5fa3-55d3-49f2-9104-07b7fa1cae21" width="800"><br>
- 좌측 이미지: 찾으려는 타겟 이미지
- 청색 사각형: 스크린샷(원본 이미지)에서 찾아낸 타겟 이미지
- 적·녹색 사각형: 찾아낸 타겟 이미지 기반 상대 좌표로 설정한 OCR을 위한 ROI
#### Client UI
<img src="https://github.com/201710808/Game-Stamina-Alarm/assets/79844211/23252fc3-e112-4d5b-bd16-a36306505a45" width="200"><br>
간단한 리모컨의 형태입니다.

### Server
<img src="https://github.com/201710808/Game-Stamina-Alarm/assets/79844211/391bd684-f4f1-4b18-af45-a878182b0037" width="500"><br>
Termux를 사용해 서버 로그와 UI가 출력됩니다.
