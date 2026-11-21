import 'package:flutter/material.dart';

import '../../core/theme/app_tokens.dart';

enum FeedbackPhase { loading, empty, error }

final class AsyncFeedback extends StatelessWidget {
  const AsyncFeedback({required this.phase, this.onRetry, super.key});

  final FeedbackPhase phase;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final String text = switch (phase) {
      FeedbackPhase.loading => 'Đang tải…',
      FeedbackPhase.empty => 'Chưa có dữ liệu.',
      FeedbackPhase.error => 'Chưa tải được dữ liệu.',
    };
    return Center(
      child: Semantics(
        liveRegion: true,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            if (phase == FeedbackPhase.loading)
              const CircularProgressIndicator(),
            const SizedBox(height: AppTokens.space12),
            Text(text),
            if (phase == FeedbackPhase.error && onRetry != null)
              Padding(
                padding: const EdgeInsets.only(top: AppTokens.space12),
                child: FilledButton(
                  onPressed: onRetry,
                  child: const Text('Thử lại'),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
