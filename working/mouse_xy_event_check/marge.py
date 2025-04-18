#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merged BLE HID Mouse (GATT HoG Peripheral) for Raspberry Pi
Based on examples new.py and ble2.py
"""

import dbus, dbus.exceptions, dbus.mainloop.glib, dbus.service
from gi.repository import GLib
import threading, sys, struct

# D-Bus Constants
BLUEZ_SERVICE = 'org.bluez'
ADAPTER_IFACE = 'org.bluez.Adapter1'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
LE_ADVERTISEMENT_IFACE = 'org.bluez.LEAdvertisement1'
GATT_MANAGER_IFACE = 'org.bluez.GattManager1'
GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE = 'org.bluez.GattCharacteristic1'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'

# HID Service and Characteristic UUIDs (Short)
HID_SERVICE_UUID = '1812'       # Human Interface Device Service
REPORT_UUID = '2a4d'           # Report Characteristic
REPORT_MAP_UUID = '2a4b'        # Report Map Characteristic
PROTOCOL_MODE_UUID = '2a4e'     # Protocol Mode Characteristic
HID_INFO_UUID = '2a4a'          # HID Information Characteristic
HID_CONTROL_POINT_UUID = '2a4c' # HID Control Point Characteristic

# HID Report Map (Boot Mouse: 3 buttons + X + Y + Wheel)
# Matches the structure used in new.py
HID_REPORT_MAP = bytes([
    0x05, 0x01,  # Usage Page (Generic Desktop Ctrls)
    0x09, 0x02,  # Usage (Mouse)
    0xA1, 0x01,  # Collection (Application)
    0x09, 0x01,  #   Usage (Pointer)
    0xA1, 0x00,  #   Collection (Physical)
    0x05, 0x09,  #     Usage Page (Button)
    0x19, 0x01,  #     Usage Minimum (0x01) - Button 1
    0x29, 0x03,  #     Usage Maximum (0x03) - Button 3
    0x15, 0x00,  #     Logical Minimum (0)
    0x25, 0x01,  #     Logical Maximum (1)
    0x95, 0x03,  #     Report Count (3) - Buttons 1, 2, 3
    0x75, 0x01,  #     Report Size (1) - 1 bit each
    0x81, 0x02,  #     Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
    0x95, 0x01,  #     Report Count (1) - Padding
    0x75, 0x05,  #     Report Size (5) - 5 bits padding
    0x81, 0x03,  #     Input (Const,Array,Abs,No Wrap,Linear,Preferred State,No Null Position)
    0x05, 0x01,  #     Usage Page (Generic Desktop Ctrls)
    0x09, 0x30,  #     Usage (X)
    0x09, 0x31,  #     Usage (Y)
    0x09, 0x38,  #     Usage (Wheel)
    0x15, 0x81,  #     Logical Minimum (-127)
    0x25, 0x7F,  #     Logical Maximum (127)
    0x75, 0x08,  #     Report Size (8) - 8 bits for X, Y, Wheel
    0x95, 0x03,  #     Report Count (3) - X, Y, Wheel
    0x81, 0x06,  #     Input (Data,Var,Rel,No Wrap,Linear,Preferred State,No Null Position)
    0xC0,        #   End Collection (Physical)
    0xC0         # End Collection (Application)
])

# --- Helper Functions ---
def find_adapter(bus):
    """Returns the path of the first found Bluetooth adapter."""
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE, '/'), DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()
    for path, ifaces in objects.items():
        if ADAPTER_IFACE in ifaces:
            return path
    return None

# --- D-Bus Service Classes (Based on new.py structure) ---

class Advertisement(dbus.service.Object):
    PATH_BASE = '/org/bluez/example/advertisement'

    def __init__(self, bus, index):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.ad_type = 'peripheral'
        self.service_uuids = [HID_SERVICE_UUID]
        self.appearance = 0x03C2  # Generic Mouse
        self.local_name = 'Pi-BLE-Mouse'
        self.discoverable = True
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
            raise dbus.exceptions.DBusException('Invalid interface')
        return self.get_properties()[LE_ADVERTISEMENT_IFACE]

    @dbus.service.method(LE_ADVERTISEMENT_IFACE, in_signature='', out_signature='')
    def Release(self):
        print(f'{self.path} released')

class Application(dbus.service.Object):
    """
    org.bluez.GattApplication1 interface implementation.
    Manages services.
    """
    PATH = '/org/bluez/example/app'

    def __init__(self, bus):
        self.path = self.PATH
        dbus.service.Object.__init__(self, bus, self.path)
        self.services = []
        self.add_service(HIDService(bus, 0))
        # Add DeviceInformationService if needed

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        response[self.get_path()] = {} # Include application path
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
                # Add descriptors if needed
                descs = chrc.get_descriptors()
                for desc in descs:
                    response[desc.get_path()] = desc.get_properties()
        return response

class Service(dbus.service.Object):
    """
    org.bluez.GattService1 interface base implementation.
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
        return [chrc.get_path() for chrc in self.characteristics]

    def get_characteristics(self):
        return self.characteristics

    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_SERVICE_IFACE:
             raise dbus.exceptions.DBusException('Invalid interface')
        return self.get_properties()[GATT_SERVICE_IFACE]


