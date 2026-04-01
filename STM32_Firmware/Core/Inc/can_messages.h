#ifndef CAN_MESSAGES_H
#define CAN_MESSAGES_H

#include <stdint.h>

/* ─── CAN Message IDs ─────────────────────────────────────────── */
#define CAN_ID_ECU1_VEHICLE     0x100U   /* Speed, Temp, Indicator  */
#define CAN_ID_ECU2_ENGINE      0x200U   /* RPM, Gear, Time         */

/* ─── DLC (Data Length Code) ─────────────────────────────────── */
#define CAN_DLC_ECU1            4U
#define CAN_DLC_ECU2            5U

/* ─── ECU1 – Vehicle Status ──────────────────────────────────── */
/* Byte layout in CAN frame:
   [0]     = speed high byte  (uint16, km/h, big-endian)
   [1]     = speed low byte
   [2]     = temperature      (uint8,  degrees C, 0-255)
   [3]     = indicator        (uint8,  0=OFF, 1=LEFT, 2=RIGHT)    */
typedef struct {
    uint16_t speed_kmh;
    uint8_t  temp_c;
    uint8_t  indicator;
} ECU1_Data_t;

/* ─── ECU2 – Engine & Time ───────────────────────────────────── */
/* Byte layout in CAN frame:
   [0]     = RPM high byte    (uint16, big-endian)
   [1]     = RPM low byte
   [2]     = gear             (uint8,  1-6)
   [3]     = time minutes     (uint8,  0-59)
   [4]     = time seconds     (uint8,  0-59)                      */
typedef struct {
    uint16_t rpm;
    uint8_t  gear;
    uint8_t  time_min;
    uint8_t  time_sec;
} ECU2_Data_t;

/* ─── Indicator states ───────────────────────────────────────── */
typedef enum {
    INDICATOR_OFF   = 0,
    INDICATOR_LEFT  = 1,
    INDICATOR_RIGHT = 2
} Indicator_t;

/* ─── Pack / Unpack API ──────────────────────────────────────── */
void ECU1_Pack  (const ECU1_Data_t *data, uint8_t *buf);
void ECU1_Unpack(const uint8_t *buf, ECU1_Data_t *data);

void ECU2_Pack  (const ECU2_Data_t *data, uint8_t *buf);
void ECU2_Unpack(const uint8_t *buf, ECU2_Data_t *data);

#endif /* CAN_MESSAGES_H */
