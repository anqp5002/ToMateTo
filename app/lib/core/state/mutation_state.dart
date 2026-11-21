import '../failure/app_failure.dart';

enum MutationPhase { idle, submitting, succeeded, failed, outcomeUnknown }

final class MutationState {
  const MutationState({
    this.phase = MutationPhase.idle,
    this.failure,
    this.generation = 0,
  });

  final MutationPhase phase;
  final AppFailure? failure;
  final int generation;

  MutationState copyWith({
    MutationPhase? phase,
    AppFailure? failure,
    bool clearFailure = false,
    int? generation,
  }) => MutationState(
    phase: phase ?? this.phase,
    failure: clearFailure ? null : failure ?? this.failure,
    generation: generation ?? this.generation,
  );
}
