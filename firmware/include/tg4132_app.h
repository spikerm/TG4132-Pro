#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef enum {
    TG_MODE_BYPASS = 0,
    TG_MODE_ACQUIRE,
    TG_MODE_STORED_TRACE,
    TG_MODE_MARKER_OVERLAY,
    TG_MODE_VECTOR_MENU,
    TG_MODE_FAULT
} tg_mode_t;

typedef struct {
    int16_t x;
    int16_t y;
    uint8_t visible;
} tg_vector_point_t;

typedef struct {
    float x_volts;
    float y_volts;
    float z_volts;
    uint32_t timestamp_us;
} tg_sample_t;

typedef struct {
    tg_mode_t requested_mode;
    tg_mode_t active_mode;
    bool analog_power_good;
    bool adc_ready;
    bool dac_ready;
    bool watchdog_ok;
    bool sweep_active;
    bool flyback_active;
    uint32_t fault_flags;
} tg_status_t;

void tg_app_init(void);
void tg_app_process(void);
void tg_app_request_mode(tg_mode_t mode);
const tg_status_t *tg_app_status(void);

bool tg_app_submit_sample(const tg_sample_t *sample);
size_t tg_app_build_marker(int16_t x, int16_t y, tg_vector_point_t *out, size_t capacity);
