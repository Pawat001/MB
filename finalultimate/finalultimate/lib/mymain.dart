import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

main() {
  runApp(const ShowInf());
}

class ShowInf extends StatefulWidget {
  const ShowInf({super.key});

  @override
  State<ShowInf> createState() => _ShowInfState();
}

class _ShowInfState extends State<ShowInf> {
  List list = [];
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _addressController = TextEditingController();
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();
  final TextEditingController _weightController = TextEditingController();
  final TextEditingController _heightController = TextEditingController();

  Future<String> listData() async {
    var response = await http.get(Uri.http('10.0.2.2:8080', 'emp'),
        headers: {"Accept": "application/json"});
    print("Response status: ${response.statusCode}");
    print("Response body: ${response.body}");
    setState(() {
      list = jsonDecode(response.body);
    });
    return 'Success';
  }

  @override
  void initState() {
    super.initState();
    listData();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('DB Test'),
      ),
      body: Center(
        child: ListView.builder(
          itemCount: list.length,
          itemBuilder: (BuildContext context, int index) {
            return Card(
              child: ListTile(
    leading: Icon(Icons.person),
    title: Text("Name: ${list[index]['name']}"),
    subtitle: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text("Email: ${list[index]['email']}"),
        Text("Phone: ${list[index]['phone']}"),
        Text("Address: ${list[index]['address']}"),
        Text("Weight: ${list[index]['weight'].toStringAsFixed(2)} kg"),
        Text("Height: ${list[index]['height'].toStringAsFixed(2)} cm"),
        Text("BMI: ${calBmi(list[index]['weight'], list[index]['height'])}"),
        Text("BMI Type: ${calBmitype(calBmi(list[index]['weight'], list[index]['height']))}"),
        Text("Weight Status: ${toBenormal(list[index]['weight'], list[index]['height'])}"),
      ],
    ),
                // leading: Text(list[index]['id'].toString()),
                trailing: Wrap(
                  // spacing: 0,
                  children: [
                    Image.asset(
          bmitypetoImage(calBmitype(calBmi(list[index]['weight'], list[index]['height']))),
          // width: 30,
          height: 50,  // Adjust size as needed
        ),
                    IconButton(
                      onPressed: () {
                        Map data = {
                          'id': list[index]['id'],
                          'name': list[index]['name'],
                          'address': list[index]['address'],
                          'email': list[index]['email'],
                          'phone': list[index]['phone'],
                          'weight': list[index]['weight'],
                          'height': list[index]['height']
                        };
                        _showedit(data);
                      },
                      icon: Icon(Icons.edit),
                      color: Colors.green,
                    ),
                    IconButton(
                        onPressed: () => _showDel(list[index]["id"]),
                        icon: const Icon(
                          Icons.delete_outline,
                          color: Colors.red,
                        )),
                  ],
                ),
              ),
            );
          },
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          _addNewDialog();
        },
        child: const Icon(Icons.add),
      ),
    );
  }

  Future<void> _addNewDialog() async {
    return showDialog(
        barrierDismissible: false,
        context: context,
        builder: (BuildContext context) {
          return AlertDialog(
            title: const Text('Add data'),
            content: SingleChildScrollView(
                child: ListBody(
              children: <Widget>[
                TextField(
                  controller: _nameController,
                  decoration: const InputDecoration(
                      labelText: 'Name', hintText: "Enter emp Name"),
                ),
                TextField(
                  controller: _emailController,
                  decoration: const InputDecoration(
                      labelText: 'Email', hintText: "Enter emp Email"),
                ),
                TextField(
                  controller: _phoneController,
                  decoration: const InputDecoration(
                      labelText: 'Phone', hintText: "Enter emp Phone"),
                ),
                TextField(
                  controller: _addressController,
                  decoration: const InputDecoration(
                      labelText: 'Address', hintText: "Enter emp Address"),
                ),
                TextField(
                  controller: _weightController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                      labelText: 'Weight', hintText: "Enter emp Weight"),
                ),
                TextField(
                  controller: _heightController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                      labelText: 'Height', hintText: "Enter emp Height"),
                ),
                const Text('กรอกข้อมูลให้เรียบร้อยแล้วกด ยืนยัน'),
              ],
            )),
            actions: <Widget>[
              TextButton(
                  onPressed: () {
                    add_data();
                    Navigator.of(context).pop();
                  },
                  child: Text('ยืนยัน')),
            ],
          );
        });
  }

  Future<void> _showDel(int id) async {
    return showDialog<void>(
        barrierDismissible: false,
        context: context,
        builder: (BuildContext context) {
          return AlertDialog(
            title: Text('ลบข้อมูล ${id}'),
            content: SingleChildScrollView(
                child: ListBody(
              children: <Widget>[
                Text('ยืนยันการลบข้อมูล กด ยืนยัน'),
              ],
            )),
            actions: <Widget>[
              TextButton(
                  onPressed: () {
                    del_data(id);
                    Navigator.of(context).pop();
                  },
                  child: Text('ยืนยัน')),
            ],
          );
        });
  }

  void add_data() async {
    Map data = {
      'name': _nameController.text,
      'email': _emailController.text,
      'phone': _phoneController.text,
      'address': _addressController.text,
      'weight': _weightController.text,
      'height': _heightController.text
    };
    var body = jsonEncode(data);
    var response = await http.post(Uri.http('10.0.2.2:8080', 'create'),
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: body);
    print("Response status: ${response.statusCode}");
    print("Response body: ${response.body}");
    listData();
  }

  void del_data(int id) async {
    var response = await http.delete(Uri.http('10.0.2.2:8080', 'delete/$id'),
        headers: {
          "Content-Type": "application/json; charset=UTF-8",
          "Accept": "application/json"
        });
    print("Response status: ${response.statusCode}");
    print("Response body: ${response.body}");
    listData();
  }

  Future<void> _showedit(Map data) async {
    _nameController.text = data['name'];
    _emailController.text = data['email'];
    _phoneController.text = data['phone'];
    _addressController.text = data['address'];
    _weightController.text = data['weight'].toString();
    _heightController.text = data['height'].toString();
    return showDialog<void>(
        barrierDismissible: false,
        context: context,
        builder: (BuildContext context) {
          return AlertDialog(
            title: const Text('ทดสอบการ Edit'),
            content: SingleChildScrollView(
                child: ListBody(
              children: <Widget>[
                TextField(
                  controller: _nameController,
                  decoration: const InputDecoration(
                      labelText: 'Name', hintText: "Enter emp Name"),
                ),
                TextField(
                  controller: _emailController,
                  decoration: const InputDecoration(
                      labelText: 'Email', hintText: "Enter emp Email"),
                ),
                TextField(
                  controller: _phoneController,
                  decoration: const InputDecoration(
                      labelText: 'Phone', hintText: "Enter emp Phone"),
                ),
                TextField(
                  controller: _addressController,
                  decoration: const InputDecoration(
                      labelText: 'Address', hintText: "Enter emp Address"),
                ),
                TextField(
                  controller: _weightController,
                  decoration: const InputDecoration(
                      labelText: 'Weight', hintText: "Enter emp Weight"),
                ),
                TextField(
                  controller: _heightController,
                  decoration: const InputDecoration(
                      labelText: 'Height', hintText: "Enter emp Height"),
                ),
                const Text('ปรับปรุงข้อมูลให้เรียบร้อยแล้วกด ยืนยัน'),
              ],
            )),
            actions: <Widget>[
              TextButton(
                  onPressed: () {
                    edit_data(data['id']);
                    Navigator.of(context).pop();
                  },
                  child: Text('ยืนยัน')),
            ],
          );
        });
  }

  void edit_data(id) async {
    Map data = {
      'id': id,
      'name': _nameController.text,
      'email': _emailController.text,
      'phone': _phoneController.text,
      'address': _addressController.text,
      'weight': double.tryParse(_weightController.text),
      'height': double.tryParse(_heightController.text)
    };
    
    // Debug print to see the data being sent
    print("Sending data to server: $data");
    
    var body = jsonEncode(data);
    print("Encoded JSON: $body");
    
    try {
      var response = await http.put(Uri.http('10.0.2.2:8080', 'update/$id'),
          headers: {
            "Content-Type": "application/json; charset=UTF-8",
          },
          body: body);
          
      print("Response status: ${response.statusCode}");
      print("Response body: ${response.body}");
      
      if (response.statusCode == 500) {
        print("Server error details: ${response.body}");
      }
      
      listData();
    } catch (e) {
      print("Error during update: $e");
    }
  }
  String calBmi(weight,height) {
    double weightfloat = double.tryParse(weight.toString()) ?? 0.0;
    double heightfloat = double.tryParse(height.toString()) ?? 0.0;
    double bmi = weightfloat / ((heightfloat / 100) * (heightfloat / 100));
    return bmi.toStringAsFixed(2);
  }
  String calBmitype(bmi) {
    double bmifloat = double.tryParse(bmi.toString()) ?? 0.0;
    if (bmifloat < 18.5) {
      return 'Underweight';
    } else if (bmifloat < 22.9) {
      return 'Normal';
    } else if (bmifloat < 24.9) {
      return 'Risk to Overweight';
    } else if (bmifloat < 29.9) {
      return 'Overweight';
    } else {
      return 'Obesity';
    }
  }
  String bmitypetoImage(bmi_type){
    if (bmi_type == "Underweight"){
      return "assets/images/bmi-1.png";
    }
    else if (bmi_type == "Normal"){
      return "assets/images/bmi-2.png";
    }
    else if (bmi_type == "Risk to Overweight"){
      return "assets/images/bmi-3.png";
    }
    else if (bmi_type == "Overweight"){
      return "assets/images/bmi-4.png";
    }
    else{
      return "assets/images/bmi-5.png";
    }
}
String toBenormal(weight,height){
  late double weighttonormal;
  late double diff;
  double nowbmi = weight / ((height/100)*(height/100));
  if (nowbmi < 18.5){
    weighttonormal = 18.5*height*height/10000;
    diff = weighttonormal - weight;
    diff = double.parse((diff).toStringAsFixed(2));
    return "You need to gain atleast ${diff} kg to be Normal";
  }
  else if (nowbmi >= 22.9){
    weighttonormal = 22.9*height*height/10000;
    diff = weight - weighttonormal;
    diff = double.parse((diff).toStringAsFixed(2));
    return "You need to lose atleast ${diff} kg to be Normal";
  }
  else{
    return "Good Health";
  }
}
}
