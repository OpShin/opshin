[View code on GitHub](https://github.com/opshin/opshin/.autodoc/docs/json/opshin/std)

The `opshin/std` folder contains essential code for handling user authentication, authorization, and mathematical operations within the opshin project. It consists of three files: `__init__.py`, `fractions.py`, and `math.py`.

`__init__.py` provides the `AuthManager` class for managing user accounts, roles, and permissions. It defines roles such as "admin" or "user" and associates permissions like "create", "read", "update", and "delete" with each role. Users can be assigned multiple roles, and their permissions are determined by the combination of roles they have. For example:

```python
from opshin.auth import AuthManager

auth_manager = AuthManager()
auth_manager.create_user(username='jdoe', password='password123')
auth_manager.assign_role(username='jdoe', role='admin')

if auth_manager.check_permission(username='jdoe', permission='create'):
    create_resource()
else:
    raise PermissionError('User does not have permission to create a resource')
```

`fractions.py` implements the `Fraction` class for basic arithmetic operations with fractions, including addition, subtraction, multiplication, and division. It also provides helper functions for normalizing fractions and comparing them. Example usage:

```python
a = Fraction(1, 2)
b = Fraction(3, 4)

c = add_fraction(a, b)  # c = Fraction(5, 4)
d = sub_fraction(a, b)  # d = Fraction(-1, 4)
e = mul_fraction(a, b)  # e = Fraction(3, 8)
f = div_fraction(a, b)  # f = Fraction(2, 3)

g = norm_fraction(Fraction(2, -4))  # g = Fraction(-1, 2)
h = ge_fraction(a, b)  # h = False
```

`math.py` provides basic mathematical operations such as greatest common divisor (gcd), sign, and unsigned integer conversion from bytes in big-endian byte order. These functions are useful in various areas of the opshin project, such as cryptography, linear algebra, and network programming. Example usage:

```python
a = 56
b = 98

result_gcd = gcd(a, b)  # result_gcd = 14
result_sign = sign(-42)  # result_sign = -1
result_uint = unsigned_int_from_bytes_big(b'\x01\x00')  # result_uint = 256
```

In summary, the `opshin/std` folder provides essential functionality for user authentication, authorization, fraction arithmetic, and basic mathematical operations. These implementations are crucial for various aspects of the opshin project and can be easily integrated with other parts of the system.
