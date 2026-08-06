#include "tr1604_ui_model.h"

#include <stddef.h>
#include <string.h>

static double clamp_frequency(const tr1604_ui_state_t *state, double hz) {
    if (hz < state->start_hz) {
        return state->start_hz;
    }
    if (hz > state->stop_hz) {
        return state->stop_hz;
    }
    return hz;
}

void tr1604_ui_state_init(tr1604_ui_state_t *state) {
    if (state == NULL) {
        return;
    }

    memset(state, 0, sizeof(*state));
    state->mode = TR1604_MODE_DUPLEX_FILTER;
    state->start_hz = 429000000.0;
    state->stop_hz = 433000000.0;
    state->reference_level_dbm = -20.0f;
    state->db_per_division = 10.0f;
    state->rbw_hz = 30000.0f;
    state->vbw_hz = 30000.0f;
    state->sweep_seconds = 0.250f;
    state->tracking_generator_dbm = -10.0f;
    state->tracking_generator_enabled = true;
    state->averaging_count = 4U;

    state->markers[0].enabled = true;
    state->markers[0].frequency_hz = 430362500.0;
    state->markers[0].trace = TR1604_TRACE_A;

    state->markers[1].enabled = true;
    state->markers[1].frequency_hz = 431962500.0;
    state->markers[1].trace = TR1604_TRACE_A;
}

bool tr1604_marker_set_frequency(tr1604_ui_state_t *state,
                                  uint8_t marker_index,
                                  double frequency_hz) {
    if ((state == NULL) || (marker_index >= TR1604_MAX_MARKERS)) {
        return false;
    }

    state->markers[marker_index].enabled = true;
    state->markers[marker_index].frequency_hz =
        clamp_frequency(state, frequency_hz);
    return true;
}

bool tr1604_marker_move(tr1604_ui_state_t *state,
                        uint8_t marker_index,
                        double step_hz) {
    if ((state == NULL) || (marker_index >= TR1604_MAX_MARKERS)) {
        return false;
    }

    return tr1604_marker_set_frequency(
        state,
        marker_index,
        state->markers[marker_index].frequency_hz + step_hz);
}

double tr1604_marker_delta_hz(const tr1604_ui_state_t *state,
                              uint8_t first,
                              uint8_t second) {
    if ((state == NULL) ||
        (first >= TR1604_MAX_MARKERS) ||
        (second >= TR1604_MAX_MARKERS)) {
        return 0.0;
    }

    return state->markers[second].frequency_hz -
           state->markers[first].frequency_hz;
}
