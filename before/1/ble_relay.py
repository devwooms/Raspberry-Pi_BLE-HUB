#!/usr/bin/env python3
import subprocess
import os
import time
import signal
import sys
import logging
from pathlib import Path

# 자체 모듈 import
from config_manager import load_config
from bluetooth_scan import check_device_connected, connect_device, disconnect_device, disconnect_all_devices, get_connected_devices

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ble_relay.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BLE-Relay")

class BLERelay:
    def __init__(self, recv_adapter, send_adapter, target_device):
        """
        BLE 릴레이 초기화
        :param recv_adapter: 수신용 어댑터 MAC 주소
        :param send_adapter: 송신용 어댑터 MAC 주소
        :param target_device: 타겟 기기(마우스 등) MAC 주소
        """
        self.recv_adapter = recv_adapter
        self.send_adapter = send_adapter
        self.target_device = target_device
        self.running = False
        self.setup_complete = False
        self.cleanup_on_exit = True  # 종료 시 연결 해제 여부
        
        # HCI 이름 매핑 (hci0, hci1 등)
        self.recv_hci = self._get_hci_name(recv_adapter)
        self.send_hci = self._get_hci_name(send_adapter)
        
        logger.info(f"릴레이 초기화: 수신={recv_adapter}({self.recv_hci}), 송신={send_adapter}({self.send_hci}), 타겟={target_device}")
    
    def _get_hci_name(self, adapter_addr):
        """MAC 주소로부터 hciX 이름 찾기"""
        try:
            result = subprocess.run(["hciconfig", "-a"], capture_output=True, text=True)
            lines = result.stdout.strip().split("\n")
            
            current_hci = None
            for line in lines:
                line = line.strip()
                if line and not line.startswith("\t"):
                    current_hci = line.split(":", 1)[0]
                elif "BD Address:" in line and adapter_addr.lower() in line.lower():
                    return current_hci
            
            logger.warning(f"어댑터 {adapter_addr}에 대한 HCI 이름을 찾을 수 없습니다")
            return None
        except Exception as e:
            logger.error(f"HCI 이름 찾기 오류: {e}")
            return None
    
    def setup(self):
        """어댑터 및 연결 설정"""
        try:
            # 수신 어댑터 설정
            logger.info(f"수신 어댑터({self.recv_adapter}) 설정 중...")
            self._setup_adapter(self.recv_adapter, is_receiver=True)
            
            # 송신 어댑터 설정
            logger.info(f"송신 어댑터({self.send_adapter}) 설정 중...")
            self._setup_adapter(self.send_adapter, is_receiver=False)
            
            # 타겟 기기가 연결되어 있는지 확인
            if not check_device_connected(self.recv_adapter, self.target_device, use_hci=True):
                logger.info(f"타겟 기기({self.target_device})가 연결되어 있지 않아 연결 시도 중...")
                if not connect_device(self.recv_adapter, self.target_device, use_hci=True):
                    logger.error("타겟 기기 연결 실패")
                    return False
            
            self.setup_complete = True
            logger.info("BLE 릴레이 설정 완료")
            return True
        except Exception as e:
            logger.error(f"설정 오류: {e}")
            return False
    
    def _setup_adapter(self, adapter_addr, is_receiver=True):
        """어댑터 설정"""
        # 어댑터 선택
        subprocess.run(["bluetoothctl", "select", adapter_addr], capture_output=True)
        
        # 필요한 설정 (예: discoverable, pairable 등)
        if is_receiver:
            # 수신용 설정
            subprocess.run(["bluetoothctl", "discoverable", "on"], capture_output=True)
            subprocess.run(["bluetoothctl", "pairable", "on"], capture_output=True)
        else:
            # 송신용 설정
            subprocess.run(["bluetoothctl", "discoverable", "off"], capture_output=True)
            # 송신용 추가 설정...
    
    def start(self):
        """릴레이 시작"""
        if not self.setup_complete and not self.setup():
            logger.error("릴레이 설정이 완료되지 않아 시작할 수 없습니다.")
            return False
        
        logger.info("BLE 릴레이 시작 중...")
        self.running = True
        
        try:
            # HID 프록시 설정 - 실제 구현은 디바이스와 커널 지원에 따라 달라질 수 있음
            # 여기서는 데모 목적으로 로깅만 수행
            
            # 테스트용 무한 루프
            while self.running:
                # 주기적으로 연결 상태 확인
                if not check_device_connected(self.recv_adapter, self.target_device, use_hci=True):
                    logger.warning("타겟 기기 연결이 끊어졌습니다. 재연결 시도 중...")
                    connect_device(self.recv_adapter, self.target_device, use_hci=True)
                
                # 실제 구현에서는 여기서 HID 이벤트를 수신하고 전달하는 로직이 필요
                # 예: evdev나 bluez를 사용한 이벤트 처리
                
                # 로그 테스트용
                logger.info("릴레이 동작 중...")
                time.sleep(10)  # 실제 구현에서는 이벤트 기반으로 동작
                
        except KeyboardInterrupt:
            logger.info("사용자에 의해 중단됨")
        except Exception as e:
            logger.error(f"릴레이 실행 중 오류: {e}")
        finally:
            self.stop()
        
        return True
    
    def stop(self):
        """릴레이 중지"""
        logger.info("BLE 릴레이 중지 중...")
        self.running = False
        
        # 종료 시 블루투스 연결 해제
        if self.cleanup_on_exit:
            try:
                logger.info("종료 시 블루투스 연결 해제 옵션이 활성화되어 있습니다.")
                
                # 특정 타겟 기기 연결 해제
                if self.target_device:
                    logger.info(f"타겟 기기({self.target_device}) 연결 해제 중...")
                    if disconnect_device(self.recv_adapter, self.target_device, use_hci=True):
                        logger.info(f"타겟 기기({self.target_device}) 연결 해제 성공")
                    else:
                        logger.warning(f"타겟 기기({self.target_device}) 연결 해제 실패")
                
                # 수신 어댑터에 연결된 모든 기기 연결 해제 (선택 사항)
                logger.info(f"수신 어댑터({self.recv_adapter})에 연결된 모든 기기 연결 해제 중...")
                if disconnect_all_devices(self.recv_adapter, use_hci=True):
                    logger.info(f"수신 어댑터({self.recv_adapter}) 연결 해제 성공")
                else:
                    logger.warning(f"일부 기기 연결 해제 실패")
                
                # 송신 어댑터에 연결된 모든 기기 연결 해제 (선택 사항)
                logger.info(f"송신 어댑터({self.send_adapter})에 연결된 모든 기기 연결 해제 중...")
                disconnect_all_devices(self.send_adapter, use_hci=True)
            except Exception as e:
                logger.error(f"연결 해제 중 오류: {e}")
        
        logger.info("BLE 릴레이 중지 완료")

