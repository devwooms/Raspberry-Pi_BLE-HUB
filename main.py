import dbus, dbus.exceptions, dbus.mainloop.glib, dbus.service
from gi.repository import GLib
import threading, sys, struct
import subprocess, shlex


# D-Bus 상수
# https://www.bluez.org/
# https://github.com/bluez/bluez
BLUEZ_SERVICE = 'org.bluez'
ADAPTER_IFACE = 'org.bluez.Adapter1'                
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1' 
LE_ADVERTISEMENT_IFACE = 'org.bluez.LEAdvertisement1'    
GATT_MANAGER_IFACE = 'org.bluez.GattManager1'        
GATT_SERVICE_IFACE = 'org.bluez.GattService1'         
GATT_CHRC_IFACE = 'org.bluez.GattCharacteristic1'     
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'  
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'     

# HID 서비스 및 UUID 
# Bluetooth SIG https://www.bluetooth.com/specifications/assigned-numbers/
HID_SERVICE_UUID = '1812'       # HID(Human Interface Device) Service (마우스, 키보드, 게임패드 등등 입력장치)
REPORT_UUID = '2a4d'           # BLE 입력 데이터 전달
REPORT_MAP_UUID = '2a4b'        # HID Report Descriptor를 보낼거라는 것을 알려줌
PROTOCOL_MODE_UUID = '2a4e'     # 프로토콜 모드 (데이터 전송 방식)
HID_INFO_UUID = '2a4a'          # HID 정보 버전과 어떤 기능을 지원하는지 알려줌
HID_CONTROL_POINT_UUID = '2a4c' # 절전모드 같은 기능에 사용

# 마우스: 버튼 3개 + X + Y + 휠
# HID Descriptor Tool https://www.usb.org/document-library/hid-descriptor-tool 추가 개발 계획 X
# -> https://github.com/microsoft/hidtools
HID_REPORT_MAP = bytes([
    0x05, 0x01,  # 일반적인 입력 장치 (마우스, 키보드, 게임패드)
    0x09, 0x02,  # 마우스

    0xA1, 0x01,  # HID 데이터의 시작 (Json 같은 느낌으로 묶어야함 - 들여쓰기처럼) Application 이라는 큰 틀
    0x09, 0x01,  #   마우스 관련이라고 설정
    0xA1, 0x00,  #   물리적 입력 데이터를 나타냄 (버튼클릭, 휠클릭)
    0x05, 0x09,  #     버튼에 대한 설정
    0x19, 0x01,  #     min 버튼 1개
    0x29, 0x03,  #     max 버튼 3개 (1~3개의 버튼)
    0x15, 0x00,  #     min 버튼 눌림
    0x25, 0x01,  #     max 버튼 눌림 상태 (0~1)
    0x95, 0x03,  #     버튼이 최대 3개 이므로 3개를 보냄
    0x75, 0x01,  #     버튼 데이터 크기 1비트 (0~1)
    0x81, 0x02,  #     실제 입력: 버튼 3개 (각 1비트, 총 3비트)
    0x95, 0x01,  #     채우는 용도 추가 입력 1개 (패딩)  -  (후에 다시 이해 확인)
    0x75, 0x05,  #     채우는 용도 (5비트)  -  (후에 다시 이해 확인)
    0x81, 0x03,  #     채우는 용도 (패딩)  -  (후에 다시 이해 확인)
    0x05, 0x01,  #     마우스 이동 관련 데이터 
    0x09, 0x30,  #       마우스 이동 X 좌표
    0x09, 0x31,  #       마우스 이동 Y 좌표
    0x09, 0x38,  #       마우스 휠
    0x15, 0x81,  #       min 마우스 이동 값 1000 0001 (-127)
    0x25, 0x7F,  #       max 마우스 이동 값 0111 1111  (127)
    0x75, 0x08,  #       데이터 크기 8비트 (1바이트)
    0x95, 0x03,  #       데이터 개수 3개 (X, Y, 휠)
    0x81, 0x06,  #     입력값 3개 8비트 (마우스 이동 X, Y, 휠)
    0xC0,        #   물리적 입력 데이터 설정 끝
    0xC0         # HID 데이터 끝 Application의 끝
])

# 마우스 이동 데이터 입력 시
#      _
# 
# -         +
#
#      +

