from flask import Flask, render_template, redirect, request, flash, url_for, session, send_from_directory
import fdb
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("CREDMAIS_SECRET_KEY", "troque-esta-chave-em-producao-credmais")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

host = "localhost"
database = os.environ.get("CREDMAIS_DB_PATH", os.path.join(app.root_path, "BANCO.FDB"))
user = "SYSDBA"
password = "sysdba"


def conectar_banco():
    return fdb.connect(
        host=host,
        database=database,
        user=user,
        password=password
    )


def validar_senha(senha):

    if len(senha) < 8:
        return False

    tem_maiuscula = False
    tem_minuscula = False
    tem_numero = False
    tem_especial = False

    for caractere in senha:

        if caractere.isupper():
            tem_maiuscula = True

        elif caractere.islower():
            tem_minuscula = True

        elif caractere.isdigit():
            tem_numero = True

        else:
            tem_especial = True

    return ( tem_maiuscula and tem_minuscula and tem_numero and tem_especial)


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/logo")
def logo():
    return send_from_directory( os.path.join(app.root_path, "static/uploads"), "logo.png")


@app.route("/fundo")
def fundo():
    return send_from_directory( os.path.join(app.root_path, "static/uploads"), "fundo.png" )


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":

        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not nome or not email or not senha:
            flash("Preencha todos os campos.")
            return render_template("cadastro_usuario.html")

        if not validar_senha(senha):
            flash( "A senha deve ter no mínimo 8 caracteres, " "uma letra maiúscula, uma letra minúscula, " "um número e um caractere especial.")
            return render_template("cadastro_usuario.html")

        conexao = None
        cursor = None

        try:

            conexao = conectar_banco()
            cursor = conexao.cursor()

            cursor.execute(
                """
                SELECT ID_USUARIO
                FROM USUARIO
                WHERE EMAIL = ?
                """,
                (email,)
            )

            usuario_existente = cursor.fetchone()

            if usuario_existente:
                flash("Este e-mail já está cadastrado.")
                return render_template("cadastro_usuario.html")

            senha_criptografada = generate_password_hash(senha)

            cursor.execute(
                """
                INSERT INTO USUARIO
                (
                    NOME,
                    EMAIL,
                    SENHA,
                    TIPO,
                    ATIVO,
                    TENTATIVAS_LOGIN,
                    BLOQUEADO
                ) VALUES (?,?,?,?,?, ?,?) """,
                (nome,email,senha_criptografada,1,True,0,False))

            conexao.commit()

            cursor.execute(
                """
                SELECT ID_USUARIO
                FROM USUARIO
                WHERE EMAIL = ?
                """,
                (email,)
            )

            usuario = cursor.fetchone()

            if not usuario:
                raise Exception("Usuário não foi encontrado após o cadastro.")

            id_usuario = usuario[0]

            cursor.execute(
                """
                INSERT INTO HISTORICO_SENHA
                (
                    SENHA,
                    ID_USUARIO,
                    DATA_ALTERACAO
                )
                VALUES
                (
                    ?,
                    ?,
                    CURRENT_TIMESTAMP
                )
                """,
                (
                    senha_criptografada,
                    id_usuario
                )
            )

            conexao.commit()

            flash("Cadastro realizado com sucesso!")

            return redirect(url_for("inicio"))

        except Exception as erro:

            if conexao:
                conexao.rollback()

            print("ERRO AO SALVAR CADASTRO:")
            print(erro)

            flash("Erro ao salvar o cadastro.")

            return render_template("cadastro_usuario.html")

        finally:

            if cursor:
                cursor.close()

            if conexao:
                conexao.close()

    return render_template("cadastro_usuario.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if email == "" or senha == "":
            flash("Preencha o e-mail e a senha.")
            return render_template("login.html")

        conexao = None
        cursor = None

        try:

            conexao = conectar_banco()
            cursor = conexao.cursor()

            cursor.execute(
                """
                SELECT
                    ID_USUARIO,
                    NOME,
                    EMAIL,
                    SENHA,
                    TIPO,
                    ATIVO,
                    TENTATIVAS_LOGIN,
                    BLOQUEADO
                FROM USUARIO
                WHERE EMAIL = ?
                """,
                (email,)
            )

            usuario = cursor.fetchone()

            if usuario is None:
                flash("E-mail ou senha incorretos.")
                return render_template("login.html")

            id_usuario = usuario[0]
            nome_usuario = usuario[1]
            email_usuario = usuario[2]
            senha_banco = usuario[3]
            tipo_usuario = usuario[4]
            ativo = usuario[5]
            tentativas_login = usuario[6]
            bloqueado = usuario[7]

            if isinstance(tentativas_login, str):
                tentativas_login = int(tentativas_login)

            if ativo is False or ativo == 0:
                flash("Sua conta está inativa. " "Não é possível realizar o login.")
                return render_template("login.html")

            if bloqueado is True or bloqueado == 1:
                flash("Sua conta está bloqueada por excesso de tentativas.")
                return render_template("login.html")

            if not senha_banco:
                flash("Este usuário não possui uma senha cadastrada.")
                return render_template("login.html")

            senha_correta = check_password_hash(
                senha_banco,senha)

            if not senha_correta:

                tentativas_login += 1

                if tentativas_login >= 3:

                    cursor.execute(
                        """
                        UPDATE USUARIO
                        SET
                            TENTATIVAS_LOGIN = ?,
                            BLOQUEADO = ?
                        WHERE ID_USUARIO = ?
                        """,
                        (
                            tentativas_login,
                            True,
                            id_usuario
                        )
                    )

                    conexao.commit()

                    flash("Você atingiu o limite de 3 tentativas. " "Sua conta foi bloqueada.")

                    return render_template("login.html")

                cursor.execute(
                    """
                    UPDATE USUARIO
                    SET TENTATIVAS_LOGIN = ?
                    WHERE ID_USUARIO = ?
                    """,
                    (
                        tentativas_login,
                        id_usuario
                    )
                )

                conexao.commit()

                tentativas_restantes = 3 - tentativas_login

                if tentativas_restantes == 1:

                    flash("E-mail ou senha incorretos. ""Atenção: você tem apenas 1 tentativa restante. " "Depois disso, sua conta será bloqueada.")

                else:
                    flash("E-mail ou senha incorretos. " "Você ainda possui "+ str(tentativas_restantes)+ " tentativas.")

                return render_template("login.html")

            cursor.execute(
                """
                UPDATE USUARIO
                SET
                    TENTATIVAS_LOGIN = ?,
                    BLOQUEADO = ?
                WHERE ID_USUARIO = ?
                """,
                (
                    0,
                    False,
                    id_usuario
                )
            )

            conexao.commit()

            session.clear()

            session["usuario_id"] = id_usuario
            session["usuario_nome"] = nome_usuario
            session["usuario_email"] = email_usuario
            session["usuario_tipo"] = tipo_usuario

            print("LOGIN CORRETO - REDIRECIONANDO")

            return redirect(url_for("sucesso"))

        except Exception as erro:

            print("ERRO NO LOGIN:")
            print(erro)

            flash("Erro ao realizar o login.")

            return render_template("login.html")

        finally:

            if cursor:
                cursor.close()

            if conexao:
                conexao.close()

    return render_template("login.html")


@app.route("/sucesso")
def sucesso():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    return render_template("sucesso.html")


@app.route("/sistema")
def sistema():

    if "usuario_id" not in session:
        return redirect(url_for("inicio"))

    return render_template("sistema.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("inicio"))

# --------------------------------------------------
# BUSCAR OS DADOS DO USUÁRIO
# --------------------------------------------------

def buscar_usuario(id_usuario):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        # O ponto de interrogação representa um valor recebido
        # separadamente, evitando montar a consulta com texto.
        cursor.execute(
            """
            SELECT ID_USUARIO, NOME, EMAIL, SENHA
            FROM USUARIO
            WHERE ID_USUARIO = ?
            """,
            (id_usuario,)
        )

        # Retorna os dados encontrados ou None se não existir.
        return cursor.fetchone()

    finally:
        # Fecha a conexão mesmo se ocorrer algum erro.
        conexao.close()


# --------------------------------------------------
# VERIFICAR SE O E-MAIL JÁ ESTÁ CADASTRADO
# --------------------------------------------------

def email_ja_existe(email, id_usuario):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        # Procura o e-mail em outro usuário.
        cursor.execute(
            """
            SELECT ID_USUARIO
            FROM USUARIO
            WHERE EMAIL = ?
              AND ID_USUARIO <> ?
            """,
            (email, id_usuario)
        )

        # Se encontrou um registro, o e-mail já está em uso.
        return cursor.fetchone() is not None

    finally:
        conexao.close()


# --------------------------------------------------
# BUSCAR AS TRÊS ÚLTIMAS SENHAS
# --------------------------------------------------

def buscar_ultimas_senhas(id_usuario):
    conexao = conectar_banco()

    try:
        cursor = conexao.cursor()

        # FIRST 3 retorna somente os três registros mais recentes.
        cursor.execute(
            """
            SELECT FIRST 3 SENHA
            FROM HISTORICO_SENHA
            WHERE ID_USUARIO = ?
            ORDER BY DATA_ALTERACAO DESC,
                     ID_HISTORICO_SENHA DESC
            """,
            (id_usuario,)
        )

        # Cria uma lista contendo os hashes das senhas anteriores.
        return [registro[0] for registro in cursor.fetchall()]

    finally:
        conexao.close()


# --------------------------------------------------
# ROTA PRINCIPAL: PÁGINA DE EDIÇÃO DE PERFIL
# --------------------------------------------------

@app.route("/perfil", methods=["GET", "POST"])
def perfil():

    # O perfil só pode ser acessado por usuário autenticado.
    if "usuario_id" not in session:
        flash("Faça login para acessar seu perfil.")
        return redirect(url_for("login"))
    id_usuario = session["usuario_id"]

    # GET acontece quando a página é aberta.
    if request.method == "GET":

        try:
            # Busca os dados atuais do usuário.
            usuario = buscar_usuario(id_usuario)

        except Exception:
            # Registra o erro no terminal para ajudar na correção.
            app.logger.exception("Erro ao consultar o banco.")

            flash(
                "Não foi possível conectar ao banco de dados.",
                "erro"
            )

            return render_template(
                "editar_perfil.html",
                nome="",
                email=""
            )

        # Verifica se o ID informado realmente existe.
        if usuario is None:
            flash("Usuário não encontrado. Confira o ID de teste.", "erro")

            return render_template( "editar_perfil.html", nome="", email="" )

        # Exibe o nome e o e-mail no formulário.
        # A senha nunca é enviada para o HTML.
        return render_template(
            "editar_perfil.html",
            nome=usuario[1] or "",
            email=usuario[2] or ""
        )

    # POST acontece quando o formulário é enviado.
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower().lower()
    senha_atual = request.form.get("senha_atual", "")
    nova_senha = request.form.get("nova_senha", "")

    # Verifica se os campos obrigatórios foram preenchidos.
    if not nome or not email or not senha_atual:
        flash("Preencha nome, e-mail e senha atual.","erro")
        return redirect(url_for("perfil"))

    # Verifica os limites definidos na tabela do banco.
    if len(nome) > 100 or len(email) > 100:
        flash("Nome e e-mail devem ter no máximo 100 caracteres.", "erro" )
        return redirect(url_for("perfil"))

    try:
        # Busca novamente o usuário antes de alterar seus dados.
        usuario = buscar_usuario(id_usuario)

        if usuario is None:
            flash("Usuário não encontrado.", "erro")
            return redirect(url_for("perfil"))

        # Recupera o hash da senha que está salva atualmente.
        hash_atual = usuario[3] or ""

        # Confere a senha digitada com o hash armazenado.
        if not check_password_hash(hash_atual, senha_atual):
            flash("A senha atual está incorreta.", "erro")
            return redirect(url_for("perfil"))

        # Impede que outro usuário utilize o mesmo e-mail.
        if email_ja_existe(email, id_usuario):
            flash("Este e-mail já está cadastrado.","erro")
            return redirect(url_for("perfil"))

        # Começa sem alterar a senha.
        novo_hash = None

        # Se o campo estiver preenchido, processa a nova senha.
        if nova_senha:

            # Verifica manualmente os requisitos de senha forte.
            # Não é necessária uma biblioteca adicional para essa regra.
            senha_forte = (
                len(nova_senha) >= 8
                and any(c.islower() for c in nova_senha)
                and any(c.isupper() for c in nova_senha)
                and any(c.isdigit() for c in nova_senha)
                and any(not c.isalnum() for c in nova_senha)
            )

            if not senha_forte:
                flash(
                    "A nova senha precisa ter 8 caracteres ou mais, "
                    "uma letra maiúscula, uma minúscula, um número "
                    "e um símbolo.",
                    "erro")

                return redirect(url_for("perfil"))

            # Busca as três senhas anteriores no histórico.
            senhas_anteriores = buscar_ultimas_senhas(id_usuario)

            # Também impede que a nova senha seja igual à atual.
            if check_password_hash(hash_atual, nova_senha):
                flash("A nova senha deve ser diferente da senha atual.","erro")

                return redirect(url_for("perfil"))

            # Compara a nova senha com cada hash do histórico.
            for senha_antiga in senhas_anteriores:

                if check_password_hash(senha_antiga, nova_senha):

                    flash("Não é permitido reutilizar as três últimas senhas.","erro")
                    return redirect(url_for("perfil"))

            # Gera um hash seguro da nova senha.
            # O hash não permite recuperar diretamente a senha original.
            novo_hash = generate_password_hash(nova_senha)

        # Abre uma conexão para realizar as alterações.
        conexao = conectar_banco()

        try:
            cursor = conexao.cursor()

            # Se existe uma nova senha, salva a senha anterior no histórico.
            if novo_hash is not None:

                cursor.execute(
                    """
                    INSERT INTO HISTORICO_SENHA
                        (SENHA, ID_USUARIO, DATA_ALTERACAO)
                    VALUES (?, ?, ?)
                    """,
                    (hash_atual, id_usuario, datetime.now())
                )

                # Atualiza os dados pessoais e o hash da senha.
                cursor.execute(
                    """
                    UPDATE USUARIO
                    SET NOME = ?,
                        EMAIL = ?,
                        SENHA = ?
                    WHERE ID_USUARIO = ?
                    """,
                    (nome, email, novo_hash, id_usuario)
                )

            else:
                # Sem nova senha, altera apenas nome e e-mail.
                cursor.execute(
                    """
                    UPDATE USUARIO
                    SET NOME = ?,
                        EMAIL = ?
                    WHERE ID_USUARIO = ?
                    """,
                    (nome, email, id_usuario)
                )

            # Confirma todas as alterações no banco.
            conexao.commit()

        except Exception:
            # Se houver erro, desfaz as alterações da transação.
            conexao.rollback()
            raise

        finally:
            # Fecha a conexão utilizada para salvar os dados.
            conexao.close()

        # Exibe uma mensagem após a atualização.
        flash(
            "Dados pessoais atualizados com sucesso!",
            "sucesso"
        )

        return redirect(url_for("perfil"))

    except Exception:
        # Registra os detalhes técnicos do erro no terminal.
        app.logger.exception("Erro ao atualizar o perfil.")

        flash(
            "Não foi possível salvar os dados. "
            "Confira a conexão e a estrutura do banco.",
            "erro"
        )

        return redirect(url_for("perfil"))




if __name__ == "__main__":
    app.run(debug=True)
