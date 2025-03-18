class Model {
  final String id;
  final String name;
  final String address;
  final String email;
  final double weight;
  final double height;

  Model._({
    required this.id,
    required this.name,
    required this.address,
    required this.email,
    required this.weight,
    required this.height
});
  factory Model.fromJson(Map<String, dynamic> json) {
    return Model._(
      id: json['id'],
      name: json['name'],
      address: json['address'],
      email: json['email'],
      weight: json['weight'],
      height: json['height'],
    );
  }
}