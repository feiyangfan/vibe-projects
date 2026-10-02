#include "ptp.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PTP_USB_TIMEOUT_MS 3000
#define PTP_MAX_CONTAINER (1024U * 1024U)

static uint16_t get_le16(const uint8_t *p) {
    return (uint16_t)(p[0] | ((uint16_t)p[1] << 8));
}

static uint32_t get_le32(const uint8_t *p) {
    return (uint32_t)p[0] |
           ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) |
           ((uint32_t)p[3] << 24);
}

static void put_le16(uint8_t *p, uint16_t value) {
    p[0] = (uint8_t)(value & 0xff);
    p[1] = (uint8_t)((value >> 8) & 0xff);
}

static void put_le32(uint8_t *p, uint32_t value) {
    p[0] = (uint8_t)(value & 0xff);
    p[1] = (uint8_t)((value >> 8) & 0xff);
    p[2] = (uint8_t)((value >> 16) & 0xff);
    p[3] = (uint8_t)((value >> 24) & 0xff);
}

static void trace_bytes(bool enabled, const char *label,
                        const uint8_t *data, size_t len) {
    if (!enabled) return;

    fprintf(stderr, "%s (%zu bytes)\n", label, len);
    for (size_t i = 0; i < len; i += 16) {
        fprintf(stderr, "  %04zx: ", i);
        size_t end = i + 16;
        if (end > len) end = len;
        for (size_t j = i; j < end; ++j) {
            fprintf(stderr, "%02x ", data[j]);
        }
        fputc('\n', stderr);
    }
}

static int bulk_write_all(struct ptp_transport *t,
                          const uint8_t *buf, size_t len) {
    size_t offset = 0;

    while (offset < len) {
        int transferred = 0;
        int rc = libusb_bulk_transfer(
            t->handle,
            t->ep_out,
            (unsigned char *)(buf + offset),
            (int)(len - offset),
            &transferred,
            PTP_USB_TIMEOUT_MS
        );

        if (rc != 0) {
            fprintf(stderr, "USB write failed: %s\n", libusb_error_name(rc));
            return -1;
        }
        if (transferred <= 0) {
            fprintf(stderr, "USB write made no progress\n");
            return -1;
        }
        offset += (size_t)transferred;
    }

    return 0;
}

static int bulk_read_some(struct ptp_transport *t,
                          uint8_t *buf, size_t capacity,
                          size_t *out_len) {
    if (capacity == 0 || capacity > INT_MAX) return -1;

    int transferred = 0;
    int rc = libusb_bulk_transfer(
        t->handle,
        t->ep_in,
        buf,
        (int)capacity,
        &transferred,
        PTP_USB_TIMEOUT_MS
    );

    if (rc != 0) {
        fprintf(stderr, "USB read failed: %s\n", libusb_error_name(rc));
        return -1;
    }
    if (transferred <= 0) {
        fprintf(stderr, "USB read made no progress\n");
        return -1;
    }

    *out_len = (size_t)transferred;
    return 0;
}

