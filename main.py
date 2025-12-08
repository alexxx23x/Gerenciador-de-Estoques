# ============================================================
#                           IMPORTAÇÕES
# ============================================================

import sqlite3          # Biblioteca para usar banco de dados SQLite (arquivo local)
from datetime import datetime  # Para registrar data/hora das operações
import hashlib          # Usado para criptografar senhas

# Nome do arquivo do banco de dados SQLite
DB_FILE = "estoque.db"

# Estoque mínimo para exibir alerta de "ESTOQUE BAIXO!"
LOW_STOCK_THRESHOLD = 5


# ============================================================
#      CONEXÃO COM O BANCO DE DADOS + CRIAÇÃO DAS TABELAS
# ============================================================

# Abre conexão com SQLite (arquivo local)
conn = sqlite3.connect(DB_FILE)

# Cursor é o "objeto que envia comandos SQL"
cursor = conn.cursor()

# ---------------------------- Tabela de produtos ----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID único e auto crescente
    nome TEXT NOT NULL,                    -- Nome do produto
    valor_venda REAL NOT NULL,             -- Preço de venda
    valor_custo REAL NOT NULL,             -- Custo de compra
    quantidade INTEGER NOT NULL,           -- Qtd no estoque
    peso REAL NOT NULL,                    -- Peso do produto
    marca TEXT                              -- Marca
)
""")

# ---------------------------- Tabela de vendas ----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER NOT NULL,           -- Chave estrangeira para produtos
    nome_produto TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    data TEXT NOT NULL,
    valor_unitario REAL NOT NULL,
    valor_total REAL NOT NULL,
    forma_pagamento TEXT NOT NULL,
    consumidor TEXT,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
)
""")

# ---------------------------- Tabela de clientes ----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    contato TEXT
)
""")

# ---------------------------- Tabela de fornecedores ----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS fornecedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    contato TEXT
)
""")

# ---------------------------- Tabela de movimentações ----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS movimentacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,                 -- entrada / saída / venda
    quantidade INTEGER NOT NULL,
    data TEXT NOT NULL,
    usuario TEXT,                       -- usuário logado que realizou a ação
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
)
""")

# ---------------------------- Tabela de usuários ----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,       -- nome único de usuário
    password_hash TEXT NOT NULL,         -- senha criptografada
    created_at TEXT NOT NULL             -- Data de criação
)
""")

# Salva alterações de criação
conn.commit()


# ============================================================
# INSERÇÃO DE PRODUTOS PADRÃO (EXECUTA APENAS NA PRIMEIRA VEZ)
# ============================================================

def inserir_dados_padrao():
    # Verifica se já tem produtos cadastrados
    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone()[0] == 0:

        # Lista de produtos iniciais
        produtos_padrao = [
            ("Arroz 5kg", 22.50, 15.00, 20, 5.0, "Tio João"),
            ("Feijão 1kg", 8.90, 5.00, 35, 1.0, "Kicaldo"),
            ("Macarrão 500g", 4.50, 2.50, 40, 0.5, "Adria"),
            ("Açúcar 1kg", 5.20, 3.00, 30, 1.0, "União"),
            ("Óleo 900ml", 7.80, 5.20, 25, 0.9, "Soya"),
            ("Café 500g", 12.90, 8.00, 15, 0.5, "Pilão"),
            ("Leite 1L", 4.10, 2.90, 50, 1.0, "Itambé"),
            ("Farinha 1kg", 6.00, 3.80, 28, 1.0, "Dona Benta"),
            ("Sal 1kg", 2.30, 1.00, 60, 1.0, "Cisne"),
            ("Bolacha 350g", 3.80, 2.00, 22, 0.35, "Marilan"),
        ]

        # Inserção múltipla de vários produtos de uma só vez
        cursor.executemany("""
            INSERT INTO produtos (nome, valor_venda, valor_custo, quantidade, peso, marca)
            VALUES (?, ?, ?, ?, ?, ?)
        """, produtos_padrao)

        conn.commit()
        print("10 produtos padrão inseridos!")

# Executa ao iniciar
inserir_dados_padrao()


