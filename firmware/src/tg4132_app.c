#include "tg4132_app.h"

#include <string.h>

#define TG_SAMPLE_BUFFER_SIZE 4096U
#define TG_FAULT_ANALOG_POWER (1UL << 0)
#define TG_FAULT_ADC          (1UL << 1)
#define TG_FAULT_DAC          (1UL << 2)
#define TG_FAULT_WATCHDOG     (1UL << 3)

static tg_status_t g_status;
static tg_sample_t g_samples[TG_SAMPLE_BUFFER_SIZE];
static size_t g_sample_write;

static bool tg_output_path_safe(void) {
    return g_status.analog_power_good && g_status.dac_ready && g_status.watchdog_ok;
}

static void tg_update_faults(void) {
    uint32_t faults = 0;

    if (!g_status.analog_power_good) {
        faults |= TG_FAULT_ANALOG_POWER;
    }
    if (!g_status.adc_ready) {
        faults |= TG_FAULT_ADC;
    }
    if (!g_status.dac_ready) {
        faults |= TG_FAULT_DAC;
    }
    if (!g_status.watchdog_ok) {
        faults |= TG_FAULT_WATCHDOG;
    }

    g_status.fault_flags = faults;
}

void tg_app_init(void) {
    memset(&g_status, 0, sizeof(g_status));
    memset(g_samples, 0, sizeof(g_samples));

    g_status.requested_mode = TG_MODE_BYPASS;
    g_status.active_mode = TG_MODE_BYPASS;
    g_status.watchdog_ok = true;
    g_sample_write = 0U;
}

void tg_app_process(void) {
    tg_update_faults();

    if (!tg_output_path_safe()) {
        g_status.active_mode = TG_MODE_BYPASS;
        return;
    }

    if ((g_status.requested_mode != TG_MODE_BYPASS) && !g_status.adc_ready) {
        g_status.active_mode = TG_MODE_BYPASS;
        return;
    }

    if ((g_status.requested_mode == TG_MODE_MARKER_OVERLAY ||
         g_status.requested_mode == TG_MODE_VECTOR_MENU) &&
        !g_status.flyback_active) {
        /* Rev A only grants vector ownership during confirmed flyback. */
        g_status.active_mode = TG_MODE_ACQUIRE;
        return;
    }

    g_status.active_mode = g_status.requested_mode;
}

void tg_app_request_mode(tg_mode_t mode) {
    if (mode > TG_MODE_FAULT) {
        g_status.requested_mode = TG_MODE_BYPASS;
        return;
    }
    g_status.requested_mode = mode;
}

const tg_status_t *tg_app_status(void) {
    return &g_status;
}

bool tg_app_submit_sample(const tg_sample_t *sample) {
    if (sample == NULL || !g_status.adc_ready) {
        return false;
    }

    g_samples[g_sample_write] = *sample;
    g_sample_write = (g_sample_write + 1U) % TG_SAMPLE_BUFFER_SIZE;
    return true;
}

size_t tg_app_build_marker(int16_t x, int16_t y, tg_vector_point_t *out, size_t capacity) {
    static const tg_vector_point_t shape[] = {
        { 0, -2200, 0 },
        { 0,  2200, 1 },
        {-450, 1600, 0 },
        { 0,  2200, 1 },
        { 450, 1600, 1 },
    };

    const size_t required = sizeof(shape) / sizeof(shape[0]);
    if (out == NULL || capacity < required) {
        return required;
    }

    for (size_t i = 0; i < required; ++i) {
        out[i] = shape[i];
        out[i].x = (int16_t)(out[i].x + x);
        out[i].y = (int16_t)(out[i].y + y);
    }

    return required;
}
