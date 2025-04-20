#include <stdio.h>
#include <fcntl.h>
#include <linux/input.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
    const char *devnode = (argc > 1) ? argv[1] : "/dev/input/event5";
    int fd = open(devnode, O_RDONLY);
    if (fd < 0) { perror("open"); return 1; }

    int buttons = 0, dx = 0, dy = 0, wheel = 0;
    struct input_event ev;

    while (read(fd, &ev, sizeof ev) == sizeof ev) {
        if (ev.type == EV_REL) {
            if      (ev.code == REL_X)     dx    += ev.value;
            else if (ev.code == REL_Y)     dy    += ev.value;
            else if (ev.code == REL_WHEEL) wheel += ev.value;
        } else if (ev.type == EV_KEY) {
            if      (ev.code == BTN_LEFT)   buttons = ev.value ? (buttons | 1) : (buttons & ~1);
            else if (ev.code == BTN_RIGHT)  buttons = ev.value ? (buttons | 2) : (buttons & ~2);
            else if (ev.code == BTN_MIDDLE) buttons = ev.value ? (buttons | 4) : (buttons & ~4);
        } else if (ev.type == EV_SYN) {
            /* dx/dy/wheel 누적값이 있으면 한 줄로 출력 */
            if (dx || dy || wheel) {
                printf("%d %d %d %d\n", dx, dy, wheel, buttons);
                fflush(stdout);
                dx = dy = wheel = 0;
            }
        }
    }
    return 0;
}