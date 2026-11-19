import 'package:flutter/foundation.dart';

import '../../core/result/result.dart';
import '../../core/state/list_state.dart';
import 'smoke_repository.dart';

final class SmokeController extends ChangeNotifier {
  SmokeController(this._repository);

  final SmokeRepository? _repository;
  ListState<bool> _state = ListState<bool>();

  bool get isConfigured => _repository != null;
  ListState<bool> get state => _state;

  Future<void> probe() async {
    final SmokeRepository? repository = _repository;
    if (repository == null || _state.phase == ListPhase.loading) return;
    final int generation = _state.generation + 1;
    _state = _state.copyWith(
      phase: ListPhase.loading,
      generation: generation,
      clearFailure: true,
    );
    notifyListeners();
    final Result<bool> result = await repository.hasFeedItems();
    if (_state.generation != generation) return;
    _state = switch (result) {
      Success<bool>(:final value) => _state.copyWith(
        phase: value ? ListPhase.ready : ListPhase.empty,
      ),
      Failure<bool>(:final failure) => _state.copyWith(
        phase: ListPhase.error,
        failure: failure,
      ),
    };
    notifyListeners();
  }

  @override
  void dispose() {
    _state = _state.copyWith(generation: _state.generation + 1);
    super.dispose();
  }
}
