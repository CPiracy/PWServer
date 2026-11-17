#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <netinet/tcp.h>
#include <sched.h>
#include <semaphore.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

enum { MAX_PAYLOAD = 65536, WARMUP = 2000 };

struct shared_payload {
    sem_t request_ready;
    sem_t response_ready;
    unsigned char request[MAX_PAYLOAD];
    unsigned char response[MAX_PAYLOAD];
};

static void check(bool ok, const char *operation) {
    if (!ok) {
        perror(operation);
        exit(EXIT_FAILURE);
    }
}

static long parse_number(const char *text, long min, long max) {
    char *end;
    errno = 0;
    long value = strtol(text, &end, 10);
    if (errno || end == text || *end || value < min || value > max) {
        fprintf(stderr, "Invalid numeric argument: %s\n", text);
        exit(EXIT_FAILURE);
    }
    return value;
}

static void pin_cpu(int cpu) {
    cpu_set_t cpus;
    CPU_ZERO(&cpus);
    CPU_SET(cpu, &cpus);
    check(sched_setaffinity(0, sizeof(cpus), &cpus) == 0, "sched_setaffinity");
}

static uint64_t now_ns(clockid_t clock) {
    struct timespec now;
    check(clock_gettime(clock, &now) == 0, "clock_gettime");
    return (uint64_t)now.tv_sec * 1000000000 + now.tv_nsec;
}

static void transfer(int fd, void *buffer, size_t size, bool sending) {
    unsigned char *cursor = buffer;
    while (size > 0) {
        ssize_t count = sending ? write(fd, cursor, size) : read(fd, cursor, size);
        if (count < 0 && errno == EINTR) {
            continue;
        }
        if (count == 0) {
            errno = EPIPE;
        }
        check(count > 0, sending ? "write" : "read");
        cursor += count;
        size -= (size_t)count;
    }
}

static void socket_pair(bool tcp, int endpoints[2]) {
    int family = tcp ? AF_INET : AF_UNIX;
    int listener = socket(family, SOCK_STREAM, 0);
    check(listener >= 0, "socket listener");

    char directory[] = "/tmp/pw-ipc-XXXXXX";
    struct sockaddr_in inet_address = {
        .sin_family = AF_INET,
        .sin_addr.s_addr = htonl(INADDR_LOOPBACK),
    };
    struct sockaddr_un unix_address = {.sun_family = AF_UNIX};
    if (!tcp) {
        check(mkdtemp(directory) != NULL, "mkdtemp");
        snprintf(unix_address.sun_path, sizeof(unix_address.sun_path), "%s/echo", directory);
    }
    struct sockaddr *address = tcp ? (struct sockaddr *)&inet_address
                                   : (struct sockaddr *)&unix_address;
    socklen_t length = tcp ? sizeof(inet_address) : sizeof(unix_address);
    check(bind(listener, address, length) == 0, "bind");
    check(getsockname(listener, address, &length) == 0, "getsockname");
    check(listen(listener, 1) == 0, "listen");
    endpoints[0] = socket(family, SOCK_STREAM, 0);
    check(endpoints[0] >= 0, "socket requester");
    check(connect(endpoints[0], address, length) == 0, "connect");
    endpoints[1] = accept(listener, NULL, NULL);
    check(endpoints[1] >= 0, "accept");
    close(listener);
    if (tcp) {
        int enabled = 1;
        for (int i = 0; i < 2; i++) {
            check(setsockopt(endpoints[i], IPPROTO_TCP, TCP_NODELAY, &enabled,
                             sizeof(enabled)) == 0, "setsockopt TCP_NODELAY");
        }
    } else {
        check(unlink(unix_address.sun_path) == 0, "unlink socket");
        check(rmdir(directory) == 0, "rmdir socket directory");
    }
}

static struct shared_payload *make_shared(void) {
    char name[64];
    snprintf(name, sizeof(name), "/pw-ipc-%ld", (long)getpid());
    int fd = shm_open(name, O_CREAT | O_EXCL | O_RDWR, 0600);
    check(fd >= 0, "shm_open");
    check(shm_unlink(name) == 0, "shm_unlink");
    check(ftruncate(fd, sizeof(struct shared_payload)) == 0, "ftruncate");
    struct shared_payload *shared = mmap(NULL, sizeof(*shared), PROT_READ | PROT_WRITE,
                                         MAP_SHARED, fd, 0);
    check(shared != MAP_FAILED, "mmap");
    close(fd);
    check(sem_init(&shared->request_ready, 1, 0) == 0, "sem_init request");
    check(sem_init(&shared->response_ready, 1, 0) == 0, "sem_init response");
    return shared;
}

static void wait_ready(sem_t *ready) {
    int result;
    do {
        result = sem_wait(ready);
    } while (result < 0 && errno == EINTR);
    check(result == 0, "sem_wait");
}

static uint64_t echo_loop(int fd, struct shared_payload *shared, size_t size, int rounds) {
    unsigned char buffer[MAX_PAYLOAD];
    uint64_t started_cpu = 0;
    for (int i = -WARMUP; i < rounds; i++) {
        if (i == 0) {
            started_cpu = now_ns(CLOCK_PROCESS_CPUTIME_ID);
        }
        if (shared) {
            wait_ready(&shared->request_ready);
            memcpy(shared->response, shared->request, size);
            check(sem_post(&shared->response_ready) == 0, "sem_post response");
        } else {
            transfer(fd, buffer, size, false);
            transfer(fd, buffer, size, true);
        }
    }
    return now_ns(CLOCK_PROCESS_CPUTIME_ID) - started_cpu;
}