static int recv_container(struct ptp_transport *t,
                          uint8_t **out, size_t *out_len) {
    /*
     * Do not read the 12-byte PTP header into a 12-byte libusb buffer.
     * Canon bodies may deliver the header plus payload in the same USB bulk
     * packet. On macOS/libusb a too-small transfer buffer then reports
     * LIBUSB_ERROR_OVERFLOW and discards the packet.
     *
     * Instead, receive a generously sized first chunk, inspect the PTP
     * container length, then read any remaining bytes.
     */
    const size_t first_capacity = 64U * 1024U;
    uint8_t *buf = calloc(1, PTP_MAX_CONTAINER);
    if (!buf) {
        fprintf(stderr, "Out of memory\n");
        return -1;
    }

    size_t received = 0;
    size_t chunk = 0;

    if (bulk_read_some(t, buf, first_capacity, &chunk) != 0) {
        free(buf);
        return -1;
    }
    received += chunk;

    if (received < 12) {
        fprintf(stderr, "Short PTP container header: %zu bytes\n", received);
        free(buf);
        return -1;
    }

    uint32_t length = get_le32(buf);
    if (length < 12 || length > PTP_MAX_CONTAINER) {
        fprintf(stderr, "Invalid PTP container length: %u\n", length);
        free(buf);
        return -1;
    }

    if (received > length) {
        fprintf(stderr,
                "USB read returned %zu bytes for a %u-byte PTP container\n",
                received, length);
        free(buf);
        return -1;
    }

    while (received < length) {
        size_t remaining = (size_t)length - received;
        if (bulk_read_some(t, buf + received, remaining, &chunk) != 0) {
            free(buf);
            return -1;
        }
        received += chunk;
    }

    trace_bytes(t->trace, "RX", buf, received);
    *out = buf;
    *out_len = received;
    return 0;
}

/*
 * Foundation safety gate.
 *
 * There is intentionally no arbitrary-opcode path. Until the Canon service
 * protocol is understood, the transport may transmit only standard PTP
 * identity/session operations plus explicitly reviewed read-only Canon
 * queries. OpenSession/CloseSession change only transient connection state.
 */
static bool allowed_foundation_opcode(uint16_t opcode) {
    return opcode == PTP_OC_GET_DEVICE_INFO ||
           opcode == PTP_OC_OPEN_SESSION ||
           opcode == PTP_OC_CLOSE_SESSION ||
           opcode == PTP_OC_CANON_EOS_GET_DEVICE_INFO_EX ||
           opcode == PTP_OC_CANON_EOS_GET_EVENT ||
           opcode == PTP_OC_CANON_EOS_REQUEST_PROP;
}

static int send_command(struct ptp_transport *t,
                        uint16_t opcode,
                        uint32_t transaction,
                        const uint32_t *params,
                        size_t param_count) {
    if (!allowed_foundation_opcode(opcode)) {
        fprintf(stderr,
                "Refusing opcode 0x%04x: not on the reviewed "
                "read-only foundation allowlist\n",
                opcode);
        return -1;
    }

    if (param_count > 5) return -1;

    uint8_t buf[12 + 5 * 4];
    size_t length = 12 + param_count * 4;
    memset(buf, 0, sizeof(buf));

    put_le32(buf + 0, (uint32_t)length);
    put_le16(buf + 4, PTP_CONTAINER_COMMAND);
    put_le16(buf + 6, opcode);
    put_le32(buf + 8, transaction);

    for (size_t i = 0; i < param_count; ++i) {
        put_le32(buf + 12 + i * 4, params[i]);
    }

    trace_bytes(t->trace, "TX", buf, length);
    return bulk_write_all(t, buf, length);
}

static int expect_response(struct ptp_transport *t,
                           uint16_t expected_code,
                           uint32_t transaction) {
    uint8_t *buf = NULL;
    size_t len = 0;

    if (recv_container(t, &buf, &len) != 0) return -1;

    int ok = 0;
    if (get_le16(buf + 4) != PTP_CONTAINER_RESPONSE) {
        fprintf(stderr, "Expected PTP response container, got type %u\n",
                get_le16(buf + 4));
        ok = -1;
    } else if (get_le32(buf + 8) != transaction) {
        fprintf(stderr, "PTP response transaction mismatch\n");
        ok = -1;
    } else if (get_le16(buf + 6) != expected_code) {
        fprintf(stderr, "PTP response 0x%04x (expected 0x%04x)\n",
                get_le16(buf + 6), expected_code);
        ok = -1;
    }

    free(buf);
    return ok;
}

struct cursor {
    const uint8_t *p;
    const uint8_t *end;
};

static int cur_u16(struct cursor *c, uint16_t *out) {
    if ((size_t)(c->end - c->p) < 2) return -1;
    *out = get_le16(c->p);
    c->p += 2;
    return 0;
}