class Characteristic(dbus.service.Object):
    """
    org.bluez.GattCharacteristic1 interface base implementation.
    """
    def __init__(self, bus, index, uuid, flags, service):
        self.path = service.path + '/char' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.service = service
        self.flags = flags
        self.notifying = False
        self._value = [] # Internal storage for the value
        self.descriptors = [] # List to hold descriptors
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        props = {
            'Service': self.service.get_path(),
            'UUID': self.uuid,
            'Flags': dbus.Array(self.flags, signature='s')
            # Add Descriptors if needed
        }
        props['Descriptors'] = dbus.Array(
            self.get_descriptor_paths(), signature='o'
        )
        # Include 'Value' if readable, needed for GetManagedObjects
        if 'read' in self.flags or 'secure-read' in self.flags:
             props['Value'] = dbus.Array(self.ReadValue({}), signature='y')
        return {GATT_CHRC_IFACE: props}


    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_descriptor(self, descriptor):
        """Adds a descriptor to this characteristic."""
        self.descriptors.append(descriptor)

    def get_descriptor_paths(self):
        """Returns a list of object paths for the descriptors."""
        return [desc.get_path() for desc in self.descriptors]

    def get_descriptors(self):
        """Returns the list of descriptor objects."""
        return self.descriptors

    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_CHRC_IFACE:
             raise dbus.exceptions.DBusException('Invalid interface')
        return self.get_properties()[GATT_CHRC_IFACE]

    @dbus.service.method(GATT_CHRC_IFACE, in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        print(f'Default ReadValue called for {self.uuid}')
        return dbus.Array(self._value, signature='y')

    @dbus.service.method(GATT_CHRC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print(f'Default WriteValue called for {self.uuid}: {value}')
        self._value = bytes(value) # Store as bytes

    @dbus.service.method(GATT_CHRC_IFACE)
    def StartNotify(self):
        if self.notifying:
            print('Already notifying')
            return
        print(f'Starting notifications for {self.uuid}')
        self.notifying = True

    @dbus.service.method(GATT_CHRC_IFACE)
    def StopNotify(self):
        if not self.notifying:
            print('Not notifying')
            return
        print(f'Stopping notifications for {self.uuid}')
        self.notifying = False

    # Signal for value changes (notifications)
    @dbus.service.signal(DBUS_PROP_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass

# --- Standard Descriptor Implementations ---

class Descriptor(dbus.service.Object):
    """
    org.bluez.GattDescriptor1 interface base implementation.
    """
    def __init__(self, bus, index, uuid, flags, characteristic):
        self.path = characteristic.path + '/desc' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.flags = flags
        self.characteristic = characteristic
        self._value = [] # Internal storage for the value
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        props = {
            'Characteristic': self.characteristic.get_path(),
            'UUID': self.uuid,
            'Flags': dbus.Array(self.flags, signature='s')
        }
        # Include 'Value' if readable
        if 'read' in self.flags or 'secure-read' in self.flags:
             props['Value'] = dbus.Array(self.ReadValue({}), signature='y')
        return { 'org.bluez.GattDescriptor1' : props } # Use full interface name

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != 'org.bluez.GattDescriptor1':
            raise dbus.exceptions.DBusException('Invalid interface')
        return self.get_properties()['org.bluez.GattDescriptor1']

    @dbus.service.method('org.bluez.GattDescriptor1', in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        print(f'Default ReadValue called for Descriptor {self.uuid}')
        return dbus.Array(self._value, signature='y')

    @dbus.service.method('org.bluez.GattDescriptor1', in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print(f'Default WriteValue called for Descriptor {self.uuid}: {value}')
        self._value = bytes(value)


class ClientCharCfgDescriptor(Descriptor):
    """
    Client Characteristic Configuration Descriptor implementation.
    UUID 0x2902
    """
    CCCD_UUID = '2902' # Use short UUID

    def __init__(self, bus, index, characteristic):
        # CCCD is readable and writable by the client
        Descriptor.__init__(
                self, bus, index,
                self.CCCD_UUID,
                ['read', 'write'],
                characteristic)
        # Default value is 0x0000 (Notifications and Indications disabled)
        self._value = bytes([0x00, 0x00])

    def ReadValue(self, options):
        print(f"Reading CCCD value: {list(self._value)}")
        return dbus.Array(self._value, signature='y')

    def WriteValue(self, value, options):
        print(f"Writing CCCD value: {list(value)}")
        if len(value) != 2:
             raise dbus.exceptions.DBusException('Invalid Arguments') # Or InvalidValueLength

        # Update the value
        self._value = bytes(value)

        # Check the notification bit (bit 0)
        if self._value[0] & 0x01:
            print("Notifications enabled by client")
            if not self.characteristic.notifying:
                self.characteristic.StartNotify()
        else:
            print("Notifications disabled by client")
            if self.characteristic.notifying:
                self.characteristic.StopNotify()

        # Check the indication bit (bit 1) - We don't support indications here
        if self._value[0] & 0x02:
            print("Indications enabled by client (Not supported, ignoring)")


# --- HID Service and Characteristics (Based on new.py) ---

class HIDService(Service):
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, HID_SERVICE_UUID, True)
        # Instantiate and add characteristics in the correct order
        self.protocol_mode = ProtocolModeChar(bus, 0, self)
        self.report_map = ReportMapChar(bus, 1, self)
        self.hid_info = HIDInfoChar(bus, 2, self)
        self.hid_control = HIDCtrlPoint(bus, 3, self)
        self.mouse_input = MouseInputChar(bus, 4, self) # The characteristic we use

        self.add_characteristic(self.protocol_mode)
        self.add_characteristic(self.report_map)
        self.add_characteristic(self.hid_info)
        self.add_characteristic(self.hid_control)
        self.add_characteristic(self.mouse_input)


class ProtocolModeChar(Characteristic):
    def __init__(self, bus, index, service):
        # Use 'read' and 'write-without-response' as per HID spec (Boot Protocol optional)
        Characteristic.__init__(self, bus, index, PROTOCOL_MODE_UUID,
                                ['read', 'write-without-response'], service)
        self._value = [0x01] # Default to Report Protocol Mode

    def ReadValue(self, options):
        print("Read Protocol Mode")
        return dbus.Array(self._value, signature='y')

    def WriteValue(self, value, options):
        print(f"Write Protocol Mode: {value}")
        # Basic validation: expecting 1 byte, 0x00 (Boot) or 0x01 (Report)
        if len(value) == 1 and value[0] in (0, 1):
            self._value = [value[0]]
        else:
            print("Ignoring invalid write to Protocol Mode")
        # No response needed for write-without-response


class ReportMapChar(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, REPORT_MAP_UUID, ['read'], service)
        self._value = HID_REPORT_MAP # Store the report map bytes

    def ReadValue(self, options):
        print("Read Report Map")
        return dbus.Array(self._value, signature='y')


class HIDInfoChar(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, HID_INFO_UUID, ['read'], service)
        # bcdHID (e.g., 1.11), bCountryCode (0 = Not localized), Flags (Normal connect)
        self._value = struct.pack('<HBB', 0x0111, 0x00, 0x02) # v1.11, country 0, flags=normal

    def ReadValue(self, options):
        print("Read HID Information")
        return dbus.Array(self._value, signature='y')


class HIDCtrlPoint(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, HID_CONTROL_POINT_UUID,
                                ['write-without-response'], service)
        # This characteristic is write-only, no persistent value

    def WriteValue(self, value, options):
        # Handle Suspend (0x00) / Exit Suspend (0x01) if needed
        print(f"Write HID Control Point: {value}")
        if value and value[0] == 0x00:
            print("Suspend command received (ignored)")
        elif value and value[0] == 0x01:
            print("Exit Suspend command received (ignored)")
        # No response needed


class MouseInputChar(Characteristic):
    """
    HID Input Report characteristic for the mouse. Sends notifications.
    """
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, REPORT_UUID,
                                ['read', 'notify'], service)
        # Initial report (no buttons, no movement)
        # Format: buttons (1 byte), dx (1 byte), dy (1 byte), wheel (1 byte)
        self._value = bytes([0x00, 0x00, 0x00, 0x00])
        # Add the CCCD to allow notifications
        self.add_descriptor(ClientCharCfgDescriptor(bus, 0, self))

    def ReadValue(self, options):
        # Hosts might read this, return the last sent report or zeros
        print("Read Mouse Input Report (returning zeros)")
        return dbus.Array([0x00, 0x00, 0x00, 0x00], signature='y')

    def send_report(self, buttons=0, dx=0, dy=0, wheel=0):
        """Prepare and send the mouse report if notifying."""
        if not self.notifying:
            print("Cannot send report, not notifying.")
            return

        # Clamp dx, dy, wheel to signed 8-bit range [-127, 127]
        def clamp_s8(n):
            return max(-127, min(127, n))

        dx_c = clamp_s8(dx)
        dy_c = clamp_s8(dy)
        wheel_c = clamp_s8(wheel)

        # Pack the report data
        # buttons: Use lower 3 bits
        # dx, dy, wheel: signed 8-bit values
        report_bytes = struct.pack('<Bbbb', buttons & 0x07, dx_c, dy_c, wheel_c)
        self._value = report_bytes # Update internal value if needed

        print(f"Sending Report: btns={buttons & 0x07}, dx={dx_c}, dy={dy_c}, wheel={wheel_c}")

        # Send notification via PropertiesChanged signal
        self.PropertiesChanged(
            GATT_CHRC_IFACE,
            {'Value': dbus.Array(report_bytes, signature='y')},
            [] # invalidated properties
        )

# --- Main Execution ---
def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    adapter_path = find_adapter(bus)
    if not adapter_path:
        print("Bluetooth adapter not found.")
        sys.exit(1)

    print(f"Using adapter: {adapter_path}")

    # Get managers
    service_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE, adapter_path),
                                      GATT_MANAGER_IFACE)
    ad_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE, adapter_path),
                                 LE_ADVERTISING_MANAGER_IFACE)

    # Create application and advertisement
    app = Application(bus)
    advert = Advertisement(bus, 0)

    mainloop = GLib.MainLoop()

    # Callbacks for registration
    def reg_app_cb():
        print("GATT application registered")

    def reg_app_err_cb(error):
        print(f"Failed to register application: {error}")
        mainloop.quit()

    def reg_ad_cb():
        print("Advertisement registered")

    def reg_ad_err_cb(error):
        print(f"Failed to register advertisement: {error}")
        mainloop.quit()

    # Register Advertisement
    print("Registering advertisement...")
    ad_manager.RegisterAdvertisement(advert.get_path(), {},
                                     reply_handler=reg_ad_cb,
                                     error_handler=reg_ad_err_cb)

    # Register Application
    print("Registering GATT application...")
    service_manager.RegisterApplication(app.get_path(), {},
                                      reply_handler=reg_app_cb,
                                      error_handler=reg_app_err_cb)

    # Get the mouse characteristic instance for sending reports
    # Assumes HIDService is the first service and MouseInputChar is the last char
    mouse_char = app.services[0].characteristics[-1]
    if not isinstance(mouse_char, MouseInputChar):
         print("Error: Could not find MouseInputChar instance.")
         mainloop.quit()
         return

    print("BLE Mouse Ready. Connect from a host device.")
    print("Enter mouse movements in the format: dx dy [buttons]")
    print("Example: 10 0 (move right 10), 0 -5 (move up 5), 0 0 1 (left click)")
    print("Enter 'q' or Ctrl+C to quit.")

    # --- Simple CLI for input ---
    def cli_thread():
        while True:
            try:
                cmd = input("dx dy [btn] > ")
                if cmd.strip().lower() in ('q', 'quit', 'exit'):
                    mainloop.quit()
                    return
                parts = cmd.split()
                if len(parts) < 2:
                    print("Invalid input. Need at least dx and dy.")
                    continue

                dx = int(parts[0])
                dy = int(parts[1])
                buttons = int(parts[2]) if len(parts) > 2 else 0

                # Schedule the send_report call in the main GLib thread
                GLib.idle_add(mouse_char.send_report, buttons, dx, dy, 0) # wheel=0

            except ValueError:
                print("Invalid input. Please enter numbers.")
            except (EOFError, KeyboardInterrupt):
                mainloop.quit()
                break
            except Exception as e:
                print(f"An error occurred in CLI: {e}")
                mainloop.quit()
                break

    thread = threading.Thread(target=cli_thread, daemon=True)
    thread.start()

    try:
        mainloop.run()
    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt, exiting.")
    finally:
        # Cleanup (optional, BlueZ usually handles it)
        try:
            print("Unregistering advertisement...")
            ad_manager.UnregisterAdvertisement(advert.get_path())
        except Exception as e:
            print(f"Error unregistering advertisement: {e}")
        try:
            print("Unregistering application...")
            service_manager.UnregisterApplication(app.get_path())
        except Exception as e:
            print(f"Error unregistering application: {e}")
        print("Exited.")


if __name__ == '__main__':
    main()
