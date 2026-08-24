package com.example.nesto_app.utils.ui

import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarVisuals
import androidx.compose.ui.graphics.Color
import com.example.nesto_app.ui.theme.DarkGreen
import com.example.nesto_app.ui.theme.Green
import com.example.nesto_app.ui.theme.Grey
import com.example.nesto_app.ui.theme.PrimaryOrange
import com.example.nesto_app.ui.theme.RedPrimary

enum class SnackbarType(
    val containerColor: Color,
    val contentColor: Color = Color.White,
) {
    SUCCESS(containerColor = Green),
    ERROR(containerColor = RedPrimary),
    WARNING(containerColor = PrimaryOrange),
    DEFAULT(containerColor = Grey);
}

data class CustomSnackbarVisuals(
    override val actionLabel: String? = null,
    override val duration: SnackbarDuration = SnackbarDuration.Short,
    override val message: String,
    override val withDismissAction: Boolean = false,
    val type: SnackbarType = SnackbarType.DEFAULT
) : SnackbarVisuals