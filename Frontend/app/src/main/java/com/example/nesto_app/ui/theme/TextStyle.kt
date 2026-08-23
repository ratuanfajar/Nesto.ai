package com.example.nesto_app.ui.theme

import androidx.compose.material3.MaterialTheme.typography
import androidx.compose.runtime.Composable
import androidx.compose.ui.text.TextStyle

val Typography.error: TextStyle
    @Composable
    get() = typography.bodySmall.copy(
        color = RedPrimary
    )