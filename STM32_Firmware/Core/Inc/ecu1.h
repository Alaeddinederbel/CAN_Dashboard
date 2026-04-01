#ifndef ECU1_H
#define ECU1_H

#include <stdint.h>

void ECU1_SetData(uint16_t speed_kmh, uint8_t temp_c, uint8_t indicator);
void ECU1_Task   (void);

#endif /* ECU1_H */
