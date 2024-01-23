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

    subgraph Timer;
    timer_start[타이머 생성]-->sec;
    sec[sec=360]-->condition{sec != 0};
    condition-->|"Yes"|process_time[sec -= 1\ntime.sleep 1];
    process_time-->condition;
    end;
    condition-->|"No\n현재 스태미나 +1"|Stamina;

    subgraph Discord_Bot;
    TOKEN-->Client[discord.Client];
    CHANNEL_ID-->Client;
    end;
```
