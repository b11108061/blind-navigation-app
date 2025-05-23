
import streamlit as st
import cv2
import time
import webbrowser
from ultralytics import YOLO
import speech_recognition as sr
import pyttsx3

# 初始化模型與引擎
model = YOLO("yolov8n")  # 自動下載權重
engine = pyttsx3.init()


def speak(text: str):
    """
    播報文字，同時在側邊欄顯示。
    """
    st.sidebar.write(f"🤖: {text}")
    engine.say(text)
    engine.runAndWait()


def listen(prompt: str = "請開始說話") -> str:
    """
    語音錄製並辨識。
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak(prompt)
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio, language="zh-TW")
    except Exception:
        return "我沒有聽清楚，請再說一次。"


def build_maps_url(destination: str, transport: str) -> str:
    base = "https://www.google.com/maps/dir/?api=1"
    mode_map = {"走路": "walking", "公車": "transit", "捷運": "transit"}
    tm = mode_map.get(transport, "walking")
    return f"{base}&destination={destination}&travelmode={tm}"


def main():
    st.set_page_config(page_title="智慧導盲系統 SmartGuide", layout="wide")
    st.title("🤖 智慧導盲系統 Web App")

    session = st.session_state
    session.setdefault("step", 0)
    session.setdefault("dest", "")
    session.setdefault("transport", "")
    session.setdefault("detecting", False)

    # 側邊欄：導航 & 對話控制
    with st.sidebar:
        st.header("導航功能（手動）")
        dest_in = st.text_input("目的地", session.dest)
        transport_in = st.selectbox("交通方式", ["走路", "公車", "捷運"], index=["走路","公車","捷運"].index(session.transport) if session.transport in ["走路","公車","捷運"] else 0)
        if st.button("開始導航 (手動)"):
            session.dest = dest_in
            session.transport = transport_in
            url = build_maps_url(dest_in, transport_in)
            webbrowser.open(url)
            speak("已為您開啟 Google Maps 導航，並啟用智慧鏡頭偵測。")
            session.step = 1
            session.detecting = True

        st.markdown("---")
        st.header("語音互動 (自動)")
        if session.step == 0:
            # 啟動語音問路流程
            speak("您好，我是您的智慧導盲助手。請問今天想要去哪裡？")
            session.dest = listen()
            st.sidebar.write(f"目的地 (語音)：{session.dest}")
            speak("請問您想用什麼交通工具？例如走路、公車或捷運。")
            session.transport = listen()
            st.sidebar.write(f"交通方式 (語音)：{session.transport}")
            url = build_maps_url(session.dest, session.transport)
            webbrowser.open(url)
            speak("已為您開啟 Google Maps 導航，並啟用智慧鏡頭偵測。")
            session.step = 1
            session.detecting = True

        if session.detecting:
            if st.button("停止偵測"):
                session.detecting = False

    # 若已啟動偵測，使用 OpenCV loop
    if session.detecting:
        st.header("🔍 智慧鏡頭即時偵測 (OpenCV)")
        cap = cv2.VideoCapture(0)
        FRAME_WINDOW = st.empty()
        last_spoken = time.time()
        interval = 3

        while session.detecting:
            ret, frame = cap.read()
            if not ret:
                break

            # YOLO 偵測
            results = model(frame)[0]
            height, width = frame.shape[:2]
            region_labels = {"左邊": [], "中間": [], "右邊": []}
            for box in results.boxes:
                cls_id = int(box.cls[0])
                label = results.names[cls_id]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx = (x1 + x2) // 2
                region = "左邊" if cx < width/3 else ("中間" if cx < 2*width/3 else "右邊")
                region_labels[region].append(label)
                # 畫框和標籤
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)

            # 每隔 interval 播報
            if time.time() - last_spoken > interval:
                descriptions = []
                for region, items in region_labels.items():
                    if items:
                        unique = set(items)
                        text = "、".join(unique)
                        if "斑馬線" in text:
                            descriptions.append(f"{region}是斑馬線，請注意過馬路安全")
                        elif "人" in text:
                            descriptions.append(f"{region}有人")
                        elif "腳踏車" in text:
                            descriptions.append(f"{region}有腳踏車")
                        elif "交通燈" in text or "traffic light" in text:
                            descriptions.append(f"{region}是交通燈號，請注意等候或通行")
                        elif "車" in text or "car" in text:
                            descriptions.append(f"{region}有車輛經過，請小心通行")
                        elif "狗" in text or "dog" in text:
                            descriptions.append(f"{region}有狗")
                        elif "椅子" in text or "chair" in text:
                            descriptions.append(f"{region}有椅子")
                        elif "垃圾桶" in text or "trash can" in text:
                            descriptions.append(f"{region}有垃圾桶")
                        elif any(s in text for s in ["樓梯","stair","stairs"]):
                            descriptions.append(f"{region}是樓梯，請注意上下台階安全")
                        else:
                            descriptions.append(f"{region}有{text}")
                if descriptions:
                    speak("，".join(descriptions))
                last_spoken = time.time()

            # 顯示影像
            FRAME_WINDOW.image(frame, channels="BGR")
            # 偵測停止按鈕跑在同一側邊欄即可觸發退出
            if not session.detecting:
                break
        cap.release()

if __name__ == "__main__":
    main()

import streamlit as st
import cv2
import time
import webbrowser
from ultralytics import YOLO
import speech_recognition as sr
import pyttsx3

# 初始化模型與引擎
model = YOLO("yolov8n")  # 自動下載權重
engine = pyttsx3.init()


def speak(text: str):
    """
    播報文字，同時在側邊欄顯示。
    """
    st.sidebar.write(f"🤖: {text}")
    engine.say(text)
    engine.runAndWait()


def listen(prompt: str = "請開始說話") -> str:
    """
    語音錄製並辨識。
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak(prompt)
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio, language="zh-TW")
    except Exception:
        return "我沒有聽清楚，請再說一次。"