static int cur_u32(struct cursor *c, uint32_t *out) {
    if ((size_t)(c->end - c->p) < 4) return -1;
    *out = get_le32(c->p);
    c->p += 4;
    return 0;
}

static int append_utf8(char **dst, size_t *used,
                       size_t capacity, uint16_t cp) {
    if (cp <= 0x7f) {
        if (*used + 1 >= capacity) return -1;
        (*dst)[(*used)++] = (char)cp;
    } else if (cp <= 0x7ff) {
        if (*used + 2 >= capacity) return -1;
        (*dst)[(*used)++] = (char)(0xc0 | (cp >> 6));
        (*dst)[(*used)++] = (char)(0x80 | (cp & 0x3f));
    } else {
        if (*used + 3 >= capacity) return -1;
        (*dst)[(*used)++] = (char)(0xe0 | (cp >> 12));
        (*dst)[(*used)++] = (char)(0x80 | ((cp >> 6) & 0x3f));
        (*dst)[(*used)++] = (char)(0x80 | (cp & 0x3f));
    }
    return 0;
}

static int cur_ptp_string(struct cursor *c, char **out) {
    if (c->p >= c->end) return -1;

    uint8_t chars = *c->p++;
    if (chars == 0) {
        *out = calloc(1, 1);
        return *out ? 0 : -1;
    }

    size_t bytes_needed = (size_t)chars * 2;
    if ((size_t)(c->end - c->p) < bytes_needed) return -1;

    size_t capacity = (size_t)chars * 3 + 1;
    char *s = calloc(1, capacity);
    if (!s) return -1;

    size_t used = 0;
    for (uint8_t i = 0; i < chars; ++i) {
        uint16_t cp = get_le16(c->p);
        c->p += 2;

        if (cp == 0) break;
        if (append_utf8(&s, &used, capacity, cp) != 0) {
            free(s);
            return -1;
        }
    }

    s[used] = '\0';
    *out = s;
    return 0;
}

static int cur_u16_array(struct cursor *c, struct ptp_u16_list *out) {
    uint32_t count = 0;

    if (cur_u32(c, &count) != 0) return -1;
    if (count > 65536 ||
        (size_t)(c->end - c->p) < (size_t)count * 2) {
        return -1;
    }

    uint16_t *items = NULL;
    if (count) {
        items = calloc(count, sizeof(*items));
        if (!items) return -1;
    }

    for (uint32_t i = 0; i < count; ++i) {
        if (cur_u16(c, &items[i]) != 0) {
            free(items);
            return -1;
        }
    }

    out->items = items;
    out->count = count;
    return 0;
}

static int cur_u32_array(struct cursor *c, struct ptp_u32_list *out) {
    uint32_t count = 0;

    if (cur_u32(c, &count) != 0) return -1;
    if (count > 65536 ||
        (size_t)(c->end - c->p) < (size_t)count * 4) {
        return -1;
    }

    uint32_t *items = NULL;
    if (count) {
        items = calloc(count, sizeof(*items));
        if (!items) return -1;
    }

    for (uint32_t i = 0; i < count; ++i) {
        if (cur_u32(c, &items[i]) != 0) {
            free(items);
            return -1;
        }
    }

    out->items = items;
    out->count = count;
    return 0;
}


