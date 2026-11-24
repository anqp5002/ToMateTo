import 'package:flutter/material.dart';

import 'app_tokens.dart';

ThemeData buildAppTheme() {
  const colors = ColorScheme.light(
    primary: AppTokens.brand,
    onPrimary: AppTokens.surface,
    primaryContainer: AppTokens.canvas,
    onPrimaryContainer: AppTokens.ink,
    secondary: AppTokens.brand,
    onSecondary: AppTokens.surface,
    secondaryContainer: AppTokens.canvas,
    onSecondaryContainer: AppTokens.ink,
    tertiary: AppTokens.success,
    onTertiary: AppTokens.surface,
    tertiaryContainer: AppTokens.successBackground,
    onTertiaryContainer: AppTokens.success,
    surface: AppTokens.surface,
    onSurface: AppTokens.ink,
    outline: AppTokens.controlBorder,
    outlineVariant: AppTokens.border,
    error: AppTokens.error,
    onError: AppTokens.surface,
    errorContainer: AppTokens.errorBackground,
    onErrorContainer: AppTokens.error,
    onSurfaceVariant: AppTokens.muted,
    inverseSurface: AppTokens.ink,
    onInverseSurface: AppTokens.surface,
    inversePrimary: AppTokens.surface,
  );
  final shape = RoundedRectangleBorder(
    borderRadius: BorderRadius.circular(AppTokens.controlRadius),
  );
  final ThemeData theme = ThemeData(
    colorScheme: colors,
    scaffoldBackgroundColor: AppTokens.canvas,
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        minimumSize: const Size(AppTokens.minTouch, AppTokens.minTouch),
        shape: shape,
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        minimumSize: const Size(AppTokens.minTouch, AppTokens.minTouch),
        foregroundColor: AppTokens.brand,
        side: const BorderSide(color: AppTokens.controlBorder),
        shape: shape,
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        minimumSize: const Size(AppTokens.minTouch, AppTokens.minTouch),
        foregroundColor: AppTokens.brand,
        shape: shape,
      ),
    ),
    iconButtonTheme: IconButtonThemeData(
      style: IconButton.styleFrom(
        minimumSize: const Size(AppTokens.minTouch, AppTokens.minTouch),
        foregroundColor: AppTokens.ink,
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppTokens.surface,
      contentPadding: const EdgeInsets.all(AppTokens.space12),
      labelStyle: const TextStyle(
        color: AppTokens.muted,
        fontSize: AppTokens.label,
      ),
      helperStyle: const TextStyle(
        color: AppTokens.muted,
        fontSize: AppTokens.label,
      ),
      errorStyle: const TextStyle(
        color: AppTokens.error,
        fontSize: AppTokens.label,
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppTokens.controlRadius),
        borderSide: const BorderSide(color: AppTokens.controlBorder),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppTokens.controlRadius),
        borderSide: const BorderSide(
          color: AppTokens.focus,
          width: AppTokens.focusWidth,
        ),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppTokens.controlRadius),
        borderSide: const BorderSide(color: AppTokens.error),
      ),
      focusedErrorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(AppTokens.controlRadius),
        borderSide: const BorderSide(
          color: AppTokens.error,
          width: AppTokens.focusWidth,
        ),
      ),
    ),
    cardTheme: CardThemeData(
      color: AppTokens.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppTokens.panelRadius),
        side: const BorderSide(color: AppTokens.border),
      ),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: AppTokens.canvas,
      selectedColor: AppTokens.surface,
      labelStyle: const TextStyle(
        fontSize: AppTokens.chipSize,
        color: AppTokens.ink,
      ),
      side: const BorderSide(color: AppTokens.controlBorder),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppTokens.chipRadius),
      ),
    ),
  );
  return theme.copyWith(
    textTheme: theme.textTheme.copyWith(
      headlineLarge: const TextStyle(fontSize: AppTokens.titleWeb),
      headlineMedium: const TextStyle(fontSize: AppTokens.titleMobile),
      headlineSmall: const TextStyle(fontSize: AppTokens.brandSize),
      titleLarge: const TextStyle(fontSize: AppTokens.section),
      bodyMedium: const TextStyle(fontSize: AppTokens.body, height: 1.5),
      bodyLarge: const TextStyle(fontSize: AppTokens.body, height: 1.5),
      bodySmall: const TextStyle(fontSize: AppTokens.label, height: 1.5),
      labelLarge: const TextStyle(fontSize: AppTokens.body),
      labelMedium: const TextStyle(fontSize: AppTokens.label),
      labelSmall: const TextStyle(fontSize: AppTokens.chipSize),
    ),
  );
}
