#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later

import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

import array
from gi.repository import GLib
import sys

mainloop = None

BLUEZ_SERVICE_NAME = 'org.bluez'
GATT_MANAGER_IFACE = 'org.bluez.GattManager1'
DBUS_OM_IFACE =      'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE =    'org.freedesktop.DBus.Properties'

GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE =    'org.bluez.GattCharacteristic1'
GATT_DESC_IFACE =    'org.bluez.GattDescriptor1'

# LE Advertising Manager 인터페이스 추가
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
LE_ADVERTISEMENT_IFACE = 'org.bluez.LEAdvertisement1'

# --- 표준 블루투스 SIG UUID ---
HID_SERVICE_UUID = '00001812-0000-1000-8000-00805f9b34fb' # HID 서비스
HID_INFO_UUID = '00002a4a-0000-1000-8000-00805f9b34fb' # HID 정보
REPORT_MAP_UUID = '00002a4b-0000-1000-8000-00805f9b34fb' # 리포트 맵
HID_CONTROL_POINT_UUID = '00002a4c-0000-1000-8000-00805f9b34fb' # HID 제어 포인트
REPORT_UUID = '00002a4d-0000-1000-8000-00805f9b34fb' # 리포트 (입력/출력/특징)
PROTOCOL_MODE_UUID = '00002a4e-0000-1000-8000-00805f9b34fb' # 프로토콜 모드
PNP_ID_UUID = '00002a50-0000-1000-8000-00805f9b34fb' # PnP ID (Device ID 서비스 내)

DEVICE_ID_SERVICE_UUID = '0000180a-0000-1000-8000-00805f9b34fb' # 장치 정보 서비스 (PnP ID 용)

# --- HID 상수 ---
REPORT_PROTOCOL_MODE = 0x01 # 기본값은 Report 프로토콜
HID_APPEARANCE = 0x03C2 # 일반 HID / 마우스 장치 외형

# --- 예외 클래스 (example.py 에서 복사) ---
class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.freedesktop.DBus.Error.InvalidArgs'

class NotSupportedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotSupported'

class NotPermittedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotPermitted'

class InvalidValueLengthException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.InvalidValueLength'

class FailedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.Failed'


# --- 기본 클래스 (example.py 기반으로 수정) ---
class Application(dbus.service.Object):
    """
    org.bluez.GattApplication1 인터페이스 구현
    """
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
        self.add_service(HIDService(bus, 0))
        self.add_service(DeviceInformationService(bus, 1)) # 장치 정보 서비스 추가

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        print('GetManagedObjects')

        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
                descs = chrc.get_descriptors()
                for desc in descs:
                    response[desc.get_path()] = desc.get_properties()

        return response


class Service(dbus.service.Object):
    """
    org.bluez.GattService1 인터페이스 구현
    """
    PATH_BASE = '/org/bluez/example/service'

    def __init__(self, bus, index, uuid, primary):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.uuid = uuid
        self.primary = primary
        self.characteristics = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
                GATT_SERVICE_IFACE: {
                        'UUID': self.uuid,
                        'Primary': self.primary,
                        'Characteristics': dbus.Array(
                                self.get_characteristic_paths(),
                                signature='o')
                }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    def get_characteristic_paths(self):
        result = []
        for chrc in self.characteristics:
            result.append(chrc.get_path())
        return result

    def get_characteristics(self):
        return self.characteristics

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_SERVICE_IFACE:
            raise InvalidArgsException()

        return self.get_properties()[GATT_SERVICE_IFACE]