static int parse_device_info(const uint8_t *data,
                             size_t len,
                             struct ptp_device_info *info) {
    struct cursor c = {data, data + len};
    memset(info, 0, sizeof(*info));

    if (cur_u16(&c, &info->standard_version) != 0 ||
        cur_u32(&c, &info->vendor_extension_id) != 0 ||
        cur_u16(&c, &info->vendor_extension_version) != 0 ||
        cur_ptp_string(&c, &info->vendor_extension_desc) != 0 ||
        cur_u16(&c, &info->functional_mode) != 0 ||
        cur_u16_array(&c, &info->operations) != 0 ||
        cur_u16_array(&c, &info->events) != 0 ||
        cur_u16_array(&c, &info->properties) != 0 ||
        cur_u16_array(&c, &info->capture_formats) != 0 ||
        cur_u16_array(&c, &info->image_formats) != 0 ||
        cur_ptp_string(&c, &info->manufacturer) != 0 ||
        cur_ptp_string(&c, &info->model) != 0 ||
        cur_ptp_string(&c, &info->device_version) != 0 ||
        cur_ptp_string(&c, &info->serial_number) != 0) {
        ptp_device_info_free(info);
        return -1;
    }

    return 0;
}

static int get_device_info(struct ptp_transport *t,
                           struct ptp_device_info *info) {
    const uint32_t tx = 0;

    if (send_command(t, PTP_OC_GET_DEVICE_INFO, tx, NULL, 0) != 0) {
        return -1;
    }

    uint8_t *data = NULL;
    size_t data_len = 0;

    if (recv_container(t, &data, &data_len) != 0) return -1;

    if (get_le16(data + 4) != PTP_CONTAINER_DATA ||
        get_le16(data + 6) != PTP_OC_GET_DEVICE_INFO ||
        get_le32(data + 8) != tx) {
        fprintf(stderr,
                "Unexpected PTP container while reading device info\n");
        free(data);
        return -1;
    }

    if (parse_device_info(data + 12, data_len - 12, info) != 0) {
        fprintf(stderr, "Unable to parse PTP DeviceInfo dataset\n");
        free(data);
        return -1;
    }

    free(data);

    if (expect_response(t, PTP_RC_OK, tx) != 0) {
        ptp_device_info_free(info);
        return -1;
    }

    return 0;
}

static void print_raw_eos_events(const uint8_t *data, size_t len) {
    printf("EOS event payload (%zu bytes):\n", len);
    for (size_t i = 0; i < len; i += 16) {
        printf("  %04zx: ", i);
        size_t end = i + 16;
        if (end > len) end = len;
        for (size_t j = i; j < end; ++j) {
            printf("%02x ", data[j]);
        }
        putchar('\n');
    }

    /*
     * Canon EOS event records are length-prefixed:
     *   u32 size, u32 event_code, ...
     * For PropValueChanged (0xC189), the next u32 is the property code.
     * We intentionally print the remaining bytes raw because the datatype
     * depends on the property and D14A is not advertised by this R50.
     */
    size_t off = 0;
    while (off + 8 <= len) {
        uint32_t size = get_le32(data + off);
        uint32_t code = get_le32(data + off + 4);

        if (size == 8 && code == 0) {
            printf("  event terminator\n");
            break;
        }
        if (size < 8 || off + size > len) {
            printf("  malformed/unknown event framing at offset 0x%zx\n", off);
            break;
        }

        printf("  event: code=0x%08x size=%u", code, size);
        if (code == 0x0000c189 && size >= 12) {
            uint32_t prop = get_le32(data + off + 8);
            printf(" property=0x%08x value-bytes=", prop);
            for (size_t j = off + 12; j < off + size; ++j) {
                printf("%02x", data[j]);
            }
        }
        putchar('\n');
        off += size;
    }
}

