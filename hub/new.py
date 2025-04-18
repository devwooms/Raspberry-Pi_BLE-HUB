#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BLE HID Mouse (GATT HoG Peripheral) for Raspberry Pi
author : your-name
"""

import dbus, dbus.exceptions, dbus.mainloop.glib, dbus.service
from gi.repository import GLib
import threading, sys, struct

BLUEZ      = 'org.bluez'
ADAPTER_IF = 'org.bluez.Adapter1'
LE_ADV_MGR = 'org.bluez.LEAdvertisingManager1'
ADV_IF     = 'org.bluez.LEAdvertisement1'
GATT_MGR   = 'org.bluez.GattManager1'
DBUS_OM_IF = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP  = 'org.freedesktop.DBus.Properties'

HID_UUID   = '1812'          # Human Interface Device Service
REPORT_UUID= '2a4d'
REPORT_MAP_UUID='2a4b'
PROTO_MODE_UUID='2a4e'
HID_INFO_UUID='2a4a'
HID_CP_UUID='2a4c'

# ★ HID Report Map (Boot‑Mouse: buttons + X + Y + wheel) ▼
REPORT_MAP = bytes([
    0x05,0x01, 0x09,0x02, 0xA1,0x01,       # Usage Page GD / Usage Mouse / CollectionApp
    0x09,0x01, 0xA1,0x00,                  #   Usage Pointer / Collection Phys
    0x05,0x09, 0x19,0x01, 0x29,0x03,       #     Usage Page Button / Btn1‑3
    0x15,0x00, 0x25,0x01,                  #     Logical 0‑1
    0x95,0x03, 0x75,0x01, 0x81,0x02,       #     3 bits input (buttons)
    0x95,0x01, 0x75,0x05, 0x81,0x03,       #     5 bit padding
    0x05,0x01, 0x09,0x30, 0x09,0x31, 0x09,0x38, #     X,Y,Wheel
    0x15,0x81, 0x25,0x7F,                  #     Logical ‑127..127
    0x75,0x08, 0x95,0x03, 0x81,0x06,       #     3 bytes input (rel)
    0xC0, 0xC0                             #   End / End
])

def find_adapter(bus):
    """첫 번째 hci 어댑터 경로 반환"""
    obj = bus.get_object(BLUEZ, '/')
    mngr = dbus.Interface(obj, DBUS_OM_IF)
    for path, ifaces in mngr.GetManagedObjects().items():
        if ADAPTER_IF in ifaces:
            return path
    raise RuntimeError("Bluetooth Adapter not found")

class Advertisement(dbus.service.Object):
    PATH_BASE = '/org/bluez/example/advert'
    def __init__(self, bus, index):
        self.path = f"{self.PATH_BASE}{index}"
        super().__init__(bus, self.path)
        self.bus = bus
        self.properties = {
            ADV_IF: {
                'Type':      dbus.String('peripheral'),
                'ServiceUUIDs': dbus.Array([HID_UUID], signature='s'),
                'Appearance':   dbus.UInt16(0x03C2),  # Mouse
                'LocalName':    dbus.String('Pi-BLE-Mouse'),
                'Discoverable': dbus.Boolean(True),
            }
        }

    @dbus.service.method(DBUS_PROP, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        return self.properties.get(interface, {})

    @dbus.service.method(LE_ADV_MGR, in_signature='', out_signature='')
    def Release(self): pass

class Application(dbus.service.Object):
    PATH = '/org/bluez/example/app'
    def __init__(self, bus):
        self.path = self.PATH        
        super().__init__(bus, self.path)
        self.services = [HIDService(bus, 0)]

    @dbus.service.method(DBUS_OM_IF, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        resp = { self.path: {} }
        for s in self.services:
            resp.update(s.get_managed_objects())
        return resp

class HIDService(dbus.service.Object):
    def __init__(self, bus, index):
        self.path = f'/org/bluez/example/service{index}'
        super().__init__(bus, self.path)
        self.uuid = HID_UUID
        self.bus  = bus
        self.chars = [
            ProtocolModeChar(bus, 0, self),
            ReportMapChar   (bus, 1, self),
            HIDInfoChar     (bus, 2, self),
            HIDCtrlPoint    (bus, 3, self),
            MouseInputChar  (bus, 4, self)  # ★ 우리가 쓸 특성
        ]

    def get_managed_objects(self):
        result = { self.path: {
            'org.bluez.GattService1': {
                'UUID': self.uuid,
                'Primary': True,
            }
        }}
        for ch in self.chars:
            result.update(ch.get_managed_objects())
        return result

class Characteristic(dbus.service.Object):
    def __init__(self, bus, index, uuid, flags, service):
        self.path = service.path + f'/char{index}'
        super().__init__(bus, self.path)
        self.uuid  = uuid
        self.flags = flags
        self.service = service
        self.notifying = False

    # GATT Characteristic1 인터페이스
    @dbus.service.method(DBUS_PROP, in_signature='s', out_signature='a{sv}')
    def GetAll(self, iface): 
        if iface != 'org.bluez.GattCharacteristic1': return {}
        return { 'UUID': self.uuid,
                 'Service': self.service.path,
                 'Flags': dbus.Array(self.flags, signature='s') }

    @dbus.service.method('org.bluez.GattCharacteristic1', in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options): return dbus.Array([], signature='y')

    @dbus.service.method('org.bluez.GattCharacteristic1', in_signature='aya{sv}')
    def WriteValue(self, value, options): pass

    @dbus.service.method('org.bluez.GattCharacteristic1')
    def StartNotify(self): self.notifying=True

    @dbus.service.method('org.bluez.GattCharacteristic1')
    def StopNotify(self): self.notifying=False

    def get_managed_objects(self):
        return { self.path : { 'org.bluez.GattCharacteristic1': {
            'UUID': self.uuid,
            'Service': self.service.path,
            'Flags': dbus.Array(self.flags, signature='s')
        }}}

# ----------  HID 필수 특성 ----------
class ProtocolModeChar(Characteristic):
    def __init__(self, bus, idx, svc):
        super().__init__(bus, idx, PROTO_MODE_UUID, ['read','write-without-response'], svc)
        self.mode = dbus.Byte(1)   # Report Protocol (1)

    def ReadValue(self, opts): return [self.mode]

    def WriteValue(self, value, opts):
        if value and value[0] in (0,1): self.mode = value[0]

class ReportMapChar(Characteristic):
    def __init__(self, bus, idx, svc):
        super().__init__(bus, idx, REPORT_MAP_UUID, ['read'], svc)
    def ReadValue(self, opts): return list(REPORT_MAP)

class HIDInfoChar(Characteristic):
    def __init__(self, bus, idx, svc):
        super().__init__(bus, idx, HID_INFO_UUID, ['read'], svc)
        self.val = struct.pack('<HBB', 0x0111, 0x00, 0x02)  # v1.11, country 0, flags
    def ReadValue(self, o): return list(self.val)

class HIDCtrlPoint(Characteristic):
    def __init__(self, bus, idx, svc):
        super().__init__(bus, idx, HID_CP_UUID, ['write-without-response'], svc)
    def WriteValue(self, value, opts): pass    # suspend / exit suspend 무시

# ----------  ★ Mouse Input Report ----------
class MouseInputChar(Characteristic):
    def __init__(self, bus, idx, svc):
        super().__init__(bus, idx, REPORT_UUID, ['read','notify'], svc)
        self.subs = []

    def ReadValue(self, opts):       # 호스트가 읽으면 0 데이터
        return [0x00,0x00,0x00,0x00]

    def StartNotify(self):
        super().StartNotify()

    def send_report(self, dx, dy, buttons=0, wheel=0):
        if not self.notifying: return
        # ΔX,ΔY,Wheel 을 signed char로 변환
        def s8(n): return dbus.Byte(n & 0xFF)
        report = [ dbus.Byte(buttons & 0x07), s8(dx), s8(dy), s8(wheel) ]
        self.PropertiesChanged('org.bluez.GattCharacteristic1',
                               { 'Value': report }, [])

    # Helper : D‑Bus signal directly
    @dbus.service.signal(DBUS_PROP, signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalid): pass

# ----------  런타임 ----------
def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    adapter_path = find_adapter(bus)
    adapter = dbus.Interface(bus.get_object(BLUEZ, adapter_path), ADAPTER_IF)

    # 1) Advertising 등록
    ad_mgr = dbus.Interface(bus.get_object(BLUEZ, adapter_path), LE_ADV_MGR)
    advert = Advertisement(bus, 0)
    ad_mgr.RegisterAdvertisement(advert.path, {}, reply_handler=lambda:None,
                                 error_handler=lambda e: sys.exit(e))

    # 2) GATT 서버 등록
    app = Application(bus)
    gatt_mgr = dbus.Interface(bus.get_object(BLUEZ, adapter_path), GATT_MGR)
    gatt_mgr.RegisterApplication(app.path, {},
                                 reply_handler=lambda:None,
                                 error_handler=lambda e: sys.exit(e))

    mouse_char = app.services[0].chars[-1]  # MouseInputChar 인스턴스

    print("● BLE Mouse Advertising… (스마트폰에서 연결 후 커서 움직임 확인)")
    loop = GLib.MainLoop()

    # ───── 간단한 CLI 입력 스레드 ─────
    def cli():
        while True:
            try:
                cmd = input("dx dy [btn] ▶ ")
                if cmd.strip().lower() in ('q','quit','exit'):
                    loop.quit(); return
                dx, dy, *btn = map(int, cmd.split())
                b = btn[0] if btn else 0
                GLib.idle_add(mouse_char.send_report, dx, dy, b, 0)
            except (KeyboardInterrupt, EOFError):
                loop.quit(); break
            except Exception as e:
                print("잘못된 입력:", e)
    threading.Thread(target=cli, daemon=True).start()

    loop.run()

if __name__ == '__main__':
    main()