static int compare_ns(const void *a, const void *b) {
    uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b;
    return (x > y) - (x < y);
}

int main(int argc, char **argv) {
    if (argc != 6) {
        fprintf(stderr, "usage: %s tcp|unix|shm bytes rounds requester_cpu responder_cpu\n", argv[0]);
        return EXIT_FAILURE;
    }
    bool tcp = strcmp(argv[1], "tcp") == 0;
    bool use_shm = strcmp(argv[1], "shm") == 0;
    if (!tcp && !use_shm && strcmp(argv[1], "unix") != 0) {
        fprintf(stderr, "Unknown transport: %s\n", argv[1]);
        return EXIT_FAILURE;
    }
    size_t size = (size_t)parse_number(argv[2], 1, MAX_PAYLOAD);
    int rounds = (int)parse_number(argv[3], 1, 1000000);
    int requester_cpu = (int)parse_number(argv[4], 0, CPU_SETSIZE - 1);
    int responder_cpu = (int)parse_number(argv[5], 0, CPU_SETSIZE - 1);
    uint64_t *samples = calloc((size_t)rounds, sizeof(*samples));
    check(samples != NULL, "calloc");

    signal(SIGPIPE, SIG_IGN);
    alarm(35);
    int endpoints[2] = {-1, -1};
    struct shared_payload *shared = NULL;
    if (use_shm) {
        shared = make_shared();
    } else {
        socket_pair(tcp, endpoints);
    }

    int cpu_pipe[2];
    check(pipe(cpu_pipe) == 0, "pipe");
    pid_t child = fork();
    check(child >= 0, "fork");
    if (child == 0) {
        alarm(35);
        close(cpu_pipe[0]);
        if (!shared) {
            close(endpoints[0]);
        }
        pin_cpu(responder_cpu);
        uint64_t cpu = echo_loop(endpoints[1], shared, size, rounds);
        transfer(cpu_pipe[1], &cpu, sizeof(cpu), true);
        _exit(EXIT_SUCCESS);
    }

    close(cpu_pipe[1]);
    if (!shared) {
        close(endpoints[1]);
    }
    pin_cpu(requester_cpu);
    unsigned char sent[MAX_PAYLOAD], received[MAX_PAYLOAD];
    for (size_t i = 0; i < size; i++) {
        sent[i] = (unsigned char)(i * 167u + 31u);
    }

    uint64_t wall_start = 0, cpu_start = 0;
    for (int i = -WARMUP; i < rounds; i++) {
        if (i == 0) {
            cpu_start = now_ns(CLOCK_PROCESS_CPUTIME_ID);
            wall_start = now_ns(CLOCK_MONOTONIC_RAW);
        }
        sent[0] = (unsigned char)i;
        uint64_t sample_start = now_ns(CLOCK_MONOTONIC_RAW);
        if (shared) {
            memcpy(shared->request, sent, size);
            check(sem_post(&shared->request_ready) == 0, "sem_post request");
            wait_ready(&shared->response_ready);
            memcpy(received, shared->response, size);
        } else {
            transfer(endpoints[0], sent, size, true);
            transfer(endpoints[0], received, size, false);
        }
        uint64_t elapsed = now_ns(CLOCK_MONOTONIC_RAW) - sample_start;
        if (received[0] != sent[0] || (i == rounds - 1 && memcmp(sent, received, size) != 0)) {
            fputs("Echo payload mismatch\n", stderr);
            return EXIT_FAILURE;
        }
        if (i >= 0) {
            samples[i] = elapsed;
        }
    }
    uint64_t wall = now_ns(CLOCK_MONOTONIC_RAW) - wall_start;
    uint64_t cpu = now_ns(CLOCK_PROCESS_CPUTIME_ID) - cpu_start;
    uint64_t child_cpu;
    transfer(cpu_pipe[0], &child_cpu, sizeof(child_cpu), false);
    int status;
    check(waitpid(child, &status, 0) == child, "waitpid");
    if (!WIFEXITED(status) || WEXITSTATUS(status) != EXIT_SUCCESS) {
        fputs("Responder failed\n", stderr);
        return EXIT_FAILURE;
    }
    if (shared) {
        check(sem_destroy(&shared->request_ready) == 0, "sem_destroy request");
        check(sem_destroy(&shared->response_ready) == 0, "sem_destroy response");
        check(munmap(shared, sizeof(*shared)) == 0, "munmap");
    }

    qsort(samples, (size_t)rounds, sizeof(*samples), compare_ns);
    printf("%.3f,%.3f,%.3f,%.3f,%.3f\n",
           samples[((size_t)rounds - 1) * 50 / 100] / 1000.0,
           samples[((size_t)rounds - 1) * 95 / 100] / 1000.0,
           samples[((size_t)rounds - 1) * 99 / 100] / 1000.0,
           (cpu + child_cpu) / (1000.0 * rounds),
           (2.0 * size * rounds * 1e9) / (wall * 1048576.0));
    free(samples);
    return EXIT_SUCCESS;
}
