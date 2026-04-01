/**
 * @file    ecu2.c
 * @brief   ECU2 – Engine & Time transmitter.
 *
 * Transmits RPM, gear position, and elapsed time on CAN ID 0x200.
 *
 * In real hardware:
 *   - RPM from crankshaft position sensor via TIM input capture.
 *   - Gear position from a gear sensor or derived from speed/RPM ratio.
 *   - Time from RTC peripheral or a free-running TIM counter.
 *
 * For SW simulation: ECU2_SetData() is called with synthetic values.
 * Time auto-increments each second using HAL_GetTick().
 */

#include "ecu2.h"
#include "can_messages.h"
#include "stm32f4xx_hal.h"

extern CAN_HandleTypeDef hcan1;

/* ─── Private state ──────────────────────────────────────────── */
static ECU2_Data_t  s_data        = {.gear = 1U};
static uint32_t     s_last_tx     = 0U;
static uint32_t     s_last_second = 0U;

#define ECU2_TX_PERIOD_MS   100U

static CAN_TxHeaderTypeDef s_tx_header = {
    .StdId              = CAN_ID_ECU2_ENGINE,
    .ExtId              = 0U,
    .IDE                = CAN_ID_STD,
    .RTR                = CAN_RTR_DATA,
    .DLC                = CAN_DLC_ECU2,
    .TransmitGlobalTime = DISABLE
};

/* ─── Public API ─────────────────────────────────────────────── */

void ECU2_SetData(uint16_t rpm, uint8_t gear)
{
    s_data.rpm  = rpm;
    s_data.gear = gear;
}

/**
 * @brief  Main task – call from main loop every cycle.
 *         Auto-increments elapsed time every 1000 ms.
 */
void ECU2_Task(void)
{
    /* Auto-increment time counter */
    if ((HAL_GetTick() - s_last_second) >= 1000U)
    {
        s_last_second = HAL_GetTick();
        s_data.time_sec++;
        if (s_data.time_sec >= 60U)
        {
            s_data.time_sec = 0U;
            s_data.time_min++;
            if (s_data.time_min >= 60U)
                s_data.time_min = 0U;
        }
    }

    /* Transmit at fixed period */
    if ((HAL_GetTick() - s_last_tx) < ECU2_TX_PERIOD_MS)
        return;

    s_last_tx = HAL_GetTick();

    uint8_t  buf[8] = {0};
    uint32_t tx_mailbox;

    ECU2_Pack(&s_data, buf);

    if (HAL_CAN_AddTxMessage(&hcan1, &s_tx_header, buf, &tx_mailbox) != HAL_OK)
        Error_Handler();
}