class Characteristic(dbus.service.Object):
    """
    org.bluez.GattCharacteristic1 인터페이스 구현
    """
    def __init__(self, bus, index, uuid, flags, service):
        self.path = service.path + '/char' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.service = service
        self.flags = flags
        self.descriptors = []
        # 값 속성 초기화
        self._value = []
        self.notifying = False # 알림(notify) 활성화 상태
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
                GATT_CHRC_IFACE: {
                        'Service': self.service.get_path(),
                        'UUID': self.uuid,
                        'Flags': self.flags,
                        'Descriptors': dbus.Array(
                                self.get_descriptor_paths(),
                                signature='o'),
                        # 읽기 가능(read) 플래그가 있으면 현재 값 노출
                        'Value': dbus.Array(self.ReadValue({}), signature='y') if 'read' in self.flags else dbus.Array([], signature='y')
                }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_descriptor(self, descriptor):
        self.descriptors.append(descriptor)

    def get_descriptor_paths(self):
        result = []
        for desc in self.descriptors:
            result.append(desc.get_path())
        return result

    def get_descriptors(self):
        return self.descriptors

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_CHRC_IFACE:
            raise InvalidArgsException()

        return self.get_properties()[GATT_CHRC_IFACE]

    @dbus.service.method(GATT_CHRC_IFACE,
                        in_signature='a{sv}',
                        out_signature='ay')
    def ReadValue(self, options):
        print(f'기본 ReadValue 호출됨: {self.uuid}')
        # 기본적으로 현재 값 반환
        return self._value

    @dbus.service.method(GATT_CHRC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print(f'기본 WriteValue 호출됨: {self.uuid}: {value}')
        # 기본적으로 쓰여진 값 저장
        self._value = value
        # 필요 시 PropertiesChanged 시그널을 발생시킬 수 있지만, 보통은 명시적으로 처리함

    @dbus.service.method(GATT_CHRC_IFACE)
    def StartNotify(self):
        if self.notifying:
            print(f'특성 {self.uuid}은(는) 이미 알림 중입니다.')
            return
        print(f'{self.uuid}에 대한 알림 시작')
        self.notifying = True

    @dbus.service.method(GATT_CHRC_IFACE)
    def StopNotify(self):
        if not self.notifying:
            print(f'특성 {self.uuid}은(는) 알림 중이 아닙니다.')
            return
        print(f'{self.uuid}에 대한 알림 중지')
        self.notifying = False

    @dbus.service.signal(DBUS_PROP_IFACE,
                         signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass

    def update_value(self, new_value):
        """특성 값을 업데이트하고, 활성화된 경우 알림을 보내는 헬퍼 메서드."""
        if self._value == new_value:
            return # 변경 없음
        print(f"{self.uuid} 값 업데이트 중: {new_value}")
        self._value = new_value
        # 'Value' 속성이 변경되었음을 알림
        props_changed = {'Value': dbus.Array(self._value, signature='y')}
        self.PropertiesChanged(GATT_CHRC_IFACE, props_changed, [])


class Descriptor(dbus.service.Object):
    """
    org.bluez.GattDescriptor1 인터페이스 구현
    """
    def __init__(self, bus, index, uuid, flags, characteristic):
        self.path = characteristic.path + '/desc' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.flags = flags
        self.chrc = characteristic
        # 값 속성 초기화
        self._value = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
                GATT_DESC_IFACE: {
                        'Characteristic': self.chrc.get_path(),
                        'UUID': self.uuid,
                        'Flags': self.flags,
                         # 읽기 가능(read) 플래그가 있으면 현재 값 노출
                        'Value': dbus.Array(self.ReadValue({}), signature='y') if 'read' in self.flags else dbus.Array([], signature='y')
                }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_DESC_IFACE:
            raise InvalidArgsException()

        return self.get_properties()[GATT_DESC_IFACE]

    @dbus.service.method(GATT_DESC_IFACE,
                        in_signature='a{sv}',
                        out_signature='ay')
    def ReadValue(self, options):
        print(f'기본 ReadValue 호출됨 (디스크립터): {self.uuid}')
        return self._value

    @dbus.service.method(GATT_DESC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print(f'기본 WriteValue 호출됨 (디스크립터): {self.uuid}: {value}')
        self._value = value


# --- HID 리포트 디스크립터 (마우스 전용) ---
# 이 부분은 복잡합니다. 지금은 단순화된 디스크립터를 사용합니다.
# 실제 디스크립터는 훨씬 길고 상세할 것입니다.
# HID 사양 및 온라인 예제를 참조하세요.
# 리포트 ID 1: 마우스 (버튼 바이트 1개, X 2바이트, Y 2바이트, 휠 1바이트)
HID_REPORT_MAP = [
    0x05, 0x01,        # Usage Page (Generic Desktop Ctrls)
    0x09, 0x02,        # Usage (Mouse)
    0xA1, 0x01,        # Collection (Application)
    0x85, 0x01,        #   Report ID (1)
    0x09, 0x01,        #   Usage (Pointer)
    0xA1, 0x00,        #   Collection (Physical)
    0x05, 0x09,        #     Usage Page (Button)
    0x19, 0x01,        #     Usage Minimum (0x01) ; Button 1 (Left)
    0x29, 0x05,        #     Usage Maximum (0x05) ; Button 5 (Forward)
    0x15, 0x00,        #     Logical Minimum (0)
    0x25, 0x01,        #     Logical Maximum (1)
    0x95, 0x05,        #     Report Count (5) ; Buttons 1-5
    0x75, 0x01,        #     Report Size (1) ; 1 bit per button
    0x81, 0x02,        #     Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position) ; Button bits
    0x95, 0x01,        #     Report Count (1) ; 1 report
    0x75, 0x03,        #     Report Size (3) ; Pad to 1 byte (5 bits used)
    0x81, 0x01,        #     Input (Const,Array,Abs,No Wrap,Linear,Preferred State,No Null Position) ; Padding
    0x05, 0x01,        #     Usage Page (Generic Desktop Ctrls)
    0x09, 0x30,        #     Usage (X)
    0x09, 0x31,        #     Usage (Y)
    0x16, 0x01, 0xF8,  #     Logical Minimum (-2047) ; More precise movement
    0x26, 0xFF, 0x07,  #     Logical Maximum (2047)
    0x75, 0x10,        #     Report Size (16) ; 16 bits (2 bytes) for X and Y
    0x95, 0x02,        #     Report Count (2) ; X, Y
    0x81, 0x06,        #     Input (Data,Var,Rel,No Wrap,Linear,Preferred State,No Null Position) ; Relative X, Y
    0x09, 0x38,        #     Usage (Wheel)
    0x15, 0x81,        #     Logical Minimum (-127)
    0x25, 0x7F,        #     Logical Maximum (127)
    0x75, 0x08,        #     Report Size (8) ; 8 bits for wheel
    0x95, 0x01,        #     Report Count (1)
    0x81, 0x06,        #     Input (Data,Var,Rel,No Wrap,Linear,Preferred State,No Null Position) ; Relative wheel scroll
    0xC0,              #   End Collection (Physical)
    0xC0               # End Collection (Application)
]


# --- HID 서비스 구현 ---
class HIDService(Service):
    """
    Human Interface Device(HID) 서비스 구현.
    """
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, HID_SERVICE_UUID, True)
        # 프로토콜 모드 특성 (필수)
        self.protocol_mode_char = ProtocolModeCharacteristic(bus, 0, self)
        self.add_characteristic(self.protocol_mode_char)
        # HID 정보 특성 (필수)
        self.add_characteristic(HIDInformationCharacteristic(bus, 1, self))
        # 리포트 맵 특성 (필수)
        self.add_characteristic(ReportMapCharacteristic(bus, 2, self))
        # 입력 리포트 특성 (마우스)
        self.mouse_input_char = InputReportCharacteristic(bus, 3, self, 1)    # 마우스용 리포트 ID 1
        # 마우스 입력 리포트 특성에 Report Reference Descriptor 추가
        self.mouse_input_char.add_descriptor(ReportReferenceDescriptor(bus, 1, self.mouse_input_char, 1, ReportReferenceDescriptor.INPUT_REPORT))
        self.add_characteristic(self.mouse_input_char)
        # HID 제어 포인트 특성 (필수)
        self.add_characteristic(HIDControlPointCharacteristic(bus, 4, self))


class ProtocolModeCharacteristic(Characteristic):
    """
    프로토콜 모드 특성. Boot Protocol과 Report Protocol 간 전환을 허용합니다.
    기본적으로 Report Protocol을 사용합니다.
    """
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            PROTOCOL_MODE_UUID,
            # 쓰기 가능(write-without-response)은 사양상 선택 사항이지만 종종 구현됨
            ['read', 'write-without-response'],
            service)
        # Report Protocol 모드로 초기화
        self._value = [dbus.Byte(REPORT_PROTOCOL_MODE)]

    def ReadValue(self, options):
        print(f"프로토콜 모드 읽기: {self._value}")
        return self._value

    def WriteValue(self, value, options):
        # 0x00 (Boot) 및 0x01 (Report) 모드만 유효함
        if len(value) != 1 or value[0] not in [0x00, 0x01]:
            # WriteWithoutResponse의 경우 유효하지 않은 쓰기를 조용히 무시
            print(f"잘못된 프로토콜 모드 쓰기 무시: {value}")
            return
        print(f"프로토콜 모드 쓰기: {value}")
        self._value = value
        # 모드가 변경될 경우 잠재적으로 작업 트리거 (보통 호스트에서 처리)


class HIDInformationCharacteristic(Characteristic):
    """
    HID 정보 특성. 기본적인 HID 메타데이터를 제공합니다.
    """
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            HID_INFO_UUID,
            ['read'],
            service)
        # bcdHID (예: 1.11), bCountryCode (0 = 지역화되지 않음), Flags (일반 연결)
        # 버전 1.11, 지역화 안됨, 일반 연결 플래그
        self._value = [dbus.Byte(0x11), dbus.Byte(0x01), dbus.Byte(0x00), dbus.Byte(0x01)]

    def ReadValue(self, options):
        return self._value


