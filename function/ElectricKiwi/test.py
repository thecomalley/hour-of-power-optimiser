from electrickiwi import ElectricKiwi

ek       = ElectricKiwi()
token    = ek.at_token()

loaded = False
try:
    with open('ek_creds.txt') as f:
        email    = f.readline().strip()
        password = f.readline().strip()

    loaded = True
    print("Loaded Credentials: OK")
except:
    email    = input('EK Email: ')
    password = ek.password_hash(input('EK Password: '))

customer = ek.login(email, password)
print('Logged in: OK')

ek.set_hop_hour(20)

print(ek.get_hop_hour())