int ptp_probe_region(struct ptp_transport *t) {
    if (!t->session_open) {
        fprintf(stderr, "probe-region requires an open PTP session\n");
        return -1;
    }

    const uint32_t prop = PTP_DPC_CANON_EOS_NETWORK_REGION;
    uint32_t tx = t->next_transaction++;

    printf("Requesting Canon EOS property 0x%04x (NetworkServerRegion)\n",
           prop);

    if (send_command(t, PTP_OC_CANON_EOS_REQUEST_PROP,
                     tx, &prop, 1) != 0) {
        return -1;
    }
    if (expect_response(t, PTP_RC_OK, tx) != 0) {
        return -1;
    }

    tx = t->next_transaction++;
    if (send_command(t, PTP_OC_CANON_EOS_GET_EVENT,
                     tx, NULL, 0) != 0) {
        return -1;
    }

    uint8_t *data = NULL;
    size_t data_len = 0;
    if (recv_container(t, &data, &data_len) != 0) return -1;

    if (get_le16(data + 4) == PTP_CONTAINER_RESPONSE) {
        uint16_t rc = get_le16(data + 6);
        fprintf(stderr,
                "EOS_GetEvent returned PTP response 0x%04x without data\n",
                rc);
        free(data);
        return -1;
    }

    if (get_le16(data + 4) != PTP_CONTAINER_DATA ||
        get_le16(data + 6) != PTP_OC_CANON_EOS_GET_EVENT ||
        get_le32(data + 8) != tx) {
        fprintf(stderr, "Unexpected PTP container for EOS_GetEvent\n");
        free(data);
        return -1;
    }

    if (data_len < 12) {
        fprintf(stderr, "EOS_GetEvent data container is too short\n");
        free(data);
        return -1;
    }

    print_raw_eos_events(data + 12, data_len - 12);
    free(data);

    if (expect_response(t, PTP_RC_OK, tx) != 0) {
        return -1;
    }

    return 0;
}

int ptp_get_eos_device_info(struct ptp_transport *t,
                            struct ptp_eos_device_info *info) {
    memset(info, 0, sizeof(*info));

    if (!t->session_open) {
        fprintf(stderr, "EOS_GetDeviceInfoEx requires an open PTP session\n");
        return -1;
    }

    uint32_t tx = t->next_transaction++;

    if (send_command(t, PTP_OC_CANON_EOS_GET_DEVICE_INFO_EX,
                     tx, NULL, 0) != 0) {
        return -1;
    }

    uint8_t *data = NULL;
    size_t data_len = 0;
    if (recv_container(t, &data, &data_len) != 0) return -1;

    if (get_le16(data + 4) == PTP_CONTAINER_RESPONSE) {
        uint16_t rc = get_le16(data + 6);
        fprintf(stderr,
                "EOS_GetDeviceInfoEx returned PTP response 0x%04x "
                "without a data phase\n",
                rc);
        free(data);
        return -1;
    }

    if (get_le16(data + 4) != PTP_CONTAINER_DATA ||
        get_le16(data + 6) != PTP_OC_CANON_EOS_GET_DEVICE_INFO_EX ||
        get_le32(data + 8) != tx) {
        fprintf(stderr,
                "Unexpected PTP container for EOS_GetDeviceInfoEx\n");
        free(data);
        return -1;
    }

    /*
     * libgphoto2's ptp_unpack_EOS_DI starts at offset 4 of the data
     * payload, then unpacks three uint32 arrays: Events, DeviceProps,
     * and an unknown/capability array.
     */
    if (data_len < 16) {
        fprintf(stderr, "EOS_GetDeviceInfoEx payload is too short\n");
        free(data);
        return -1;
    }

    struct cursor cur = {data + 16, data + data_len};

    if (cur_u32_array(&cur, &info->events) != 0 ||
        cur_u32_array(&cur, &info->properties) != 0 ||
        cur_u32_array(&cur, &info->unknown) != 0) {
        fprintf(stderr, "Unable to parse EOS_GetDeviceInfoEx payload\n");
        free(data);
        ptp_eos_device_info_free(info);
        return -1;
    }

    free(data);

    if (expect_response(t, PTP_RC_OK, tx) != 0) {
        ptp_eos_device_info_free(info);
        return -1;
    }

    return 0;
}

static int open_session(struct ptp_transport *t) {
    uint32_t session_id = 1;
    uint32_t tx = 0;

    if (send_command(t, PTP_OC_OPEN_SESSION,
                     tx, &session_id, 1) != 0) {
        return -1;
    }

    if (expect_response(t, PTP_RC_OK, tx) != 0) return -1;

    t->session_open = true;
    t->next_transaction = 1;
    return 0;
}

