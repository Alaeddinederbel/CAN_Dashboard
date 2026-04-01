#ifndef MAIN_H
#define MAIN_H

#include "stm32f4xx_hal.h"

/* ─── Peripheral handle externs ─────────────────────────────── */
extern CAN_HandleTypeDef  hcan1;
extern UART_HandleTypeDef huart1;

/* ─── Error handler ──────────────────────────────────────────── */
void Error_Handler(void);

#endif /* MAIN_H */
