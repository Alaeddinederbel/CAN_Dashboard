/**
 * @file    ecu3_dashboard.c
 * @brief   ECU3 – Dashboard Receiver.
 *
 * Responsibilities:
 *   1. Configure CAN hardware filters to accept only 0x100 and 0x200.
 *   2. Receive CAN frames via FIFO0 interrupt (non-blocking).
 *   3. Decode received frames and update the dashboard state.
 *   4. Periodically print the dashboard over UART.
 *
 * CAN Filter strategy:
 *   Uses 32-bit mask mode. Two filter banks are configured:
 *     Bank 0 → passes only StdId 0x100
 *     Bank 1 → passes only StdId 0x200
 *
 * UART output format (printed every 500 ms):
 *   ╔══════════════════════════════╗
 *   ║  TIME  00:12  GEAR  3        ║
 *   ║  SPD   072    RPM   2400     ║
 *   ║  TEMP  089°C  IND   LEFT     ║
 *   ╚══════════════════════════════╝
 */

#include "ecu3_dashboard.h"
#include "dashboard.h"
#include "can_messages.h"
#include "stm32f4xx_hal.h"
#include <stdio.h>
#include <string.h>

extern CAN_HandleTypeDef  hcan1;
extern UART_HandleTypeDef huart1;

#define DASHBOARD_PRINT_PERIOD_MS  500U

static uint32_t s_last_print = 0U;

/* ─── CAN Filter Configuration ──────────────────────────────── */
/**
 * @brief  Configure CAN hardware filters.
 *         Two 32-bit mask-mode filter banks:
 *           Bank 0: accept StdId == 0x100 only
 *           Bank 1: accept StdId == 0x200 only
 *
 * In 32-bit mask mode the filter register value is:
 *   bits [31:21] = StdId shifted left by 21
 *   bit  [2]     = IDE bit (0 = standard frame)
 *   bit  [1]     = RTR bit (0 = data frame)
 */
void ECU3_CAN_FilterConfig(void)
{
    CAN_FilterTypeDef filter;

    /* ── Bank 0: accept CAN_ID_ECU1_VEHICLE (0x100) ── */
    filter.FilterBank           = 0U;
    filter.FilterMode           = CAN_FILTERMODE_IDMASK;
    filter.FilterScale          = CAN_FILTERSCALE_32BIT;
    filter.FilterIdHigh         = (CAN_ID_ECU1_VEHICLE << 5U);
    filter.FilterIdLow          = 0x0000U;
    filter.FilterMaskIdHigh     = 0xFFE0U;  /* match all 11 StdId bits */
    filter.FilterMaskIdLow      = 0x0006U;  /* match IDE + RTR         */
    filter.FilterFIFOAssignment = CAN_RX_FIFO0;
    filter.FilterActivation     = ENABLE;
    filter.SlaveStartFilterBank = 14U;

    if (HAL_CAN_ConfigFilter(&hcan1, &filter) != HAL_OK)
        Error_Handler();

    /* ── Bank 1: accept CAN_ID_ECU2_ENGINE (0x200) ── */
    filter.FilterBank       = 1U;
    filter.FilterIdHigh     = (CAN_ID_ECU2_ENGINE << 5U);
    filter.FilterMaskIdHigh = 0xFFE0U;

    if (HAL_CAN_ConfigFilter(&hcan1, &filter) != HAL_OK)
        Error_Handler();
}

/* ─── Init ───────────────────────────────────────────────────── */
void ECU3_Init(void)
{
    ECU3_CAN_FilterConfig();
    Dashboard_Init();

    /* Enable CAN RX FIFO0 message pending interrupt */
    if (HAL_CAN_ActivateNotification(&hcan1, CAN_IT_RX_FIFO0_MSG_PENDING) != HAL_OK)
        Error_Handler();

    /* Start CAN peripheral */
    if (HAL_CAN_Start(&hcan1) != HAL_OK)
        Error_Handler();
}

/* ─── CAN RX Interrupt Callback ─────────────────────────────── */
/**
 * @brief  Called by HAL from stm32f4xx_it.c whenever a CAN frame
 *         arrives in FIFO0. Do minimal work here — just read and
 *         dispatch. Never call HAL_Delay() inside an ISR.
 */
void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *hcan)
{
    CAN_RxHeaderTypeDef rx_header;
    uint8_t             rx_data[8];

    if (HAL_CAN_GetRxMessage(hcan, CAN_RX_FIFO0, &rx_header, rx_data) != HAL_OK)
        return;

    if (rx_header.StdId == CAN_ID_ECU1_VEHICLE)
    {
        ECU1_Data_t d;
        ECU1_Unpack(rx_data, &d);
        Dashboard_Update1(&d);
    }
    else if (rx_header.StdId == CAN_ID_ECU2_ENGINE)
    {
        ECU2_Data_t d;
        ECU2_Unpack(rx_data, &d);
        Dashboard_Update2(&d);
    }
}

/* ─── Task ───────────────────────────────────────────────────── */
/**
 * @brief  Call from main loop. Prints dashboard to UART every
 *         DASHBOARD_PRINT_PERIOD_MS milliseconds.
 */
void ECU3_Task(void)
{
    if ((HAL_GetTick() - s_last_print) < DASHBOARD_PRINT_PERIOD_MS)
        return;

    s_last_print = HAL_GetTick();
    Dashboard_Print();
}