static void close_session(struct ptp_transport *t) {
    if (!t->session_open) return;

    uint32_t tx = t->next_transaction++;
    if (send_command(t, PTP_OC_CLOSE_SESSION,
                     tx, NULL, 0) == 0) {
        (void)expect_response(t, PTP_RC_OK, tx);
    }

    t->session_open = false;
}

static int find_ptp_interface(libusb_device *dev,
                              int *interface_number,
                              uint8_t *ep_in,
                              uint8_t *ep_out) {
    struct libusb_config_descriptor *config = NULL;
    int rc = libusb_get_active_config_descriptor(dev, &config);

    if (rc != 0) return -1;

    int found = -1;

    for (uint8_t i = 0;
         i < config->bNumInterfaces && found != 0;
         ++i) {
        const struct libusb_interface *iface = &config->interface[i];

        for (int a = 0;
             a < iface->num_altsetting && found != 0;
             ++a) {
            const struct libusb_interface_descriptor *alt =
                &iface->altsetting[a];

            if (alt->bInterfaceClass != LIBUSB_CLASS_IMAGE) continue;

            uint8_t in = 0;
            uint8_t out = 0;

            for (uint8_t e = 0; e < alt->bNumEndpoints; ++e) {
                const struct libusb_endpoint_descriptor *ep =
                    &alt->endpoint[e];

                if ((ep->bmAttributes & LIBUSB_TRANSFER_TYPE_MASK) !=
                    LIBUSB_TRANSFER_TYPE_BULK) {
                    continue;
                }

                if ((ep->bEndpointAddress &
                     LIBUSB_ENDPOINT_DIR_MASK) == LIBUSB_ENDPOINT_IN) {
                    in = ep->bEndpointAddress;
                } else {
                    out = ep->bEndpointAddress;
                }
            }

            if (in && out) {
                *interface_number = alt->bInterfaceNumber;
                *ep_in = in;
                *ep_out = out;
                found = 0;
            }
        }
    }

    libusb_free_config_descriptor(config);
    return found;
}

