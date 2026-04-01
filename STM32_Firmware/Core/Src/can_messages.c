/**
 * @file    can_messages.c
 * @brief   CAN frame pack / unpack for ECU1 and ECU2.
 *
 * These functions are pure C with no HAL dependency.
 * They can be unit-tested natively on any host (GCC, MSVC).
 */

#include "can_messages.h"

/* ─── ECU1 Pack ──────────────────────────────────────────────── */
/**
 * @brief  Serialise ECU1_Data_t into an 8-byte CAN payload buffer.
 * @param  data  Pointer to source struct.
 * @param  buf   Pointer to 8-byte output buffer (only [0..3] used).
 */
void ECU1_Pack(const ECU1_Data_t *data, uint8_t *buf)
{
    buf[0] = (uint8_t)((data->speed_kmh >> 8) & 0xFFU);  /* speed MSB */
    buf[1] = (uint8_t)( data->speed_kmh       & 0xFFU);  /* speed LSB */
    buf[2] =  data->temp_c;
    buf[3] =  data->indicator;
    buf[4] = 0U;
    buf[5] = 0U;
    buf[6] = 0U;
    buf[7] = 0U;
}

/* ─── ECU1 Unpack ────────────────────────────────────────────── */
/**
 * @brief  Deserialise a raw CAN payload into ECU1_Data_t.
 * @param  buf   Pointer to received 8-byte buffer.
 * @param  data  Pointer to destination struct.
 */
void ECU1_Unpack(const uint8_t *buf, ECU1_Data_t *data)
{
    data->speed_kmh = ((uint16_t)buf[0] << 8) | (uint16_t)buf[1];
    data->temp_c    = buf[2];
    data->indicator = buf[3];
}

/* ─── ECU2 Pack ──────────────────────────────────────────────── */
/**
 * @brief  Serialise ECU2_Data_t into an 8-byte CAN payload buffer.
 */
void ECU2_Pack(const ECU2_Data_t *data, uint8_t *buf)
{
    buf[0] = (uint8_t)((data->rpm >> 8) & 0xFFU);  /* RPM MSB */
    buf[1] = (uint8_t)( data->rpm       & 0xFFU);  /* RPM LSB */
    buf[2] =  data->gear;
    buf[3] =  data->time_min;
    buf[4] =  data->time_sec;
    buf[5] = 0U;
    buf[6] = 0U;
    buf[7] = 0U;
}

/* ─── ECU2 Unpack ────────────────────────────────────────────── */
void ECU2_Unpack(const uint8_t *buf, ECU2_Data_t *data)
{
    data->rpm      = ((uint16_t)buf[0] << 8) | (uint16_t)buf[1];
    data->gear     = buf[2];
    data->time_min = buf[3];
    data->time_sec = buf[4];
}
