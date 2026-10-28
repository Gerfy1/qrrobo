"""O olho sozinho: lê o bilhete e escreve a palavra.

Não procura o bloco. Q na janela encerra.
"""

from qrrobo import Robo

robo = Robo(conexao="nenhuma")


@robo.quando("FRENTE")
def frente():
    print("O bilhete diz FRENTE. Aqui entra o movimento de vocês.")


@robo.quando("DANCAR")
def dancar():
    print("O bilhete diz DANCAR. Aqui entra o movimento de vocês.")


robo.esperar()
