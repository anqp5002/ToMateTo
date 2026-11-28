import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/failure/app_failure.dart';
import '../../core/navigation/navigation_context.dart';
import 'session_controller.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({
    super.key,
    required this.session,
    required this.navigation,
    required this.register,
    this.initialEmail = '',
    this.expired = false,
  });

  final SessionController session;
  final NavigationContext navigation;
  final bool register;
  final String initialEmail;
  final bool expired;

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _form = GlobalKey<FormState>();
  late final _email = TextEditingController(text: widget.initialEmail);
  final _name = TextEditingController();
  final _password = TextEditingController();
  final _emailFocus = FocusNode();
  final _nameFocus = FocusNode();
  final _passwordFocus = FocusNode();
  AppFailure? _failure;

  @override
  void dispose() {
    _email.dispose();
    _name.dispose();
    _password.dispose();
    _emailFocus.dispose();
    _nameFocus.dispose();
    _passwordFocus.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _failure = null);
    if (!_form.currentState!.validate()) {
      if (widget.register && _name.text.trim().isEmpty) {
        _nameFocus.requestFocus();
      } else if (!_validEmail(_email.text)) {
        _emailFocus.requestFocus();
      } else {
        _passwordFocus.requestFocus();
      }
      return;
    }
    final success = await widget.session.authenticate(
      _email.text.trim(),
      _password.text,
      widget.register ? _name.text.trim() : null,
    );
    if (!mounted) return;
    if (success) {
      context.go(widget.navigation.resume(true).path);
      return;
    }
    setState(() => _failure = widget.session.failure);
    final errors = _failure?.fieldErrors;
    if (errors?.containsKey('displayName') ?? false) {
      _nameFocus.requestFocus();
    } else if (errors?.containsKey('email') ?? false) {
      _emailFocus.requestFocus();
    } else if (errors?.containsKey('password') ?? false) {
      _passwordFocus.requestFocus();
    }
  }

  bool _validEmail(String value) =>
      RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(value.trim());

  String? _field(String name) => switch (_failure?.fieldErrors[name]) {
    'EMAIL_EXISTS' => 'Email đã được sử dụng.',
    'EMAIL_INVALID' => 'Email không hợp lệ.',
    'PASSWORD_INVALID' => 'Mật khẩu không đáp ứng yêu cầu.',
    'REQUIRED' => 'Vui lòng nhập thông tin này.',
    _ => null,
  };

  @override
  Widget build(BuildContext context) {
    final title = widget.register ? 'Đăng ký' : 'Đăng nhập';
    return ListenableBuilder(
      listenable: widget.session,
      builder: (context, _) {
        final busy = widget.session.busy;
        final failure = _failure;
        return Scaffold(
          appBar: AppBar(
            leading: BackButton(
              onPressed: busy
                  ? null
                  : () => context.go(widget.navigation.back().path),
            ),
            title: Text(title),
          ),
          body: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400),
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: AutofillGroup(
                  child: Form(
                    key: _form,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        if (widget.expired)
                          const Text('Phiên đã hết. Vui lòng đăng nhập lại.'),

                        if (widget.register) ...[
                          TextFormField(
                            controller: _name,
                            focusNode: _nameFocus,
                            enabled: !busy,
                            decoration: InputDecoration(
                              labelText: 'Tên hiển thị',
                              errorText: _field('displayName'),
                            ),
                            validator: (v) => (v ?? '').trim().isEmpty
                                ? 'Vui lòng nhập tên hiển thị.'
                                : null,
                          ),
                          const SizedBox(height: 12),
                        ],
                        TextFormField(
                          controller: _email,
                          focusNode: _emailFocus,
                          enabled: !busy,
                          keyboardType: TextInputType.emailAddress,
                          autofillHints: const [AutofillHints.email],
                          onChanged: (_) => setState(() {}),
                          decoration: InputDecoration(
                            labelText: 'Email',
                            errorText: _field('email'),
                          ),
                          validator: (v) => _validEmail(v ?? '')
                              ? null
                              : 'Email không hợp lệ.',
                        ),
                        const SizedBox(height: 12),
                        TextFormField(
                          controller: _password,
                          focusNode: _passwordFocus,
                          enabled: !busy,
                          obscureText: true,
                          autofillHints: [
                            widget.register
                                ? AutofillHints.newPassword
                                : AutofillHints.password,
                          ],
                          decoration: InputDecoration(
                            labelText: 'Mật khẩu',
                            errorText: _field('password'),
                          ),
                          validator: (v) {
                            final value = v ?? '';
                            if (value.isEmpty) return 'Vui lòng nhập mật khẩu.';
                            if (widget.register &&
                                (value.runes.length < 6 ||
                                    utf8.encode(value).length > 72)) {
                              return 'Dùng ít nhất 6 ký tự và tối đa 72 byte.';
                            }
                            return null;
                          },
                          onFieldSubmitted: busy ? null : (_) => _submit(),
                        ),
                        if (failure != null && failure.fieldErrors.isEmpty)
                          Semantics(
                            liveRegion: true,
                            child: Text(switch (failure.kind) {
                              FailureKind.unauthenticated =>
                                'Email hoặc mật khẩu chưa đúng.',
                              FailureKind.outcomeUnknown => 'Chưa xác nhận được kết quả. Hãy thử đăng nhập nếu đã đăng ký.',
                              _ => 'Không thể hoàn tất. Vui lòng thử lại.',
                            }),
                          ),
                        const SizedBox(height: 16),
                        FilledButton(
                          onPressed: busy ? null : _submit,
                          child: Text(busy ? 'Đang gửi…' : title),
                        ),
                        TextButton(
                          onPressed: busy
                              ? null
                              : () => context.go(
                                  widget.register ? '/login' : '/register',
                                  extra: _email.text.trim(),
                                ),
                          child: Text(
                            widget.register
                                ? 'Chuyển sang đăng nhập'
                                : 'Tạo tài khoản',
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
