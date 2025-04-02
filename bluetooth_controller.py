#!/usr/bin/env python3
import asyncio
from bleak import BleakScanner, BleakClient
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BluetoothController:
    def __init__(self):
        self.receiving_adapter = "hci0"  # 기본 블루투스 어댑터
        self.sending_adapter = "hci1"   # 추가된 블루투스 동글
        self.connected_devices: List[Dict] = []
        self.clients: Dict[str, BleakClient] = {}
        
    async def scan_devices(self, adapter: str) -> List[Dict]:
        """지정된 어댑터로 주변 블루투스 기기를 스캔합니다."""
        devices = []
        try:
            # BleakScanner를 사용하여 주변 기기 스캔
            scanner = BleakScanner()
            devices_found = await scanner.discover(timeout=5.0)
            
            for device in devices_found:
                devices.append({
                    'address': device.address,
                    'name': device.name or "Unknown Device",
                    'rssi': device.rssi,
                    'metadata': device.metadata
                })
                
        except Exception as e:
            logger.error(f"스캔 중 오류 발생: {e}")
        return devices

    async def connect_device(self, adapter: str, address: str) -> bool:
        """지정된 어댑터로 특정 기기에 연결합니다."""
        try:
            if address in self.clients:
                logger.warning(f"이미 연결된 기기입니다: {address}")
                return True

            # 새로운 BleakClient 생성 및 연결
            client = BleakClient(address, timeout=20.0)
            await client.connect()
            
            if client.is_connected:
                self.clients[address] = client
                self.connected_devices.append({
                    'address': address,
                    'client': client
                })
                logger.info(f"기기 연결 성공: {address}")
                return True
            else:
                logger.error(f"기기 연결 실패: {address}")
                return False
                
        except Exception as e:
            logger.error(f"연결 중 오류 발생: {e}")
            return False

    async def disconnect_device(self, adapter: str, address: str) -> bool:
        """연결된 기기를 연결 해제합니다."""
        try:
            if address in self.clients:
                client = self.clients[address]
                await client.disconnect()
                del self.clients[address]
                self.connected_devices = [d for d in self.connected_devices if d['address'] != address]
                logger.info(f"기기 연결 해제 성공: {address}")
                return True
            return False
        except Exception as e:
            logger.error(f"연결 해제 중 오류 발생: {e}")
            return False

    async def switch_connection(self, target_address: str) -> bool:
        """송신용 블루투스의 연결을 다른 기기로 전환합니다."""
        try:
            # 현재 연결된 모든 기기 연결 해제
            for device in self.connected_devices:
                await self.disconnect_device(self.sending_adapter, device['address'])
            
            # 새로운 기기 연결
            if await self.connect_device(self.sending_adapter, target_address):
                return True
            return False
        except Exception as e:
            logger.error(f"연결 전환 중 오류 발생: {e}")
            return False

    async def get_device_services(self, address: str) -> List[Dict]:
        """연결된 기기의 서비스 목록을 가져옵니다."""
        try:
            if address in self.clients:
                client = self.clients[address]
                services = await client.get_services()
                return [{'uuid': service.uuid, 'description': service.description} 
                        for service in services]
            return []
        except Exception as e:
            logger.error(f"서비스 목록 가져오기 중 오류 발생: {e}")
            return []

async def main():
    controller = BluetoothController()
    
    # 수신용 어댑터로 주변 기기 스캔
    print("\n수신용 블루투스로 주변 기기 스캔 중...")
    receiving_devices = await controller.scan_devices(controller.receiving_adapter)
    print("발견된 기기:")
    for device in receiving_devices:
        print(f"- {device['name']} ({device['address']}) [RSSI: {device['rssi']}]")
    
    # 송신용 어댑터로 주변 기기 스캔
    print("\n송신용 블루투스로 주변 기기 스캔 중...")
    sending_devices = await controller.scan_devices(controller.sending_adapter)
    print("발견된 기기:")
    for device in sending_devices:
        print(f"- {device['name']} ({device['address']}) [RSSI: {device['rssi']}]")

if __name__ == "__main__":
    asyncio.run(main()) 