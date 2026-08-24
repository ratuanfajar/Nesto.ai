package com.example.nesto_app.utils.ui

import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusManager
import androidx.compose.ui.input.pointer.pointerInput

fun Modifier.clearFocusOnTap(focusManager: FocusManager): Modifier {
    return pointerInput(Unit) {
        detectTapGestures {
            focusManager.clearFocus()
        }
    }
}