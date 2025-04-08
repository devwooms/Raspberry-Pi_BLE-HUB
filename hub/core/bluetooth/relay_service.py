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
            
            # HID 전송 방식 선택: 1. bt-hid-device 2. DBus 직접 사용 3. 시뮬레이션
            # 1. 먼저 bt-hid-device 도구 시도
            hid_output_process = self._setup_hid_output(target_device)
            
            # 2. bt-hid-device 실패 시 DBus 직접 사용 시도
            dbus_hid = None
            if not hid_output_process:
                print("bt-hid-device 도구 초기화 실패. DBus 직접 사용 시도...")
                dbus_hid = self._setup_dbus_hid(target_device)
                
                if not dbus_hid:
                    print("DBus HID 초기화 실패. 시뮬레이션 모드로 실행합니다.")
                    self._run_simulation_mode(source_device, target_device, stop_event)
                    return
            
            # 로그에 기록
            with open('blehub.log', 'a') as f:
                if hid_output_process:
                    f.write(f"HID 릴레이 시작 (bt-hid-device): {source_device['name']} -> {target_device['name']} (장치: {input_device_path})\n")
                else:
                    f.write(f"HID 릴레이 시작 (DBus): {source_device['name']} -> {target_device['name']} (장치: {input_device_path})\n")
            
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
                                if hid_output_process:
                                    # bt-hid-device로 HID 이벤트 전송
                                    self._process_hid_event(event, hid_output_process, mouse_state)
                                elif dbus_hid:
                                    # DBus로 HID 이벤트 전송
                                    self._process_dbus_hid_event(event, dbus_hid, mouse_state)
                                
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
            
            # DBus HID 정리
            if dbus_hid:
                try:
                    # DBus 리소스 정리 (필요한 경우)
                    print("DBus HID 연결 종료")
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
            # bt-hid-device 경로 자동 검색
            bt_hid_device_paths = [
                "/usr/local/bin/bt-hid-device",
                "/usr/bin/bt-hid-device",
                os.path.expanduser("~/P4wnP1_aloa/bluetooth/bt_hid_device/build/bt-hid-device"),
                # 상대 경로도 확인
                "./bt-hid-device",
                "../tools/bt-hid-device",
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tools/bt-hid-device")
            ]
            
            bt_hid_path = None
            for path in bt_hid_device_paths:
                if os.path.exists(path):
                    bt_hid_path = path
                    print(f"bt-hid-device 도구를 찾았습니다: {path}")
                    break
            
            if not bt_hid_path:
                # 시스템 경로에서 찾기 시도
                try:
                    which_result = subprocess.run(
                        ["which", "bt-hid-device"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=2
                    )
                    if which_result.returncode == 0 and which_result.stdout.strip():
                        bt_hid_path = which_result.stdout.strip()
                        print(f"시스템 경로에서 bt-hid-device를 찾았습니다: {bt_hid_path}")
                except Exception:
                    pass
                
            if not bt_hid_path:
                print("bt-hid-device 도구를 찾을 수 없습니다. 다음 명령어로 설치하세요:")
                print("sudo apt install git cmake build-essential libbluetooth-dev libdbus-1-dev")
                print("git clone https://github.com/mame82/P4wnP1_aloa.git")
                print("cd P4wnP1_aloa/bluetooth/bt_hid_device")
                print("mkdir build && cd build")
                print("cmake ..")
                print("make")
                print("sudo cp bt-hid-device /usr/local/bin/")
                return None
            
            # HID 출력 프로세스 설정
            print(f"HID 출력 초기화: {target_device['name']} ({target_device['mac']})")
            
            # 연결 상태 확인
            info_cmd = ["bluetoothctl", "info", target_device['mac']]
            info_result = subprocess.run(
                info_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            ).stdout
            
            if "Connected: no" in info_result:
                print(f"장치 {target_device['name']} ({target_device['mac']})가 연결되어 있지 않습니다. 연결 시도 중...")
                connect_cmd = ["bluetoothctl", "connect", target_device['mac']]
                connect_result = subprocess.run(
                    connect_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10
                )
                print(f"연결 결과: {connect_result.stdout}")
                # 연결 후 잠시 대기
                time.sleep(2)
            
            # 실행 권한 확인 및 부여
            if not os.access(bt_hid_path, os.X_OK):
                print(f"{bt_hid_path}에 실행 권한이 없습니다. 권한 부여 중...")
                try:
                    subprocess.run(
                        ["chmod", "+x", bt_hid_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                except Exception as e:
                    print(f"실행 권한 부여 실패: {e}")
                    print("다음 명령어를 수동으로 실행해보세요: chmod +x " + bt_hid_path)
            
            # 그래도 실행 권한이 없으면 sudo로 시도
            use_sudo = False
            if not os.access(bt_hid_path, os.X_OK):
                print("sudo를 사용하여 도구를 실행합니다.")
                use_sudo = True
            
            # bt-hid-device 실행 (마우스 모드)
            cmd = []
            if use_sudo:
                cmd.append("sudo")
            cmd.extend([bt_hid_path, "-m", target_device['mac']])
            
            print(f"실행 명령어: {' '.join(cmd)}")
            hid_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False  # 바이너리 모드로 통신
            )
            
            # 실행 결과 확인을 위한 짧은 시간 대기
            time.sleep(1)
            
            # 프로세스가 여전히 실행 중인지 확인
            if hid_process.poll() is not None:
                stdout = hid_process.stdout.read().decode('utf-8') if hid_process.stdout else ""
                stderr = hid_process.stderr.read().decode('utf-8') if hid_process.stderr else ""
                print(f"HID 프로세스 시작 실패. 종료 코드: {hid_process.returncode}")
                if stdout:
                    print(f"표준 출력: {stdout}")
                if stderr:
                    print(f"오류 출력: {stderr}")
                
                # DBus 권한 오류 확인
                if "org.freedesktop.DBus.Error.AccessDenied" in stderr:
                    print("DBus 접근 권한이 없습니다. 다음 명령어로 권한을 부여하세요:")
                    print("sudo usermod -aG bluetooth $USER")
                    print("또는 sudo로 프로그램을 실행하세요.")
                
                return None
            
            print("HID 출력이 성공적으로 초기화되었습니다.")
            print("마우스 데이터가 송신 장치로 전송됩니다.")
            
            # 테스트 데이터 전송 (가벼운 마우스 이동)
            test_report = bytes([0, 5, 0, 0])  # 오른쪽으로 5픽셀 이동
            try:
                hid_process.stdin.write(test_report)
                hid_process.stdin.flush()
                print("테스트 HID 데이터 전송 성공")
            except Exception as e:
                print(f"테스트 HID 데이터 전송 실패: {e}")
            
            time.sleep(0.5)  # 초기화를 위한 짧은 대기 시간
            return hid_process
            
        except Exception as e:
            print(f"HID 출력 설정 오류: {e}")
            return None
    
    def _setup_dbus_hid(self, target_device):
        """DBus를 사용한 HID 출력 설정
        
        Args:
            target_device (dict): 송신 장치 정보
            
        Returns:
            dict: DBus HID 정보 (성공 시) 또는 None (실패 시)
        """
        try:
            # 필요한 패키지 가져오기
            import dbus
            import dbus.service
            import dbus.mainloop.glib
            
            print("DBus를 사용한 HID 출력 초기화 중...")
            print(f"대상 장치: {target_device['name']} ({target_device['mac']})")
            
            # D-Bus 초기화
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            bus = dbus.SystemBus()
            
            # BlueZ 객체 경로 찾기
            adapter_path = None
            device_path = None
            
            # BlueZ 버전 확인
            bluez_obj = bus.get_object('org.bluez', '/')
            manager = dbus.Interface(bluez_obj, 'org.freedesktop.DBus.ObjectManager')
            objects = manager.GetManagedObjects()
            
            # 어댑터 및 장치 경로 찾기
            for path, interfaces in objects.items():
                if 'org.bluez.Adapter1' in interfaces:
                    adapter_path = path
                    print(f"블루투스 어댑터 경로: {adapter_path}")
                
                if 'org.bluez.Device1' in interfaces:
                    device_props = interfaces['org.bluez.Device1']
                    if 'Address' in device_props and device_props['Address'] == target_device['mac']:
                        device_path = path
                        print(f"장치 경로: {device_path}")
            
            if not adapter_path:
                print("블루투스 어댑터를 찾을 수 없습니다.")
                return None
                
            if not device_path:
                print(f"장치 {target_device['mac']}의 D-Bus 경로를 찾을 수 없습니다.")
                return None
            
            # 장치 인터페이스 가져오기
            device_obj = bus.get_object('org.bluez', device_path)
            device_iface = dbus.Interface(device_obj, 'org.bluez.Device1')
            
            # 연결 상태 확인
            device_props = dbus.Interface(device_obj, 'org.freedesktop.DBus.Properties')
            if not device_props.Get('org.bluez.Device1', 'Connected'):
                print("장치가 연결되어 있지 않습니다. 연결 시도 중...")
                device_iface.Connect()
                print("장치 연결됨")
            else:
                print("장치가 이미 연결되어 있습니다.")
            
            # HID 서비스 찾기
            hid_uuid = '00001124-0000-1000-8000-00805f9b34fb'  # HID UUID
            
            # 연결을 위한 정보 반환
            return {
                'bus': bus,
                'device_path': device_path,
                'device_obj': device_obj,
                'device_iface': device_iface,
                'adapter_path': adapter_path
            }
            
        except ImportError as e:
            print(f"DBus 라이브러리를 가져올 수 없습니다: {e}")
            print("다음 명령어로 필요한 패키지를 설치하세요:")
            print("sudo apt-get install python3-dbus python3-gi")
            return None
        except Exception as e:
            print(f"DBus HID 설정 오류: {e}")
            import traceback
            traceback.print_exc()
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
                print("HID 프로세스가 종료되었습니다. 이벤트 처리를 중단합니다.")
                return
            
            # 디버깅을 위한 이벤트 정보 출력 (필요 시 주석 해제)
            # print(f"이벤트: type={event.type}, code={event.code}, value={event.value}")
            
            # 이벤트 유형에 따른 처리
            if event.type == ecodes.EV_REL:  # 마우스 이동
                # X, Y 이동값 처리 (값을 -127~127 범위로 제한)
                if event.code == ecodes.REL_X:
                    # 이동 값 범위 조정
                    adjusted_value = max(-127, min(127, event.value))
                    mouse_state['x'] = adjusted_value
                    if abs(adjusted_value) > 10:
                        print(f"X축 이동: {adjusted_value}")
                elif event.code == ecodes.REL_Y:
                    adjusted_value = max(-127, min(127, event.value))
                    mouse_state['y'] = adjusted_value
                    if abs(adjusted_value) > 10:
                        print(f"Y축 이동: {adjusted_value}")
                elif event.code == ecodes.REL_WHEEL:
                    adjusted_value = max(-127, min(127, event.value))
                    mouse_state['wheel'] = adjusted_value
                    print(f"휠 스크롤: {adjusted_value}")
                    
            elif event.type == ecodes.EV_KEY:  # 마우스 버튼
                if event.code == ecodes.BTN_LEFT:
                    if event.value:  # 버튼 누름
                        mouse_state['buttons'] |= 0x01  # 첫 번째 비트 설정
                        print("왼쪽 버튼 누름")
                    else:  # 버튼 해제
                        mouse_state['buttons'] &= ~0x01  # 첫 번째 비트 해제
                        print("왼쪽 버튼 해제")
                        
                elif event.code == ecodes.BTN_RIGHT:
                    if event.value:  # 버튼 누름
                        mouse_state['buttons'] |= 0x02  # 두 번째 비트 설정
                        print("오른쪽 버튼 누름")
                    else:  # 버튼 해제
                        mouse_state['buttons'] &= ~0x02  # 두 번째 비트 해제
                        print("오른쪽 버튼 해제")
                        
                elif event.code == ecodes.BTN_MIDDLE:
                    if event.value:  # 버튼 누름
                        mouse_state['buttons'] |= 0x04  # 세 번째 비트 설정
                        print("가운데 버튼 누름")
                    else:  # 버튼 해제
                        mouse_state['buttons'] &= ~0x04  # 세 번째 비트 해제
                        print("가운데 버튼 해제")
                else:
                    # 기타 버튼 이벤트
                    print(f"기타 버튼 이벤트: code={event.code}, value={event.value}")
            
            # 값이 모두 0이면 보고서를 보내지 않음
            if (mouse_state['buttons'] == 0 and 
                mouse_state['x'] == 0 and 
                mouse_state['y'] == 0 and 
                mouse_state['wheel'] == 0):
                return
            
            # 마우스 값 디버깅 (움직임이 있을 때만 표시)
            if mouse_state['x'] != 0 or mouse_state['y'] != 0 or mouse_state['wheel'] != 0:
                print(f"← → X:{mouse_state['x']:4d} | Y:{mouse_state['y']:4d} | 휠:{mouse_state['wheel']:4d} | 버튼:{bin(mouse_state['buttons'])[2:]:8s}")
            
            # HID 보고서 작성 및 전송
            # 마우스 HID 보고서 형식: [버튼, X, Y, 휠]
            # 값이 음수인 경우를 처리하기 위해 비트 마스킹 사용
            hid_report = bytes([
                mouse_state['buttons'] & 0xFF,
                mouse_state['x'] & 0xFF,
                mouse_state['y'] & 0xFF,
                mouse_state['wheel'] & 0xFF
            ])
            
            # HID 보고서를 프로세스로 전송
            try:
                hid_process.stdin.write(hid_report)
                hid_process.stdin.flush()
            except BrokenPipeError:
                print("HID 프로세스 통신 오류 (파이프 끊김)")
                return
            except OSError as e:
                print(f"OS 오류: {e}")
                return
            
            # 이동값 재설정 (지속적인 이동 방지)
            mouse_state['x'] = 0
            mouse_state['y'] = 0
            mouse_state['wheel'] = 0
            
        except BrokenPipeError:
            print("HID 프로세스 통신 오류 (파이프 끊김)")
        except Exception as e:
            print(f"이벤트 처리 오류: {e}")
            import traceback
            traceback.print_exc()
    
    def _process_dbus_hid_event(self, event, dbus_hid, mouse_state):
        """DBus를 사용한 HID 이벤트 처리 및 전송
        
        Args:
            event (evdev.InputEvent): 입력 이벤트
            dbus_hid (dict): DBus HID 정보
            mouse_state (dict): 현재 마우스 상태
        """
        try:
            from evdev import categorize, ecodes
            import dbus
            
            # 이벤트 유형에 따른 처리
            if event.type == ecodes.EV_REL:  # 마우스 이동
                # X, Y 이동값 처리 (값을 -127~127 범위로 제한)
                if event.code == ecodes.REL_X:
                    adjusted_value = max(-127, min(127, event.value))
                    mouse_state['x'] = adjusted_value
                    if abs(adjusted_value) > 10:
                        print(f"X축 이동: {adjusted_value}")
                elif event.code == ecodes.REL_Y:
                    adjusted_value = max(-127, min(127, event.value))
                    mouse_state['y'] = adjusted_value
                    if abs(adjusted_value) > 10:
                        print(f"Y축 이동: {adjusted_value}")
                elif event.code == ecodes.REL_WHEEL:
                    adjusted_value = max(-127, min(127, event.value))
                    mouse_state['wheel'] = adjusted_value
                    print(f"휠 스크롤: {adjusted_value}")
                    
            elif event.type == ecodes.EV_KEY:  # 마우스 버튼
                if event.code == ecodes.BTN_LEFT:
                    if event.value:  # 버튼 누름
                        mouse_state['buttons'] |= 0x01  # 첫 번째 비트 설정
                        print("왼쪽 버튼 누름")
                    else:  # 버튼 해제
                        mouse_state['buttons'] &= ~0x01  # 첫 번째 비트 해제
                        print("왼쪽 버튼 해제")
                        
                elif event.code == ecodes.BTN_RIGHT:
                    if event.value:  # 버튼 누름
                        mouse_state['buttons'] |= 0x02  # 두 번째 비트 설정
                        print("오른쪽 버튼 누름")
                    else:  # 버튼 해제
                        mouse_state['buttons'] &= ~0x02  # 두 번째 비트 해제
                        print("오른쪽 버튼 해제")
                        
                elif event.code == ecodes.BTN_MIDDLE:
                    if event.value:  # 버튼 누름
                        mouse_state['buttons'] |= 0x04  # 세 번째 비트 설정
                        print("가운데 버튼 누름")
                    else:  # 버튼 해제
                        mouse_state['buttons'] &= ~0x04  # 세 번째 비트 해제
                        print("가운데 버튼 해제")
                else:
                    # 기타 버튼 이벤트
                    print(f"기타 버튼 이벤트: code={event.code}, value={event.value}")
            
            # 값이 모두 0이면 보고서를 보내지 않음
            if (mouse_state['buttons'] == 0 and 
                mouse_state['x'] == 0 and 
                mouse_state['y'] == 0 and 
                mouse_state['wheel'] == 0):
                return
            
            # 마우스 값 디버깅 (움직임이 있을 때만 표시)
            if mouse_state['x'] != 0 or mouse_state['y'] != 0 or mouse_state['wheel'] != 0:
                print(f"← → X:{mouse_state['x']:4d} | Y:{mouse_state['y']:4d} | 휠:{mouse_state['wheel']:4d} | 버튼:{bin(mouse_state['buttons'])[2:]:8s}")
            
            # D-Bus를 통한 HID 데이터 전송 시도
            # 주의: BlueZ의 HID 프로필 인터페이스는 비공개(private) API이며, 
            # 이 코드는 개념적인 것으로 실제 BluezZ 구현에 따라 달라질 수 있습니다.
            try:
                device_obj = dbus_hid['device_obj']
                
                # HID 인터페이스 존재 여부 확인 및 접근 (실제 BlueZ 구현에 따라 다를 수 있음)
                print("DBus로 HID 데이터 전송 시도 (실험적 기능)")
                
                # 이 부분은 BlueZ 구현에 따라 실제 작동하지 않을 수 있으며,
                # 정확한 구현은 BlueZ 소스 코드를 참조해야 함
                
                # 실제 DBus 전송 코드는 여기에 구현
                
            except Exception as e:
                print(f"DBus HID 전송 오류: {e}")
            
            # 이동값 재설정 (지속적인 이동 방지)
            mouse_state['x'] = 0
            mouse_state['y'] = 0
            mouse_state['wheel'] = 0
            
        except Exception as e:
            print(f"DBus 이벤트 처리 오류: {e}")
            import traceback
            traceback.print_exc()
    
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