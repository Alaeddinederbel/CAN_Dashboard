/**
 * @file    ecu1.c
 * @brief   ECU1 – Vehicle Status transmitter.
 *
 * Periodically reads simulated sensor values (speed, temperature,
 * indicator) and transmits them on the CAN bus as ID 0x100.
 *
 * In real hardware:
 *   - Speed would come from a wheel speed sensor via TIM input capture.
 *   - Temp would come from an NTC thermistor via ADC.
 *   - Indicator from a GPIO tied to the turn-signal stalk.
 *
 * For SW simulation: values are updated by ECU1_SetData() which the
 * main loop or a RTOS task calls with synthetic data.
 */

#include "ecu1.h"
#include "can_messages.h"
#include "stm32f4xx_hal.h"

extern CAN_HandleTypeDef hcan1;

/* ─── Private state ──────────────────────────────────────────── */
static ECU1_Data_t  s_data    = {0};
static uint32_t     s_last_tx = 0U;

#define ECU1_TX_PERIOD_MS   100U   /* transmit every 100 ms       */

/* ─── CAN Tx header (constant for ECU1) ─────────────────────── */
static CAN_TxHeaderTypeDef s_tx_header = {
    .StdId              = CAN_ID_ECU1_VEHICLE,
    .ExtId              = 0U,
    .IDE                = CAN_ID_STD,
    .RTR                = CAN_RTR_DATA,
    .DLC                = CAN_DLC_ECU1,
    .TransmitGlobalTime = DISABLE
};

/* ─── Public API ─────────────────────────────────────────────── */

/**
 * @brief  Inject sensor data into ECU1 (called from main loop or
 *         RTOS task; replace with real sensor reads on hardware).
 */
void ECU1_SetData(uint16_t speed_kmh, uint8_t temp_c, uint8_t indicator)
{
    s_data.speed_kmh = speed_kmh;
    s_data.temp_c    = temp_c;
    s_data.indicator = indicator;
}

/**
 * @brief  Must be called repeatedly from the main loop.
 *         Transmits a CAN frame every ECU1_TX_PERIOD_MS milliseconds.
 */
void ECU1_Task(void)
{
    if ((HAL_GetTick() - s_last_tx) < ECU1_TX_PERIOD_MS)
        return;

    s_last_tx = HAL_GetTick();

    uint8_t  buf[8]   = {0};
    uint32_t tx_mailbox;

    ECU1_Pack(&s_data, buf);

    if (HAL_CAN_AddTxMessage(&hcan1, &s_tx_header, buf, &tx_mailbox) != HAL_OK)
    {
        /* TX mailbox full – handle error or increment error counter */
        Error_Handler();
    }
}