class ReportMapCharacteristic(Characteristic):
    """
    리포트 맵 특성. HID 리포트 디스크립터를 포함합니다.
    """
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            REPORT_MAP_UUID,
            ['read'],
            service)
        # HID_REPORT_MAP 리스트를 바이트 배열로 변환하여 값 설정
        self._value = [dbus.Byte(b) for b in HID_REPORT_MAP]

    def ReadValue(self, options):
        return self._value


class InputReportCharacteristic(Characteristic):
    """
    입력 리포트 특성. 마우스 데이터를 호스트로 보내는 데 사용됩니다.
    알림(Notification)을 위해 CCCD(Client Characteristic Configuration Descriptor)가 필요합니다.
    """
    def __init__(self, bus, index, service, report_id):
        self.report_id = report_id
        self.simulation_timer_id = None # 마우스 시뮬레이션 타이머 ID
        self.mouse_move_direction = 1 # 마우스 이동 방향: 1 (오른쪽 아래), -1 (왼쪽 위)
        Characteristic.__init__(
            self, bus, index,
            REPORT_UUID,
            # 쓰기(Write)는 선택 사항이며, 일반적으로 입력 리포트에는 필요하지 않음
            ['read', 'notify'],
            service)
        # CCCD (Client Characteristic Configuration Descriptor) 추가
        # CCCD는 알림(Notify) 기능을 클라이언트가 제어할 수 있게 함
        self.add_descriptor(ClientCharCfgDescriptor(bus, 0, self)) # 디스크립터 인덱스 0

        # 마우스: 버튼(1), X(2), Y(2), 휠(1) = 6 바이트
        self._value = [dbus.Byte(report_id)] + [dbus.Byte(0x00)] * 6

    def send_report(self, report_data):
        """특성 값을 업데이트하고 활성화된 경우 알림을 보냅니다."""
        # 데이터 앞에 리포트 ID 추가
        full_report = [dbus.Byte(self.report_id)] + [dbus.Byte(b) for b in report_data]
        print(f"리포트 ID {self.report_id} 전송 중: {full_report}")
        # update_value 메서드가 PropertiesChanged 시그널 처리
        self.update_value(full_report)

    def ReadValue(self, options):
        # 사양에 따르면 입력 리포트 읽기는 선택 사항이지만, 필요한 경우 마지막 전송 값 반환
        return self._value

    # 리포트 ID를 출력하기 위해 Start/Stop Notify 재정의
    def StartNotify(self):
        if self.notifying:
            print(f'입력 리포트 ID {self.report_id}은(는) 이미 알림 중입니다.')
            return
        print(f'입력 리포트 ID {self.report_id}에 대한 알림 시작')
        self.notifying = True

        # 마우스 리포트 특성에 대해서만 마우스 시뮬레이션 시작
        if self.report_id == 1 and self.simulation_timer_id is None:
            print("마우스 이동 시뮬레이션 시작 중...")
            # 3초(3000ms)마다 _simulate_mouse_movement 호출하는 타이머 시작
            self.simulation_timer_id = GLib.timeout_add(3000, self._simulate_mouse_movement)

    def StopNotify(self):
        if not self.notifying:
            print(f'입력 리포트 ID {self.report_id}은(는) 알림 중이 아닙니다.')
            return
        print(f'입력 리포트 ID {self.report_id}에 대한 알림 중지')
        self.notifying = False

        # 실행 중인 마우스 시뮬레이션 중지
        if self.report_id == 1 and self.simulation_timer_id is not None:
            print("마우스 이동 시뮬레이션 중지 중...")
            GLib.source_remove(self.simulation_timer_id)
            self.simulation_timer_id = None

    def _simulate_mouse_movement(self):
        """마우스 이동을 시뮬레이션하기 위해 타이머에 의해 호출됩니다."""
        if not self.notifying:
            # 타이머가 올바르게 관리되면 발생하지 않아야 하지만, 예방 차원
            self.simulation_timer_id = None
            return False # 타이머 중지

        # 현재 방향에 따라 이동량 계산
        move_delta = 10 * self.mouse_move_direction
        print(f"마우스 이동 시뮬레이션 ({move_delta}, {move_delta})")
        # 리포트 형식: 버튼(1), dX(2), dY(2), 휠(1)
        report = [
            0, # 버튼 누르지 않음
            # dX (리틀 엔디안)
            move_delta & 0xFF, (move_delta >> 8) & 0xFF,
            # dY (리틀 엔디안)
            move_delta & 0xFF, (move_delta >> 8) & 0xFF,
            0 # 휠 움직임 없음
        ]
        self.send_report(report)

        # 다음 이동을 위해 방향 반전
        self.mouse_move_direction *= -1

        # 1초 대기
        GLib.timeout_add(1000, lambda: None)

        return True # 타이머 계속 실행


