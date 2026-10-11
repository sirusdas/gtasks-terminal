class GTasksAccount {
  final String id;
  final String name;
  final String? email;
  final bool isDefault;

  GTasksAccount({
    required this.id,
    required this.name,
    this.email,
    this.isDefault = false,
  });

  factory GTasksAccount.fromJson(Map<String, dynamic> json) {
    return GTasksAccount(
      id: json['id']?.toString() ?? json['name']?.toString() ?? 'default',
      name: json['name']?.toString() ?? 'Default Account',
      email: json['email']?.toString(),
      isDefault: json['is_default'] == true,
    );
  }
}
