# Copie este arquivo para o Pybricks. Ele não faz parte do pip.
# O computador manda uma palavra. Vocês decidem o que ela faz.

from usys import stdin


def frente():
    # Escrevam aqui o movimento de FRENTE.
    print("FRENTE")


def dancar():
    # Escrevam aqui o movimento de DANCAR.
    print("DANCAR")


ACOES = {
    "FRENTE": frente,
    "DANCAR": dancar,
}

print("Esperando um bilhete.")

while True:
    linha = stdin.readline()
    if not linha:
        break

    comando = linha.strip().upper()
    print("Bloco recebeu:", comando)

    acao = ACOES.get(comando)
    if acao is not None:
        acao()
    elif comando == "SAIR":
        break
    else:
        print("Ainda não criamos esta palavra.")