def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE, '/'), DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()
    for path, ifaces in objects.items():
        if ADAPTER_IFACE in ifaces:
            return path
    return None

# D-Bus 서비스 클래스
class Advertisement(dbus.service.Object):
    PATH_BASE = '/org/bluez/example/advertisement'

    def __init__(self, bus, index):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.ad_type = 'peripheral' # 광고 타입: 주변 장치
        self.service_uuids = [HID_SERVICE_UUID] # 광고할 서비스 UUID 목록
        self.appearance = 0x03C2  # 장치 : 일반 마우스
        self.local_name = 'Pi-BLE-Mouse' # 로컬 장치 이름
        self.discoverable = True # 검색 가능 여부
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        properties = dict()
        properties['Type'] = self.ad_type
        properties['ServiceUUIDs'] = dbus.Array(self.service_uuids, signature='s')
        properties['Appearance'] = dbus.UInt16(self.appearance)
        properties['LocalName'] = dbus.String(self.local_name)
        properties['Discoverable'] = dbus.Boolean(self.discoverable)
        return {LE_ADVERTISEMENT_IFACE: properties}

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != LE_ADVERTISEMENT_IFACE:
            raise dbus.exceptions.DBusException('유효하지 않은 인터페이스')
        return self.get_properties()[LE_ADVERTISEMENT_IFACE]

    @dbus.service.method(LE_ADVERTISEMENT_IFACE, in_signature='', out_signature='')
    def Release(self):
        print(f'{self.path} 해제됨')

class Application(dbus.service.Object):
    PATH = '/org/bluez/example/app'

    def __init__(self, bus):
        self.path = self.PATH
        dbus.service.Object.__init__(self, bus, self.path)
        self.services = []
        self.add_service(HIDService(bus, 0))
        # 필요한 경우 DeviceInformationService 추가

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        response[self.get_path()] = {} # 애플리케이션 경로 포함
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
                # 필요한 경우 디스크립터 추가
                descs = chrc.get_descriptors()
                for desc in descs:
                    response[desc.get_path()] = desc.get_properties()
        return response

