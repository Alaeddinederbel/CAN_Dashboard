#ifndef ECU2_H
#define ECU2_H

#include <stdint.h>

void ECU2_SetData(uint16_t rpm, uint8_t gear);
void ECU2_Task   (void);

#endif /* ECU2_H */