class HIDControlPointCharacteristic(Characteristic):
    """
    HID 제어 포인트 특성. Suspend/Exit Suspend와 같은 명령에 사용됩니다.
    """
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            HID_CONTROL_POINT_UUID,
            ['write-without-response'], # 응답 없는 쓰기
            service)
        self._value = [] # 쓰기 전용, 값은 일시적인 명령임

    def WriteValue(self, value, options):
        if not value:
            return # 빈 쓰기 무시
        command = value[0]
        print(f"HID 제어 포인트 쓰기: 명령 {command}")
        if command == 0x00: # Suspend (일시 중지)
            print("Suspend 명령 수신됨")
            # TODO: 필요 시 일시 중지 로직 구현 (예: 리포트 전송 중지)
        elif command == 0x01: # Exit Suspend (일시 중지 해제)
            print("Exit Suspend 명령 수신됨")
            # TODO: 재개 로직 구현
        else:
            print(f"알 수 없는 HID 제어 포인트 명령: {command}")
        # WriteWithoutResponse의 경우 응답 필요 없음


# --- 표준 디스크립터 구현 ---
class ClientCharCfgDescriptor(Descriptor):
    """
    CCCD (Client Characteristic Configuration Descriptor) 구현.
    클라이언트(예: PC, 폰)가 알림(Notification)을 활성화/비활성화할 수 있도록 합니다.
    """
    CCCD_UUID = '00002902-0000-1000-8000-00805f9b34fb'

    def __init__(self, bus, index, characteristic):
        Descriptor.__init__(
            self, bus, index,
            self.CCCD_UUID,
            ['read', 'write'], # 읽기 및 쓰기 가능
            characteristic)
        # 기본값: 알림/Indication 비활성화 (0x0000)
        self._value = [dbus.Byte(0x00), dbus.Byte(0x00)]

    def ReadValue(self, options):
        print(f"CCCD 읽기 ({self.chrc.uuid}): {self._value}")
        return self._value

    def WriteValue(self, value, options):
        if len(value) != 2:
            raise InvalidValueLengthException()

        print(f"CCCD 쓰기 ({self.chrc.uuid}): {value}")
        self._value = value
        # 첫 번째 바이트의 첫 번째 비트(알림 비트) 확인
        if value[0] & 0x01:
            # 알림이 활성화되었지만 아직 시작되지 않은 경우
            if not self.chrc.notifying:
                self.chrc.StartNotify()
        else:
            # 알림이 비활성화되었지만 실행 중인 경우
            if self.chrc.notifying:
                self.chrc.StopNotify()
        # Indication (두 번째 비트)은 이 예제에서 사용되지 않음


