#ifndef GTP_EXTENSION_H
#define GTP_EXTENSION_H

#include <stdint.h>

typedef struct {
    uint8_t type;
    uint8_t length;
    char satellite_id[32];
    uint16_t beam_id;
    uint32_t sequence_number;
} gtp_satellite_extension_t;

#define GTP_EXT_TYPE_SATELLITE 0xA1

#endif