int ptp_transport_open_r50(struct ptp_transport *t,
                           struct ptp_device_info *info,
                           bool trace) {
    memset(t, 0, sizeof(*t));
    memset(info, 0, sizeof(*info));

    t->interface_number = -1;
    t->trace = trace;

    int rc = libusb_init(&t->usb);
    if (rc != 0) {
        fprintf(stderr, "libusb init failed: %s\n",
                libusb_error_name(rc));
        return -1;
    }

    libusb_device **list = NULL;
    ssize_t count = libusb_get_device_list(t->usb, &list);

    if (count < 0) {
        fprintf(stderr, "Unable to enumerate USB devices: %s\n",
                libusb_error_name((int)count));
        ptp_transport_close(t);
        return -1;
    }

    libusb_device *candidate = NULL;

    for (ssize_t i = 0; i < count; ++i) {
        struct libusb_device_descriptor desc;

        if (libusb_get_device_descriptor(list[i], &desc) != 0) {
            continue;
        }
        if (desc.idVendor != CANON_USB_VENDOR_ID) continue;

        int iface = -1;
        uint8_t in = 0;
        uint8_t out = 0;

        if (find_ptp_interface(list[i], &iface, &in, &out) == 0) {
            candidate = libusb_ref_device(list[i]);
            t->interface_number = iface;
            t->ep_in = in;
            t->ep_out = out;
            break;
        }
    }

    libusb_free_device_list(list, 1);

    if (!candidate) {
        fprintf(stderr,
                "No Canon PTP camera found. Check USB mode/cable "
                "and close EOS Utility/Photos.\n");
        ptp_transport_close(t);
        return -1;
    }

    rc = libusb_open(candidate, &t->handle);
    libusb_unref_device(candidate);

    if (rc != 0) {
        fprintf(stderr, "Unable to open Canon USB device: %s\n",
                libusb_error_name(rc));
        ptp_transport_close(t);
        return -1;
    }

    rc = libusb_claim_interface(t->handle, t->interface_number);
    if (rc != 0) {
        fprintf(stderr, "Unable to claim PTP interface: %s\n",
                libusb_error_name(rc));
        fprintf(stderr,
                "On macOS, close Photos/Image Capture/EOS Utility. "
                "If PTPCamera still owns the device, reconnect "
                "the camera and retry.\n");
        ptp_transport_close(t);
        return -1;
    }

    t->claimed = true;

    if (get_device_info(t, info) != 0) {
        ptp_transport_close(t);
        return -1;
    }

    /*
     * Newer Canon bodies commonly report the Microsoft/MTP vendor extension
     * ID (0x00000006) in raw DeviceInfo. libgphoto2 applies the same fix-up:
     * when the USB VID/manufacturer identifies Canon, treat the effective
     * vendor extension as Canon (0x0000000b).
     */
    info->effective_vendor_extension_id = info->vendor_extension_id;
    if (info->vendor_extension_id == 0x00000006 &&
        info->manufacturer &&
        strstr(info->manufacturer, "Canon") != NULL) {
        info->effective_vendor_extension_id = 0x0000000b;
    }

    if (!info->manufacturer ||
        !info->model ||
        strstr(info->manufacturer, "Canon") == NULL ||
        strcmp(info->model, "Canon EOS R50") != 0) {
        fprintf(stderr,
                "Refusing device: expected Canon EOS R50, "
                "got '%s' / '%s'\n",
                info->manufacturer ? info->manufacturer : "?",
                info->model ? info->model : "?");
        ptp_device_info_free(info);
        ptp_transport_close(t);
        return -1;
    }

    if (open_session(t) != 0) {
        fprintf(stderr, "Unable to open PTP session\n");
        ptp_device_info_free(info);
        ptp_transport_close(t);
        return -1;
    }

    return 0;
}

void ptp_transport_close(struct ptp_transport *t) {
    if (!t) return;

    if (t->handle) close_session(t);

    if (t->handle && t->claimed) {
        libusb_release_interface(t->handle, t->interface_number);
    }

    if (t->handle) libusb_close(t->handle);
    if (t->usb) libusb_exit(t->usb);

    memset(t, 0, sizeof(*t));
    t->interface_number = -1;
}

void ptp_eos_device_info_free(struct ptp_eos_device_info *info) {
    if (!info) return;
    free(info->events.items);
    free(info->properties.items);
    free(info->unknown.items);
    memset(info, 0, sizeof(*info));
}

void ptp_device_info_free(struct ptp_device_info *info) {
    if (!info) return;

    free(info->vendor_extension_desc);
    free(info->operations.items);
    free(info->events.items);
    free(info->properties.items);
    free(info->capture_formats.items);
    free(info->image_formats.items);
    free(info->manufacturer);
    free(info->model);
    free(info->device_version);
    free(info->serial_number);

    memset(info, 0, sizeof(*info));
}

