import bcrypt

# Função para gerar o hash da senha
def hash_password(password: str) -> str:
    # Converte a senha para bytes e gera o hash
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

# Função para verificar a senha
def verify_password(password: str, hashed_password: str) -> bool:
    # Verifica se a senha corresponde ao hash armazenado
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))