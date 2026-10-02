#include "ptp.h"

#include <stdio.h>
#include <string.h>

static void usage(const char *argv0) {
    fprintf(stderr,
            "Usage: %s [--trace] <command>\n"
            "\n"
            "Read-only foundation commands:\n"
            "  info      Show R50 identity and PTP versions\n"
            "  ptp-info  List advertised operations, events, and properties\n"
            "  eos-info      Query Canon EOS extended device information (read-only)\n"
            "  probe-region  Request Canon NetworkServerRegion (0xD14A) and dump returned EOS events\n"
            "  dump          Show identity plus advertised PTP capabilities\n"
            "\n"
            "Options:\n"
            "  --trace   Hex-dump raw PTP USB containers to stderr\n"
            "\n"
            "No persistent write/service commands are implemented in v0.1.\n",
            argv0);
}

int main(int argc, char **argv) {
    bool trace = false;
    const char *command = NULL;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--trace") == 0) trace = true;
        else if (!command) command = argv[i];
        else {
            usage(argv[0]);
            return 2;
        }
    }

    if (!command ||
        (strcmp(command, "info") != 0 &&
         strcmp(command, "ptp-info") != 0 &&
         strcmp(command, "eos-info") != 0 &&
         strcmp(command, "probe-region") != 0 &&
         strcmp(command, "dump") != 0)) {
        usage(argv[0]);
        return 2;
    }

    struct ptp_transport transport;
    struct ptp_device_info info;
    if (ptp_transport_open_r50(&transport, &info, trace) != 0) return 1;

    if (strcmp(command, "info") == 0) {
        ptp_print_info(&info);
    } else if (strcmp(command, "ptp-info") == 0) {
        ptp_print_capabilities(&info);
    } else if (strcmp(command, "eos-info") == 0) {
        struct ptp_eos_device_info eos_info;
        if (ptp_get_eos_device_info(&transport, &eos_info) != 0) {
            ptp_device_info_free(&info);
            ptp_transport_close(&transport);
            return 1;
        }
        ptp_print_eos_device_info(&eos_info);
        ptp_eos_device_info_free(&eos_info);
    } else if (strcmp(command, "probe-region") == 0) {
        if (ptp_probe_region(&transport) != 0) {
            ptp_device_info_free(&info);
            ptp_transport_close(&transport);
            return 1;
        }
    } else {
        ptp_print_info(&info);
        ptp_print_capabilities(&info);
    }

    ptp_device_info_free(&info);
    ptp_transport_close(&transport);
    return 0;
}