const char *ptp_operation_name(uint16_t code) {
    switch (code) {
        case 0x1001: return "GetDeviceInfo";
        case 0x1002: return "OpenSession";
        case 0x1003: return "CloseSession";
        case 0x1004: return "GetStorageIDs";
        case 0x1005: return "GetStorageInfo";
        case 0x1006: return "GetNumObjects";
        case 0x1007: return "GetObjectHandles";
        case 0x1008: return "GetObjectInfo";
        case 0x1009: return "GetObject";
        case 0x100a: return "GetThumb";
        case 0x100b: return "DeleteObject";
        case 0x100c: return "SendObjectInfo";
        case 0x100d: return "SendObject";
        case 0x100f: return "FormatStore";
        case 0x1014: return "GetDevicePropDesc";
        case 0x1016: return "SetDevicePropValue";
        case 0x101b: return "GetPartialObject";
        case 0x9108: return "EOS_GetDeviceInfoEx";
        case 0x9110: return "EOS_SetDevicePropValueEx";
        case 0x9114: return "EOS_SetRemoteMode";
        case 0x9115: return "EOS_SetEventMode";
        case 0x9116: return "EOS_GetEvent";
        case 0x911f: return "EOS_UpdateFirmware";
        case 0x9127: return "EOS_RequestDevicePropValue";
        case 0x9136: return "EOS_GetLensAdjust";
        case 0x9137: return "EOS_SetLensAdjust";
        case 0x913f: return "EOS_GetCameraSupport";
        default: return NULL;
    }
}

const char *ptp_property_name(uint16_t code) {
    switch (code) {
        case 0x5001: return "BatteryLevel";
        case 0xd303: return "Unknown_D303";
        case 0xd402: return "FriendlyDeviceName";
        case 0xd406: return "SessionInitiatorInfo";
        case 0xd407: return "PerceivedDeviceType";
        default: return NULL;
    }
}

const char *ptp_event_name(uint16_t code) {
    switch (code) {
        case 0x4002: return "ObjectAdded";
        case 0x4003: return "ObjectRemoved";
        case 0x4006: return "DevicePropChanged";
        case 0x4009: return "RequestObjectTransfer";
        default: return NULL;
    }
}

void ptp_print_info(const struct ptp_device_info *info) {
    printf("Manufacturer: %s\n",
           info->manufacturer ? info->manufacturer : "");
    printf("Model: %s\n",
           info->model ? info->model : "");
    printf("Device version: %s\n",
           info->device_version ? info->device_version : "");
    printf("Serial: %s\n",
           info->serial_number ? info->serial_number : "");
    printf("PTP standard: %u.%02u\n",
           info->standard_version / 100,
           info->standard_version % 100);
    printf("Raw vendor extension ID: 0x%08x\n",
           info->vendor_extension_id);
    printf("Effective vendor extension ID: 0x%08x%s\n",
           info->effective_vendor_extension_id,
           (info->effective_vendor_extension_id != info->vendor_extension_id)
               ? " (Canon normalization)"
               : "");
    printf("Vendor extension version: %u\n",
           info->vendor_extension_version);
    printf("Vendor extension description: %s\n",
           info->vendor_extension_desc
               ? info->vendor_extension_desc
               : "");
}

static void print_code_list(const char *heading,
                            const struct ptp_u16_list *list,
                            const char *(*name_fn)(uint16_t)) {
    printf("\n%s (%u):\n", heading, list->count);

    for (uint32_t i = 0; i < list->count; ++i) {
        uint16_t code = list->items[i];
        const char *name = name_fn ? name_fn(code) : NULL;

        if (name) {
            printf("  0x%04x  %s\n", code, name);
        } else {
            printf("  0x%04x  Unknown\n", code);
        }
    }
}

void ptp_print_capabilities(const struct ptp_device_info *info) {
    print_code_list("Operations",
                    &info->operations,
                    ptp_operation_name);
    print_code_list("Events",
                    &info->events,
                    ptp_event_name);
    print_code_list("Device properties",
                    &info->properties,
                    ptp_property_name);
}

static void print_u32_code_list(const char *heading,
                                const struct ptp_u32_list *list) {
    printf("\n%s (%u):\n", heading, list->count);
    for (uint32_t i = 0; i < list->count; ++i) {
        printf("  0x%08x\n", list->items[i]);
    }
}

void ptp_print_eos_device_info(const struct ptp_eos_device_info *info) {
    print_u32_code_list("EOS events", &info->events);
    print_u32_code_list("EOS device properties", &info->properties);
    print_u32_code_list("EOS unknown/capability values", &info->unknown);
}
