import 'package:flutter/material.dart';

final class PlaceholderScreen extends StatelessWidget {
  const PlaceholderScreen({
    required this.title,
    required this.onBack,
    super.key,
  });

  final String title;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(title)),
    body: Center(
      child: FilledButton(onPressed: onBack, child: const Text('Quay lại')),
    ),
  );
}
