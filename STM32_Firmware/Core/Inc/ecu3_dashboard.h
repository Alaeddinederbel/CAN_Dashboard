#ifndef ECU3_DASHBOARD_H
#define ECU3_DASHBOARD_H

#include "stm32f4xx_hal.h"

void ECU3_Init            (void);
void ECU3_CAN_FilterConfig(void);
void ECU3_Task            (void);

/* ISR callback – implemented here, declared weak in HAL */
void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *hcan);

#endif /* ECU3_DASHBOARD_H */
