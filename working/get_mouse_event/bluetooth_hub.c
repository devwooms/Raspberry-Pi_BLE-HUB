#include <stdio.h>
#include <fcntl.h>
#include <linux/input.h>
#include <unistd.h>
#include <string.h>

int main() {
    const char *device = "/dev/input/event5";  // 블루투스 마우스의 실제 경로로 바꿔야 함
    struct input_event ev;

    printf("🔍 HID 릴레이 실행 중 (Ctrl+C 로 종료)\n");

    int fd = open(device, O_RDONLY);
    if (fd < 0) {
        perror("🔴 장치 열기 실패");
        return 1;
    }

    while (1) {
        ssize_t n = read(fd, &ev, sizeof(struct input_event));
        if (n == (ssize_t)sizeof(struct input_event)) {
            if (ev.type == EV_REL || ev.type == EV_KEY) {
                printf("🖱️ 이벤트: type=%d, code=%d, value=%d\n", ev.type, ev.code, ev.value);
            }
        }
    }

    close(fd);
    return 0;
}