class Service(dbus.service.Object):
    PATH_BASE = '/org/bluez/example/service'

    def __init__(self, bus, index, uuid, primary):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.uuid = uuid
        self.primary = primary # 기본 서비스 여부
        self.characteristics = [] # 서비스에 속한 특성 목록
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            GATT_SERVICE_IFACE: {
                'UUID': self.uuid,
                'Primary': self.primary,
                'Characteristics': dbus.Array(
                    self.get_characteristic_paths(), # 포함된 특성들의 경로 목록
                    signature='o')
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    def get_characteristic_paths(self):
        return [chrc.get_path() for chrc in self.characteristics]

    def get_characteristics(self):
        return self.characteristics

    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_SERVICE_IFACE:
             raise dbus.exceptions.DBusException('유효하지 않은 인터페이스')
        return self.get_properties()[GATT_SERVICE_IFACE]


class Characteristic(dbus.service.Object):

    def __init__(self, bus, index, uuid, flags, service):
        self.path = service.path + '/char' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.service = service # 이 특성이 속한 서비스
        self.flags = flags     # 특성 속성 플래그 (e.g., ['read', 'notify'])
        self.notifying = False # 알림 활성화 상태
        self._value = []       # 특성 값을 저장하는 내부 변수
        self.descriptors = []  # 이 특성에 속한 디스크립터 목록
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        props = {
            'Service': self.service.get_path(),
            'UUID': self.uuid,
            'Flags': dbus.Array(self.flags, signature='s')
            # 필요한 경우 디스크립터 추가
        }
        props['Descriptors'] = dbus.Array(
            self.get_descriptor_paths(), signature='o' # 포함된 디스크립터들의 경로 목록
        )
        # 읽기 가능 플래그가 있으면 'Value' 속성 포함 (GetManagedObjects 위해 필요)
        if 'read' in self.flags or 'secure-read' in self.flags:
             props['Value'] = dbus.Array(self.ReadValue({}), signature='y')
        return {GATT_CHRC_IFACE: props}


    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_descriptor(self, descriptor):
        self.descriptors.append(descriptor)

    def get_descriptor_paths(self):
        return [desc.get_path() for desc in self.descriptors]

    def get_descriptors(self):
        return self.descriptors

    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_CHRC_IFACE:
             raise dbus.exceptions.DBusException('유효하지 않은 인터페이스')
        return self.get_properties()[GATT_CHRC_IFACE]

    @dbus.service.method(GATT_CHRC_IFACE, in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        print(f'{self.uuid} 에 대한 기본 ReadValue 호출됨')
        return dbus.Array(self._value, signature='y')

    @dbus.service.method(GATT_CHRC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print(f'{self.uuid} 에 대한 기본 WriteValue 호출됨: {value}')
        self._value = bytes(value) # 바이트로 저장

    @dbus.service.method(GATT_CHRC_IFACE)
    def StartNotify(self):
        if self.notifying:
            print('이미 알림 중')
            return
        print(f'{self.uuid} 에 대한 알림 시작 중')
        self.notifying = True

    @dbus.service.method(GATT_CHRC_IFACE)
    def StopNotify(self):
        if not self.notifying:
            print('알림 중이 아님')
            return
        print(f'{self.uuid} 에 대한 알림 중지 중')
        self.notifying = False

    # 값 변경 시 알림(Notification)을 위한 시그널
    @dbus.service.signal(DBUS_PROP_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass

# --- 표준 디스크립터 구현 ---

class Descriptor(dbus.service.Object):
    def __init__(self, bus, index, uuid, flags, characteristic):
        self.path = characteristic.path + '/desc' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.flags = flags
        self.characteristic = characteristic # 이 디스크립터가 속한 특성
        self._value = [] # 디스크립터 값을 저장하는 내부 변수
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        props = {
            'Characteristic': self.characteristic.get_path(),
            'UUID': self.uuid,
            'Flags': dbus.Array(self.flags, signature='s')
        }
        # 읽기 가능 플래그가 있으면 'Value' 속성 포함
        if 'read' in self.flags or 'secure-read' in self.flags:
             props['Value'] = dbus.Array(self.ReadValue({}), signature='y')
        return { 'org.bluez.GattDescriptor1' : props } # 전체 인터페이스 이름 사용

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != 'org.bluez.GattDescriptor1':
            raise dbus.exceptions.DBusException('유효하지 않은 인터페이스')
        return self.get_properties()['org.bluez.GattDescriptor1']

    @dbus.service.method('org.bluez.GattDescriptor1', in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        print(f'디스크립터 {self.uuid} 에 대한 기본 ReadValue 호출됨')
        return dbus.Array(self._value, signature='y')

    @dbus.service.method('org.bluez.GattDescriptor1', in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print(f'디스크립터 {self.uuid} 에 대한 기본 WriteValue 호출됨: {value}')
        self._value = bytes(value)

# 클라이언트 특성 구성 디스크립터
class ClientCharCfgDescriptor(Descriptor):
    CCCD_UUID = '2902'

    def __init__(self, bus, index, characteristic):
        # CCCD는 클라이언트가 읽고 쓸 수 있어야 함
        Descriptor.__init__(
                self, bus, index,
                self.CCCD_UUID,
                ['read', 'write'], # 읽기 및 쓰기 플래그
                characteristic)
        # 기본값은 0x0000 (알림 및 표시 비활성화)
        self._value = bytes([0x00, 0x00])

    def ReadValue(self, options):
        print(f"CCCD 값 읽기: {list(self._value)}")
        return dbus.Array(self._value, signature='y')

    def WriteValue(self, value, options):
        print(f"CCCD 값 쓰기: {list(value)}")
        if len(value) != 2:
             raise dbus.exceptions.DBusException('잘못된 인수') # 또는 InvalidValueLength

        # 값 업데이트
        self._value = bytes(value)

        # 알림 비트(bit 0) 확인
        if self._value[0] & 0x01:
            print("클라이언트에 의해 알림 활성화됨")
            if not self.characteristic.notifying:
                self.characteristic.StartNotify() # 특성의 알림 시작 메소드 호출
        else:
            print("클라이언트에 의해 알림 비활성화됨")
            if self.characteristic.notifying:
                self.characteristic.StopNotify() # 특성의 알림 중지 메소드 호출

        # 표시 비트(bit 1) 확인 - 여기서는 표시(Indication)를 지원하지 않음
        if self._value[0] & 0x02:
            print("클라이언트에 의해 표시 활성화됨 (지원되지 않음, 무시)")


# --- HID 서비스 및 특성 ---

class HIDService(Service):
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, HID_SERVICE_UUID, True)
        # 필요한 특성들을 올바른 순서로 인스턴스화하고 추가
        self.protocol_mode = ProtocolModeChar(bus, 0, self)
        self.report_map = ReportMapChar(bus, 1, self)
        self.hid_info = HIDInfoChar(bus, 2, self)
        self.hid_control = HIDCtrlPoint(bus, 3, self)
        self.mouse_input = MouseInputChar(bus, 4, self) # 우리가 사용할 마우스 입력 특성

        self.add_characteristic(self.protocol_mode)
        self.add_characteristic(self.report_map)
        self.add_characteristic(self.hid_info)
        self.add_characteristic(self.hid_control)
        self.add_characteristic(self.mouse_input)


class ProtocolModeChar(Characteristic):
    def __init__(self, bus, index, service):
        # HID 사양에 따라 'read' 및 'write-without-response' 사용 (부트 프로토콜은 선택 사항)
        Characteristic.__init__(self, bus, index, PROTOCOL_MODE_UUID,
                                ['read', 'write-without-response'], service)
        self._value = [0x01] # 기본값: 리포트 프로토콜 모드

    def ReadValue(self, options):
        print("프로토콜 모드 읽기")
        return dbus.Array(self._value, signature='y')

    def WriteValue(self, value, options):
        print(f"프로토콜 모드 쓰기: {value}")
        # 기본 유효성 검사: 1 바이트, 0x00 (부트) 또는 0x01 (리포트) 기대
        if len(value) == 1 and value[0] in (0, 1):
            self._value = [value[0]]
        else:
            print("프로토콜 모드에 대한 잘못된 쓰기 무시")
        # write-without-response 에는 응답 불필요


class ReportMapChar(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, REPORT_MAP_UUID, ['read'], service)
        self._value = HID_REPORT_MAP # 리포트 맵 바이트 저장

    def ReadValue(self, options):
        print("리포트 맵 읽기")
        return dbus.Array(self._value, signature='y')


class HIDInfoChar(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, HID_INFO_UUID, ['read'], service)
        # bcdHID (예: 1.11), bCountryCode (0 = 지역화 안됨), Flags (일반 연결)
        self._value = struct.pack('<HBB', 0x0111, 0x00, 0x02) # v1.11, 국가 0, 플래그=일반

    def ReadValue(self, options):
        print("HID 정보 읽기")
        return dbus.Array(self._value, signature='y')


class HIDCtrlPoint(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, HID_CONTROL_POINT_UUID,
                                ['write-without-response'], service)
        # 이 특성은 쓰기 전용이며, 영구적인 값은 없음

    def WriteValue(self, value, options):
        # 필요한 경우 Suspend (0x00) / Exit Suspend (0x01) 처리
        print(f"HID 제어 포인트 쓰기: {value}")
        if value and value[0] == 0x00:
            print("Suspend 명령 수신 (무시됨)")
        elif value and value[0] == 0x01:
            print("Exit Suspend 명령 수신 (무시됨)")
        # 응답 불필요


class MouseInputChar(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, REPORT_UUID,
                                ['read', 'notify'], service) # 읽기 및 알림 가능 플래그
        # 초기 리포트 (버튼 없음, 움직임 없음)
        # 형식: 버튼 (1 바이트), dx (1 바이트), dy (1 바이트), 휠 (1 바이트)
        self._value = bytes([0x00, 0x00, 0x00, 0x00])
        # 알림을 허용하기 위해 CCCD 추가
        self.add_descriptor(ClientCharCfgDescriptor(bus, 0, self))

    def ReadValue(self, options):
        # 호스트가 이 값을 읽을 수 있음. 마지막 전송된 리포트 또는 0을 반환.
        print("마우스 입력 리포트 읽기 (0 반환)")
        return dbus.Array([0x00, 0x00, 0x00, 0x00], signature='y')

    def send_report(self, buttons=0, dx=0, dy=0, wheel=0):
        if not self.notifying:
            print("리포트를 보낼 수 없음, 알림 상태 아님.")
            return

        # dx, dy, wheel 값을 부호 있는 8비트 범위 [-127, 127]로 제한
        def clamp_s8(n):
            return max(-127, min(127, n))

        dx_c = clamp_s8(dx)
        dy_c = clamp_s8(dy)
        wheel_c = clamp_s8(wheel)

        # 리포트 데이터 패킹
        # buttons: 하위 3비트 사용
        # dx, dy, wheel: 부호 있는 8비트 값
        report_bytes = struct.pack('<Bbbb', buttons & 0x07, dx_c, dy_c, wheel_c)
        self._value = report_bytes # 필요한 경우 내부 값 업데이트

        print(f"리포트 전송: 버튼={buttons & 0x07}, dx={dx_c}, dy={dy_c}, 휠={wheel_c}")

        # PropertiesChanged 시그널을 통해 알림 전송
        self.PropertiesChanged(
            GATT_CHRC_IFACE,
            {'Value': dbus.Array(report_bytes, signature='y')}, # 변경된 속성 값
            [] # 무효화된 속성 없음
        )

# ---------- 메인 ----------
def main():
    # D‑Bus 초기화
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    adapter_path = find_adapter(bus)
    if not adapter_path:
        print("블루투스 어댑터를 찾을 수 없습니다.")
        sys.exit(1)
    print(f"사용 중인 어댑터: {adapter_path}")

    service_manager = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE, adapter_path), GATT_MANAGER_IFACE)
    ad_manager = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE, adapter_path), LE_ADVERTISING_MANAGER_IFACE)

    app     = Application(bus)
    advert  = Advertisement(bus, 0)
    mainloop = GLib.MainLoop()

    # BLE 등록 콜백
    def reg_app_cb():      print("GATT 애플리케이션 등록됨")
    def reg_app_err_cb(e): print(f"애플리케이션 등록 실패: {e}"); mainloop.quit()
    def reg_ad_cb():       print("광고 등록됨")
    def reg_ad_err_cb(e):  print(f"광고 등록 실패: {e}"); mainloop.quit()

    print("광고 등록 중…")
    ad_manager.RegisterAdvertisement(
        advert.get_path(), {}, reply_handler=reg_ad_cb, error_handler=reg_ad_err_cb)

    print("GATT 애플리케이션 등록 중…")
    service_manager.RegisterApplication(
        app.get_path(), {}, reply_handler=reg_app_cb, error_handler=reg_app_err_cb)

    # HID 입력 특성
    mouse_char = app.services[0].mouse_input
    if not isinstance(mouse_char, MouseInputChar):
        print("MouseInputChar 인스턴스를 찾을 수 없습니다.")
        sys.exit(1)

    # 마우스 센서 데이터를 get_mouse_sensor.c 로부터 수신하기 위한 프로세스 시작
    try:
        proc = subprocess.Popen(
            ["./get_mouse_sensor", "/dev/input/event5"],        # 필요하면 경로 수정 (마우스)
            stdout=subprocess.PIPE, stdin=subprocess.DEVNULL,
            stderr=subprocess.STDOUT, text=True, bufsize=1
        )
        print("[get_mouse_sensor] 시작됨")
    except FileNotFoundError:
        print("get_mouse_sensor 실행 파일을 찾을 수 없습니다.")
        sys.exit(1)
    except PermissionError as e:
        print(f"get_mouse_sensor 실행 권한 오류: {e}")
        sys.exit(1)

    # C → Python 한줄 파싱 스레드 
    def relay_thread():
        for line in proc.stdout:                # “dx dy wheel buttons\n”
            try:
                dx, dy, wheel, buttons = map(int, line.strip().split())
                GLib.idle_add(mouse_char.send_report,
                              buttons, dx, dy, wheel)
            except ValueError:
                continue   # 잘못된 줄 무시

    threading.Thread(target=relay_thread, daemon=True).start()

    print("BLE 마우스 준비 완료")

    # ---------- 메인 루프 및 정리 ----------
    try:
        mainloop.run()
    except KeyboardInterrupt:
        print("Ctrl+C 종료합니다.")
    finally:
        try:
            print("광고 등록 해제 중…")
            ad_manager.UnregisterAdvertisement(advert.get_path())
        except Exception as e:
            print(f"광고 등록 해제 오류: {e}")
        try:
            print("애플리케이션 등록 해제 중…")
            service_manager.UnregisterApplication(app.get_path())
        except Exception as e:
            print(f"애플리케이션 등록 해제 오류: {e}")

        if proc.poll() is None:         
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()

        print("종료됨.")


if __name__ == '__main__':
    main()
