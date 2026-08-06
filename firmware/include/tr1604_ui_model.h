#ifndef TR1604_UI_MODEL_H
#define TR1604_UI_MODEL_H

#include <stdbool.h>
#include <stdint.h>

#define TR1604_MAX_MARKERS 10U
#define TR1604_ACTIVE_MARKERS_REV_A 4U

typedef enum {
    TR1604_MODE_STARTUP = 0,
    TR1604_MODE_SPECTRUM,
    TR1604_MODE_DUPLEX_FILTER,
    TR1604_MODE_NOTCH_ZOOM,
    TR1604_MODE_INSERTION_LOSS,
    TR1604_MODE_MEMORY_COMPARE,
    TR1604_MODE_ANTENNA,
    TR1604_MODE_SYSTEM_SETUP
} tr1604_mode_t;

typedef enum {
    TR1604_TRACE_A = 0,
    TR1604_TRACE_B,
    TR1604_TRACE_REFERENCE_1,
    TR1604_TRACE_REFERENCE_2,
    TR1604_TRACE_REFERENCE_3,
    TR1604_TRACE_REFERENCE_4
} tr1604_trace_id_t;

typedef struct {
    bool enabled;
    double frequency_hz;
    float level_db;
    tr1604_trace_id_t trace;
    bool delta_reference;
    bool tracking;
} tr1604_marker_t;

typedef struct {
    tr1604_mode_t mode;
    double start_hz;
    double stop_hz;
    float reference_level_dbm;
    float db_per_division;
    float rbw_hz;
    float vbw_hz;
    float sweep_seconds;
    float tracking_generator_dbm;
    bool tracking_generator_enabled;
    uint8_t selected_marker;
    tr1604_marker_t markers[TR1604_MAX_MARKERS];
    bool memory_trace_enabled;
    uint16_t averaging_count;
} tr1604_ui_state_t;

void tr1604_ui_state_init(tr1604_ui_state_t *state);
bool tr1604_marker_set_frequency(tr1604_ui_state_t *state,
                                  uint8_t marker_index,
                                  double frequency_hz);
bool tr1604_marker_move(tr1604_ui_state_t *state,
                        uint8_t marker_index,
                        double step_hz);
double tr1604_marker_delta_hz(const tr1604_ui_state_t *state,
                              uint8_t first,
                              uint8_t second);

#endif
