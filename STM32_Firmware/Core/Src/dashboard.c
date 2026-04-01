/**
 * @file    dashboard.c
 * @brief   Aggregated dashboard state and UART display formatter.
 *
 * Dashboard_Update1() / Update2() are called from the CAN RX ISR,
 * so they must be fast and side-effect free (no HAL calls, no printf).
 *
 * Dashboard_Print() is called from ECU3_Task() in the main loop
 * and is safe to use blocking UART transmission.
 *
 * UART output example (115200 baud, \r\n line endings):
 *
 *   ================================
 *    CAN DASHBOARD  |  STM32F429
 *   ================================
 *    Time  :  00:14
 *    Speed :  072 km/h
 *    RPM   :  2400 rpm
 *    Gear  :  3
 *    Temp  :  089 C
 *    Ind   :  LEFT
 *   ================================
 */

#include "dashboard.h"
#include "stm32f4xx_hal.h"
#include <stdio.h>
#include <string.h>

extern UART_HandleTypeDef huart1;

/* ─── Private state ──────────────────────────────────────────── */
static Dashboard_State_t s_state = {0};

/* ─── Init ───────────────────────────────────────────────────── */
void Dashboard_Init(void)
{
    memset(&s_state, 0, sizeof(s_state));
}

/* ─── Update from ISR (called from CAN RX callback) ─────────── */
void Dashboard_Update1(const ECU1_Data_t *d)
{
    s_state.speed_kmh  = d->speed_kmh;
    s_state.temp_c     = d->temp_c;
    s_state.indicator  = d->indicator;
    s_state.ecu1_valid = 1U;
}

void Dashboard_Update2(const ECU2_Data_t *d)
{
    s_state.rpm        = d->rpm;
    s_state.gear       = d->gear;
    s_state.time_min   = d->time_min;
    s_state.time_sec   = d->time_sec;
    s_state.ecu2_valid = 1U;
}

/* ─── Get state pointer (for RTOS tasks or logging) ─────────── */
const Dashboard_State_t* Dashboard_GetState(void)
{
    return &s_state;
}

/* ─── UART print helper ──────────────────────────────────────── */
static void uart_print(const char *str)
{
    HAL_UART_Transmit(&huart1,
                      (uint8_t *)str,
                      (uint16_t)strlen(str),
                      HAL_MAX_DELAY);
}

/* ─── Dashboard_Print ────────────────────────────────────────── */
/**
 * @brief  Format and transmit the full dashboard over UART.
 *         Uses a single stack-allocated buffer to avoid heap.
 */
void Dashboard_Print(void)
{
    char buf[256];
    int  n = 0;

    /* Indicator string */
    const char *ind_str;
    switch (s_state.indicator)
    {
        case 1:  ind_str = "LEFT ";  break;
        case 2:  ind_str = "RIGHT";  break;
        default: ind_str = "OFF  ";  break;
    }

    n += snprintf(buf + n, sizeof(buf) - (size_t)n,
        "\r\n================================\r\n"
        " CAN DASHBOARD  |  STM32F429\r\n"
        "================================\r\n");

    n += snprintf(buf + n, sizeof(buf) - (size_t)n,
        " Time  :  %02u:%02u\r\n",
        s_state.time_min, s_state.time_sec);

    n += snprintf(buf + n, sizeof(buf) - (size_t)n,
        " Speed :  %03u km/h\r\n", s_state.speed_kmh);

    n += snprintf(buf + n, sizeof(buf) - (size_t)n,
        " RPM   :  %04u rpm\r\n", s_state.rpm);

    n += snprintf(buf + n, sizeof(buf) - (size_t)n,
        " Gear  :  %u\r\n", s_state.gear);

    n += snprintf(buf + n, sizeof(buf) - (size_t)n,
        " Temp  :  %03u C\r\n", s_state.temp_c);

    n += snprintf(buf + n, sizeof(buf) - (size_t)n,
        " Ind   :  %s\r\n"
        "================================\r\n",
        ind_str);

    uart_print(buf);
}
