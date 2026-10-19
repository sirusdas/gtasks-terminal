class GTasksAccount {
  final String id;
  final String name;
  final String? email;
  final bool isDefault;
  final String provider; // 'google' | 'microsoft'

  GTasksAccount({
    required this.id,
    required this.name,
    this.email,
    this.isDefault = false,
    this.provider = 'google',
  });

  bool get isMicrosoft => provider.toLowerCase() == 'microsoft';
  bool get isGoogle => !isMicrosoft;

  factory GTasksAccount.fromJson(Map<String, dynamic> json) {
    return GTasksAccount(
      id: json['id']?.toString() ?? json['name']?.toString() ?? 'default',
      name: json['name']?.toString() ?? 'Default Account',
      email: json['email']?.toString(),
      isDefault: json['is_default'] == true,
      provider: json['provider']?.toString() ?? 'google',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'email': email,
      'is_default': isDefault,
      'provider': provider,
    };
  }
}

