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
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'
ADVERTISING_IFACE = 'org.bluez.LEAdvertisement1'

GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE = 'org.bluez.GattCharacteristic1'
GATT_DESC_IFACE = 'org.bluez.GattDescriptor1'

# HID 서비스 및 특성 UUID
HID_SERVICE_UUID = '1812'
HID_INFORMATION_UUID = '2A4A'
REPORT_MAP_UUID = '2A4B'
PROTOCOL_MODE_UUID = '2A4E'
REPORT_UUID = '2A4D'
REPORT_REFERENCE_UUID = '2908'

# Report Map 데이터 (키보드 + 마우스)
REPORT_MAP = bytes.fromhex(
    # Report ID 1 : 키보드, 8바이트
    # Report ID 2 : 마우스, 4바이트
    '05010906A101850175019508050719E029E7150025018102'
    '950175088103950575010508190129059102950175039103'
    '95067508150026FF000507190029FF8100C0'
    '05010902A10185020901A100050919012903150025017501'
    '9503810275059501810105010930093109381581257F7508'
    '95038106C0C0'
)

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

class Application(dbus.service.Object):
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
        self.add_service(HIDService(bus, 0))

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
    def __init__(self, bus, index, uuid, flags, service):
        self.path = service.path + '/char' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.service = service
        self.flags = flags
        self.descriptors = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            GATT_CHRC_IFACE: {
                'Service': self.service.get_path(),
                'UUID': self.uuid,
                'Flags': self.flags,
                'Descriptors': dbus.Array(
                    self.get_descriptor_paths(),
                    signature='o')
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
        print('Default ReadValue called, returning error')
        raise NotSupportedException()

    @dbus.service.method(GATT_CHRC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print('Default WriteValue called, returning error')
        raise NotSupportedException()

    @dbus.service.method(GATT_CHRC_IFACE)
    def StartNotify(self):
        print('Default StartNotify called, returning error')
        raise NotSupportedException()

    @dbus.service.method(GATT_CHRC_IFACE)
    def StopNotify(self):
        print('Default StopNotify called, returning error')
        raise NotSupportedException()

    @dbus.service.signal(DBUS_PROP_IFACE,
                        signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass

class Descriptor(dbus.service.Object):
    def __init__(self, bus, index, uuid, flags, characteristic):
        self.path = characteristic.path + '/desc' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.flags = flags
        self.chrc = characteristic
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            GATT_DESC_IFACE: {
                'Characteristic': self.chrc.get_path(),
                'UUID': self.uuid,
                'Flags': self.flags,
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
        print('Default ReadValue called, returning error')
        raise NotSupportedException()

    @dbus.service.method(GATT_DESC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print('Default WriteValue called, returning error')
        raise NotSupportedException()

class HIDService(Service):
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, HID_SERVICE_UUID, True)
        
        # HID Information 특성
        self.add_characteristic(HIDInformationCharacteristic(bus, 0, self))
        
        # Report Map 특성
        self.add_characteristic(ReportMapCharacteristic(bus, 1, self))
        
        # Protocol Mode 특성
        self.add_characteristic(ProtocolModeCharacteristic(bus, 2, self))
        
        # Keyboard Report 특성 (ID 1)
        self.kbd_report = ReportCharacteristic(bus, 3, self, 1, 'input')
        self.add_characteristic(self.kbd_report)
        
        # Mouse Report 특성 (ID 2)
        self.mouse_report = ReportCharacteristic(bus, 4, self, 2, 'input')
        self.add_characteristic(self.mouse_report)

class HIDInformationCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            HID_INFORMATION_UUID,
            ['read'],
            service)

    def ReadValue(self, options):
        # HID 정보 (버전 1.11, 국가 코드 0x00, 플래그 0x01)
        return [
            dbus.Byte(0x11),  # HID 버전 (1.11)
            dbus.Byte(0x01),
            dbus.Byte(0x00),  # 국가 코드
            dbus.Byte(0x01)   # 플래그 (원격 웨이크 지원)
        ]

class ReportMapCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            REPORT_MAP_UUID,
            ['read'],
            service)

    def ReadValue(self, options):
        return [dbus.Byte(b) for b in REPORT_MAP]

class ProtocolModeCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            PROTOCOL_MODE_UUID,
            ['read', 'write-without-response'],
            service)
        self.value = [dbus.Byte(0x01)]  # Report Protocol

    def ReadValue(self, options):
        return self.value

    def WriteValue(self, value, options):
        if len(value) != 1:
            raise InvalidValueLengthException()
        if value[0] not in [0x00, 0x01]:  # Boot Protocol or Report Protocol
            raise FailedException("0x80")
        self.value = value

class ReportCharacteristic(Characteristic):
    def __init__(self, bus, index, service, report_id, report_type):
        Characteristic.__init__(
            self, bus, index,
            REPORT_UUID,
            ['read', 'notify'],
            service)
        
        self.report_id = report_id
        self.report_type = report_type
        self.notifying = False
        
        # Report Reference 디스크립터 추가
        self.add_descriptor(ReportReferenceDescriptor(bus, 0, self))

    def ReadValue(self, options):
        # 기본 리포트 값 (모든 키/버튼 해제)
        if self.report_id == 1:  # 키보드
            return [dbus.Byte(0)] * 8
        else:  # 마우스
            return [dbus.Byte(0)] * 4

    def StartNotify(self):
        if self.notifying:
            return
        self.notifying = True

        # —★ 첫 빈 리포트 전송 ★—
        if self.report_id == 1:          # 키보드 8B
            empty = bytes([1, 0,0,0,0,0,0,0])
        else:                            # 마우스 4B
            empty = bytes([2, 0, 0, 0])
        self.PropertiesChanged(
            GATT_CHRC_IFACE,
            {'Value': dbus.Array(empty, signature='y')},
            []
        )

        # (선택) 2 초마다 keep‑alive 0 리포트
        GLib.timeout_add_seconds(2, self._keep_alive)
    
    def _keep_alive(self):
        if not self.notifying:
            return False  # stop callback
        zero = b'\x01\x00\x00\x00\x00\x00\x00\x00' if self.report_id == 1 else b'\x02\x00\x00\x00'
        self.PropertiesChanged(GATT_CHRC_IFACE,
                               {'Value': dbus.Array(zero, signature='y')}, [])
        return True  # continue

    def StopNotify(self):
        if not self.notifying:
            print('Not notifying, nothing to do')
            return
        self.notifying = False

class ReportReferenceDescriptor(Descriptor):
    def __init__(self, bus, index, characteristic):
        Descriptor.__init__(
            self, bus, index,
            REPORT_REFERENCE_UUID,
            ['read'],
            characteristic)
        self.chrc = characteristic

    def ReadValue(self, options):
        # Report ID와 Report Type 반환
        return [
            dbus.Byte(self.chrc.report_id),
            dbus.Byte(1 if self.chrc.report_type == 'input' else 
                      2 if self.chrc.report_type == 'output' else 3)
        ]

def register_app_cb():
    print('GATT application registered')

def register_app_error_cb(error):
    print('Failed to register application: ' + str(error))
    mainloop.quit()

def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                             DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()

    for o, props in objects.items():
        if GATT_MANAGER_IFACE in props.keys():
            return o

    return None

class Advertisement(dbus.service.Object):
    PATH_BASE = '/org/bluez/example/advertisement'

    def __init__(self, bus, index):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_properties(self):
        return {
            'org.bluez.LEAdvertisement1': {
                'Type':        'peripheral',
                'ServiceUUIDs':['1812'],
                'Appearance':  dbus.UInt16(0x03C2),
                'LocalName':   'test',
                'Discoverable': dbus.Boolean(True)
            }
        }

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        return self.get_properties()['org.bluez.LEAdvertisement1']

    @dbus.service.method('org.bluez.LEAdvertisement1')
    def Release(self):
        print('Advertisement released')

def register_ad_cb():
    print('✓ LE Advertisement registered')

def register_ad_error_cb(error):
    print('× Failed to register advertisement:', error)
    mainloop.quit()

def main():
    global mainloop

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()

    adapter = find_adapter(bus)
    if not adapter:
        print('GattManager1 interface not found')
        return

    service_manager = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE_NAME, adapter),
        GATT_MANAGER_IFACE)

    app = Application(bus)

    mainloop = GLib.MainLoop()

    print('Registering GATT application...')

    service_manager.RegisterApplication(app.get_path(), {},
                                     reply_handler=register_app_cb,
                                     error_handler=register_app_error_cb)

    # 광고 매니저 인터페이스
    ad_mgr = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE_NAME, adapter),
        'org.bluez.LEAdvertisingManager1')

    advert = Advertisement(bus, 0)
    ad_mgr.RegisterAdvertisement(
        advert.get_path(), {},  # 빈 dict 옵션
        reply_handler=register_ad_cb,
        error_handler=register_ad_error_cb)


    mainloop.run()

if __name__ == '__main__':
    main() 