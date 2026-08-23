package com.example.nesto_app.ui.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

private val DarkColorScheme = darkColorScheme(
    primary = PrimaryOrange,
    onPrimary = Black,
    secondary = RedSecondary,
    onSecondary = White,
    tertiary = Green,
    onTertiary = Black,
    error = RedPrimary,
    onError = White,
    background = Color(0xFF1C1B1F),
    onBackground = White,
    surface = Color(0xFF1C1B1F),
    onSurface = White,
    surfaceVariant = Grey,
    onSurfaceVariant = Black,
)

private val LightColorScheme = lightColorScheme(
    primary = PrimaryOrange,
    onPrimary = White,
    secondary = RedSecondary,
    onSecondary = White,
    tertiary = Green,
    onTertiary = White,
    error = RedPrimary,
    onError = White,
    background = White,
    onBackground = Black,
    surface = SecondaryGrey,
    onSurface = Black,
    surfaceVariant = Grey,
    onSurfaceVariant = Black,
)

@Composable
fun Nesto_AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    // Disabled: dynamic color would override your brand palette above
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }

        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}