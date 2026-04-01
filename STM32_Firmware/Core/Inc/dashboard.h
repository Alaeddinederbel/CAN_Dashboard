#ifndef DASHBOARD_H
#define DASHBOARD_H

#include "can_messages.h"

/* ─── Aggregated dashboard state ─────────────────────────────── */
typedef struct {
    uint16_t    speed_kmh;
    uint16_t    rpm;
    uint8_t     gear;
    uint8_t     temp_c;
    uint8_t     indicator;
    uint8_t     time_min;
    uint8_t     time_sec;
    uint8_t     ecu1_valid;   /* 1 = fresh data received          */
    uint8_t     ecu2_valid;   /* 1 = fresh data received          */
} Dashboard_State_t;

/* ─── API ────────────────────────────────────────────────────── */
void Dashboard_Init   (void);
void Dashboard_Update1(const ECU1_Data_t *d);
void Dashboard_Update2(const ECU2_Data_t *d);
void Dashboard_Print  (void);

/* Expose state for external read (e.g. RTOS task) */
const Dashboard_State_t* Dashboard_GetState(void);

#endif /* DASHBOARD_H */
