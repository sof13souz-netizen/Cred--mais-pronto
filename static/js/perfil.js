// Espera o HTML ser carregado antes de procurar os elementos.
document.addEventListener("DOMContentLoaded", function () {

    // Localiza o formulário de edição pessoal.
    const formulario = document.getElementById("form-editar-perfil");

    // Localiza o campo da nova senha.
    const campoNovaSenha = document.getElementById("nova_senha");

    // Localiza o espaço onde serão exibidas mensagens.
    const mensagem = document.getElementById("mensagem-js");

    // Interrompe a execução se os elementos não existirem.
    if (!formulario || !campoNovaSenha || !mensagem) {
        return;
    }

    // Verifica os dados antes de enviar o formulário.
    formulario.addEventListener("submit", function (evento) {

        // Limpa a mensagem anterior.
        mensagem.textContent = "";
        mensagem.className = "mensagem-js";

        // Obtém os valores dos campos.
        const nome = document.getElementById("nome").value.trim();
        const email = document.getElementById("email").value.trim();
        const senhaAtual = document.getElementById("senha_atual").value;
        const novaSenha = campoNovaSenha.value;

        // Confere se os campos obrigatórios foram preenchidos.
        if (!nome || !email || !senhaAtual) {

            evento.preventDefault();

            mensagem.textContent =
                "Preencha nome, e-mail e senha atual.";
            mensagem.classList.add("erro");

            return;
        }

        // Se a nova senha estiver vazia, não é necessário validá-la.
        // O Python permitirá a alteração somente do nome e do e-mail.
        if (novaSenha === "") {
            return;
        }

        // Verifica se existe pelo menos uma letra minúscula.
        const temMinuscula = /[a-z]/.test(novaSenha);

        // Verifica se existe pelo menos uma letra maiúscula.
        const temMaiuscula = /[A-Z]/.test(novaSenha);

        // Verifica se existe pelo menos um número.
        const temNumero = /[0-9]/.test(novaSenha);

        // Verifica se existe pelo menos um caractere especial.
        const temSimbolo = /[^A-Za-z0-9]/.test(novaSenha);

        // Confere se a senha possui oito caracteres ou mais.
        const tamanhoValido = novaSenha.length >= 8;

        // Bloqueia o envio caso a nova senha não atenda às regras.
        if (
            !tamanhoValido ||
            !temMinuscula ||
            !temMaiuscula ||
            !temNumero ||
            !temSimbolo
        ) {

            evento.preventDefault();

            mensagem.textContent =
                "A nova senha precisa ter pelo menos 8 caracteres, " +
                "uma letra maiúscula, uma minúscula, um número e um símbolo.";

            mensagem.classList.add("erro");
        }

        // Se estiver válida, o navegador envia o formulário ao Flask.
        // A validação definitiva também é feita no Python.
    });
});