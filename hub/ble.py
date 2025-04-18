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

# Add LE Advertising Manager interface
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
LE_ADVERTISEMENT_IFACE = 'org.bluez.LEAdvertisement1'

# --- Standard Bluetooth SIG UUIDs ---
HID_SERVICE_UUID = '00001812-0000-1000-8000-00805f9b34fb'
HID_INFO_UUID = '00002a4a-0000-1000-8000-00805f9b34fb'
REPORT_MAP_UUID = '00002a4b-0000-1000-8000-00805f9b34fb'
HID_CONTROL_POINT_UUID = '00002a4c-0000-1000-8000-00805f9b34fb'
REPORT_UUID = '00002a4d-0000-1000-8000-00805f9b34fb'
PROTOCOL_MODE_UUID = '00002a4e-0000-1000-8000-00805f9b34fb'
PNP_ID_UUID = '00002a50-0000-1000-8000-00805f9b34fb' # Device ID service

DEVICE_ID_SERVICE_UUID = '0000180a-0000-1000-8000-00805f9b34fb' # For PnP ID

# --- HID Constants ---
REPORT_PROTOCOL_MODE = 0x01 # Default is Report Protocol
HID_APPEARANCE = 0x03C0 # Generic HID / Combo Keyboard/Mouse

# --- Exception Classes (Copied from example.py) ---
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

