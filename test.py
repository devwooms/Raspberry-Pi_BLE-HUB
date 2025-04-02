import asyncio
from bleak import BleakScanner

async def check_bluetooth_hardware():
    try:
        print("블루투스 장치 스캔 중...")
        devices = await BleakScanner.discover()
        
        if not devices:
            print("주변에 블루투스 장치가 없습니다.")
            return
        
        print("\n=== 발견된 블루투스 장치 ===")
        for device in devices:
            print(f"장치 이름: {device.name or '이름 없음'}")
            print(f"MAC 주소: {device.address}")
            print(f"RSSI: {device.rssi} dBm")
            print("-" * 30)
            
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(check_bluetooth_hardware())