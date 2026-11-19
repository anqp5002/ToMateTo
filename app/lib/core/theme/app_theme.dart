import 'package:flutter/material.dart';

import 'app_tokens.dart';

ThemeData buildAppTheme() {
  const colors = ColorScheme.light(
    primary: AppTokens.brand,
    onPrimary: AppTokens.surface,
    surface: AppTokens.surface,
    onSurface: AppTokens.ink,
    outline: AppTokens.controlBorder,
    outlineVariant: AppTokens.border,
    error: AppTokens.error,
    errorContainer: AppTokens.errorBackground,
  );
  final ThemeData theme = ThemeData(
    colorScheme: colors,
    scaffoldBackgroundColor: AppTokens.canvas,
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        minimumSize: const Size(AppTokens.minTouch, AppTokens.minTouch),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppTokens.controlRadius),
        ),
      ),
    ),
  );
  return theme.copyWith(
    textTheme: theme.textTheme.copyWith(
      headlineLarge: const TextStyle(fontSize: AppTokens.titleWeb),
      headlineMedium: const TextStyle(fontSize: AppTokens.titleMobile),
      titleLarge: const TextStyle(fontSize: AppTokens.section),
      bodyMedium: const TextStyle(fontSize: AppTokens.body, height: 1.5),
      labelMedium: const TextStyle(fontSize: AppTokens.label),
    ),
  );
}
