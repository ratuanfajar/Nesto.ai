package com.example.nesto_app.utils.ui

interface UiEvent {
    data class ShowSnackbar(
        val data : CustomSnackbarVisuals
    ) : UiEvent
}