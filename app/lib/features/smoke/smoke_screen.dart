import 'package:flutter/material.dart';

import '../../core/state/list_state.dart';
import '../../core/theme/app_tokens.dart';
import '../../shared/widgets/async_feedback.dart';
import 'smoke_controller.dart';

final class SmokeScreen extends StatelessWidget {
  const SmokeScreen({required this.controller, super.key});

  final SmokeController controller;

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: controller,
    builder: (context, child) {
      final ListPhase phase = controller.state.phase;
      final FeedbackPhase? feedback = switch (phase) {
        ListPhase.loading => FeedbackPhase.loading,
        ListPhase.empty => FeedbackPhase.empty,
        ListPhase.error => FeedbackPhase.error,
        _ => null,
      };
      return Scaffold(
        appBar: AppBar(title: const Text('ToMateTo')),
        body: Padding(
          padding: const EdgeInsets.all(AppTokens.space16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Text(
                'Kiểm tra kết nối S8',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: AppTokens.space12),
              if (!controller.isConfigured)
                const Text('Cấu hình API để kiểm tra kết nối.'),
              if (controller.isConfigured && phase != ListPhase.error)
                FilledButton(
                  onPressed: phase == ListPhase.loading
                      ? null
                      : controller.probe,
                  child: const Text('Đọc bảng tin thử'),
                ),
              if (feedback != null)
                Expanded(
                  child: AsyncFeedback(
                    phase: feedback,
                    onRetry: controller.probe,
                  ),
                ),
              if (phase == ListPhase.ready) const Text('Đã đọc được bảng tin.'),
            ],
          ),
        ),
      );
    },
  );
}