class ReportReferenceDescriptor(Descriptor):
    """
    리포트 참조 디스크립터 구현.
    리포트 ID와 타입(Input/Output/Feature)을 리포트 특성과 연결합니다.
    """
    REPORT_REF_UUID = '00002908-0000-1000-8000-00805f9b34fb'

    # 리포트 타입 상수
    INPUT_REPORT = 0x01  # 입력 리포트
    OUTPUT_REPORT = 0x02 # 출력 리포트
    FEATURE_REPORT = 0x03# 특징 리포트

    def __init__(self, bus, index, characteristic, report_id, report_type):
        Descriptor.__init__(
            self, bus, index,
            self.REPORT_REF_UUID,
            ['read'], # 읽기 전용
            characteristic)
        # 값은 [Report ID, Report Type] 형태의 바이트 배열
        self._value = [dbus.Byte(report_id), dbus.Byte(report_type)]

    def ReadValue(self, options):
        return self._value


# --- 장치 정보 서비스 구현 ---
class DeviceInformationService(Service):
    """
    장치 정보 서비스 구현.
    제조사 이름, 모델 번호, PnP ID 등을 제공합니다.
    """
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, DEVICE_ID_SERVICE_UUID, True)
        # PnP ID 특성 추가 (필수)
        self.add_characteristic(PnPIdCharacteristic(bus, 0, self))
        # 선택적으로 제조사 이름, 모델 번호 특성 추가 가능


