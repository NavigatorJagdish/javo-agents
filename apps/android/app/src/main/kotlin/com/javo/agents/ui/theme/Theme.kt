package com.javo.agents.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val DarkColorScheme = darkColorScheme(
    primary = ElectricCyan,
    onPrimary = MidnightNavy,
    secondary = VioletAccent,
    onSecondary = PureWhite,
    tertiary = EmeraldSuccess,
    background = MidnightNavy,
    onBackground = SoftSilver,
    surface = DeepSpace,
    onSurface = PureWhite,
    surfaceVariant = CardSurfaceDark,
    onSurfaceVariant = SoftSilver,
    outline = CardBorderDark,
    error = CoralDanger,
    onError = PureWhite
)

private val LightColorScheme = lightColorScheme(
    primary = Color(0xFF0099B8),
    onPrimary = PureWhite,
    secondary = VioletAccent,
    onSecondary = PureWhite,
    tertiary = EmeraldSuccess,
    background = LightBackground,
    onBackground = LightTextPrimary,
    surface = LightSurface,
    onSurface = LightTextPrimary,
    surfaceVariant = LightSurfaceVariant,
    onSurfaceVariant = LightTextSecondary,
    outline = LightBorder,
    error = CoralDanger,
    onError = PureWhite
)

@Composable
fun JavoAgentsTheme(
    darkTheme: Boolean = true,
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    MaterialTheme(
        colorScheme = colorScheme,
        typography = JavoTypography,
        content = content
    )
}
