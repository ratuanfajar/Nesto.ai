package com.example.nesto_app.utils.ui

import kotlinx.coroutines.flow.MutableSharedFlow

object AppEventBus {
    val events = MutableSharedFlow<UiEvent>()
}