# ============================================================
# FUNÇÕES UTILITÁRIAS DE INPUT (GARANTEM QUE VALORES SEJAM NÚMEROS)
# ============================================================

def pedir_int(txt, minimo=None):

    #Lê um número inteiro do usuário e valida.
    while True:
        try:
            v = int(input(txt))
            if minimo is not None and v < minimo:
                print(f"Digite um número >= {minimo}.")
                continue
            return v
        except:
            print("Valor inválido.")

def pedir_float(txt, minimo=None):

    #Igual ao pedir_int, mas para números com decimal.
    #Aceita vírgula, substitui por ponto.

    while True:
        try:
            v = float(input(txt).replace(",", "."))
            if minimo is not None and v < minimo:
                print(f"Digite um número >= {minimo}.")
                continue
            return v
        except:
            print("Valor inválido.")


# ============================================================
#                  SISTEMA DE SENHAS E LOGIN
# ============================================================

def pedir_senha(prompt="Senha: "):

    #Pede senha

    return input(prompt)

def hash_password(password: str) -> str:

    #Converte senha original em hash

    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def criar_usuario(username: str, password: str) -> bool:

    #Insere usuário no banco com senha criptografada.
    #Retorna False se username já existir.

    try:
        ph = hash_password(password)
        cursor.execute(
            "INSERT INTO usuarios (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, ph, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def validar_login(username: str, password: str) -> bool:

    #Verifica usuário e senha.

    ph = hash_password(password)
    cursor.execute("SELECT password_hash FROM usuarios WHERE username=?", (username,))
    row = cursor.fetchone()

    if not row:
        return False

    return ph == row[0]

def existe_usuario(username: str) -> bool:

    #Retorna True se o usuário já existir.

    cursor.execute("SELECT 1 FROM usuarios WHERE username=?", (username,))
    return cursor.fetchone() is not None


# ============================================================
#         LISTAGENS (PRODUTOS, VENDAS, MOVIMENTAÇÕES)
# ============================================================

def listar_produtos():

    #Exibe tabela completa de produtos.

    cursor.execute("SELECT * FROM produtos ORDER BY id")
    lista = cursor.fetchall()

    if not lista:
        print("Nenhum produto.")
        return

    print("\n" + "-"*98)
    print(f"{'ID':<3} | {'Nome':<25} | {'Venda':<8} | {'Custo':<8} | {'Qtd':<5} | {'Peso':<5} | {'Marca':<15} | ALERTA")
    print("-"*98)

    for p in lista:
        alerta = "ESTOQUE BAIXO!" if p[4] <= LOW_STOCK_THRESHOLD else ""
        print(f"{p[0]:<3} | {p[1]:<25} | R${p[2]:<7.2f} | R${p[3]:<7.2f} | {p[4]:<5} | {p[5]:<5} | {p[6]:<15} | {alerta}")

    print("-"*98)

def listar_vendas():

    #Lista o histórico de vendas registradas.

    cursor.execute("""
        SELECT id, nome_produto, quantidade, data, valor_unitario, valor_total, forma_pagamento, consumidor
        FROM vendas ORDER BY data DESC
    """)
    vendas = cursor.fetchall()

    if not vendas:
        print("Nenhuma venda registrada.")
        return

    print("\n" + "-"*110)
    print(f"{'ID':<4} | {'Produto':<25} | {'Qtd':<4} | {'Data':<19} | {'Unitário':<10} | {'Total':<10} | {'Pgto':<8} | Consumidor")
    print("-"*110)

    for v in vendas:
        print(f"{v[0]:<4} | {v[1]:<25} | {v[2]:<4} | {v[3]:<19} | R${v[4]:<10.2f} | R${v[5]:<10.2f} | {v[6]:<8} | {v[7]}")

    print("-"*110)

def listar_movimentacoes():

    #Exibe todas entradas/saídas de estoque.

    cursor.execute("""
        SELECT m.id, p.nome, m.tipo, m.quantidade, m.data, m.usuario
        FROM movimentacoes m
        JOIN produtos p ON p.id = m.produto_id
        ORDER BY m.data DESC
    """)
    movs = cursor.fetchall()

    if not movs:
        print("Nenhuma movimentação.")
        return

    print("\nMovimentações:")
    for m in movs:
        print(f"{m[0]} | {m[1]} | {m[2]} | {m[3]} un | {m[4]} | Usuário: {m[5] or 'N/A'}")


# ============================================================
#                      USUÁRIO LOGADO
# ============================================================

current_user = None

def prompt_usuario_default(msg="Usuário (opcional): "):

    #O usuário estiver logado, usado como padrão.

    global current_user
    if current_user:
        txt = input(f"{msg}[{current_user}] (Enter para usar): ").strip()
        return current_user if txt == "" else txt
    else:
        txt = input(msg).strip()
        return txt or None


# ============================================================
#                       CRUD DE PRODUTOS
# ============================================================

def adicionar_produto():

    #Cria um novo produto no sistema.

    nome = input("Nome: ")
    venda = pedir_float("Valor de venda: R$ ")
    custo = pedir_float("Valor de custo: R$ ")
    qtd = pedir_int("Quantidade inicial: ", 0)
    peso = pedir_float("Peso (kg): ", 0)
    marca = input("Marca: ")

    cursor.execute("""
        INSERT INTO produtos (nome, valor_venda, valor_custo, quantidade, peso, marca)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (nome, venda, custo, qtd, peso, marca))

    conn.commit()
    print("✔ Produto adicionado!")

def excluir_produto():

    #Remove produto do banco.

    listar_produtos()
    pid = pedir_int("ID para excluir: ", 1)
    cursor.execute("DELETE FROM produtos WHERE id=?", (pid,))
    conn.commit()
    print("✔ Produto excluído!")

def editar_produto():
    
    #Permite editar campos de um produto.

    listar_produtos()
    pid = pedir_int("ID do produto: ", 1)

    while True:
        print("\nEditar:")
        print("1 - Nome")
        print("2 - Valor venda")
        print("3 - Valor custo")
        print("4 - Quantidade")
        print("5 - Peso")
        print("6 - Marca")
        print("0 - Voltar")

        op = input("> ")

        if op == "1":
            novo = input("Novo nome: ")
            cursor.execute("UPDATE produtos SET nome=? WHERE id=?", (novo, pid))

        elif op == "2":
            novo = pedir_float("Novo valor de venda: ")
            cursor.execute("UPDATE produtos SET valor_venda=? WHERE id=?", (novo, pid))

        elif op == "3":
            novo = pedir_float("Novo valor de custo: ")
            cursor.execute("UPDATE produtos SET valor_custo=? WHERE id=?", (novo, pid))

        elif op == "4":
            novo = pedir_int("Nova quantidade: ", 0)
            cursor.execute("UPDATE produtos SET quantidade=? WHERE id=?", (novo, pid))

        elif op == "5":
            novo = pedir_float("Novo peso: ", 0)
            cursor.execute("UPDATE produtos SET peso=? WHERE id=?", (novo, pid))

        elif op == "6":
            novo = input("Nova marca: ")
            cursor.execute("UPDATE produtos SET marca=? WHERE id=?", (novo, pid))

        elif op == "0":
            break

        else:
            print("Inválido!")
            continue

        conn.commit()
        print("✔ Atualizado!")
        break


# ============================================================
#                   ENTRADA E SAÍDA DE ESTOQUE
# ============================================================

def entrada_estoque():

    #Adiciona quantidade ao estoque de um produto.
    #Registra movimentação.

    listar_produtos()
    pid = pedir_int("ID do produto (entrada): ", 1)
    qtd = pedir_int("Quantidade: ", 1)

    usuario = current_user

    cursor.execute("UPDATE produtos SET quantidade = quantidade + ? WHERE id=?", (qtd, pid))

    cursor.execute("""
        INSERT INTO movimentacoes (produto_id, tipo, quantidade, data, usuario)
        VALUES (?, 'entrada', ?, ?, ?)
    """, (pid, qtd, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), usuario))

    conn.commit()
    print(f"✔ Entrada registrada pelo usuário '{usuario}'.")


def saida_estoque():

    #Remove quantidade do estoque.
    #Registra movimentação.

    listar_produtos()
    pid = pedir_int("ID (saída): ", 1)
    qtd = pedir_int("Quantidade: ", 1)

    cursor.execute("SELECT quantidade FROM produtos WHERE id=?", (pid,))
    estoque = cursor.fetchone()

    if not estoque:
        print("Produto não encontrado.")
        return

    if qtd > estoque[0]:
        print("Estoque insuficiente.")
        return

    usuario = current_user

    cursor.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id=?", (qtd, pid))

    cursor.execute("""
        INSERT INTO movimentacoes (produto_id, tipo, quantidade, data, usuario)
        VALUES (?, 'saida', ?, ?, ?)
    """, (pid, qtd, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), usuario))

    conn.commit()
    print(f"✔ Saída registrada pelo usuário '{usuario}'.")


# ============================================================
#                   CLIENTES E FORNECEDORES
# ============================================================

def cadastrar_cliente():
    nome = input("Nome: ")
    contato = input("Contato: ")
    cursor.execute("INSERT INTO clientes (nome, contato) VALUES (?, ?)", (nome, contato))
    conn.commit()
    print("✔ Cliente cadastrado.")

def listar_clientes():
    cursor.execute("SELECT id, nome, contato FROM clientes")
    for c in cursor.fetchall():
        print(f"{c[0]} - {c[1]} ({c[2]})")

def cadastrar_fornecedor():
    nome = input("Nome: ")
    contato = input("Contato: ")
    cursor.execute("INSERT INTO fornecedores (nome, contato) VALUES (?, ?)", (nome, contato))
    conn.commit()
    print("✔ Fornecedor cadastrado.")

def listar_fornecedores():
    cursor.execute("SELECT id, nome, contato FROM fornecedores")
    for f in cursor.fetchall():
        print(f"{f[0]} - {f[1]} ({f[2]})")


# ============================================================
#                      REGISTRO DE VENDAS
# ============================================================

def registrar_venda():

    #Executa uma venda real:
    #reduz estoque
    #grava venda
    #grava movimentação "saida | venda"

    listar_produtos()

    pid = pedir_int("ID do produto: ", 1)

    cursor.execute("SELECT nome, valor_venda, quantidade FROM produtos WHERE id=?", (pid,))
    p = cursor.fetchone()

    if not p:
        print("Produto não encontrado.")
        return

    nome, valor, estoque = p

    print(f"Estoque: {estoque}, Valor: R$ {valor:.2f}")

    qtd = pedir_int("Quantidade vendida: ", 1)

    if qtd > estoque:
        print("Estoque insuficiente.")
        return

    forma = input("Forma de pagamento: ")
    consumidor = input("Nome do cliente/consumidor: ").strip()

    if consumidor == "":
        consumidor = "Cliente não informado"

    total = valor * qtd
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO vendas (produto_id, nome_produto, quantidade, data, valor_unitario, valor_total, forma_pagamento, consumidor)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (pid, nome, qtd, data, valor, total, forma, consumidor))

    cursor.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id=?", (qtd, pid))

    cursor.execute("""
        INSERT INTO movimentacoes (produto_id, tipo, quantidade, data, usuario)
        VALUES (?, 'saida - venda', ?, ?, ?)
    """, (pid, qtd, data, consumidor))

    conn.commit()
    print(f"✔ Venda registrada! Total: R$ {total:.2f}")


# ============================================================
#                    RELATÓRIO FINANCEIRO
# ============================================================

def relatorio_financeiro():

    #Calcula:
    #total vendido
    #custo total
    #lucro estimado

    cursor.execute("SELECT SUM(valor_total) FROM vendas")
    total = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT SUM(v.quantidade * p.valor_custo)
        FROM vendas v
        JOIN produtos p ON v.produto_id = p.id
    """)
    custo = cursor.fetchone()[0] or 0

    lucro = total - custo

    print("\n--- RELATÓRIO FINANCEIRO ---")
    print(f"Total vendido: R$ {total:.2f}")
    print(f"Custo: R$ {custo:.2f}")
    print(f"Lucro estimado: R$ {lucro:.2f}")


# ============================================================
#     MENUS (ESTOQUE / CLIENTES / RELATÓRIOS / PRINCIPAL)
# ============================================================

def menu_estoque():
    while True:
        print("\n--- ESTOQUE ---")
        print("1 - Criar produto")
        print("2 - Editar produto")
        print("3 - Excluir produto")
        print("4 - Entrada de estoque")
        print("5 - Saída de estoque")
        print("6 - Movimentações")
        print("0 - Voltar")

        op = input("> ")

        if op == "1": adicionar_produto()
        elif op == "2": editar_produto()
        elif op == "3": excluir_produto()
        elif op == "4": entrada_estoque()
        elif op == "5": saida_estoque()
        elif op == "6": listar_movimentacoes()
        elif op == "0": break
        else:
            print("Inválido!")

def menu_clientes():
    while True:
        print("\n--- CLIENTES / FORNECEDORES ---")
        print("1 - Cadastrar cliente")
        print("2 - Listar clientes")
        print("3 - Cadastrar fornecedor")
        print("4 - Listar fornecedores")
        print("0 - Voltar")

        op = input("> ")

        if op == "1": cadastrar_cliente()
        elif op == "2": listar_clientes()
        elif op == "3": cadastrar_fornecedor()
        elif op == "4": listar_fornecedores()
        elif op == "0": break
        else:
            print("Inválido!")

def menu_relatorios():
    while True:
        print("\n--- RELATÓRIOS ---")
        print("1 - Listar produtos")
        print("2 - Listar vendas")
        print("3 - Financeiro")
        print("0 - Voltar")

        op = input("> ")

        if op == "1": listar_produtos()
        elif op == "2": listar_vendas()
        elif op == "3": relatorio_financeiro()
        elif op == "0": break
        else:
            print("Inválido!")

def menu_principal():

    #Menu principal do sistema.

    while True:
        print("\n====== MENU ======")
        print("1 - Estoque")
        print("2 - Clientes/Fornecedores")
        print("3 - Registrar venda")
        print("4 - Relatórios")
        print("0 - Sair")

        op = input("> ")

        if op == "1": menu_estoque()
        elif op == "2": menu_clientes()
        elif op == "3": registrar_venda()
        elif op == "4": menu_relatorios()
        elif op == "0":
            print("Saindo...")
            break
        else:
            print("Inválido!")


# ============================================================
#              TELA INICIAL (LOGIN / REGISTRO)
# ============================================================

def tela_inicial():

    #Primeiro menu do sistema:
    #Login
    #Registrar conta
    #Sair

    global current_user

    while True:
        print("\n===== INÍCIO =====")
        print("1 - Login")
        print("2 - Registrar")
        print("3 - Sair")
        op = input("> ").strip()

        if op == "1":
            # LOGIN
            username = input("Username: ").strip()
            password = pedir_senha("Senha: ")

            if validar_login(username, password):
                current_user = username
                print(f"Login OK! Bem-vindo(a), {current_user}.")
                return
            else:
                print("Usuário ou senha incorretos.")

        elif op == "2":
            # REGISTRO
            username = input("Escolha um username: ").strip()

            if username == "":
                print("Username não pode ser vazio.")
                continue

            if existe_usuario(username):
                print("Esse username já existe.")
                continue

            s1 = pedir_senha("Senha: ")
            s2 = pedir_senha("Confirme a senha: ")

            if s1 != s2:
                print("As senhas não conferem.")
                continue

            if criar_usuario(username, s1):
                print("Usuário criado! Faça login.")
            else:
                print("Erro ao criar usuário.")

        elif op == "3":
            print("Saindo...")
            exit()

        else:
            print("Opção inválida.")


# ============================================================
#                   INICIALIZAÇÃO DO SISTEMA
# ============================================================

if __name__ == "__main__":
    tela_inicial()      # Pede login
    menu_principal()    # Abre sistema após login
    conn.close()        # Fecha o banco