class PnPIdCharacteristic(Characteristic):
    """
    PnP ID 특성. 장치 공급업체/제품을 식별합니다.
    """
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            PNP_ID_UUID,
            ['read'], # 읽기 전용
            service)
        # Vendor ID Source (0x02 = USB Implementer's Forum)
        # Vendor ID (예: 0x05AC = Apple, 0x046D = Logitech) - 테스트/일반 ID 사용
        # Product ID (공급업체 할당)
        # Product Version (공급업체 할당)
        self._value = [
            dbus.Byte(0x02), # Vendor ID Source: USB
            dbus.Byte(0x57), dbus.Byte(0x04), # Vendor ID: 0x0457 (예시)
            dbus.Byte(0x01), dbus.Byte(0x00), # Product ID: 0x0001 (예시)
            dbus.Byte(0x00), dbus.Byte(0x01)  # Product Version: 0x0100 (1.0)
        ]

    def ReadValue(self, options):
        return self._value


# --- 광고 클래스 ---
class Advertisement(dbus.service.Object):
    PATH_BASE = '/org/bluez/example/advertisement'

    def __init__(self, bus, index, advertising_type):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.ad_type = advertising_type # 광고 타입 ('peripheral' 등)
        self.service_uuids = None      # 서비스 UUID 목록
        self.manufacturer_data = None  # 제조사 데이터
        self.solicit_uuids = None      # Solicited 서비스 UUID 목록
        self.service_data = None       # 서비스 데이터
        self.local_name = None         # 로컬 장치 이름
        self.include_tx_power = None   # 전송 전력 레벨 포함 여부
        self.data = None               # 추가 광고 데이터
        self.appearance = None         # 장치 외형 (Appearance) 추가
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        properties = dict()
        properties['Type'] = self.ad_type
        if self.service_uuids is not None:
            properties['ServiceUUIDs'] = dbus.Array(self.service_uuids,
                                                    signature='s')
        if self.solicit_uuids is not None:
            properties['SolicitUUIDs'] = dbus.Array(self.solicit_uuids,
                                                    signature='s')
        if self.manufacturer_data is not None:
            properties['ManufacturerData'] = dbus.Dictionary(
                self.manufacturer_data, signature='qv') # q: uint16, v: variant<ay>
        if self.service_data is not None:
            properties['ServiceData'] = dbus.Dictionary(self.service_data,
                                                        signature='sv') # s: string (UUID), v: variant<ay>
        if self.local_name is not None:
            properties['LocalName'] = dbus.String(self.local_name)
        if self.include_tx_power is not None:
            properties['IncludeTxPower'] = dbus.Boolean(self.include_tx_power)
        if self.data is not None:
            # raw 데이터 (type: byte, value: variant<byte[]>)
            properties['Data'] = dbus.Dictionary(self.data, signature='yv')
        # 외형(Appearance) 속성 추가
        if self.appearance is not None:
            properties['Appearance'] = dbus.UInt16(self.appearance)
        return {LE_ADVERTISEMENT_IFACE: properties}

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != LE_ADVERTISEMENT_IFACE:
            raise InvalidArgsException()
        return self.get_properties()[LE_ADVERTISEMENT_IFACE]

    @dbus.service.method(LE_ADVERTISEMENT_IFACE,
                         in_signature='',
                         out_signature='')
    def Release(self):
        # 광고가 해제될 때 호출됨
        print(f'{self.path}: 해제됨!')


