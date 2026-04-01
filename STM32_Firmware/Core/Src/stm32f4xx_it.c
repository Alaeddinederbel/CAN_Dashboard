/**
 * @file    stm32f4xx_it.c
 * @brief   STM32F4xx interrupt service routines.
 *
 * The CAN1 RX0 IRQ handler calls the HAL, which in turn calls
 * HAL_CAN_RxFifo0MsgPendingCallback() – our hook defined in
 * ecu3_dashboard.c. This keeps the ISR itself minimal.
 *
 * SysTick_Handler drives HAL_GetTick() which all tasks use for
 * non-blocking periodic timing.
 */

#include "main.h"
#include "stm32f4xx_it.h"

extern CAN_HandleTypeDef hcan1;

/* ─── SysTick – 1 ms timebase ───────────────────────────────── */
void SysTick_Handler(void)
{
    HAL_IncTick();
}

/* ─── CAN1 RX0 – FIFO0 message pending ──────────────────────── */
/**
 * @brief  Fires when a CAN frame passes the hardware filter and
 *         lands in RX FIFO0. HAL dispatches to
 *         HAL_CAN_RxFifo0MsgPendingCallback().
 */
void CAN1_RX0_IRQHandler(void)
{
    HAL_CAN_IRQHandler(&hcan1);
}

/* ─── CAN1 SCE – error/status change ────────────────────────── */
/**
 * @brief  Handles bus-off, error-passive, error-warning events.
 *         AutoBusOff is enabled in MX_CAN1_Init so the peripheral
 *         recovers automatically; this handler just feeds HAL.
 */
void CAN1_SCE_IRQHandler(void)
{
    HAL_CAN_IRQHandler(&hcan1);
}

/* ─── HardFault – catch runaway pointers ────────────────────── */
void HardFault_Handler(void)
{
    __disable_irq();
    while (1) { /* trap – attach debugger here */ }
}

void MemManage_Handler(void) { while (1) {} }
void BusFault_Handler (void) { while (1) {} }
void UsageFault_Handler(void){ while (1) {} }
