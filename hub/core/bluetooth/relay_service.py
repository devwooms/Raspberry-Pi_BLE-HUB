#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
블루투스 릴레이 서비스 - 수신 디바이스에서 송신 디바이스로 데이터 중계
evdev 라이브러리를 사용하여 마우스 입력을 처리하고 HID 출력으로 전송
"""

import os
import time
import threading
import subprocess
import signal
import atexit
import json
import glob
import select

class BluetoothRelayService:
    """블루투스 릴레이 서비스 클래스"""
    
    def __init__(self):
        """릴레이 서비스 초기화"""
        self.running = False
        self.relay_threads = []
        self.stop_event = threading.Event()
        
        # 정리 함수 등록
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def start_relay(self, source_module, target_module, receiving_devices, transmitting_device):
        """릴레이 시작
        
        Args:
            source_module (str): 수신용 블루투스 모듈 MAC 주소
            target_module (str): 송신용 블루투스 모듈 MAC 주소
            receiving_devices (list): 수신 디바이스 목록
            transmitting_device (dict): 송신 디바이스 정보
            
        Returns:
            bool: 성공 여부
        """
        if self.running:
            print("릴레이가 이미 실행 중입니다.")
            return False
        
        try:
            # 필요한 정보 검증
            if not source_module or not target_module:
                print("블루투스 모듈이 설정되지 않았습니다.")
                return False
                
            if not receiving_devices:
                print("수신 디바이스가 설정되지 않았습니다.")
                return False
                
            if not transmitting_device:
                print("송신 디바이스가 설정되지 않았습니다.")
                return False
            
            print("블루투스 릴레이 시작 중...")
            print(f"수신 모듈: {source_module}, 송신 모듈: {target_module}")
            print(f"수신 디바이스: {len(receiving_devices)}개, 송신 디바이스: {transmitting_device['name']}")
            
            # evdev 패키지 확인
            try:
                import evdev
                print("evdev 패키지가 설치되어 있습니다.")
            except ImportError:
                print("evdev 패키지가 필요합니다. 다음 명령어로 설치하세요:")
                print("sudo apt-get install python3-evdev")
                return False
            
            # 릴레이 스레드 준비
            self.stop_event.clear()
            self.relay_threads = []
            
            # 각 수신 디바이스마다 릴레이 설정
            for device in receiving_devices:
                print(f"수신 디바이스 {device['name']} ({device['mac']})에 대한 릴레이 설정 중...")
                
                # bluetoothctl 설정 확인 (인터페이스 및 장치 연결 상태)
                self._check_and_setup_device(device['mac'])
                
                # 입력 장치 찾기
                input_devices = self._find_input_devices(device['mac'], device['name'])
                
                if not input_devices:
                    print(f"장치 {device['name']}에 대한 입력 장치를 찾을 수 없습니다.")
                    continue
                
                for input_device in input_devices:
                    print(f"입력 장치 사용: {input_device}")
                    
                    # 릴레이 스레드 시작
                    thread = threading.Thread(
                        target=self._relay_data,
                        args=(device, transmitting_device, input_device, self.stop_event),
                        daemon=True
                    )
                    self.relay_threads.append(thread)
                    thread.start()
            
            if not self.relay_threads:
                print("릴레이 스레드를 시작할 수 없습니다. 수신 장치의 입력 장치를 찾을 수 없습니다.")
                return False
            
            # 서비스 상태 업데이트
            self.running = True
            
            print("블루투스 릴레이가 성공적으로 시작되었습니다!")
            print("이제 수신 디바이스의 입력이 송신 디바이스로 전달됩니다.")
            with open('blehub.log', 'a') as f:
                f.write(f"블루투스 릴레이 시작: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                
            return True
            
        except Exception as e:
            print(f"릴레이 시작 중 오류 발생: {e}")
            self.stop_relay()  # 오류 발생 시 정리
            return False
    
    def stop_relay(self):
        """릴레이 중지
        
        Returns:
            bool: 성공 여부
        """
        if not self.running:
            print("릴레이가 실행 중이 아닙니다.")
            return False
            
        try:
            print("블루투스 릴레이 중지 중...")
            
            # 스레드 중지 신호 전송
            self.stop_event.set()
            
            # 모든 스레드 종료 대기
            for thread in self.relay_threads:
                thread.join(timeout=2.0)  # 최대 2초 대기
            
            # 실행 중인 프로세스 정리
            self._cleanup_processes()
            
            # 서비스 상태 업데이트
            self.running = False
            self.relay_threads = []
            
            print("블루투스 릴레이가 중지되었습니다.")
            with open('blehub.log', 'a') as f:
                f.write(f"블루투스 릴레이 중지: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                
            return True
            
        except Exception as e:
            print(f"릴레이 중지 중 오류 발생: {e}")
            # 서비스 상태 강제 업데이트
            self.running = False
            self.relay_threads = []
            return False
    
    def is_running(self):
        """릴레이 실행 중 여부 확인
        
        Returns:
            bool: 실행 중 여부
        """
        return self.running
    
    def _check_and_setup_device(self, device_mac):
        """블루투스 장치 설정 확인 및 설정
        
        Args:
            device_mac (str): 장치 MAC 주소
        """
        try:
            # bluetoothctl로 장치 정보 확인
            info_cmd = ["bluetoothctl", "info", device_mac]
            info_result = subprocess.run(
                info_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            ).stdout
            
            # 연결 상태 확인
            if "Connected: yes" not in info_result:
                # 연결 시도
                print(f"장치 {device_mac}에 연결 시도 중...")
                connect_cmd = ["bluetoothctl", "connect", device_mac]
                subprocess.run(
                    connect_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10
                )
                
            # 신뢰 상태 확인
            if "Trusted: no" in info_result:
                # 신뢰 설정
                print(f"장치 {device_mac} 신뢰 설정 중...")
                trust_cmd = ["bluetoothctl", "trust", device_mac]
                subprocess.run(
                    trust_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5
                )
                
        except Exception as e:
            print(f"장치 설정 중 오류: {e}")
    
    def _find_input_devices(self, device_mac, device_name):
        """해당 장치에 대한 입력 장치 찾기
        
        Args:
            device_mac (str): 장치 MAC 주소
            device_name (str): 장치 이름
            
        Returns:
            list: 입력 장치 경로 목록
        """
        try:
            import evdev
            
            # 모든 입력 장치 검사
            input_devices = []
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            
            for device in devices:
                if device_name.lower() in device.name.lower() or device_mac.replace(':', '') in device.phys.lower():
                    input_devices.append(device.path)
            
            # 장치를 찾지 못했다면 마우스/키보드 장치 추가
            if not input_devices:
                for device in devices:
                    # evdev.categorize를 사용해 장치 유형 확인
                    caps = device.capabilities()
                    if evdev.ecodes.EV_KEY in caps:  # 키 이벤트 지원
                        # 마우스 버튼 확인
                        if evdev.ecodes.BTN_MOUSE in caps[evdev.ecodes.EV_KEY]:
                            print(f"가능한 마우스 장치 감지: {device.name}")
                            input_devices.append(device.path)
                        # 키보드 키 확인
                        elif any(k in caps[evdev.ecodes.EV_KEY] for k in range(evdev.ecodes.KEY_ESC, evdev.ecodes.KEY_MICMUTE)):
                            print(f"가능한 키보드 장치 감지: {device.name}")
                            input_devices.append(device.path)
            
            return input_devices
            
        except ImportError:
            print("evdev 패키지가 필요합니다. 다음 명령어로 설치하세요:")
            print("sudo apt-get install python3-evdev")
            return []
        except Exception as e:
            print(f"입력 장치 검색 중 오류: {e}")
            return []
    
    def _relay_data(self, source_device, target_device, input_device_path, stop_event):
        """수신 장치에서 송신 장치로 데이터 릴레이
        
        Args:
            source_device (dict): 수신 장치 정보
            target_device (dict): 송신 장치 정보
            input_device_path (str): 입력 장치 경로
            stop_event (threading.Event): 중지 이벤트
        """
        try:
            import evdev
            from evdev import InputDevice, categorize, ecodes
            
            source_mac = source_device['mac']
            target_mac = target_device['mac']
            
            print(f"장치 {source_device['name']} ({source_mac})에서 {target_device['name']} ({target_mac})로 데이터 릴레이 시작...")
            
            # 입력 장치 열기
            print(f"입력 장치 열기: {input_device_path}")
            mouse = InputDevice(input_device_path)
            
            # HID 장치 에뮬레이션 설정
            # 송신 장치로 HID 데이터 전송을 위한 준비
            hid_output_process = self._setup_hid_output(target_device)
            if not hid_output_process:
                print("HID 출력 설정 실패. 시뮬레이션 모드로 실행합니다.")
                self._run_simulation_mode(source_device, target_device, stop_event)
                return
            
            # 로그에 기록
            with open('blehub.log', 'a') as f:
                f.write(f"HID 릴레이 시작: {source_device['name']} -> {target_device['name']} (장치: {input_device_path})\n")
            
            # 이벤트 처리 루프
            print("입력 이벤트 대기 중...")
            processed_events = 0
            
            # 마우스 상태 초기화
            mouse_state = {
                'buttons': 0,  # 버튼 상태 (bit 0: 왼쪽, bit 1: 오른쪽, bit 2: 가운데)
                'x': 0,        # X축 이동 (-127~127)
                'y': 0,        # Y축 이동 (-127~127)
                'wheel': 0     # 휠 스크롤 (-127~127)
            }
            
            # 이벤트 처리 루프
            while not stop_event.is_set():
                try:
                    # select를 사용하여 비차단 방식으로 이벤트 읽기 (0.1초 타임아웃)
                    r, w, x = select.select([mouse.fd], [], [], 0.1)
                    if r:
                        for event in mouse.read():
                            if event.type in [ecodes.EV_REL, ecodes.EV_ABS, ecodes.EV_KEY]:
                                # 이벤트 데이터 처리 및 HID 보고서 전송
                                self._process_hid_event(event, hid_output_process, mouse_state)
                                
                                processed_events += 1
                                if processed_events % 10 == 0:  # 10개 이벤트마다 한 번씩 표시
                                    print(".", end="", flush=True)
                                if processed_events % 500 == 0:  # 500개 이벤트마다 줄바꿈
                                    print(f" ({processed_events} 이벤트)")
                                
                except Exception as e:
                    print(f"이벤트 처리 오류: {e}")
                    time.sleep(0.1)
                
                # 중지 이벤트 확인
                if stop_event.is_set():
                    break
            
            # HID 출력 프로세스 종료
            if hid_output_process and hid_output_process.poll() is None:
                try:
                    hid_output_process.terminate()
                    hid_output_process.wait(timeout=1)
                except:
                    pass
            
            print(f"\n장치 {source_device['name']}에서 {target_device['name']}로의 릴레이가 중지되었습니다.")
            print(f"처리된 이벤트: {processed_events}")
            
        except ImportError as e:
            print(f"필요한 라이브러리를 가져올 수 없습니다: {e}")
            print("필요한 패키지를 설치하세요: sudo apt-get install python3-evdev")
            
            # 시뮬레이션 모드로 실행
            self._run_simulation_mode(source_device, target_device, stop_event)
            
        except Exception as e:
            print(f"\n릴레이 작업 중 오류 발생: {e}")
    
    def _setup_hid_output(self, target_device):
        """HID 출력 설정 - bt-hid-device 도구를 사용하여 HID 에뮬레이션
        
        Args:
            target_device (dict): 송신 장치 정보
            
        Returns:
            subprocess.Popen: 실행된 bt-hid-device 프로세스 객체 또는 None
        """
        try:
            # bt-hid-device 경로 설정 (설치 위치에 따라 조정 필요)
            bt_hid_device_paths = [
                "/usr/local/bin/bt-hid-device",
                "/usr/bin/bt-hid-device",
                os.path.expanduser("~/P4wnP1_aloa/bluetooth/bt_hid_device/build/bt-hid-device")
            ]
            
            bt_hid_path = None
            for path in bt_hid_device_paths:
                if os.path.exists(path):
                    bt_hid_path = path
                    break
            
            if not bt_hid_path:
                print("bt-hid-device 도구를 찾을 수 없습니다. 다음 명령어로 설치하세요:")
                print("sudo apt install git cmake build-essential libbluetooth-dev libdbus-1-dev")
                print("git clone https://github.com/mame82/P4wnP1_aloa.git")
                print("cd P4wnP1_aloa/bluetooth/bt_hid_device")
                print("mkdir build && cd build")
                print("cmake ..")
                print("make")
                return None
            
            # HID 출력 프로세스 설정
            print(f"HID 출력 초기화: {target_device['name']} ({target_device['mac']})")
            
            # bt-hid-device 실행 (마우스 모드)
            hid_process = subprocess.Popen(
                [bt_hid_path, "-m", target_device['mac']],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False  # 바이너리 모드로 통신
            )
            
            # 프로세스가 시작되었는지 확인
            if hid_process.poll() is not None:
                stderr = hid_process.stderr.read().decode('utf-8')
                print(f"HID 프로세스 시작 실패: {stderr}")
                return None
            
            print("HID 출력이 초기화되었습니다.")
            time.sleep(0.5)  # 초기화를 위한 짧은 대기 시간
            return hid_process
            
        except Exception as e:
            print(f"HID 출력 설정 오류: {e}")
            return None
    
    def _process_hid_event(self, event, hid_process, mouse_state):
        """HID 이벤트 처리 및 전송
        
        Args:
            event (evdev.InputEvent): 입력 이벤트
            hid_process (subprocess.Popen): HID 출력 프로세스
            mouse_state (dict): 현재 마우스 상태
        """
        try:
            from evdev import categorize, ecodes
            
            # 이미 프로세스가 종료되었으면 무시
            if hid_process.poll() is not None:
                return
            
            # 이벤트 유형에 따른 처리
            if event.type == ecodes.EV_REL:  # 마우스 이동
                # X, Y 이동값 처리 (값을 -127~127 범위로 제한)
                if event.code == ecodes.REL_X:
                    mouse_state['x'] = max(-127, min(127, event.value))
                elif event.code == ecodes.REL_Y:
                    mouse_state['y'] = max(-127, min(127, event.value))
                elif event.code == ecodes.REL_WHEEL:
                    mouse_state['wheel'] = max(-127, min(127, event.value))
                    
            elif event.type == ecodes.EV_KEY:  # 마우스 버튼
                if event.code == ecodes.BTN_LEFT:
                    if event.value:  # 버튼 누름
                        mouse_state['buttons'] |= 0x01  # 첫 번째 비트 설정
                    else:  # 버튼 해제
                        mouse_state['buttons'] &= ~0x01  # 첫 번째 비트 해제
                        
                elif event.code == ecodes.BTN_RIGHT:
                    if event.value:  # 버튼 누름
                        mouse_state['buttons'] |= 0x02  # 두 번째 비트 설정
                    else:  # 버튼 해제
                        mouse_state['buttons'] &= ~0x02  # 두 번째 비트 해제
                        
                elif event.code == ecodes.BTN_MIDDLE:
                    if event.value:  # 버튼 누름
                        mouse_state['buttons'] |= 0x04  # 세 번째 비트 설정
                    else:  # 버튼 해제
                        mouse_state['buttons'] &= ~0x04  # 세 번째 비트 해제
            
            # HID 보고서 작성 및 전송
            # 마우스 HID 보고서 형식: [버튼, X, Y, 휠]
            hid_report = bytes([
                mouse_state['buttons'] & 0xFF,
                mouse_state['x'] & 0xFF,
                mouse_state['y'] & 0xFF,
                mouse_state['wheel'] & 0xFF
            ])
            
            # HID 보고서를 프로세스로 전송
            hid_process.stdin.write(hid_report)
            hid_process.stdin.flush()
            
            # 이동값 재설정 (지속적인 이동 방지)
            mouse_state['x'] = 0
            mouse_state['y'] = 0
            mouse_state['wheel'] = 0
            
        except BrokenPipeError:
            print("HID 프로세스 통신 오류 (파이프 끊김)")
        except Exception as e:
            print(f"이벤트 처리 오류: {e}")
    
    def _run_simulation_mode(self, source_device, target_device, stop_event):
        """시뮬레이션 모드로 릴레이 실행
        
        Args:
            source_device (dict): 수신 장치 정보
            target_device (dict): 송신 장치 정보
            stop_event (threading.Event): 중지 이벤트
        """
        source_mac = source_device['mac']
        target_mac = target_device['mac']
        
        print(f"장치 {source_device['name']} ({source_mac})에서 {target_device['name']} ({target_mac})로 데이터 릴레이 시작(시뮬레이션 모드)...")
            
        # 시뮬레이션 모드 메시지
        print("시뮬레이션 모드로 실행 중입니다.")
        print("실제 데이터 전송을 위해서는 추가 라이브러리 설치가 필요합니다.")
        print("필요한 패키지: python3-evdev")
        
        # 로그에 기록
        with open('blehub.log', 'a') as f:
            f.write(f"릴레이 시작(시뮬레이션 모드): {source_device['name']} -> {target_device['name']}\n")
        
        # 릴레이 루프
        dots = 0
        while not stop_event.is_set():
            # 진행 표시 애니메이션
            if dots >= 10:
                print("\r" + " " * 20, end="")
                print(f"\r릴레이 중: {source_device['name']} -> {target_device['name']}", end="")
                dots = 0
            print(".", end="", flush=True)
            dots += 1
            
            # 1초마다 체크
            for _ in range(10):
                if stop_event.wait(0.1):  # 0.1초 간격으로 중지 신호 확인
                    break
                
        print(f"\n장치 {source_device['name']}에서 {target_device['name']}로의 릴레이가 중지되었습니다.")
    
    def _cleanup_processes(self):
        """실행 중인 프로세스 정리"""
        # 현재는 특별히 정리할 프로세스가 없음
        pass
    
    def cleanup(self):
        """정리 작업 수행"""
        if self.running:
            self.stop_relay()
    
    def signal_handler(self, sig, frame):
        """신호 처리기"""
        print("\n신호 수신: 정리 중...")
        self.cleanup()
        # sys.exit(0)  # 필요하면 주석 해제 