# --- Base Classes (Adapted from example.py) ---
class Application(dbus.service.Object):
    """
    org.bluez.GattApplication1 interface implementation
    """
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
        self.add_service(HIDService(bus, 0))
        self.add_service(DeviceInformationService(bus, 1)) # Add Device Info Service

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
    org.bluez.GattService1 interface implementation
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
    org.bluez.GattCharacteristic1 interface implementation
    """
    def __init__(self, bus, index, uuid, flags, service):
        self.path = service.path + '/char' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.service = service
        self.flags = flags
        self.descriptors = []
        # Initialize value property
        self._value = []
        self.notifying = False
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
                        # Expose current value if readable
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
        print(f'Default ReadValue called for {self.uuid}')
        # Return current value by default
        return self._value

    @dbus.service.method(GATT_CHRC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print(f'Default WriteValue called for {self.uuid}: {value}')
        # Store written value by default
        self._value = value
        # Optionally notify PropertiesChanged if needed, but usually done explicitly

    @dbus.service.method(GATT_CHRC_IFACE)
    def StartNotify(self):
        if self.notifying:
            print(f'Already notifying characteristic {self.uuid}')
            return
        print(f'Starting notifications for {self.uuid}')
        self.notifying = True

    @dbus.service.method(GATT_CHRC_IFACE)
    def StopNotify(self):
        if not self.notifying:
            print(f'Characteristic {self.uuid} not notifying')
            return
        print(f'Stopping notifications for {self.uuid}')
        self.notifying = False

    @dbus.service.signal(DBUS_PROP_IFACE,
                         signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass

    def update_value(self, new_value):
        """Helper method to update characteristic value and notify if enabled."""
        if self._value == new_value:
            return # No change
        print(f"Updating value for {self.uuid}: {new_value}")
        self._value = new_value
        props_changed = {'Value': dbus.Array(self._value, signature='y')}
        self.PropertiesChanged(GATT_CHRC_IFACE, props_changed, [])


class Descriptor(dbus.service.Object):
    """
    org.bluez.GattDescriptor1 interface implementation
    """
    def __init__(self, bus, index, uuid, flags, characteristic):
        self.path = characteristic.path + '/desc' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.flags = flags
        self.chrc = characteristic
        # Initialize value property
        self._value = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
                GATT_DESC_IFACE: {
                        'Characteristic': self.chrc.get_path(),
                        'UUID': self.uuid,
                        'Flags': self.flags,
                         # Expose current value if readable
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
        print(f'Default ReadValue called for descriptor {self.uuid}')
        return self._value

    @dbus.service.method(GATT_DESC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print(f'Default WriteValue called for descriptor {self.uuid}: {value}')
        self._value = value

# --- HID Report Descriptor (Combined Keyboard & Mouse) ---
# This is a complex part. Using a simplified descriptor for now.
# A proper descriptor would be much longer and more detailed.
# See HID specification and examples online.
# Report ID 1: Keyboard (8 modifier byte, 1 reserved, 6 keycodes)
# Report ID 2: Mouse (1 button byte, 2 bytes X, 2 bytes Y, 1 byte wheel)
# Report ID 3: Consumer Control (e.g., Volume up/down)
HID_REPORT_MAP = [
    0x05, 0x01,        # Usage Page (Generic Desktop Ctrls)
    0x09, 0x06,        # Usage (Keyboard)
    0xA1, 0x01,        # Collection (Application)
    0x85, 0x01,        #   Report ID (1)
    0x05, 0x07,        #   Usage Page (Kbrd/Keypad)
    0x19, 0xE0,        #   Usage Minimum (0xE0)
    0x29, 0xE7,        #   Usage Maximum (0xE7)
    0x15, 0x00,        #   Logical Minimum (0)
    0x25, 0x01,        #   Logical Maximum (1)
    0x75, 0x01,        #   Report Size (1)
    0x95, 0x08,        #   Report Count (8)
    0x81, 0x02,        #   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position) ; Modifier byte
    0x95, 0x01,        #   Report Count (1)
    0x75, 0x08,        #   Report Size (8)
    0x81, 0x01,        #   Input (Const,Array,Abs,No Wrap,Linear,Preferred State,No Null Position) ; Reserved byte
    0x95, 0x06,        #   Report Count (6)
    0x75, 0x08,        #   Report Size (8)
    0x15, 0x00,        #   Logical Minimum (0)
    0x26, 0xFF, 0x00,  #   Logical Maximum (255)
    0x05, 0x07,        #   Usage Page (Kbrd/Keypad)
    0x19, 0x00,        #   Usage Minimum (0x00)
    0x29, 0xFF,        #   Usage Maximum (0xFF)
    0x81, 0x00,        #   Input (Data,Array,Abs,No Wrap,Linear,Preferred State,No Null Position) ; Keycodes
    # Optional: Output report for LEDs (NumLock etc.)
    # 0x95, 0x05,        #   Report Count (5) ; Need 5 bits for ScrollLock, CapsLock, NumLock, Compose, Kana
    # 0x75, 0x01,        #   Report Size (1)
    # 0x05, 0x08,        #   Usage Page (LEDs)
    # 0x19, 0x01,        #   Usage Minimum (Num Lock LED)
    # 0x29, 0x05,        #   Usage Maximum (Kana LED)
    # 0x91, 0x02,        #   Output (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position,Non-volatile) ; LED report
    # 0x95, 0x01,        #   Report Count (1) ; Pad to full byte
    # 0x75, 0x03,        #   Report Size (3)
    # 0x91, 0x01,        #   Output (Const,Array,Abs,No Wrap,Linear,Preferred State,No Null Position,Non-volatile) ; LED report padding
    0xC0,              # End Collection

    0x05, 0x01,        # Usage Page (Generic Desktop Ctrls)
    0x09, 0x02,        # Usage (Mouse)
    0xA1, 0x01,        # Collection (Application)
    0x85, 0x02,        #   Report ID (2)
    0x09, 0x01,        #   Usage (Pointer)
    0xA1, 0x00,        #   Collection (Physical)
    0x05, 0x09,        #     Usage Page (Button)
    0x19, 0x01,        #     Usage Minimum (0x01) ; Button 1
    0x29, 0x05,        #     Usage Maximum (0x05) ; Button 5
    0x15, 0x00,        #     Logical Minimum (0)
    0x25, 0x01,        #     Logical Maximum (1)
    0x95, 0x05,        #     Report Count (5) ; Buttons 1-5
    0x75, 0x01,        #     Report Size (1)
    0x81, 0x02,        #     Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
    0x95, 0x01,        #     Report Count (1) ; Pad to 1 byte
    0x75, 0x03,        #     Report Size (3)
    0x81, 0x01,        #     Input (Const,Array,Abs,No Wrap,Linear,Preferred State,No Null Position)
    0x05, 0x01,        #     Usage Page (Generic Desktop Ctrls)
    0x09, 0x30,        #     Usage (X)
    0x09, 0x31,        #     Usage (Y)
    0x16, 0x01, 0xF8,  #     Logical Minimum (-2047)
    0x26, 0xFF, 0x07,  #     Logical Maximum (2047)
    0x75, 0x10,        #     Report Size (16) ; 2 bytes for X, 2 bytes for Y
    0x95, 0x02,        #     Report Count (2)
    0x81, 0x06,        #     Input (Data,Var,Rel,No Wrap,Linear,Preferred State,No Null Position)
    0x09, 0x38,        #     Usage (Wheel)
    0x15, 0x81,        #     Logical Minimum (-127)
    0x25, 0x7F,        #     Logical Maximum (127)
    0x75, 0x08,        #     Report Size (8)
    0x95, 0x01,        #     Report Count (1)
    0x81, 0x06,        #     Input (Data,Var,Rel,No Wrap,Linear,Preferred State,No Null Position)
    0xC0,              #   End Collection
    0xC0,              # End Collection

    # Optional: Consumer Control Device (Volume, Play/Pause etc.)
    0x05, 0x0C,        # Usage Page (Consumer)
    0x09, 0x01,        # Usage (Consumer Control)
    0xA1, 0x01,        # Collection (Application)
    0x85, 0x03,        #   Report ID (3)
    0x15, 0x00,        #   Logical Minimum (0)
    0x25, 0x01,        #   Logical Maximum (1)
    0x75, 0x01,        #   Report Size (1)
    0x95, 0x08,        #   Report Count (8) # Define 8 consumer control buttons (bits)
    0x09, 0xB5,        #   Usage (Scan Next Track)
    0x09, 0xB6,        #   Usage (Scan Previous Track)
    0x09, 0xB7,        #   Usage (Stop)
    0x09, 0xCD,        #   Usage (Play/Pause)
    0x09, 0xE2,        #   Usage (Mute)
    0x09, 0xE9,        #   Usage (Volume Increment)
    0x09, 0xEA,        #   Usage (Volume Decrement)
    0x0A, 0xAE, 0x01,  #   Usage (AL Email Reader)
    0x81, 0x02,        #   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
    0xC0               # End Collection
]

# --- HID Service Implementation ---
class HIDService(Service):
    """
    Human Interface Device Service implementation.
    """
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, HID_SERVICE_UUID, True)
        # Protocol Mode Characteristic (Required)
        self.protocol_mode_char = ProtocolModeCharacteristic(bus, 0, self)
        self.add_characteristic(self.protocol_mode_char)
        # HID Information Characteristic (Required)
        self.add_characteristic(HIDInformationCharacteristic(bus, 1, self))
        # Report Map Characteristic (Required)
        self.add_characteristic(ReportMapCharacteristic(bus, 2, self))
        # Input Report Characteristics (Keyboard and Mouse)
        self.keyboard_input_char = InputReportCharacteristic(bus, 3, self, 1) # Report ID 1 for Keyboard
        self.mouse_input_char = InputReportCharacteristic(bus, 4, self, 2)    # Report ID 2 for Mouse
        # self.consumer_input_char = InputReportCharacteristic(bus, 5, self, 3) # Report ID 3 for Consumer Control
        self.add_characteristic(self.keyboard_input_char)
        self.add_characteristic(self.mouse_input_char)
        # self.add_characteristic(self.consumer_input_char)
        # HID Control Point Characteristic (Required)
        self.add_characteristic(HIDControlPointCharacteristic(bus, 6, self))

        # TODO: Add Output Report Characteristic if needed (e.g., for keyboard LEDs)
        # TODO: Add Feature Report Characteristic if needed

class ProtocolModeCharacteristic(Characteristic):
    """
    Protocol Mode Characteristic. Allows switching between Boot Protocol and Report Protocol.
    We default to Report Protocol.
    """
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            PROTOCOL_MODE_UUID,
            ['read', 'write-without-response'], # Writable is optional by spec, but often implemented
            service)
        # Initialize to Report Protocol Mode
        self._value = [dbus.Byte(REPORT_PROTOCOL_MODE)]

    def ReadValue(self, options):
        print(f"Protocol Mode Read: {self._value}")
        return self._value

    def WriteValue(self, value, options):
        # Only modes 0x00 (Boot) and 0x01 (Report) are valid
        if len(value) != 1 or value[0] not in [0x00, 0x01]:
            # Silently ignore invalid writes for WriteWithoutResponse
            print(f"Ignoring invalid Protocol Mode write: {value}")
            return
        print(f"Protocol Mode Write: {value}")
        self._value = value
        # Potentially trigger actions if mode changes, but usually handled by host

class HIDInformationCharacteristic(Characteristic):
    """
    HID Information Characteristic. Provides basic HID metadata.
    """
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            HID_INFO_UUID,
            ['read'],
            service)
        # bcdHID (e.g., 1.11), bCountryCode (0 = Not localized), Flags (normal connect)
        self._value = [dbus.Byte(0x11), dbus.Byte(0x01), dbus.Byte(0x00), dbus.Byte(0x01)] # 1.11, Not localized, Normal connect

    def ReadValue(self, options):
        return self._value

class ReportMapCharacteristic(Characteristic):
    """
    Report Map Characteristic. Contains the HID Report Descriptor.
    """
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            REPORT_MAP_UUID,
            ['read'],
            service)
        self._value = [dbus.Byte(b) for b in HID_REPORT_MAP]

    def ReadValue(self, options):
        return self._value

class InputReportCharacteristic(Characteristic):
    """
    Input Report Characteristic. Used to send keyboard/mouse/consumer data to the host.
    Requires Client Characteristic Configuration Descriptor (CCCD) for notifications.
    """
    def __init__(self, bus, index, service, report_id):
        self.report_id = report_id
        self.simulation_timer_id = None
        self.mouse_move_direction = 1 # 1 for down-right, -1 for up-left
        Characteristic.__init__(
            self, bus, index,
            REPORT_UUID,
            ['read', 'notify'], # Write is optional, usually not needed for Input Reports
            service)
        # Add CCCD (Client Characteristic Configuration Descriptor)
        self.add_descriptor(ClientCharCfgDescriptor(bus, 0, self)) # Index 0 for CCCD

        # Initialize value based on report ID
        if report_id == 1: # Keyboard: Modifier (1), Reserved (1), Keycodes (6) = 8 bytes
           self._value = [dbus.Byte(report_id)] + [dbus.Byte(0x00)] * 8
        elif report_id == 2: # Mouse: Buttons (1), X (2), Y (2), Wheel (1) = 6 bytes
           self._value = [dbus.Byte(report_id)] + [dbus.Byte(0x00)] * 6
        # elif report_id == 3: # Consumer: Buttons (1 byte bitmask)
        #    self._value = [dbus.Byte(report_id)] + [dbus.Byte(0x00)] * 1
        else:
            self._value = [dbus.Byte(report_id)] # Fallback

    def send_report(self, report_data):
        """Updates the characteristic value and sends notification if enabled."""
        # Prepend the Report ID to the data
        full_report = [dbus.Byte(self.report_id)] + [dbus.Byte(b) for b in report_data]
        print(f"Sending Report ID {self.report_id}: {full_report}")
        self.update_value(full_report) # update_value handles PropertiesChanged signal

    def ReadValue(self, options):
        # Spec says reading Input Report is optional, but return last sent value if needed.
        return self._value

    # Override Start/Stop Notify to print report ID
    def StartNotify(self):
        if self.notifying:
            print(f'Already notifying Input Report ID {self.report_id}')
            return
        print(f'Starting notifications for Input Report ID {self.report_id}')
        self.notifying = True

        # Start mouse simulation only for mouse report characteristic
        if self.report_id == 2 and self.simulation_timer_id is None:
            print("Starting mouse movement simulation...")
            # Start timer to call _simulate_mouse_movement every 2 seconds (2000 ms)
            self.simulation_timer_id = GLib.timeout_add(2000, self._simulate_mouse_movement)

        # When notifications start, potentially send an initial 'all clear' report?
        # if self.report_id == 1: self.send_report([0]*8) # Keyboard clear
        # elif self.report_id == 2: self.send_report([0]*6) # Mouse clear

    def StopNotify(self):
        if not self.notifying:
            print(f'Input Report ID {self.report_id} not notifying')
            return
        print(f'Stopping notifications for Input Report ID {self.report_id}')
        self.notifying = False

        # Stop mouse simulation if it's running
        if self.report_id == 2 and self.simulation_timer_id is not None:
            print("Stopping mouse movement simulation...")
            GLib.source_remove(self.simulation_timer_id)
            self.simulation_timer_id = None

    def _simulate_mouse_movement(self):
        """Called by timer to simulate mouse movement."""
        if not self.notifying:
            # Should not happen if timer is managed correctly, but good practice
            self.simulation_timer_id = None
            return False # Stop the timer

        move_delta = 10 * self.mouse_move_direction
        print(f"Simulating mouse move ({move_delta}, {move_delta})")
        # Format: Buttons (1), dX (2), dY (2), Wheel (1)
        report = [
            0, # No buttons pressed
            move_delta & 0xFF, (move_delta >> 8) & 0xFF, # dX
            move_delta & 0xFF, (move_delta >> 8) & 0xFF, # dY
            0 # No wheel movement
        ]
        self.send_report(report)

        # Reverse direction for next time
        self.mouse_move_direction *= -1

        return True # Keep timer running


class HIDControlPointCharacteristic(Characteristic):
    """
    HID Control Point Characteristic. Used for commands like Suspend/Exit Suspend.
    """
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            HID_CONTROL_POINT_UUID,
            ['write-without-response'],
            service)
        self._value = [] # Write-only, value is transient command

    def WriteValue(self, value, options):
        if not value:
            return # Ignore empty write
        command = value[0]
        print(f"HID Control Point Write: Command {command}")
        if command == 0x00: # Suspend
            print("Suspend command received")
            # TODO: Implement suspend logic if needed (e.g., stop sending reports)
        elif command == 0x01: # Exit Suspend
            print("Exit Suspend command received")
            # TODO: Implement resume logic
        else:
            print(f"Unknown HID Control Point command: {command}")
        # No response needed for WriteWithoutResponse


# --- Standard Descriptor Implementations ---
class ClientCharCfgDescriptor(Descriptor):
    """
    Client Characteristic Configuration Descriptor implementation.
    Allows the client (e.g., PC, phone) to enable/disable notifications.
    """
    CCCD_UUID = '00002902-0000-1000-8000-00805f9b34fb'

    def __init__(self, bus, index, characteristic):
        Descriptor.__init__(
            self, bus, index,
            self.CCCD_UUID,
            ['read', 'write'],
            characteristic)
        self._value = [dbus.Byte(0x00), dbus.Byte(0x00)] # Default: Notifications/Indications disabled

    def ReadValue(self, options):
        print(f"CCCD Read for {self.chrc.uuid}: {self._value}")
        return self._value

    def WriteValue(self, value, options):
        if len(value) != 2:
            raise InvalidValueLengthException()

        print(f"CCCD Write for {self.chrc.uuid}: {value}")
        self._value = value
        if value[0] & 0x01: # Check if notifications bit is set
            if not self.chrc.notifying:
                self.chrc.StartNotify()
        else:
            if self.chrc.notifying:
                self.chrc.StopNotify()
        # Indications (bit 1) are not used in this example


class ReportReferenceDescriptor(Descriptor):
    """
    Report Reference Descriptor implementation.
    Associates a Report ID and type (Input/Output/Feature) with a Report characteristic.
    """
    REPORT_REF_UUID = '00002908-0000-1000-8000-00805f9b34fb'

    # Report Types
    INPUT_REPORT = 0x01
    OUTPUT_REPORT = 0x02
    FEATURE_REPORT = 0x03

    def __init__(self, bus, index, characteristic, report_id, report_type):
        Descriptor.__init__(
            self, bus, index,
            self.REPORT_REF_UUID,
            ['read'],
            characteristic)
        self._value = [dbus.Byte(report_id), dbus.Byte(report_type)]

    def ReadValue(self, options):
        return self._value

# --- Device Information Service Implementation ---
class DeviceInformationService(Service):
    """
    Device Information Service implementation.
    Provides manufacturer name, model number, PnP ID etc.
    """
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, DEVICE_ID_SERVICE_UUID, True)
        self.add_characteristic(PnPIdCharacteristic(bus, 0, self))
        # Optionally add Manufacturer Name, Model Number characteristics

class PnPIdCharacteristic(Characteristic):
    """
    PnP ID Characteristic. Identifies the device vendor/product.
    """
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            PNP_ID_UUID,
            ['read'],
            service)
        # Vendor ID Source (0x02 = USB Implementer's Forum)
        # Vendor ID (e.g., 0x05AC = Apple, 0x046D = Logitech) - Use a test/generic one
        # Product ID (Assigned by vendor)
        # Product Version (Assigned by vendor)
        self._value = [
            dbus.Byte(0x02), # Vendor ID Source: USB
            dbus.Byte(0x57), dbus.Byte(0x04), # Vendor ID: 0x0457 (Example)
            dbus.Byte(0x01), dbus.Byte(0x00), # Product ID: 0x0001 (Example)
            dbus.Byte(0x00), dbus.Byte(0x01)  # Product Version: 0x0100 (1.0)
        ]

    def ReadValue(self, options):
        return self._value


# --- Advertising Class ---
class Advertisement(dbus.service.Object):
    PATH_BASE = '/org/bluez/example/advertisement'

    def __init__(self, bus, index, advertising_type):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.ad_type = advertising_type
        self.service_uuids = None
        self.manufacturer_data = None
        self.solicit_uuids = None
        self.service_data = None
        self.local_name = None
        self.include_tx_power = None
        self.data = None
        self.appearance = None # Added appearance
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
                self.manufacturer_data, signature='qv')
        if self.service_data is not None:
            properties['ServiceData'] = dbus.Dictionary(self.service_data,
                                                        signature='sv')
        if self.local_name is not None:
            properties['LocalName'] = dbus.String(self.local_name)
        if self.include_tx_power is not None:
            properties['IncludeTxPower'] = dbus.Boolean(self.include_tx_power)
        if self.data is not None:
            properties['Data'] = dbus.Dictionary(self.data, signature='yv')
        # Add appearance to properties
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
        print('%s: Released!' % self.path)


class TestAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.service_uuids = [HID_SERVICE_UUID, DEVICE_ID_SERVICE_UUID] # Advertise services
        self.local_name = "test" # Set device name to "test"
        self.appearance = HID_APPEARANCE # Set appearance to HID Combo
        self.include_tx_power = True
        # self.manufacturer_data = ... # Optional


# --- Main Application Logic (Adapted from example.py) ---
def register_app_cb():
    print('GATT application registered')

def register_app_error_cb(error):
    print('Failed to register application: ' + str(error))
    mainloop.quit()

def register_ad_cb():
    print('Advertisement registered')

def register_ad_error_cb(error):
    print('Failed to register advertisement: ' + str(error))
    mainloop.quit()

def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                               DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()

    for o, props in objects.items():
        if GATT_MANAGER_IFACE in props.keys():
            return o
    return None

# --- Functions to send HID reports ---
# These would be called from your main application logic
# based on GPIO events, user input, etc.

app_instance = None # Global reference to Application instance

def send_key_report(modifiers, keycodes):
    """Sends a keyboard report."""
    global app_instance
    if not app_instance: return
    hid_service = next((s for s in app_instance.services if isinstance(s, HIDService)), None)
    if hid_service and hid_service.keyboard_input_char.notifying:
        # Format: Modifier byte, Reserved byte (0), Keycode1, ..., Keycode6
        report = [modifiers, 0] + keycodes[:6]
        # Pad with 0s if less than 6 keycodes provided
        report.extend([0] * (6 - len(keycodes)))
        hid_service.keyboard_input_char.send_report(report)

def release_keys():
    """Sends a keyboard report with no keys pressed."""
    send_key_report(0, [])

def send_mouse_report(buttons, dx, dy, wheel):
    """Sends a mouse report."""
    global app_instance
    if not app_instance: return
    hid_service = next((s for s in app_instance.services if isinstance(s, HIDService)), None)
    if hid_service and hid_service.mouse_input_char.notifying:
        # Format: Buttons (1 byte), dX (2 bytes, little-endian), dY (2 bytes, little-endian), Wheel (1 byte)
        report = [
            buttons & 0xFF,
            dx & 0xFF, (dx >> 8) & 0xFF,
            dy & 0xFF, (dy >> 8) & 0xFF,
            wheel & 0xFF
        ]
        hid_service.mouse_input_char.send_report(report)

def main():
    global mainloop
    global app_instance

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    adapter = find_adapter(bus)
    if not adapter:
        print('GattManager1 interface not found')
        return

    service_manager = dbus.Interface(
            bus.get_object(BLUEZ_SERVICE_NAME, adapter),
            GATT_MANAGER_IFACE)

    # Get LE Advertising Manager
    ad_manager = dbus.Interface(
            bus.get_object(BLUEZ_SERVICE_NAME, adapter),
            LE_ADVERTISING_MANAGER_IFACE)

    app_instance = Application(bus) # Store the application instance

    mainloop = GLib.MainLoop()

    # Create and register advertisement
    test_advertisement = TestAdvertisement(bus, 0)

    print('Registering GATT application...')

    try:
        service_manager.RegisterApplication(app_instance.get_path(), {},
                                        reply_handler=register_app_cb,
                                        error_handler=register_app_error_cb)
    except dbus.exceptions.DBusException as e:
        print(f"Error registering application: {e}")
        if "Already Exists" in str(e):
             print("Application might be already registered. Try unregistering first or restarting Bluetooth.")
             # Consider attempting unregister here if needed
             # unregister_app(service_manager, app_instance.get_path())
        mainloop.quit()
        return

    # Register Advertisement
    print('Registering advertisement...')
    ad_manager.RegisterAdvertisement(test_advertisement.get_path(), {},
                                     reply_handler=register_ad_cb,
                                     error_handler=register_ad_error_cb)

    # Simulation now starts automatically when notifications are enabled for mouse

    try:
        mainloop.run()
    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt, exiting.")
    finally:
        # Optional: Unregister application and advertisement on exit?
        # try:
        #     print("Unregistering advertisement...")
        #     ad_manager.UnregisterAdvertisement(test_advertisement.get_path())
        # except Exception as e:
        #     print(f"Error unregistering advertisement: {e}")
        pass # Usually letting the bluetoothd handle cleanup is fine

if __name__ == '__main__':
    main()
