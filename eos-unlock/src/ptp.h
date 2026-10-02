#ifndef R50TOOL_PTP_H
#define R50TOOL_PTP_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include <libusb.h>

#define CANON_USB_VENDOR_ID 0x04A9
#define PTP_OC_GET_DEVICE_INFO 0x1001
#define PTP_OC_OPEN_SESSION    0x1002
#define PTP_OC_CLOSE_SESSION   0x1003
#define PTP_OC_CANON_EOS_GET_DEVICE_INFO_EX 0x9108
#define PTP_RC_OK              0x2001

#define PTP_CONTAINER_COMMAND  1
#define PTP_CONTAINER_DATA     2
#define PTP_CONTAINER_RESPONSE 3

struct ptp_u16_list {
    uint16_t *items;
    uint32_t count;
};

struct ptp_u32_list {
    uint32_t *items;
    uint32_t count;
};

struct ptp_eos_device_info {
    struct ptp_u32_list events;
    struct ptp_u32_list properties;
    struct ptp_u32_list unknown;
};

struct ptp_device_info {
    uint16_t standard_version;
    uint32_t vendor_extension_id;
    uint32_t effective_vendor_extension_id;
    uint16_t vendor_extension_version;
    char *vendor_extension_desc;
    uint16_t functional_mode;

    struct ptp_u16_list operations;
    struct ptp_u16_list events;
    struct ptp_u16_list properties;
    struct ptp_u16_list capture_formats;
    struct ptp_u16_list image_formats;

    char *manufacturer;
    char *model;
    char *device_version;
    char *serial_number;
};

struct ptp_transport {
    libusb_context *usb;
    libusb_device_handle *handle;
    int interface_number;
    uint8_t ep_in;
    uint8_t ep_out;
    bool claimed;
    bool session_open;
    uint32_t next_transaction;
    bool trace;
};

int ptp_transport_open_r50(struct ptp_transport *t, struct ptp_device_info *info, bool trace);
void ptp_transport_close(struct ptp_transport *t);
void ptp_device_info_free(struct ptp_device_info *info);
int ptp_get_eos_device_info(struct ptp_transport *t, struct ptp_eos_device_info *info);
void ptp_eos_device_info_free(struct ptp_eos_device_info *info);

void ptp_print_info(const struct ptp_device_info *info);
void ptp_print_capabilities(const struct ptp_device_info *info);
void ptp_print_eos_device_info(const struct ptp_eos_device_info *info);

const char *ptp_operation_name(uint16_t code);
const char *ptp_property_name(uint16_t code);
const char *ptp_event_name(uint16_t code);

#endif