class TestAdvertisement(Advertisement):
    """테스트용 광고 설정 클래스"""
    def __init__(self, bus, index):
        # 'peripheral' 타입 광고 설정
        Advertisement.__init__(self, bus, index, 'peripheral')
        # HID 및 장치 정보 서비스 UUID 광고
        self.service_uuids = [HID_SERVICE_UUID, DEVICE_ID_SERVICE_UUID]
        # 장치 이름 "test"로 설정
        self.local_name = "test"
        # 장치 외형을 마우스로 설정
        self.appearance = HID_APPEARANCE
        # 전송 전력 정보 포함
        self.include_tx_power = True
        # self.manufacturer_data = ... # 선택 사항: 제조사 특정 데이터 추가 가능


# --- 메인 애플리케이션 로직 (example.py 기반으로 수정) ---

# GATT 애플리케이션 등록 성공 콜백
def register_app_cb():
    print('GATT 애플리케이션 등록됨')

# GATT 애플리케이션 등록 실패 콜백
def register_app_error_cb(error):
    print('애플리케이션 등록 실패: ' + str(error))
    mainloop.quit()

# 광고 등록 성공 콜백
def register_ad_cb():
    print('광고 등록됨')

# 광고 등록 실패 콜백
def register_ad_error_cb(error):
    print('광고 등록 실패: ' + str(error))
    mainloop.quit()

# 사용 가능한 블루투스 어댑터 찾기
def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                               DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()

    for o, props in objects.items():
        # GATT Manager 인터페이스를 가진 어댑터 반환
        if GATT_MANAGER_IFACE in props.keys():
            return o
    return None


# --- HID 리포트 전송 함수 ---
# 이 함수들은 주 애플리케이션 로직에서 GPIO 이벤트, 사용자 입력 등에 따라 호출됨

app_instance = None # 애플리케이션 인스턴스 전역 참조