def run_as_daemon():
    """데몬으로 실행"""
    # PID 파일 확인
    pid_file = Path("ble_relay.pid")
    
    if pid_file.exists():
        with open(pid_file, 'r') as f:
            old_pid = int(f.read().strip())
        
        # 이미 실행 중인지 확인
        try:
            os.kill(old_pid, 0)  # 프로세스 상태 확인
            logger.error(f"BLE 릴레이가 이미 실행 중입니다 (PID: {old_pid})")
            return False
        except OSError:
            # 프로세스가 존재하지 않음
            logger.info(f"이전 PID 파일이 존재하지만 프로세스({old_pid})는 실행 중이 아닙니다.")
    
    # 설정 로드
    config = load_config()
    if not config:
        logger.error("설정을 로드할 수 없습니다. 먼저 main.py를 실행하여 설정을 생성하세요.")
        return False
    
    # 데몬 프로세스 생성
    pid = os.fork()
    
    if pid < 0:
        logger.error("데몬 생성 실패")
        return False
    
    if pid > 0:
        # 부모 프로세스는 종료
        logger.info(f"BLE 릴레이 데몬이 PID {pid}로 시작되었습니다.")
        with open(pid_file, 'w') as f:
            f.write(str(pid))
        return True
    
    # 자식 프로세스 계속 실행
    
    # 세션 리더가 됨
    os.setsid()
    
    # 작업 디렉토리 변경
    os.chdir('/')
    
    # 표준 파일 디스크립터 리디렉션
    sys.stdout.flush()
    sys.stderr.flush()
    
    with open('/dev/null', 'r') as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    
    with open('/dev/null', 'a+') as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
    
    with open('/dev/null', 'a+') as f:
        os.dup2(f.fileno(), sys.stderr.fileno())
    
    # 릴레이 시작
    relay = BLERelay(
        config["recv_adapter"],
        config["send_adapter"],
        config["target_device"]
    )
    
    # 종료 핸들러
    def handle_signal(signum, frame):
        logger.info(f"신호 {signum} 수신됨, 릴레이 종료 중...")
        relay.stop()
        if pid_file.exists():
            pid_file.unlink()
        sys.exit(0)
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    
    # 릴레이 실행
    relay.start()
    return True

if __name__ == "__main__":
    # 명령행 인수 처리
    if len(sys.argv) > 1:
        if sys.argv[1] == "start":
            run_as_daemon()
        elif sys.argv[1] == "stop":
            # PID 파일에서 PID 읽기
            pid_file = Path("ble_relay.pid")
            if pid_file.exists():
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                try:
                    os.kill(pid, signal.SIGTERM)
                    logger.info(f"BLE 릴레이 데몬(PID: {pid})에 종료 신호를 보냈습니다.")
                except OSError as e:
                    logger.error(f"데몬 종료 오류: {e}")
            else:
                logger.error("PID 파일이 존재하지 않습니다. 릴레이가 실행 중이 아닙니다.")
        else:
            print("사용법: ble_relay.py [start|stop]")
    else:
        # 직접 실행 (포그라운드)
        config = load_config()
        if config:
            relay = BLERelay(
                config["recv_adapter"],
                config["send_adapter"],
                config["target_device"]
            )
            relay.start()
        else:
            logger.error("설정을 로드할 수 없습니다. 먼저 main.py를 실행하여 설정을 생성하세요.") 