def build_maps_url(destination: str, transport: str) -> str:
    base = "https://www.google.com/maps/dir/?api=1"
    mode_map = {"走路": "walking", "公車": "transit", "捷運": "transit"}
    tm = mode_map.get(transport, "walking")
    return f"{base}&destination={destination}&travelmode={tm}"


def main():
    st.set_page_config(page_title="智慧導盲系統 SmartGuide", layout="wide")
    st.title("🤖 智慧導盲系統 Web App")

    session = st.session_state
    session.setdefault("step", 0)
    session.setdefault("dest", "")
    session.setdefault("transport", "")
    session.setdefault("detecting", False)

    # 側邊欄：導航 & 對話控制
    with st.sidebar:
        st.header("導航功能（手動）")
        dest_in = st.text_input("目的地", session.dest)
        transport_in = st.selectbox("交通方式", ["走路", "公車", "捷運"], index=["走路","公車","捷運"].index(session.transport) if session.transport in ["走路","公車","捷運"] else 0)
        if st.button("開始導航 (手動)"):
            session.dest = dest_in
            session.transport = transport_in
            url = build_maps_url(dest_in, transport_in)
            webbrowser.open(url)
            speak("已為您開啟 Google Maps 導航，並啟用智慧鏡頭偵測。")
            session.step = 1
            session.detecting = True

        st.markdown("---")
        st.header("語音互動 (自動)")
        if session.step == 0:
            # 啟動語音問路流程
            speak("您好，我是您的智慧導盲助手。請問今天想要去哪裡？")
            session.dest = listen()
            st.sidebar.write(f"目的地 (語音)：{session.dest}")
            speak("請問您想用什麼交通工具？例如走路、公車或捷運。")
            session.transport = listen()
            st.sidebar.write(f"交通方式 (語音)：{session.transport}")
            url = build_maps_url(session.dest, session.transport)
            webbrowser.open(url)
            speak("已為您開啟 Google Maps 導航，並啟用智慧鏡頭偵測。")
            session.step = 1
            session.detecting = True

        if session.detecting:
            if st.button("停止偵測"):
                session.detecting = False

    # 若已啟動偵測，使用 OpenCV loop
    if session.detecting:
        st.header("🔍 智慧鏡頭即時偵測 (OpenCV)")
        cap = cv2.VideoCapture(0)
        FRAME_WINDOW = st.empty()
        last_spoken = time.time()
        interval = 3

        while session.detecting:
            ret, frame = cap.read()
            if not ret:
                break

            # YOLO 偵測
            results = model(frame)[0]
            height, width = frame.shape[:2]
            region_labels = {"左邊": [], "中間": [], "右邊": []}
            for box in results.boxes:
                cls_id = int(box.cls[0])
                label = results.names[cls_id]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx = (x1 + x2) // 2
                region = "左邊" if cx < width/3 else ("中間" if cx < 2*width/3 else "右邊")
                region_labels[region].append(label)
                # 畫框和標籤
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)

            # 每隔 interval 播報
            if time.time() - last_spoken > interval:
                descriptions = []
                for region, items in region_labels.items():
                    if items:
                        unique = set(items)
                        text = "、".join(unique)
                        if "斑馬線" in text:
                            descriptions.append(f"{region}是斑馬線，請注意過馬路安全")
                        elif "人" in text:
                            descriptions.append(f"{region}有人")
                        elif "腳踏車" in text:
                            descriptions.append(f"{region}有腳踏車")
                        elif "交通燈" in text or "traffic light" in text:
                            descriptions.append(f"{region}是交通燈號，請注意等候或通行")
                        elif "車" in text or "car" in text:
                            descriptions.append(f"{region}有車輛經過，請小心通行")
                        elif "狗" in text or "dog" in text:
                            descriptions.append(f"{region}有狗")
                        elif "椅子" in text or "chair" in text:
                            descriptions.append(f"{region}有椅子")
                        elif "垃圾桶" in text or "trash can" in text:
                            descriptions.append(f"{region}有垃圾桶")
                        elif any(s in text for s in ["樓梯","stair","stairs"]):
                            descriptions.append(f"{region}是樓梯，請注意上下台階安全")
                        else:
                            descriptions.append(f"{region}有{text}")
                if descriptions:
                    speak("，".join(descriptions))
                last_spoken = time.time()

            # 顯示影像
            FRAME_WINDOW.image(frame, channels="BGR")
            # 偵測停止按鈕跑在同一側邊欄即可觸發退出
            if not session.detecting:
                break
        cap.release()

if __name__ == "__main__":
    main()