def send_mouse_report(buttons, dx, dy, wheel):
    """마우스 리포트를 전송합니다."""
    global app_instance
    if not app_instance: return
    # HID 서비스 인스턴스 찾기
    hid_service = next((s for s in app_instance.services if isinstance(s, HIDService)), None)
    # HID 서비스가 있고 마우스 입력 특성이 알림 중인 경우
    if hid_service and hid_service.mouse_input_char.notifying:
        # 형식: 버튼(1 바이트), dX(2 바이트, 리틀 엔디안), dY(2 바이트, 리틀 엔디안), 휠(1 바이트)
        report = [
            buttons & 0xFF,
            dx & 0xFF, (dx >> 8) & 0xFF, # dX
            dy & 0xFF, (dy >> 8) & 0xFF, # dY
            wheel & 0xFF # Wheel
        ]
        hid_service.mouse_input_char.send_report(report)


def main():
    global mainloop
    global app_instance

    # 기본 GLib 메인 루프 설정
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    # 시스템 버스 가져오기
    bus = dbus.SystemBus()

    # 블루투스 어댑터 찾기
    adapter = find_adapter(bus)
    if not adapter:
        print('GattManager1 인터페이스를 찾을 수 없습니다.')
        return

    # GATT 서비스 매니저 인터페이스 가져오기
    service_manager = dbus.Interface(
            bus.get_object(BLUEZ_SERVICE_NAME, adapter),
            GATT_MANAGER_IFACE)

    # LE 광고 매니저 인터페이스 가져오기
    ad_manager = dbus.Interface(
            bus.get_object(BLUEZ_SERVICE_NAME, adapter),
            LE_ADVERTISING_MANAGER_IFACE)

    # 애플리케이션 인스턴스 생성 및 저장
    app_instance = Application(bus)

    # GLib 메인 루프 생성
    mainloop = GLib.MainLoop()

    # 테스트 광고 생성
    test_advertisement = TestAdvertisement(bus, 0)

    print('GATT 애플리케이션 등록 중...')

    try:
        # GATT 애플리케이션 등록
        service_manager.RegisterApplication(app_instance.get_path(), {},
                                        reply_handler=register_app_cb,
                                        error_handler=register_app_error_cb)
    except dbus.exceptions.DBusException as e:
        print(f"애플리케이션 등록 오류: {e}")
        # 이미 등록된 경우 처리
        if "Already Exists" in str(e):
             print("애플리케이션이 이미 등록되었을 수 있습니다. 먼저 등록 해제하거나 블루투스를 재시작하세요.")
             # 필요 시 여기서 등록 해제 시도 가능
             # unregister_app(service_manager, app_instance.get_path())
        mainloop.quit()
        return

    # 광고 등록
    print('광고 등록 중...')
    ad_manager.RegisterAdvertisement(test_advertisement.get_path(), {},
                                     reply_handler=register_ad_cb,
                                     error_handler=register_ad_error_cb)

    # 시뮬레이션은 이제 클라이언트가 마우스 알림을 활성화하면 자동으로 시작됨

    try:
        # 메인 루프 실행 (이벤트 대기)
        mainloop.run()
    except KeyboardInterrupt:
        print("KeyboardInterrupt 감지, 종료합니다.")
    finally:
        # 선택 사항: 종료 시 애플리케이션 및 광고 등록 해제?
        # try:
        #     print("광고 등록 해제 중...")
        #     ad_manager.UnregisterAdvertisement(test_advertisement.get_path())
        # except Exception as e:
        #     print(f"광고 등록 해제 오류: {e}")
        # try:
        #     print("GATT 애플리케이션 등록 해제 중...")
        #     # 어댑터 경로와 앱 경로 필요
        #     # unregister_app(service_manager, app_instance.get_path()) # 이 함수는 정의 필요
        # except Exception as e:
        #     print(f"애플리케이션 등록 해제 오류: {e}")
        # 일반적으로 bluetoothd가 정리하도록 두는 것이 괜찮음
        pass

if __name__ == '__main__':
    main()
